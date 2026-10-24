# imports
import os 
from pathlib import Path
from dotenv import load_dotenv

# project imports
import analyzer
import espn_data
import constants
import config
import excel_util
import player
import proTeam
import json_util
import pandas as pd
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(filename)s:%(lineno)d - %(funcName)s - %(levelname)s - %(message)s"
)

# Load .env from the same directory as main.py
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

league_id = int(os.environ["ESPN_LEAGUE_ID"])
year = int(os.environ["ESPN_YEAR"])
espn_s2 = os.environ["ESPN_S2"]
swid = os.environ["ESPN_SWID"]

# output dir loc
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
proTeams = {}

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

            nflSchedule[team]["ranks"][pos] = ptsByWeek[team][str(config.currDataWeek)][2]

def loadJsonData():
    
    try:
        allTeamStats = json_util.loadDataFromJson(teamStatsJson)
        nflSchedule = json_util.loadDataFromJson(scheduleJson)
        players = json_util.loadDataFromJson(playersJson)
        fantasyTeams = json_util.loadDataFromJson(fantasyTeamsJson)

        if allTeamStats:
            print("Data loaded successfully")

        config.currDataWeek = len(allTeamStats['ARI']['weeks'])
        config.currLiveWeek = config.currDataWeek + 1

        return allTeamStats, nflSchedule, players, fantasyTeams
    except:
        print("Missing Data files. Fetch data first.")
        return {}, {}, [], {}

def fetchESPNdata():

    global allTeamStats, nflSchedule, players, fantasyTeams

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
            weeksReq = input("Enter trailing weeks: ")
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

    schedCurrWeek = config.currLiveWeek

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
    global allTeamStats, nflSchedule, players, fantasyTeams, proTeams

    print("Checking for saved data")
    allTeamStats, nflSchedule, players, fantasyTeams = loadJsonData()

    # check if data has been loaded
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

    for team in constants.NFL_TEAMS:
        proTeams[team] = proTeam.ProTeam(allTeamStats[team])

    print("Current Week:", config.currLiveWeek)
    print("Data based off week:", config.currDataWeek)
    
    while True:

        # data exists, enter main loop
        print("\n===== ESPN Fantasy Analyzer =====")
        print  ("=========== Main Menu ===========")
        print  ("=================================\n")
        print("1. Fetch ESPN data")
        print("2. Generate Points/Rank Reports")
        print("3. Generate Schedules")
        print("4. WIP - Team Analyzer - not started")
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
            # experiment - calc 'real' def rank, maybe this could lead to more 
            print("Generate Best Available FA (WIP algo)")
            print("Available Positions: QB, RB, WR, TE, K, DEF")
            validInput = False
            while validInput == False:
                posInput = input("\nSelect a Position: ")
                if posInput == "DEF":
                    pos = "D/ST"
                elif posInput == "b" or posInput == "9": break
                else: pos = posInput
                if pos in constants.POSITIONS:
                    validInput = True
                else: print("Invalid position selected. Try again.")

            if posInput == "b" or posInput == "9": continue

            trailingWeeks = input("Enter Trailing Weeks: ")
            if (trailingWeeks == ""):
                trailingWeeks = 0
            else:
                trailingWeeks = int(trailingWeeks)

            futureWeek = input("Enter Future Week: ")
            if (futureWeek == ""):
                futureWeek = 0
            else:
                futureWeek = int(futureWeek)

            ptThreshold = input("Enter Point Threshold: ")
            if (ptThreshold == ""): ptThreshold = 0
            ptThreshold = int(ptThreshold)

            playersList = analyzer.getFAvsProjection(allTeamStats, players, nflSchedule, pos, trailingWeeks, futureWeek)

            if trailingWeeks == 0:
                excelFile = outputDir / f"WeightedScores-{pos}-week-{config.currLiveWeek}.xlsx"
            else:
                excelFile = outputDir / f"WeightedScores-{pos}-week-{config.currLiveWeek}-trailing-{trailingWeeks}.xlsx"
            excel_util.closeExcelFile(excelFile)
            excel_util.printWeightedScoresToExcel(
                playersList,
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
            if not pick: continue  

            p = player.Player(matchList[int(pick)-1][0])
            playersTeam = p.getProTeam()
            print("players team: ", playersTeam)
            t = proTeam.ProTeam(allTeamStats[playersTeam])
            
            while True:
                print(f"\nSelected {p.name}")
                print("(1) Points for specfic week")
                print("(2) Avg points")
                print("(3) Projections for future games")
                print("(4) Future Opp Matchups")
                opt = input("Option: ")

                if opt == "1":
                    week = input("\nEnter week: ")
                    print (f"Week {week} - {p.getPtsForWeek(week)}")

                elif opt == "2":
                    start = input("\nEnter start week: ")
                    end = input("Enter end week: ")
                    if not start: start = 1
                    if not end: end = config.currDataWeek
                    avgPts, played = p.getAvgPts(int(start), int(end))
                    
                    print(f"Avg points from weeks {start} to {end}: {avgPts}")
                    print(f"Played in {played} games")

                elif opt == "4":
                    print("\nNext 3 Opponents")
                    print(f"Team\tPoints Allowed to {p.pos}\tRank")
                    for i in range(config.currLiveWeek, config.currLiveWeek+3):
                        oppTeam = p.getOppByWeek(i)
                        if oppTeam == "BYE":
                            print(f"{oppTeam}")
                        else:
                            print(f"{oppTeam}\t{proTeams[oppTeam].getAverage("allowed",p.pos)}")

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

