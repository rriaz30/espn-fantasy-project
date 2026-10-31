# project imports
import espn_data
import constants
import pandas as pd
import statistics
from player import Player
from proTeam import ProTeam
import config
import copy

def getFAvsProjection(allTeamStats, players, nflSchedule, pos, trailingWeeks=0, futureWeek=0, ptThreshold=0):

    # get stats of player points scored per game and their avg and their curr opp
    playersList = {}
    for p in players:
        if ((p["position"] == pos and p["proTeam"] != "None" and p["onTeamId"] == 0)
            or 
            (p["position"] == pos and p["onTeamId"] == 1)): # The RFL
            # (p["position"] == pos and p["onTeamId"] == 3)): # The RFL - dc snappers
            # (p["position"] == pos and p["onTeamId"] == 11)): # The Tommy Foundation

            if not (p["injuryStatus"] == "ACTIVE" or p["injuryStatus"] == "QUESTIONABLE" or p["injuryStatus"] == [] ):
                continue

            if ("0" not in p["stats"]): continue

            playerStats, valid = calcPlayerWeightedScore(p, allTeamStats, nflSchedule, trailingWeeks, futureWeek)

            if valid == True:
                playersList[p["name"]] = playerStats

    # Sort players by weighted score (highest first)
    scoreTypes = [
        "weightedScore1",
        "weightedScore2",
        "weightedScore3",
        "weightedScore4"
    ]

    playersWSRanks = {}

    for scoreType in scoreTypes:

        sortedPlayers = sorted(
            playersList.items(),
            key=lambda x: x[1][scoreType],
            reverse=True
        )
        data = []

        for playerName, stats in sortedPlayers:

            score = stats[scoreType]

            if score <= ptThreshold:
                continue

            opp = stats["currOpp"]

            data.append({
                "Player Name": playerName,
                "Weighted Score": round(score, 1),
                "Team" : stats["ownTeam"],
                "Team Rank" : stats["ownTeamRank"],
                "Opp": opp,
                "Opp Rank": stats["currOppRank"]
            })

        df = pd.DataFrame(
            data,
            columns=["Player Name", "Weighted Score", "Team", "Team Rank", "Opp", "Opp Rank"]
        )

        # Add ranking column
        df.insert(0, "Rank", range(1, len(df) + 1))

        playersWSRanks[scoreType] = df

    return playersWSRanks

def calcPlayerWeightedScore(p, allTeamStats, nflSchedule, trailingWeeks=0, futureWeek=0):

    valid = False
    # print(p["name"])
    teamName = p["proTeam"]
    playerName = p["name"]
    pos = p["position"]
    playerStats = {
        "name":playerName,
        "ptsScored":[],
        "opp":[],
        "ptDiff":[],
        "ptScoredMinusOppAvg":[]
    }
    
    if trailingWeeks == 0:
        startWeek = 1
        endIter = config.currDataWeek
    else:
        # startWeek = len(p["stats"]) - trailingWeeks
        startWeek = config.currDataWeek+1 - trailingWeeks
        endIter = trailingWeeks
    if startWeek <= 0:
        return playerStats, valid

    # first gather stats to do calculations on
    oppAllowedAvgList = []
    playerScoredList = []
    teamScoredTotal = 0
    ptTotal = 0
    oppAllowedAvgTotal = 0
    recordedWeeks = []
    for i in range(1, endIter+1):

        statWeek = config.currDataWeek + 1 - i
        while True:
            if (statWeek <= 0):
                break
            if str(statWeek) in p["stats"] and statWeek not in recordedWeeks:
                recordedWeeks.append(statWeek)
                break
            else:
                statWeek -= 1

        if statWeek <= 0:
            continue
        else:
            playerStats["ptsScored"].append(p["stats"][str(statWeek)]["points"])
            playerStats["opp"].append(p["schedule"][str(statWeek)]["team"])

            playerScored = p["stats"][str(statWeek)]["points"]
            playerScoredList.append(playerScored)
            ptTotal += playerScored

            team = p["proTeam"]
            teamScored = allTeamStats[team]["weeks"][str(statWeek)]["scored"][pos]
            teamScoredTotal += teamScored

            opp = p["schedule"][str(statWeek)]["team"]
            oppAllowedAvg = allTeamStats[opp]["averages"]["allowed"][pos]
            oppAllowedAvgList.append(oppAllowedAvg)
            oppAllowedAvgTotal += oppAllowedAvg

            # if (p["name"] == "Tre Tucker"):
            #     print("week = ", statWeek)
            #     print("opp = " , p["schedule"][str(statWeek)]["team"])
            #     print("playerScored = " , playerScored)
            #     print("teamScored = ", teamScored)
            #     print("oppAllowedAvg = ", oppAllowedAvg)

    if ptTotal == 0 or teamScoredTotal == 0:
        return playerStats, valid

    ptsScoredTeamRatio = ptTotal / teamScoredTotal
    # if (p["name"] == "Tre Tucker"):
    #     print("ptTotal = ", ptTotal)
    #     print("teamScoredTotal = ", teamScoredTotal)
    #     print("ptsScoredTeamRatio = ", ptsScoredTeamRatio)

    ptDiffExpectedTotal = 0
    # loop thru opp scored to find ptDiffExpectedTotal and oppAllowedExpected
    for i in range(0, endIter):
        # print("i =" , i , " player = " , p["name"])
        if i >= len(oppAllowedAvgList): continue
        oppAllowedExpected = oppAllowedAvgList[i] * ptsScoredTeamRatio
        ptDiffExpectedTotal += playerScoredList[i] - oppAllowedExpected
        # if (p["name"] == "Tre Tucker"):
        #     print("oppAllowedExpected = ", oppAllowedExpected)
                
    playerStats["median"] = statistics.median(playerStats["ptsScored"])
    playerStats["average"] = statistics.mean(playerStats["ptsScored"])

    if trailingWeeks == 0:
        weeks = config.currDataWeek
    else: weeks = trailingWeeks

    try:
        playerStats["ptDiffAverage"] = ptDiffExpectedTotal / (weeks)
        playerStats["ptDiffAvgByPct1"] = ptDiffExpectedTotal / (oppAllowedAvgTotal / (weeks))
        playerStats["ptDiffAvgByPct2"] = ptDiffExpectedTotal / (oppAllowedAvgTotal*ptsScoredTeamRatio / (weeks))
    except ZeroDivisionError:
        playerStats["ptDiffAverage"] = 0
        playerStats["ptDiffAvgByPct1"] = 0
        playerStats["ptDiffAvgByPct2"] = 0


    # now find curr opp avg pts allowed
    currWeek = config.currDataWeek
    if futureWeek == 0:
        currOpp = nflSchedule[teamName]["games"][(currWeek)]
    else: 
        currOpp = nflSchedule[teamName]["games"][(futureWeek - 1)]  

    # handle bye week
    if (currOpp == "BYE"): return playerStats, valid

    # get opp rank and avg allowed depending on trailing weeks
    ptsByWeek = espn_data.getPtsByWeek(pos, allTeamStats, "allowed", trailingWeeks)
    ptsByWeek = espn_data.addRunningRanks(ptsByWeek)
    currRanks = espn_data.getCurrentRanks(ptsByWeek)

    playerStats["currOpp"] = currOpp
    playerStats["currOppRank"] = currRanks[currOpp]
    currOppAvgAllowed = ptsByWeek[currOpp][str(currWeek)][1]
    # if (p["name"] == "Tre Tucker"):
    #     print("currWeek = " , currWeek)
    #     print("currOpp = " , currOpp)
    #     print("ptsByWeek[currOpp] = " , ptsByWeek[currOpp])
    #     print("currOppRank = " , currRanks[currOpp])
    #     print("currOppAvgAllowed = ", currOppAvgAllowed)

    # get own team rank
    ptsByWeek = espn_data.getPtsByWeek(pos, allTeamStats, "scored", trailingWeeks)
    ptsByWeek = espn_data.addRunningRanks(ptsByWeek)
    currRanks = espn_data.getCurrentRanks(ptsByWeek)

    playerStats["ownTeam"] = teamName
    playerStats["ownTeamRank"] = currRanks[teamName]

    # if (p["name"] == "Tre Tucker"):
    #     print("\ncurrOppAvgAllowed = ", currOppAvgAllowed)
    #     print("ptDiffAverage = ", playerStats["ptDiffAverage"])
    #     print("ptDiffAvgByPct1 = ", playerStats["ptDiffAvgByPct1"])
    #     print("ptDiffAvgByPct2 = ", playerStats["ptDiffAvgByPct2"])
    #     print("median = ", playerStats["median"])
    #     print("average = ", playerStats["average"])
    #     print("ptsScoredTeamRatio = ", ptsScoredTeamRatio)
    #     print("oppAllowedAvgTotal = ", oppAllowedAvgTotal)
    #     print("oppAllowedAvgTotal2 = ", oppAllowedAvgTotal*ptsScoredTeamRatio, "\n")

    playerStats["weightedScore1"] = (
        playerStats["average"] * 0.5
        + playerStats["ptDiffAverage"] * 0.25
        + currOppAvgAllowed * ptsScoredTeamRatio * 0.25
    )
    playerStats["weightedScore2"] = (
        playerStats["average"] * 0.5
        + currOppAvgAllowed * ptsScoredTeamRatio * 0.5 * (1 + playerStats["ptDiffAvgByPct1"])
    )
    medianMeanBlend = (
        playerStats["average"] * 0.5
        + playerStats["median"] * 0.5
    )
    playerStats["weightedScore3"] = (
        medianMeanBlend * 0.5
        + currOppAvgAllowed * ptsScoredTeamRatio * 0.5 * (1 + playerStats["ptDiffAvgByPct1"])
    )
    playerStats["weightedScore4"] = (
        medianMeanBlend * 0.5
        + currOppAvgAllowed * ptsScoredTeamRatio * 0.5 * (1 + playerStats["ptDiffAvgByPct2"])
    )

    # playersList[playerName] = playerStats
    valid = True
    return playerStats, valid


def getProjPtsVsFutureOpp(p: Player, opp: str, week, proTeams):
    #############
    ### TODO ####
    ##############
    print(f"Get proj points for {p.getName()} vs {opp} in week {week}")
    print("Using WS3")

    # find ptsScoredTeamRatio
    playerAvgPts = p.getAvgPts()
    playersTeamAvg = proTeams[p.getProTeam].getAverage("scored", p.pos)
    ptsScoredTeamRatio = playerAvgPts / playersTeamAvg

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

def getPosRanks(allTeamStats, nflSchedule, option):

    nflScheduleRanks = copy.deepcopy(nflSchedule)
    
    for team in constants.NFL_TEAMS:

        nflScheduleRanks[team]["ranks"] = {}

    for pos in constants.POSITIONS:

        ptsByWeek = espn_data.getPtsByWeek(pos, allTeamStats, option)
        ptsByWeek = espn_data.addRunningRanks(ptsByWeek)

        for team in constants.NFL_TEAMS:

            nflScheduleRanks[team]["ranks"][pos] = ptsByWeek[team][str(config.currDataWeek)][2]

    return nflScheduleRanks

def playerSearchMatches(userInput, players):
    splitName = True
    if " " in userInput:
        splitName = False
    userInput = userInput.strip().lower()

    playersList = []
    for p in players:
        if p.get("stats", {}).get("0", {}).get("avg_points", 0) >= 5:
            playersList.append(p)
        
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

    matchList.sort(key=lambda x: x[1], reverse=True)

    return playerFound, matchList

def getRealPosRanks(allTeamStats, players, minPtsThreshold, minGames=0, trailingWeeks=0):

    if trailingWeeks == 0:
        startWeek = 1
    else:
        startWeek = config.currDataWeek+1 - trailingWeeks

    if minGames == 0:
        minGames = 3

    realPosRanksDF = {}

    for pos in constants.POSITIONS:

        teamRankings = espn_data.getPtsByWeek(pos, allTeamStats, "allowed", trailingWeeks)
        teamRankings = espn_data.addRunningRanks(teamRankings)
        teamRankings = espn_data.getCurrentRanks(teamRankings)
        
        elgibleList = []

        for p in players:

            if p["position"] == pos:
                gamesPlayed = 0
                totalPts = 0
                # iter thru games to count games played
                for i in range(startWeek, config.currDataWeek+1):
                    weekStats = p["stats"].get(str(i), {})

                    if weekStats.get("breakdown"):
                        totalPts += weekStats["points"]
                        gamesPlayed += 1

                if gamesPlayed >= minGames:
                    if (totalPts / gamesPlayed) <= minPtsThreshold: continue

                    opp = p["schedule"].get(str(config.currDataWeek + 1), {}).get("team", "BYE")
                    oppRank = teamRankings.get(opp, "BYE")

                    data = {
                        "name": p["name"],
                        "proTeam": p["proTeam"],
                        "fantasyTeam": p["onTeamId"],
                        "average": round(totalPts / gamesPlayed, 2),
                        "gamesPlayed": gamesPlayed,
                        "opp": opp,
                        "oppRank": oppRank
                    }

                    elgibleList.append(data)

        elgibleList.sort(
            key=lambda p: p["average"],
            reverse=True
        )

        top50List = elgibleList[:50]

        df = pd.DataFrame(top50List)

        df.rename(
            columns = {
                "name":"Player Name", 
                "proTeam": "Pro Team", 
                "fantasyTeam": "Fantasy Team", 
                "average": "Average",
                "gamesPlayed":"Games Played",
                "opp": "Next Opp",
                "oppRank": "Opp Rank"
            },
            inplace = True
        )

        # Add ranking column
        df.insert(0, "Top Guys", range(1, len(df) + 1))

        realPosRanksDF[pos] = df

    return realPosRanksDF
