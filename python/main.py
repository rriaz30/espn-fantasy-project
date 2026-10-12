# imports
import os 
from pathlib import Path
from dotenv import load_dotenv

# project imports
import analyzer
import espn_data
import constants
import excel_util
import player
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

        if allTeamStats:
            print("Data loaded successfully")

        global currentWeek
        currentWeek = len(allTeamStats['ARI']['weeks']) - 1

        return allTeamStats, nflSchedule, players, fantasyTeams
    except:
        print("Missing Data files. Fetch data first.")
        return {}, {}, [], {}

def fetchESPNdata():

    global allTeamStats, nflSchedule, players, fantasyTeams, currentWeek

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

    global currentWeek
    currentWeek = len(allTeamStats['ARI']['weeks']) - 1

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
            if optionStr == "back": continue
            print("Generating report...")
            
            excelFile = outputDir / f"OverallReport-{optionStr}.xlsx"
            excel_util.closeExcelFile(excelFile)
            excel_util.printOverallPosRankToExcel(allTeamStats, excelFile, optionStr)
            os.startfile(excelFile)

        elif choice == "2":
            print("Generate Weekly Position Report")
            optionStr = getPtsType()
            if optionStr == "back": continue
            print("Generating Weekly Position report...")
            
            excelFile = outputDir / f"WeeklyPosReport-{optionStr}.xlsx"
            excel_util.closeExcelFile(excelFile)
            getWeeklyPositionReport(excelFile, allTeamStats, optionStr)
            os.startfile(excelFile)

        elif choice == "3":
            print("Generate Weekly Points Report for Allowed or Scored filtered for most recent weeks")
            weeksReq = input("Enter how many past weeks of data you want to filter for:")
            if weeksReq == "b": continue
            weeksReq = int(weeksReq)
            optionStr = getPtsType()
            if optionStr == "back": continue
            
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
            if posTag == "back": continue
            optionStr = getPtsType()
            if optionStr == "back": continue

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

    print("Current Week:", currentWeek + 1)
    print("Data based off week:", currentWeek)

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
        print  ("=================================\n")
        print("1. Fetch ESPN data")
        print("2. Generate Points/Rank Reports")
        print("3. Generate Schedules")
        print(f"4. Get FA Available vs Bottom Opponents for week {currentWeek+1} WIP")
        print("5. Player Analyzer WIP")
        print("6. Player Search")
        print("9. Exit")
        
        choice = input("\nSelect an option: ")
        clearConsole()

        if choice == "1":
            fetchESPNdata()
            allTeamStats, nflSchedule, players, fantasyTeams = loadJsonData()

        elif choice == "2":
            generateReportsMenu()       

        elif choice == "3":
            schedulesMenu()

        elif choice == "4":
            # WIP team analyzer
            print("WIP Team Analyzer")


        elif choice == "5":
            playersList, currRanks, ptThreshold, pos = analyzer.rankFAandMyTeamPlayerVsCurrOppWIP(allTeamStats, players, nflSchedule, currentWeek)
            
            excelFile = outputDir / f"WeightedScores-{pos}-week-{currentWeek+1}.xlsx"
            excel_util.closeExcelFile(excelFile)
            excel_util.printWeightedScoresToExcel(
                playersList,
                currRanks,
                excelFile,
                ptThreshold
            )

            os.startfile(excelFile)

        elif choice == "6":
            print("WIP Player search")
            print("Populating players list")
            playersList = []
            for p in players:
                if p["stats"]["0"]["avg_points"] >= 5:
                    playersList.append(p)

            userInput = input("Enter name: ")
            if not userInput:
                continue
            splitName = True
            if " " in userInput:
                splitName = False
            userInput = userInput.strip().lower()
                
            threshold = 0.7
            playerFound = False
            matchList = []

            for p in playersList:

                playerName = p["name"]

                if splitName == True:
                    firstName, *lastName = playerName.split()
                    lastName = " ".join(lastName)

                    firstMatchPct = matchName(userInput, firstName)
                    lastMatchPct = matchName(userInput, lastName)

                    matchPct = max(firstMatchPct, lastMatchPct)
                else:

                    matchPct = matchName(userInput, playerName)
          
                if matchPct > threshold:
                    matchList.append((p, matchPct))
                    playerFound = True

            if (not playerFound):
                print("Sorry player not found")
                continue

            matchList.sort(key=lambda x: x[1], reverse=True)

            index = 1
            print("\nFound the following players: ")
            if matchList:
                for playerData, accuracy in matchList:
                    print(f"({index}) {playerData["name"]}: \t{accuracy:.1%}")  
                    index += 1

            pick = input("\nSelect a player by index: ")  

            p = player.Player(matchList[int(pick)-1][0])
            
            while True:
                print(f"\nSelected {p.name}")
                print("(1) Points for specfic week")
                print("(2) Avg points")
                opt = input("Option: ")

                if opt == "1":
                    week = input("\nEnter week: ")
                    print (f"Week {week} - {p.getPtsForWeek(week)}")

                elif opt == "2":
                    start = input("\nEnter start week: ")
                    end = input("Enter end week: ")
                    if not start: start = 1
                    if not end: end = currentWeek
                    avgPts, played = p.getAvgPts(int(start), int(end))
                    
                    print(f"Avg points from weeks {start} to {end}: {avgPts}")
                    print(f"Played in {played} games")

                elif opt == "9": break

            

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

    print("Allowed = 1\nScored = 2\nGo Back = b")
    while True:
        option = input("\nSelect an option: ")
        if option == str(1):
            optionStr = "allowed"
            break
        elif option == str(2):
            optionStr = "scored"
            break
        elif option == "b":
            optionStr = "back"
            break
        else: print("Invalid position selected. Try again.")

    return optionStr

def getPosInput():
    
    print("Available Positions: QB, RB, WR, TE, K, DEF")
    while True:
        pos = input("\nSelect a Position or Go Back(b): ")
        if pos == "b":
            posTag = "back"
            break
        if pos == "DEF":
            posTag = "D/ST"
        else: posTag = pos
        if posTag in constants.POSITIONS:
            break
        else: print("Invalid position selected. Try again.")

    return posTag

def matchName(userInput, playerName):

    playerName = playerName.strip().lower()
    match = 0
    error = 0
    i = 0
    j = playerName.find(userInput[i])
    if j == -1: return 0
    while i < len(userInput) and j < len(playerName):

        if (userInput[i] == playerName[j]):
            match +=1
        elif ((len(playerName) > j+1) and (userInput[i] == playerName[j+1])):
            match +=1
            error +=1
            j = j+1
        elif ((len(userInput) > i+1) and (userInput[i+1] == playerName[j])):
            match +=1
            error +=1
            i = i+1
        else:
            error += 1

        if error > 5:
            match = 0
            break

        i += 1
        j += 1

    matchPct = match / len(userInput) 
    return matchPct

def checkLoadedData(allTeamStats):
    if not allTeamStats:
        print("No data has been loaded yet. Load data and try again.")
        return False
    return True

if __name__ == "__main__":
    main()

