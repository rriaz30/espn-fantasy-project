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
import data_service

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
            
            excelFile = outputDir / f"OverallReport-{optionStr.capitalize()}.xlsx"
            excel_util.closeExcelFile(excelFile)

            overallPosRanksData = espn_data.getOverallPosRanks(allTeamStats, optionStr)
            filePath = excel_util.exportOverallPosRanks(overallPosRanksData, optionStr, excelFile)

            os.startfile(filePath)

        elif choice == "2":
            print("Generate Weekly Position Report")
            optionStr = getPtsType()
            if optionStr == "back": continue
            print("Generating Weekly Position report...")
            
            excelFile = outputDir / f"WeeklyPosReport-{optionStr}.xlsx"
            excel_util.closeExcelFile(excelFile)
            weeklyPosReportData = espn_data.getWeeklyPosReportData(allTeamStats, optionStr)
            filePath = excel_util.exportWeeklyPosReport(excelFile, weeklyPosReportData, optionStr)

            os.startfile(filePath)

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
            weeklyPosReportData = espn_data.getWeeklyPosReportData(allTeamStats, optionStr, weeksReq)
            filePath = excel_util.exportWeeklyPosReport(excelFile, weeklyPosReportData, optionStr)

            os.startfile(filePath)   

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
            # excel_util.scheduleToExcel(nflSchedule, excelFile, schedCurrWeek)
            nflScheduleDF = espn_data.getNflScheduleDF(nflSchedule)
            filePath = excel_util.exportNflSSchedule(nflScheduleDF, excelFile)

            os.startfile(filePath)

        elif choice == "2":
            print("Generate NFL Schedule with Positional Heat Map")

            optionStr = getPtsType()
            if optionStr == "back": continue
            
            excelFile = outputDir / "ColorNflSchedule.xlsx"
            excel_util.closeExcelFile(excelFile)

            nflScheduleDF = espn_data.getNflScheduleDF(nflSchedule)

            nflScheduleRanks = analyzer.getPosRanks(allTeamStats, nflSchedule, optionStr)
            filePath = excel_util.exportColorNflSSchedule(nflScheduleDF, nflScheduleRanks, excelFile, schedCurrWeek)

            print(f"Printing NFL Schedule with Positional Heat Map for Current Week - {config.currLiveWeek}")
            os.startfile(filePath)

        elif choice == "9":
            print("Returning to Main Menu")
            break

        else:
            print("Invalid option. Try again.")

def playerSearchMenu():
    print("WIP Player search")

    userInput = input("Enter name: ")
    if not userInput:
        print("No input, returning to main menu")
        return

    playerFound, matchList = analyzer.playerSearchMatches(userInput, players)

    if (not playerFound):
        print("Sorry player not found. Returning to main menu")
        return

    index = 1
    print("\nFound the following players: ")
    if matchList:
        for playerData, accuracy in matchList:
            print(f"({index}) {playerData["name"]}: \t{accuracy:.1%}")  
            index += 1

    pick = input("\nSelect a player by index: ")
    if not pick: 
        print("No player selected. Returning to main menu")
        return  

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
        print("(9) Return to main menu")
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

def analyzeFAAvailable():
    print("WIP")
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

    if posInput == "b" or posInput == "9":
        return

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

    playersWSRanks = analyzer.getFAvsProjection(allTeamStats, players, nflSchedule, pos, trailingWeeks, futureWeek, ptThreshold)

    if trailingWeeks == 0:
        excelFile = outputDir / f"WeightedScores-{posInput}-week-{config.currLiveWeek}.xlsx"
    else:
        excelFile = outputDir / f"WeightedScores-{posInput}-week-{config.currLiveWeek}-trailing-{trailingWeeks}.xlsx"
    excel_util.closeExcelFile(excelFile)
    # excel_util.printWeightedScoresToExcel(playersList, excelFile, ptThreshold)
    filePath = excel_util.exportWeightedScores(playersWSRanks, excelFile)

    os.startfile(filePath)

def realPosRanksMenu():
    print("Get real position ranks")

    minGames = input("Enter min games: ")
    if (minGames == ""):
        minGames = 0
    else:
        minGames = int(minGames)

    minPtsThreshold = input("Enter min points threshold: ")
    if (minPtsThreshold == ""):
        minPtsThreshold = 7
    else:
        minPtsThreshold = int(minPtsThreshold)

    trailingWeeks = input("Enter Trailing Weeks: ")
    if (trailingWeeks == ""):
        trailingWeeks = 0
    else:
        trailingWeeks = int(trailingWeeks)

    if trailingWeeks == 0:
        excelFile = outputDir / f"RealPosRanks-week-{config.currLiveWeek}.xlsx"
    else:
        excelFile = outputDir / f"RealPosRanks-week-{config.currLiveWeek}-trailing-{trailingWeeks}.xlsx"

    excel_util.closeExcelFile(excelFile)
    realPosRanksDF = analyzer.getRealPosRanks(allTeamStats, players, fantasyTeams, minPtsThreshold, minGames, trailingWeeks)
    filePath = excel_util.exportRealPosRanks(realPosRanksDF, excelFile)

    os.startfile(filePath)




################################################################################################
################################################################################################
################################################################################################

def main():
    global allTeamStats, nflSchedule, players, fantasyTeams, proTeams

    print("Checking for saved data")
    allTeamStats, nflSchedule, players, fantasyTeams = data_service.loadJsonData(dataDir)

    # check if data has been loaded
    dataValid = checkLoadedData(allTeamStats)
    if (dataValid == False):
        while dataValid == False:
            print("No Data loaded. Either fetch ESPN data(1) or load from Json file(2)")
            dataInput = input("Select an option:")
            if dataInput == "1":
                # fetchESPNdata()
                allTeamStats, nflSchedule, players, fantasyTeams = data_service.fetchESPNdata(dataDir, league_id, year, espn_s2, swid)
            elif dataInput == "2":
                print("Loading saved data...")
                allTeamStats, nflSchedule, players, fantasyTeams = data_service.loadJsonData(dataDir)
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
        print("4. Player Analyzer WIP")
        print("5. Player Search")
        print("6. See Real Position Ranks")
        print("8. WIP - Team Analyzer - not started")
        print("9. Exit")

        choice = input("\nSelect an option: ")
        clearConsole()

        if choice == "1":
            # fetchESPNdata()
            allTeamStats, nflSchedule, players, fantasyTeams = data_service.fetchESPNdata(dataDir, league_id, year, espn_s2, swid)
            allTeamStats, nflSchedule, players, fantasyTeams = data_service.loadJsonData(dataDir)

            for team in constants.NFL_TEAMS:
                proTeams[team] = proTeam.ProTeam(allTeamStats[team])

        elif choice == "2":
            generateReportsMenu()       

        elif choice == "3":
            schedulesMenu()

        elif choice == "4":
            analyzeFAAvailable()

        elif choice == "5":
            playerSearchMenu()    

        elif choice == "6":
            realPosRanksMenu()

        elif choice == "8":
            # WIP team analyzer
            print("WIP Team Analyzer")       

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

def checkLoadedData(allTeamStats):
    if not allTeamStats:
        print("No data has been loaded yet. Load data and try again.")
        return False
    return True

if __name__ == "__main__":
    main()

