# NFL Import
from espn_api.football import League
from espn_api.football import Player
# from espn_api.football.espn_requests import EspnFantasyRequests
from espn_api.football.constant import PRO_TEAM_MAP, POSITION_MAP
from typing import Callable, Dict, List, Set, Tuple, Union
from espn_api.football.settings import Settings

from constants import POSITIONS, NFL_TEAMS

# debug mode
#league = League(league_id, year, espn_s2, swid, debug=False)
# won't get any league data when initialized. Make sure to call league.fetch_league() when ready to use. 
#league = League(league_id, year, espn_s2, swid, fetch_league=True)


def fetchNflData(league_id, year, espn_s2, swid, nflSchedule):
    # private league with cookies
    league = League(league_id, year, espn_s2, swid)
    print("Current league week: ", league.current_week)

    # load players
    print("Loading all possible NFL fantasy players for your league")
    players = getPlayers(league, league.current_week)

    # load nfl team stats
    allTeamStats = {}
    # teamAverageStats = {}

    print("Getting Team Stats")
    for team in NFL_TEAMS:
        print("Loading team data for", team)
        stats = getPtsAllowedStats(league, players, team)
        allTeamStats[team] = stats

    print("\nBuilding NFL Teams Schedule")

    pro_schedule = league._get_all_pro_schedule()
    for team in NFL_TEAMS:
        nflSchedule[team] = {}
        print("Getting team sched for", team)
        # find team key 
        for key, val in PRO_TEAM_MAP.items():
            if val == team:
                teamKey = key
                break

        teamSched = pro_schedule[teamKey]
        listOfOpp = []
        for i in range(1, 19):
            weekNumber = str(i)
            try:
                game = teamSched[str(i)][0]
                if game["awayProTeamId"] == teamKey:
                    opp = game["homeProTeamId"]
                else: opp = game["awayProTeamId"]
                oppName = PRO_TEAM_MAP[opp]
            except:
                oppName = 'BYE'
            listOfOpp.append(oppName)

        nflSchedule[team]["games"] = listOfOpp

    print("\nTeam data loaded succesfully")

    # all teamstats format
    # allTeamStats = {
    #     "ARI": stats,
    #     "ATL": stats,
    # }

    return allTeamStats

def getPosPlayersByTeam(
    players: list,
    position: str,
    team: str
) -> List[Player]:
    if position in POSITION_MAP:
        positionID = POSITION_MAP[position]
    else: 
        print("Invalid position")
        return

    for key, val in PRO_TEAM_MAP.items():
        if val == team:
            teamKey = key
            # print("found team key: ", teamKey)
            break
    if teamKey is None:
        print("Invalid team")
        return

    posPlayers = []
    for p in players:
        if p.proTeam == team and p.position == position:
            posPlayers.append(p)

    return posPlayers

def getPlayers(
        league: League,
        max_scoring_period: int
) -> List[Player]:

    playerPoolIds = league.espn_request.get_player_pool_ids(max_scoring_period)
    data = league.espn_request.get_player_card(playerPoolIds, max_scoring_period)

    players = data["players"]
    pro_schedule = league._get_all_pro_schedule()

    return [
        Player(player, 2026, pro_schedule)
        for player in players
    ]

def getPtsAllowedStats(league: League, players: list, team: str):
    # gets points allowed stats by positon for the whole season

    # ensure team key is found
    for key, val in PRO_TEAM_MAP.items():
        if val == team:
            teamKey = key
            # print("found team key: ", teamKey)
            break

    # get team schedule
    pro_schedule = league._get_all_pro_schedule()
    teamSched = pro_schedule[teamKey]

    # get opp points allowed by position up until current week
    
    stats = {
        "weeks":{},
        "totals":{
            "QB":0,
            "WR":0,
            "RB":0,
            "TE":0,
            "K":0,
            "D/ST":0
        },
        "averages":{},
        "gamesPlayed":int
    }

    gamesPlayed = 0

    for i in range(1, league.current_week+1):
        weekNumber = str(i)
        game = teamSched[str(i)][0]
        if game["awayProTeamId"] == teamKey:
            opp = game["homeProTeamId"]
        else: opp = game["awayProTeamId"]
        oppName = PRO_TEAM_MAP[opp]

        gamePlayed = 0

        stats["weeks"][weekNumber] = {
            "opp": oppName,
            "played": gamePlayed
        }

        for position in POSITIONS:
            # print("pos = ",position)
            oppPosPlayers = getPosPlayersByTeam(players, position, oppName)
            ptsAllowed = 0
            for player in oppPosPlayers:
                # print("player =", player.name)
                if i in player.stats:
                    ptsAllowed += player.stats[i].get("points", 0 )
                    # print("ptsAllowed running total = ", ptsAllowed)

            # posStats[position][i] = round(ptsAllowed, 1)
            stats["weeks"][weekNumber][position] = round(ptsAllowed, 1)
            stats["totals"][position] += round(ptsAllowed, 1)

            if stats["weeks"][weekNumber][position] != 0:
                gamePlayed = 1

        if gamePlayed == 1:
            gamesPlayed += 1
            stats['weeks'][weekNumber]["played"] = gamePlayed

    # calc avg pts allowed
    for position in POSITIONS:
        stats["averages"][position] = round(stats["totals"][position]/gamesPlayed, 1)

    stats['gamesPlayed'] = gamesPlayed
    return stats

### Structure for stats
# {
#     "weeks": {
#         "1": {
#             "opp": "DAL",
#             "QB": 18.5,
#             "WR": 31.2,
#             "RB": 22.4,
#             "TE": 8.7,
#             "K": 9.0,
#             "D/ST": 5.0
#             "played": 1
#         },
#         "2": {
#             "opp": "KC",
#             ...
#         }
#     },

#     "totals": {
#         "QB": 40.2,
#         "WR": 65.7,
#         ...
#     },

#     "averages": {
#         "QB": 20.1,
#         "WR": 32.85,
#         ...
#     },

#     "gamesPlayed": int
# }

def printStats(stats: {}):
    print("Printing stats for points allowed by position")

    for i in stats["weeks"]:
        weekNum = str(i)
        print('Week', i, "vs", stats['weeks'][weekNum]['opp'])
        for position in POSITIONS:
            print(f"{position}: {stats['weeks'][weekNum][position]:.1f}", end="\t")
        print()

    print("\nAverages")
    for position in POSITIONS:
        print(f"{position}: {stats['averages'][position]:.1f}", end="\t")
    print()

def getPtsByWeek(pos: str, allTeamStats: {}):

    ptsByWeek = {}
    currentWeek = len(allTeamStats['ARI']['weeks'])

    for team in NFL_TEAMS:
        ptsByWeek[team] = {}
        gamesPlayed = 0
        totalPts = 0
        for week in range(1, currentWeek+1):
            weekStats = [0,0]
            weekNum = str(week)
            weekData = allTeamStats[team]['weeks'][weekNum]

            if weekData['played'] == 1:
                gamesPlayed += 1

            weekStats[0] = weekData[pos]
            totalPts = totalPts + weekData[pos]

            runningAvg = round(totalPts/gamesPlayed, 1)
            weekStats[1] = runningAvg

            ptsByWeek[team][str(week)] = weekStats    

    return ptsByWeek

def addRunningRanks(ptsByWeek):
    weeks = next(iter(ptsByWeek.values())).keys()

    for week in weeks:

        # Collect running avg for teams in curr week
        averages = {}
        for team, stats in ptsByWeek.items():
            averages[team] = stats[week][1]

        # Sort highest average first
        sortedTeams = sorted(
            averages,
            key=averages.get,
            reverse=True
        )

        # assign rank to teams
        previousAvg = None
        previousRank = None
        for index, team in enumerate(sortedTeams, start=1):
            avg = averages[team]

            # Tied averages receive the same rank
            rank = previousRank if avg == previousAvg else index

            ptsByWeek[team][str(week)].append(rank)

            previousAvg = avg
            previousRank = rank

    return ptsByWeek

def getCurrentRanks(ptsByWeek):
    currentRanks = {}

    currentWeek = list(
        next(iter(ptsByWeek.values())).keys()
    )[-1]

    for team in ptsByWeek:
        currentRanks[team] = ptsByWeek[team][currentWeek][2]

    return currentRanks