# imports
import os 
from pathlib import Path
from dotenv import load_dotenv

# project imports
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

def clearConsole():
    os.system("cls")

def getWeeklyPositionReport(filePath, allTeamStats):

    with pd.ExcelWriter(filePath, engine="openpyxl") as writer:

        for pos in constants.POSITIONS:
            ptsByWeek = espn_data.getPtsByWeek(pos, allTeamStats)
            ptsByWeek = espn_data.addRunningRanks(ptsByWeek)
            df = excel_util.createPositionDataFrame(ptsByWeek)

            title = pos + " - Points Allowed By Week"
            excel_util.writePositionSheet(writer, df, pos, title)

    print(f"Saved Excel file to {filePath}")

    # Color rankings in excel
    excel_util.colorRankings(filePath)

def getPosRanks(allTeamStats, nflSchedule, currentWeek):
    
    for team in constants.NFL_TEAMS:

        nflSchedule[team]["ranks"] = {}

        for pos in constants.POSITIONS:

            ptsByWeek = espn_data.getPtsByWeek(pos, allTeamStats)
            ptsByWeek = espn_data.addRunningRanks(ptsByWeek)

            nflSchedule[team]["ranks"][pos] = ptsByWeek[team][str(currentWeek)][2]

def getCurrentWeek(allTeamStats):
    currentWeek = len(allTeamStats['ARI']['weeks'])
    return currentWeek


################################################
################################################
################################################


# testing for one team
# ptsAllowed = getPtsAllowedStats(players, "LAR")
# printStats(ptsAllowed)

# printOverallPosRankToExcel("testing.xlsx")

def main():
    allTeamStats = {}
    nflSchedule = {}

    print("Checking for saved data")
    dataDir = Path(__file__).resolve().parent.parent / "data"
    teamStatsJson = dataDir / "TeamStatsData.json"
    scheduleJson = dataDir / "NflSchedule.json"
    if teamStatsJson.exists() and scheduleJson.exists():
        print("Found saved data. Loading...")
        allTeamStats = json_util.loadDataFromJson(teamStatsJson)
        nflSchedule = json_util.loadDataFromJson(scheduleJson)
    else:
        print("No data exists. Fetch data first.")

    while True:
        print("\n===== ESPN Fantasy Analyzer =====")
        print("1. Fetch ESPN data")
        print("2. Load saved data")
        print("3. Generate Overall Points Allowed report")
        print("4. Generate Points Allowed by Week per Position report")
        print("5. See full team schedule")
        print("6. Generate full team schedule with Positional Heat Map")
        print("9. Exit")

        choice = input("\nSelect an option: ")
        clearConsole()

        if choice == "1":
            print("Fetching ESPN data...")
            allTeamStats = espn_data.fetchNflData(league_id, year, espn_s2, swid, nflSchedule)
            dataDir = Path(__file__).resolve().parent.parent / "data"
            dataDir.mkdir(parents=True, exist_ok=True)
            json_util.saveDataToJson(allTeamStats, dataDir / "TeamStatsData.json")
            json_util.saveDataToJson(nflSchedule, dataDir / "NflSchedule.json")

        elif choice == "2":
            print("Loading saved data...")
            dataDir = Path(__file__).resolve().parent.parent / "data"
            teamStatsJson = dataDir / "TeamStatsData.json"
            scheduleJson = dataDir / "NflSchedule.json"
            if teamStatsJson.exists() and scheduleJson.exists():
                allTeamStats = json_util.loadDataFromJson(teamStatsJson)
                nflSchedule = json_util.loadDataFromJson(scheduleJson)
            else:
                print("No data exists. Fetch data first.")

        elif choice == "3":
            if not allTeamStats:
                print("No data has been loaded yet. Load data and try again.")
                continue
            print("Generating Overall report...")
            excelFile = outputDir / "OverallReport.xlsx"
            excel_util.closeExcelFile(excelFile)
            excel_util.printOverallPosRankToExcel(allTeamStats, excelFile)
            os.startfile(excelFile)

        elif choice == "4":
            if not allTeamStats:
                print("No data has been loaded yet. Load data and try again.")
                continue
            print("Generating Weekly Position report...")
            excelFile = outputDir / "WeeklyPosReport.xlsx"
            excel_util.closeExcelFile(excelFile)
            getWeeklyPositionReport(excelFile, allTeamStats)
            os.startfile(excelFile)           

        elif choice == "5":
            if not allTeamStats:
                print("No data has been loaded yet. Load data and try again.")
                continue
            print("Printing Full NFL Team Schedule")
            excelFile = outputDir / "NflSchedule.xlsx"
            excel_util.closeExcelFile(excelFile)
            currentWeek = getCurrentWeek(allTeamStats)
            excel_util.scheduleToExcel(nflSchedule, excelFile, currentWeek)
            os.startfile(excelFile)


        elif choice == "6":
            if not allTeamStats:
                print("No data has been loaded yet. Load data and try again.")
                continue
            print("Available Positions: QB, RB, WR, TE, K, DEF")
            validInput = False
            while validInput == False:
                pos = input("\nSelect a Position: ")
                if pos == "DEF":
                    posTag = "D/ST"
                if posTag in constants.POSITIONS:
                    validInput = True
                else: print("Invalid position selected. Try again.")

            
            print("Calculating...")
            currentWeek = getCurrentWeek(allTeamStats)
            getPosRanks(allTeamStats, nflSchedule, currentWeek)
            # print(nflSchedule)
            posFileName = pos + "-ColorNflSchedule.xlsx"
            excelFile = outputDir / posFileName
            excel_util.closeExcelFile(excelFile)
            excel_util.scheduleToExcel(nflSchedule, excelFile, currentWeek)
            excel_util.colorScheduleByPosition(nflSchedule, excelFile, posTag, currentWeek)

            print("Printing NFL Schedule with Positional Heat Map for Current Week for",pos)
            os.startfile(excelFile)
            

        elif choice == "9":
            print("Goodbye!")
            break

        else:
            print("Invalid option. Try again.")


if __name__ == "__main__":
    main()

