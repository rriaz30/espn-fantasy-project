# project imports
import espn_data
import constants
import pandas as pd
import statistics
from player import Player
from proTeam import ProTeam
import config

def getFAvsProjection(allTeamStats, players, nflSchedule, pos, trailingWeeks=0, futureWeek=0):

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

    return playersList

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

    if ptTotal == 0:
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
    currOppAvgAllowed = ptsByWeek[currOpp][str(currWeek)][0]
    # print("currOpp = " , currOpp)
    # print("ptsByWeek[currOpp] = " , ptsByWeek[currOpp])
    # print("currOppRank = " , currRanks[currOpp])
    # print("currOppAvgAllowed = ", currOppAvgAllowed)

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
    print(f"Get proj points for {p.getName()} vs {opp} in week {week}")
    print("Using WS3")

    # find ptsScoredTeamRatio
    playerAvgPts = p.getAvgPts()
    playersTeamAvg = proTeams[p.getProTeam].getAverage("scored", p.pos)
    ptsScoredTeamRatio = playerAvgPts / playersTeamAvg




