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

# init json file names
dataDir = Path(__file__).resolve().parent.parent / "data"
teamStatsJson = dataDir / "TeamStatsData.json"
scheduleJson = dataDir / "NflSchedule.json"
playersJson = dataDir / "Players.json"
fantasyTeamsJson = dataDir / "FantasyTeams.json"

def clearConsole():
    os.system("cls")

def getWeeklyPositionReport(filePath, allTeamStats, option):

    if option == "allowed":
        optionStr = "Allowed"
    else: optionStr = "Scored"
    with pd.ExcelWriter(filePath, engine="openpyxl") as writer:

        for pos in constants.POSITIONS:
            ptsByWeek = espn_data.getPtsByWeek(pos, allTeamStats, option)
            ptsByWeek = espn_data.addRunningRanks(ptsByWeek)
            df = excel_util.createPositionDataFrame(ptsByWeek)

            title = pos + f" - Points {optionStr} By Week"
            excel_util.writePositionSheet(writer, df, pos, title)

    print(f"Saved Excel file to {filePath}")

    # Color rankings in excel
    excel_util.colorRankings(filePath)

def getPosRanks(allTeamStats, nflSchedule, currentWeek, option):
    
    for team in constants.NFL_TEAMS:

        nflSchedule[team]["ranks"] = {}

        for pos in constants.POSITIONS:

            ptsByWeek = espn_data.getPtsByWeek(pos, allTeamStats, option)
            ptsByWeek = espn_data.addRunningRanks(ptsByWeek)

            nflSchedule[team]["ranks"][pos] = ptsByWeek[team][str(currentWeek)][2]

def getCurrentWeek(allTeamStats):
    currentWeek = len(allTeamStats['ARI']['weeks'])
    return currentWeek

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

################################################
################################################
################################################

def main():

    # init data structs
    allTeamStats = {}
    nflSchedule = {}
    freeAgents = []
    players = []
    fantasyTeams = {}

    print("Checking for saved data")
    allTeamStats, nflSchedule, players, fantasyTeams = loadJsonData()

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
            # first reset data structs
            allTeamStats = {}
            nflSchedule = {}
            freeAgents = []
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
            print("Loading saved data...")
            allTeamStats, nflSchedule, players, fantasyTeams = loadJsonData()

        elif choice == "3":
            if not allTeamStats:
                print("No data has been loaded yet. Load data and try again.")
                continue
            print("Generate Points Report for Allowed or Scored\nAllowed = 1\nScored = 2")
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
            
            print("Generating Overall report...")
            excelFile = outputDir / f"OverallReport-{optionStr}.xlsx"
            excel_util.closeExcelFile(excelFile)
            excel_util.printOverallPosRankToExcel(allTeamStats, excelFile, optionStr)
            os.startfile(excelFile)

        elif choice == "4":
            if not allTeamStats:
                print("No data has been loaded yet. Load data and try again.")
                continue
            print("Generate Weekly Position Report for Allowed or Scored\nAllowed = 1\nScored = 2")
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
            print("Generating Weekly Position report...")
            excelFile = outputDir / f"WeeklyPosReport-{optionStr}.xlsx"
            excel_util.closeExcelFile(excelFile)
            getWeeklyPositionReport(excelFile, allTeamStats, optionStr)
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
            print("Generate NFL Schedule with Positional Heat Map")
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
            print("Allowed or Scored\nAllowed = 1\nScored = 2")
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

            print("Calculating...")
            currentWeek = getCurrentWeek(allTeamStats)
            getPosRanks(allTeamStats, nflSchedule, currentWeek, optionStr)
            posFileName = pos + "-ColorNflSchedule.xlsx"
            excelFile = outputDir / posFileName
            excel_util.closeExcelFile(excelFile)
            excel_util.scheduleToExcel(nflSchedule, excelFile, currentWeek)
            excel_util.colorScheduleByPosition(nflSchedule, excelFile, posTag, currentWeek)

            print("Printing NFL Schedule with Positional Heat Map for Current Week for",pos)
            os.startfile(excelFile)

        elif choice == "7":
            print("Get free agents available vs bottom rank opponents")
            print(len(players))
            defFree = {}
            defFreeTop10 = []
            defFreeOpp = {}
            currWeek = getCurrentWeek(allTeamStats)
            for p in players:
                if p["position"] == "D/ST" and p["onTeamId"] == 0:
                    print(p["name"])
                    defFree[p["proTeam"]] = p

                    # find curr opp
                    if ((str(currWeek)) not in p["schedule"]): continue
                    defFreeOpp[p["schedule"][str(currWeek)]["team"]] = p["proTeam"]

            # find best def pts allowed ranks
            ptsByWeek = espn_data.getPtsByWeek("D/ST", allTeamStats, option="allowed")
            ptsByWeek = espn_data.addRunningRanks(ptsByWeek)

            
            for team, week in ptsByWeek.items():
                if week[str(currWeek)][2] <= 16 and team in defFreeOpp:
                    faTeam = defFreeOpp[team]
                    print(f"{team} ranked: {week[str(currWeek)][2]} vs FA team: {faTeam} ranked: {defFree[faTeam]["posRank"]}")
                    print(f"")
            ### need to finish. stopped at able to see def fa left and their rank and opp rank

        elif choice == "8":
            players = json_util.loadDataFromJson(playersJson)

            # experiment - calc 'real' def rank, maybe this could lead to more 
            if not allTeamStats:
                print("No data has been loaded yet. Load data and try again.")
                continue
            print("Generate Best Available FA (WIP algo)")
            print("Available Positions: QB, RB, WR, TE, K, DEF")
            validInput = False
            while validInput == False:
                posInput = input("\nSelect a Position: ")
                if posInput == "DEF":
                    pos = "D/ST"
                else: pos = posInput
                if pos in constants.POSITIONS:
                    validInput = True
                else: print("Invalid position selected. Try again.")
            stats = {}

            # find best def pts allowed ranks
            ptsByWeek = espn_data.getPtsByWeek(pos, allTeamStats, option="allowed")
            ptsByWeek = espn_data.addRunningRanks(ptsByWeek)
            currRanks = espn_data.getCurrentRanks(ptsByWeek)
            # get stats of team points scored per game and their avg and their opp
            playersList = {}
            for p in players:
                if ((p["position"] == pos and p["proTeam"] != "None" and p["onTeamId"] == 0)
                    or 
                    (p["position"] == pos and p["onTeamId"] == 1)):
                    # print(p["name"])
                    teamName = p["proTeam"]
                    playerName = p["name"]
                    playerStats = {
                        "name":playerName,
                        "ptsScored":[],
                        "opp":[],
                        "ptDiff":[],
                        "ptScoredMinusOppAvg":[]
                    }

                    ptDiffTotal = 0
                    ptTotal = 0
                    oppAllowedAvgTotal = 0
                    # ratio player's avg pts scored/player's team's pts scored
                    if ("0" not in p["stats"]): continue
                    ptsScoredTeamRatio = p["stats"]["0"]["avg_points"] / allTeamStats[p["proTeam"]]["averages"]["scored"][pos]
                    for i in range(1,len(p["stats"])):
                        if str(i) in p["stats"]:
                            playerStats["ptsScored"].append(p["stats"][str(i)]["points"])
                            playerStats["opp"].append(p["schedule"][str(i)]["team"])
                            playerScored = p["stats"][str(i)]["points"]
                            ptTotal += playerScored
                            opp = p["schedule"][str(i)]["team"]
                            oppAllowed = allTeamStats[opp]["weeks"][str(i)]["allowed"][pos]
                            oppAllowedAvg = allTeamStats[opp]["averages"]["allowed"][pos]
                            oppAllowedAvgTotal += oppAllowedAvg

                            # match pos:
                            #     case "RB": normalizeAllowedAvg = 2
                            #     case "TE": normalizeAllowedAvg = 2
                            #     case "WR": normalizeAllowedAvg = 4
                            #     case _: normalizeAllowedAvg = 1

                            # oppAllowedAvg = oppAllowedAvg/normalizeAllowedAvg
                            oppAllowedAvg = oppAllowedAvg * ptsScoredTeamRatio
                            playerStats["ptScoredMinusOppAvg"].append(playerScored-oppAllowedAvg)
                            ptDiffTotal += (playerScored-oppAllowedAvg)
                        else: continue

                    if ptTotal == 0:
                        continue
                                                
                        # cant we calc everything here? calc points diff, we have he opp,
                        # maybe we can look up how many pts they allowed here every week? in allTeamStats?

                    playerStats["average"] = p["stats"]["0"]["avg_points"]
                    try:
                        playerStats["ptDiffAverage"] = ptDiffTotal / (len(p["stats"]) - 1)
                        playerStats["ptDiffAvgByPct"] = ptDiffTotal / (oppAllowedAvgTotal / (len(p["stats"]) - 1))
                    except ZeroDivisionError:
                        playerStats["ptDiffAverage"] = 0

                    # now find curr opp avg pts allowed
                    currWeek = getCurrentWeek(allTeamStats)
                    currOpp = nflSchedule[teamName]["games"][(currWeek-1)] # -1 because python is 0 based
                    # handle bye week
                    if (currOpp == "BYE"): continue
                    playerStats["currOpp"] = currOpp
                    playerStats["currOppRank"] = allTeamStats[currOpp]["averages"]["allowed"]
                    currOppAvgAllowed = allTeamStats[currOpp]["averages"]["allowed"][pos]

                    playerStats["weightedScore1"] = playerStats["average"]*0.5 + playerStats["ptDiffAverage"]*0.25 + currOppAvgAllowed*ptsScoredTeamRatio*0.25
                    playerStats["weightedScore2"] = playerStats["average"]*0.5 + currOppAvgAllowed*ptsScoredTeamRatio*0.5*playerStats["ptDiffAvgByPct"]

                    # print(f"{teamName}: weightedScore = {teamStats["weightedScore"]}")
                    playersList[playerName] = playerStats

            playersSortedWS1 = {}
            playersSortedWS2 = {}
            ptThreshold1 = 5
            ptThreshold2 = 3
            for player, stats in sorted(playersList.items()):
                if stats["weightedScore1"] > ptThreshold1 :
                    playersSortedWS1[player] = round(stats["weightedScore1"], 1)
                if stats["weightedScore2"] > ptThreshold2 :
                    playersSortedWS2[player] = round(stats["weightedScore2"], 1)

            dataWS1 = {
                "name": [],
                "ws1": [],
                "opp": [],
                "rank" : []
            }
            dataWS2 = {
                "name": [],
                "ws1": [],
                "opp": [],
                "rank" : []
            }

            print("Top Players based on WS1")
            for player, score in sorted(playersSortedWS1.items(), key=lambda x: x[1], reverse=True):
                dataWS1["name"].append(player)
                dataWS1["ws1"].append(score)
                dataWS1["opp"].append(playersList[player]["currOpp"])
                dataWS1["rank"].append(currRanks[playersList[player]["currOpp"]])

            df = pd.DataFrame(dataWS1)
            print(df)

            print("\nTop Players based on WS2")
            for player, score in sorted(playersSortedWS2.items(), key=lambda x: x[1], reverse=True):
                dataWS2["name"].append(player)
                dataWS2["ws1"].append(score)
                dataWS2["opp"].append(playersList[player]["currOpp"])
                dataWS2["rank"].append(currRanks[playersList[player]["currOpp"]])

            df = pd.DataFrame(dataWS2)
            print(df)

        elif choice == "9":
            print("Goodbye!")
            break

        else:
            print("Invalid option. Try again.")


if __name__ == "__main__":
    main()

