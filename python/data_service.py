
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

        config.currDataWeek = len(allTeamStats["ARI"]["weeks"])
        config.currLiveWeek = config.currDataWeek + 1

        return allTeamStats, nflSchedule, players, fantasyTeams

    except (FileNotFoundError, KeyError, ValueError) as error:
        print(f"Could not load saved data: {error}")
        return {}, {}, [], {}


def fetchESPNdata(dataDir, league_id, year, espn_s2, swid):
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
        fantasyTeams
    )

    json_util.saveDataToJson(allTeamStats, dataDir / "TeamStatsData.json")
    json_util.saveDataToJson(nflSchedule, dataDir / "NflSchedule.json")
    json_util.saveDataToJson(players, dataDir / "Players.json")
    json_util.saveDataToJson(fantasyTeams, dataDir / "FantasyTeams.json")

    return allTeamStats, nflSchedule, players, fantasyTeams
