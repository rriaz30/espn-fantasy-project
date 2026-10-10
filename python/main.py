# imports
import os 
from pathlib import Path
from dotenv import load_dotenv

# project imports
import analyzer
import espn_data
import constants
import excel_util
import json_util
import pandas as pd

# Load .env from the same directory as main.py
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

league_id = int(os.environ["ESPN_LEAGUE_ID"])
year = int(os.environ["ESPN_YEAR"])
espn_s2 = os.environ["ESPN_S2"]
swid = os.environ["ESPN_SWID"]

# Assuming this script is in ESPN_API/python/
projectDir = Path(__file__).resolve().parent.parent
outputDir = projectDir / "output"
outputDir.mkdir(parents=True, exist_ok=True)

# init json file names
dataDir = Path(__file__).resolve().parent.parent / "data"
teamStatsJson = dataDir / "TeamStatsData.json"
scheduleJson = dataDir / "NflSchedule.json"
playersJson = dataDir / "Players.json"
fantasyTeamsJson = dataDir / "FantasyTeams.json"

# init data structs
allTeamStats = {}
nflSchedule = {}
players = []
fantasyTeams = {}

# init global var
currentWeek = 0

def clearConsole():
    os.system("cls")

def getWeeklyPositionReport(filePath, allTeamStats, option, weeksRequested = 0):

    if option == "allowed":
        optionStr = "Allowed"
    else: optionStr = "Scored"
    with pd.ExcelWriter(filePath, engine="openpyxl") as writer:

        for pos in constants.POSITIONS:
            ptsByWeek = espn_data.getPtsByWeek(pos, allTeamStats, option, weeksRequested)
            ptsByWeek = espn_data.addRunningRanks(ptsByWeek)
            df = excel_util.createPositionDataFrame(ptsByWeek)

            title = pos + f" - Points {optionStr} By Week"
            excel_util.writePositionSheet(writer, df, pos, title)

    print(f"Saved Excel file to {filePath}")

    # Color rankings in excel
    excel_util.colorRankings(filePath)

def getPosRanks(allTeamStats, nflSchedule, option):
    
    for team in constants.NFL_TEAMS:

        nflSchedule[team]["ranks"] = {}

        for pos in constants.POSITIONS:

            ptsByWeek = espn_data.getPtsByWeek(pos, allTeamStats, option)
            ptsByWeek = espn_data.addRunningRanks(ptsByWeek)

            nflSchedule[team]["ranks"][pos] = ptsByWeek[team][str(currentWeek)][2]

def loadJsonData():
    
    try:
        allTeamStats = json_util.loadDataFromJson(teamStatsJson)
        nflSchedule = json_util.loadDataFromJson(scheduleJson)
        players = json_util.loadDataFromJson(playersJson)
        fantasyTeams = json_util.loadDataFromJson(fantasyTeamsJson)

        return allTeamStats, nflSchedule, players, fantasyTeams
    except:
        print("Missing Data files. Fetch data first.")
        return {}, {}, [], {}

def fetchESPNdata():
    print(print("Fetching ESPN data... TODO"))

def generateReportsMenu():
    while True:

        print("\n===== ESPN Fantasy Analyzer =====")
        print  ("**** Generate Ranking Reports ***\n")
        print("1. Overall Points and Rankings")
        print("2. Weekly Points and Rankings")
        print("3. Filter Reports for most recent weeks")
        print("9. Return to Main Menu")

        choice = input("\nSelect an option: ")
        clearConsole()

        if choice == "1":
            print("Generate Overall Points and Rankings")
            optionStr = getPtsType()
            print("Generating report...")
            
            excelFile = outputDir / f"OverallReport-{optionStr}.xlsx"
            excel_util.closeExcelFile(excelFile)
            excel_util.printOverallPosRankToExcel(allTeamStats, excelFile, optionStr)
            os.startfile(excelFile)

        elif choice == "2":
            print("Generate Weekly Position Report")
            optionStr = getPtsType()
            print("Generating Weekly Position report...")
            
            excelFile = outputDir / f"WeeklyPosReport-{optionStr}.xlsx"
            excel_util.closeExcelFile(excelFile)
            getWeeklyPositionReport(excelFile, allTeamStats, optionStr)
            os.startfile(excelFile)

        elif choice == "3":
            print("Generate Weekly Points Report for Allowed or Scored filtered for most recent weeks")
            weeksReq = input("Enter how many past weeks of data you want to filter for:")
            weeksReq = int(weeksReq)
            optionStr = getPtsType()
            
            print("Generating Weekly Position report...")
            excelFile = outputDir / f"WeeklyPosReport-{optionStr}-past-{weeksReq}-weeks.xlsx"
            excel_util.closeExcelFile(excelFile)
            getWeeklyPositionReport(excelFile, allTeamStats, optionStr, weeksReq)
            os.startfile(excelFile)   

        elif choice == "9":
            print("Returning to Main Menu")
            break

        else:
            print("Invalid option. Try again.")

def schedulesMenu():
    schedCurrWeek = currentWeek + 1 # have to adjust for current week to make it the actual week
    while True:

        print("\n===== ESPN Fantasy Analyzer =====")
        print  ("****** Generate Schedules *******\n")
        print("\n*** Generate Schedules ***")
        print("1. See All NFL Schedule")
        print("2. Overlay NFL Schedule with Heat Map")
        print("9. Return to Main Menu")

        choice = input("\nSelect an option: ")
        clearConsole()

        if choice == "1":
            print("Printing Full NFL Team Schedule")
            excelFile = outputDir / "NflSchedule.xlsx"
            excel_util.closeExcelFile(excelFile)
            excel_util.scheduleToExcel(nflSchedule, excelFile, schedCurrWeek)
            os.startfile(excelFile)

        elif choice == "2":
            print("Generate NFL Schedule with Positional Heat Map")
            posTag = getPosInput()
            optionStr = getPtsType()

            if posTag == "D/ST":
                pos = "DEF"
            else: pos = posTag

            print("Calculating...")
            getPosRanks(allTeamStats, nflSchedule, optionStr)
            posFileName = pos + "-ColorNflSchedule.xlsx"
            excelFile = outputDir / posFileName
            excel_util.closeExcelFile(excelFile)
            excel_util.scheduleToExcel(nflSchedule, excelFile, schedCurrWeek)
            excel_util.colorScheduleByPosition(nflSchedule, excelFile, posTag, schedCurrWeek)

            print("Printing NFL Schedule with Positional Heat Map for Current Week for",pos)
            os.startfile(excelFile)

        elif choice == "9":
            print("Returning to Main Menu")
            break

        else:
            print("Invalid option. Try again.")


################################################################################################
################################################################################################
################################################################################################

def main():
    global allTeamStats, nflSchedule, players, fantasyTeams, currentWeek

    print("Checking for saved data")
    allTeamStats, nflSchedule, players, fantasyTeams = loadJsonData()
    currentWeek = len(allTeamStats['ARI']['weeks']) - 1

    # check if data has been loaded
    while True:
        dataValid = checkLoadedData(allTeamStats)
        if (dataValid == False):
            while dataValid == False:
                print("No Data loaded. Either fetch ESPN data(1) or load from Json file(2)")
                dataInput = input("Select an option:")
                if dataInput == "1":
                    fetchESPNdata()
                elif dataInput == "2":
                    print("Loading saved data...")
                    allTeamStats, nflSchedule, players, fantasyTeams = loadJsonData()
                else: print("Invalid position selected. Try again.")
                dataValid = checkLoadedData(allTeamStats)

        # data exists, enter main loop
        print("\n===== ESPN Fantasy Analyzer =====")
        print  ("=========== Main Menu ===========")
        print("1. Fetch ESPN data")
        print("2. Generate Points/Rank Reports")
        print("3. Generate Schedules")
        print("4. Player Analyzer WIP")
        print("9. Exit")
        
        choice = input("\nSelect an option: ")
        clearConsole()

        if choice == "1":
            print("Fetching ESPN data...")
            # first reset data structs
            allTeamStats = {}
            nflSchedule = {}
            players = []
            fantasyTeams = {}

            allTeamStats = espn_data.fetchNflData(league_id, year, espn_s2, swid, nflSchedule, players, fantasyTeams)
            dataDir = Path(__file__).resolve().parent.parent / "data"
            dataDir.mkdir(parents=True, exist_ok=True)
            json_util.saveDataToJson(allTeamStats, teamStatsJson)
            json_util.saveDataToJson(nflSchedule, dataDir / scheduleJson)
            json_util.saveDataToJson(players, dataDir / playersJson)
            json_util.saveDataToJson(fantasyTeams, dataDir / fantasyTeamsJson)

        elif choice == "2":
            generateReportsMenu()       

        elif choice == "3":
            schedulesMenu()

        elif choice == "7":
            print("Get free agents available vs bottom rank opponents")
            print(len(players))
            defFree = {}
            defFreeTop10 = []
            defFreeOpp = {}
            for p in players:
                if p["position"] == "D/ST" and p["onTeamId"] == 0:
                    print(p["name"])
                    defFree[p["proTeam"]] = p

                    # find curr opp
                    schedcurrWeek = currentWeek + 1
                    if ((str(schedcurrWeek)) not in p["schedule"]): continue
                    defFreeOpp[p["schedule"][str(schedcurrWeek)]["team"]] = p["proTeam"]

            # find best def pts allowed ranks
            ptsByWeek = espn_data.getPtsByWeek("D/ST", allTeamStats, option="allowed")
            ptsByWeek = espn_data.addRunningRanks(ptsByWeek)

            
            for team, week in ptsByWeek.items():
                if week[str(currentWeek)][2] <= 16 and team in defFreeOpp:
                    faTeam = defFreeOpp[team]
                    print(f"{team} ranked: {week[str(currentWeek)][2]} vs FA team: {faTeam} ranked: {defFree[faTeam]["posRank"]}")
                    print(f"")
            ### need to finish. stopped at able to see def fa left and their rank and opp rank

        elif choice == "8":

            analyzer.rankFAandMyTeamPlayerVsCurrOppWIP(allTeamStats, players, nflSchedule, currentWeek)
            

        elif choice == "9":
            print("Goodbye!")
            break

        else:
            print("Invalid option. Try again.")

################################################################################################
################################################################################################
################################################################################################

# helper functions
def getPtsType():

    print("Allowed = 1\nScored = 2")
    validInput = False
    while validInput == False:
        option = input("\nSelect an option: ")
        if option == str(1):
            optionStr = "allowed"
            validInput = True
        elif option == str(2):
            optionStr = "scored"
            validInput = True
        else: print("Invalid position selected. Try again.")

    return optionStr

def getPosInput():
    
    print("Available Positions: QB, RB, WR, TE, K, DEF")
    validInput = False
    while validInput == False:
        pos = input("\nSelect a Position: ")
        if pos == "DEF":
            posTag = "D/ST"
        else: posTag = pos
        if posTag in constants.POSITIONS:
            validInput = True
        else: print("Invalid position selected. Try again.")

    return posTag

def checkLoadedData(allTeamStats):
    if not allTeamStats:
        print("No data has been loaded yet. Load data and try again.")
        return False
    return True

if __name__ == "__main__":
    main()

