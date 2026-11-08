
from pathlib import Path

import config
import espn_data
import json_util


def loadJsonData(dataDir):

    dataDir = Path(dataDir)

    try:
        allTeamStats = json_util.loadDataFromJson(dataDir / "TeamStatsData.json")
        nflSchedule = json_util.loadDataFromJson(dataDir / "NflSchedule.json")
        players = json_util.loadDataFromJson(dataDir / "Players.json")
        fantasyTeams = json_util.loadDataFromJson(dataDir / "FantasyTeams.json")

        with open(dataDir / "FetchInfo.txt", "r") as file:
            lines = [line.strip() for line in file]

        leagueInfo = lines[0].split(":", 1)[1].strip()
        config.league_id, config.league_name = leagueInfo.split(" - ", 1)
        config.league_id = int(config.league_id)

        config.currLiveWeek = int(lines[1].split(":", 1)[1].strip())
        config.currDataWeek = int(lines[2].split(":", 1)[1].strip())

        fantasyInfo = lines[3].split(":", 1)[1].strip()
        config.fantasyTeamNum, config.fantasyTeamName = fantasyInfo.split(" - ", 1)
        config.fantasyTeamNum = int(config.fantasyTeamNum)

        return allTeamStats, nflSchedule, players, fantasyTeams

    except (FileNotFoundError, KeyError, ValueError) as error:
        print(f"Could not load saved data: {error}")
        return {}, {}, [], {}


def fetchESPNdata(dataDir, league_id, year, espn_s2, swid, fantasyTeamNum=None):
    dataDir = Path(dataDir)
    dataDir.mkdir(parents=True, exist_ok=True)

    nflSchedule = {}
    players = []
    fantasyTeams = {}

    allTeamStats = espn_data.fetchNflData(
        league_id,
        year,
        espn_s2,
        swid,
        nflSchedule,
        players,
        fantasyTeams,
        fantasyTeamNum=fantasyTeamNum,
        dataDir=dataDir
    )

    json_util.saveDataToJson(allTeamStats, dataDir / "TeamStatsData.json")
    json_util.saveDataToJson(nflSchedule, dataDir / "NflSchedule.json")
    json_util.saveDataToJson(players, dataDir / "Players.json")
    json_util.saveDataToJson(fantasyTeams, dataDir / "FantasyTeams.json")

    return allTeamStats, nflSchedule, players, fantasyTeams
