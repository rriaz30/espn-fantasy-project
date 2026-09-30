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
load_dotenv(Path(__file__).resolve().parent / ".env")

league_id = int(os.environ["ESPN_LEAGUE_ID"])
year = int(os.environ["ESPN_YEAR"])
espn_s2 = os.environ["ESPN_S2"]
swid = os.environ["ESPN_SWID"]

# Assuming this script is in ESPN_API/python/
projectDir = Path(__file__).resolve().parent.parent
outputDir = projectDir / "espn-fantasy-project/output"

def clearConsole():
    os.system("cls")

def getWeeklyPositionReport(filePath, allTeamStats):
    filePath = filePath.with_suffix(".xlsx")

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

    while True:
        print("\n===== ESPN Fantasy Analyzer =====")
        print("1. Fetch ESPN data")
        print("2. Load saved data")
        print("3. Generate Overall Points Allowed report")
        print("4. Generate Points Allowed by Week per Position report")
        print("5. See full team schedule")
        print("9. Exit")

        choice = input("\nSelect an option: ")
        clearConsole()

        if choice == "1":
            print("Fetching ESPN data...")
            allTeamStats = espn_data.fetchNflData(league_id, year, espn_s2, swid, nflSchedule)
            json_util.saveDataToJson(allTeamStats, "storeTeamStatsData")
            json_util.saveDataToJson(nflSchedule, "storeNflSchedule")

        elif choice == "2":
            print("Loading saved data...")
            allTeamStats = json_util.loadDataFromJson("storeTeamStatsData")
            nflSchedule = json_util.loadDataFromJson("storeNflSchedule")

        elif choice == "3":
            if not allTeamStats:
                print("No data has been loaded yet. Load data and try again.")
                continue
            print("Generating Overall report...")
            excelFile = outputDir / "OverallReport"
            excel_util.printOverallPosRankToExcel(allTeamStats, excelFile)
            excelFile = excelFile.with_suffix(".xlsx")
            os.startfile(excelFile)

        elif choice == "4":
            print("Generating Weekly Position report...")
            excelFile = outputDir / "WeeklyPosReport"
            getWeeklyPositionReport(excelFile, allTeamStats)
            excelFile = excelFile.with_suffix(".xlsx")
            os.startfile(excelFile)

        elif choice == "5":
            print("Printing Full NFL Team Schedule")
            filePath = outputDir / "NflSchedule.xlsx"
            excel_util.scheduleToExcel(nflSchedule, filePath)
            os.startfile(filePath)

        elif choice == "9":
            print("Goodbye!")
            break

        else:
            print("Invalid option. Try again.")


if __name__ == "__main__":
    main()

