import truststore
truststore.inject_into_ssl()

# project imports
import pandas as pd

# NFL Import
from espn_api.football import League
from espn_api.football import Player
# from espn_api.football.espn_requests import EspnFantasyRequests
from espn_api.football.constant import PRO_TEAM_MAP, POSITION_MAP
from typing import Callable, Dict, List, Set, Tuple, Union
from espn_api.football.settings import Settings
from constants import POSITIONS, NFL_TEAMS
import config

# debug mode
#league = League(league_id, year, espn_s2, swid, debug=False)
# won't get any league data when initialized. Make sure to call league.fetch_league() when ready to use. 
#league = League(league_id, year, espn_s2, swid, fetch_league=True)


def fetchNflData(league_id, year, espn_s2, swid, nflSchedule, players, fantasyTeams):
    # private league with cookies
    league = League(league_id, year, espn_s2, swid)
    print("Current league week: ", league.current_week)

    config.currLiveWeek = league.current_week
    config.currDataWeek = league.current_week - 1

    # load players
    print("Loading all NFL fantasy players for your league")
    # players = getPlayers(league, league.current_week)
    players.extend(getPlayers(league, league.current_week))

    print("Total player pool:", len(players))

    # load fantasy team rosters
    print("Loading fantasy rosters")
    fantasyTeamsData = league.teams

    for team in fantasyTeamsData:
        teamData = {}
        teamData["teamName"] = team.team_name
        teamData["teamAbbrev"] = team.team_abbrev
        roster = []
        for p in team.roster:
            roster.append(p.name)
        teamData["players"] = roster
        fantasyTeams[team.team_id] = teamData

    # load nfl team stats
    allTeamStats = {}
    # teamAverageStats = {}

    print("Getting NFL Team Stats")
    for team in NFL_TEAMS:
        print("Loading team data for", team)
        stats = getPtsAllowedStats(league, players, team)
        allTeamStats[team] = stats
        allTeamStats[team]["name"] = team

    print("\nBuilding NFL Teams Schedule")
    pro_schedule = league._get_all_pro_schedule()
    for team in NFL_TEAMS:
        nflSchedule[team] = {}
        # find team key 
        for key, val in PRO_TEAM_MAP.items():
            if val == team:
                teamKey = key
                break

        teamSched = pro_schedule[teamKey]
        listOfOpp = []
        listOfLoc = []
        for i in range(1, 19):
            weekNumber = str(i)
            try:
                game = teamSched[str(i)][0]
                if game["awayProTeamId"] == teamKey:
                    opp = game["homeProTeamId"]
                    location = "AWAY"
                else: 
                    opp = game["awayProTeamId"]
                    location = "HOME"
                oppName = PRO_TEAM_MAP[opp]
            except:
                oppName = 'BYE'
                location = "HOME"
            listOfOpp.append(oppName)
            listOfLoc.append(location)

        nflSchedule[team]["games"] = listOfOpp
        nflSchedule[team]["location"] = listOfLoc

    print("\nTeam data loaded succesfully")

    # all teamstats format
    # allTeamStats = {
    #     "ARI": stats,
    #     "ATL": stats,
    # }

    return allTeamStats

# def getFreeAgents(league_id, year, espn_s2, swid):
#     league = League(league_id, year, espn_s2, swid)
#     return league.free_agents(league.current_week, 1)


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
        Player(player, league.year, pro_schedule)
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

    if (team == "CHI"):
        print("team = ", team)

    # get opp points allowed by position up until current week
    
    stats = {
        "weeks":{},
        "totals":{
            "allowed": {
                "QB":0,
                "RB":0,
                "WR":0,
                "TE":0,
                "K":0,
                "D/ST":0
            },
            "scored": {
                "QB":0,
                "RB":0,
                "WR":0,
                "TE":0,
                "K":0,
                "D/ST":0
            }
        },
        "averages":{
            "allowed": {},
            "scored": {}
        },
        "gamesPlayed":int
    }

    gamesPlayed = 0

    # print("league.current_week+1 = " , league.current_week+1)
    # print("config.currWeek = " , config.currDataWeek)
    for i in range(1, config.currDataWeek+1):
        weekNumber = str(i)
        # check if week is a bye week
        if ((str(i)) not in teamSched):
            stats["weeks"][str(i)] = {
                "opp": "BYE",
                "played": 0,
                "allowed": {
                    "QB":0,
                    "RB":0,
                    "WR":0,
                    "TE":0,
                    "K":0,
                    "D/ST":0
                },
                "scored": {
                    "QB":0,
                    "RB":0,
                    "WR":0,
                    "TE":0,
                    "K":0,
                    "D/ST":0
                }
            }
            continue

        game = teamSched[str(i)][0]
        if game["awayProTeamId"] == teamKey:
            opp = game["homeProTeamId"]
        else: opp = game["awayProTeamId"]
        oppName = PRO_TEAM_MAP[opp]

        # if (team == "CHI"):
        #     print("week # = ", weekNumber, " opp = " , opp)

        gamePlayed = 0

        stats["weeks"][weekNumber] = {
            "opp": oppName,
            "played": gamePlayed,
            "allowed": {},
            "scored": {}
        }

        for position in POSITIONS:
            # print("pos = ",position)
            # get points allowed
            # iter thru opp pos players and add them up
            oppPosPlayers = getPosPlayersByTeam(players, position, oppName)
            ptsAllowed = 0
            for player in oppPosPlayers:
                # if (team == "CHI" and position == "WR"):
                #     print("player =", player.name)
                if i in player.stats:
                    ptsAllowed += player.stats[i].get("points", 0 )
                    # if (team == "CHI" and position == "WR"):
                    #     print("ptsAllowed running total = ", ptsAllowed)

            # posStats[position][i] = round(ptsAllowed, 1)
            stats["weeks"][weekNumber]["allowed"][position] = round(ptsAllowed, 1)
            stats["totals"]["allowed"][position] += round(ptsAllowed, 1)
            # if (team == "CHI" and position == "WR"):
            #     print("weekly allower = ", stats["weeks"][weekNumber]["allowed"][position])
            #     print("running total allowed = ", stats["totals"]["allowed"][position])

            # get points scored
            # iter thru own pos players and add them up
            ownPosPlayers = getPosPlayersByTeam(players, position, team)
            ptsScored = 0
            for player in ownPosPlayers:
                # print("player =", player.name)
                if i in player.stats:
                    ptsScored += player.stats[i].get("points", 0 )
                    # print("ptsAllowed running total = ", ptsAllowed)

            # posStats[position][i] = round(ptsAllowed, 1)
            stats["weeks"][weekNumber]["scored"][position] = round(ptsScored, 1)
            stats["totals"]["scored"][position] += round(ptsScored, 1)


            if stats["weeks"][weekNumber]["allowed"][position] != 0:
                gamePlayed = 1

        if gamePlayed == 1:
            gamesPlayed += 1
            stats['weeks'][weekNumber]["played"] = gamePlayed

    # calc avg pts allowed
    for position in POSITIONS:
        stats["averages"]["allowed"][position] = round(stats["totals"]["allowed"][position]/gamesPlayed, 1)
        stats["averages"]["scored"][position] = round(stats["totals"]["scored"][position]/gamesPlayed, 1)

        if (team == "CHI" and position == "WR"):
            print("final avg allowed = ", stats["averages"]["allowed"][position])

    stats['gamesPlayed'] = gamesPlayed
    return stats

# # Team Stats Structure
# {
#     "weeks": {
#         "1": {
#             "opp": "DAL",
#             "played": 1,

#             "allowed": {
#                 "QB": 0
#             },

#             "scored": {
#                 "QB": 0
#             }
#         }
#     },

#     "gamesPlayed": 1,

#     "totals": {
#         "allowed": {
#             "QB": 0
#         },

#         "scored": {
#             "QB": 0
#         }
#     },

#     "averages": {
#         "allowed": {
#             "QB": 0
#         },

#         "scored": {
#             "QB": 0
#         }
#     }
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

def getPtsByWeek(pos: str, allTeamStats, option="allowed", weeksRequested = 0):

    ptsByWeek = {}

    currentWeek = len(allTeamStats['ARI']['weeks'])
    # print("getPtsByWeek - currentWeek = ", currentWeek, " config.curr = ", config.currDataWeek)

    if weeksRequested == 0:
        initWeek = 1
    else:
        initWeek = currentWeek+1 - weeksRequested

    for team in NFL_TEAMS:
        ptsByWeek[team] = {}
        gamesPlayed = 0
        totalPts = 0
        for week in range(initWeek, currentWeek+1):
            weekStats = [0,0]
            weekNum = str(week)
            # if (team == "CAR"):
                # print(allTeamStats["CAR"])
            weekData = allTeamStats[team]['weeks'][weekNum]
            weekPosData = weekData[option]

            if weekData['played'] == 1:
                gamesPlayed += 1

            weekStats[0] = weekPosData[pos]
            totalPts = totalPts + weekPosData[pos]

            runningAvg = round(totalPts/gamesPlayed, 1) if gamesPlayed else 0
            weekStats[1] = runningAvg

            ptsByWeek[team][str(week)] = weekStats
            # if (team == "SF"):
                # print("week = ", week , " - points = " , weekStats[0])    

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

def getWeeklyPosReportData(allTeamStats, option, weeksRequested = 0):

    weeklyPosReportData = {}

    for pos in POSITIONS:
        ptsByWeek = getPtsByWeek(pos, allTeamStats, option, weeksRequested)
        ptsByWeek = addRunningRanks(ptsByWeek)

        weeklyPosReportData[pos] = ptsByWeek

    return weeklyPosReportData

def getOverallPosRanks(allTeamStats, option: str):
    # load points allowed by pos for each team
    print(f"Calculating points {option} by position for each team")
    
    teamAverageStats = {}

    for team in NFL_TEAMS:
        # print(team)
        teamAverageStats[team] = allTeamStats[team]['averages'][option]

    # create 2d table for pts allowed
    df = pd.DataFrame.from_dict(teamAverageStats, orient="index")
    df.index.name = "Team"

    for position in POSITIONS:
        df[position + " Rank"] = df[position].rank(
            ascending=False, method="min"
        ).astype(int)

    columns = []

    for position in POSITIONS:
        columns.append(position)
        columns.append(position + " Rank")

    df = df[columns]

    return df

def getNflScheduleDF(schedule):
    games = {}

    for team in schedule:
        listOfOpp = []
        for i in range(len(schedule[team]["games"])):
            if schedule[team]["location"][i] == "AWAY":
                listOfOpp.append(schedule[team]["games"][i] + "*")
            else: listOfOpp.append(schedule[team]["games"][i])
        
        games[team] = listOfOpp

    df = pd.DataFrame.from_dict(
        games,
        orient="index"
    )

    # Create Week 1, Week 2, ... column names
    df.columns = [
        f"{week}"
        for week in range(1, len(df.columns) + 1)
    ]

    return df