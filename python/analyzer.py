# project imports
import espn_data
import constants
import pandas as pd
import statistics
from player import Player
from proTeam import ProTeam
import config

def rankFAandMyTeamPlayerVsCurrOppWIP(allTeamStats, players, nflSchedule, currentWeek):
    # experiment - calc 'real' def rank, maybe this could lead to more 
    print("currWeek = " , currentWeek)
    print("config.currWeek = " , config.currentWeek)
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

    trailingWeeks = input("Enter Trailing Weeks: ")
    if (trailingWeeks == ""):
        trailingWeeks = 0
    else:
        trailingWeeks = int(trailingWeeks)
    print("trailingWeeks = ", trailingWeeks)

    ptThreshold = input("Enter Point Threshold: ")
    ptThreshold = int(ptThreshold)

    # find best pts allowed ranks
    ptsByWeek = espn_data.getPtsByWeek(pos, allTeamStats, option="allowed")
    ptsByWeek = espn_data.addRunningRanks(ptsByWeek)
    currRanks = espn_data.getCurrentRanks(ptsByWeek)
    # get stats of player points scored per game and their avg and their curr opp
    playersList = {}
    for p in players:
        if ((p["position"] == pos and p["proTeam"] != "None" and p["onTeamId"] == 0)
            or 
            (p["position"] == pos and p["onTeamId"] == 1)): # The RFL
            # (p["position"] == pos and p["onTeamId"] == 11)): # The Tommy Foundation
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
            # ptsScoredTeamRatio = player's avg pts scored/player's team's pts scored
            if ("0" not in p["stats"]): continue
            try:
                ptsScoredTeamRatio = p["stats"]["0"]["avg_points"] / allTeamStats[p["proTeam"]]["averages"]["scored"][pos]
            except:
                ptsScoredTeamRatio = 0

            print("len(p[\"stats\"]) = " , len(p["stats"]))

            if trailingWeeks == 0:
                startWeek = 1
            else:
                startWeek = len(p["stats"]) - trailingWeeks
            if startWeek <= 0:
                continue
            for i in range(startWeek, len(p["stats"])):
                if str(i) in p["stats"]:
                    playerStats["ptsScored"].append(p["stats"][str(i)]["points"])
                    playerStats["opp"].append(p["schedule"][str(i)]["team"])
                    playerScored = p["stats"][str(i)]["points"]
                    ptTotal += playerScored
                    opp = p["schedule"][str(i)]["team"]
                    oppAllowed = allTeamStats[opp]["weeks"][str(i)]["allowed"][pos]
                    oppAllowedAvg = allTeamStats[opp]["averages"]["allowed"][pos]
                    oppAllowedAvgTotal += oppAllowedAvg
                    oppAllowedAvg = oppAllowedAvg * ptsScoredTeamRatio
                    playerStats["ptScoredMinusOppAvg"].append(playerScored-oppAllowedAvg)
                    ptDiffTotal += (playerScored-oppAllowedAvg)
                else: continue

            if ptTotal == 0:
                continue
                        
            playerStats["median"] = statistics.median(playerStats["ptsScored"])
            playerStats["average"] = statistics.mean(playerStats["ptsScored"])
            # if p["name"] == "Broncos D/ST":
            #     print("median = " , playerStats["median"])
            #     print("avg from stats, " , playerStats["average"])
            #     print("avg calc", statistics.mean(playerStats["ptsScored"]))
            try:
                playerStats["ptDiffAverage"] = ptDiffTotal / (len(p["stats"]) - 1)
                playerStats["ptDiffAvgByPct"] = ptDiffTotal / (oppAllowedAvgTotal / (len(p["stats"]) - 1))
            except ZeroDivisionError:
                playerStats["ptDiffAverage"] = 0

            # now find curr opp avg pts allowed
            currOpp = nflSchedule[teamName]["games"][(currentWeek)] # -1 because python is 0 based
            # handle bye week
            if (currOpp == "BYE"): continue
            playerStats["currOpp"] = currOpp
            playerStats["currOppRank"] = allTeamStats[currOpp]["averages"]["allowed"]
            currOppAvgAllowed = allTeamStats[currOpp]["averages"]["allowed"][pos]

            playerStats["weightedScore1"] = (
                playerStats["average"] * 0.5
                + playerStats["ptDiffAverage"] * 0.25
                + currOppAvgAllowed * ptsScoredTeamRatio * 0.25
            )
            playerStats["weightedScore2"] = (
                playerStats["average"] * 0.5
                + currOppAvgAllowed * ptsScoredTeamRatio * 0.5 * (1 + playerStats["ptDiffAvgByPct"])
            )
            medianMeanBlend = (
                playerStats["average"] * 0.5
                + playerStats["median"] * 0.5
            )
            playerStats["weightedScore3"] = (
                medianMeanBlend * 0.5
                + currOppAvgAllowed * ptsScoredTeamRatio * 0.5 * (1 + playerStats["ptDiffAvgByPct"])
            )

            # if p["name"] == "Broncos D/ST":
            #     print("curr opp all avg = " , currOppAvgAllowed)
            #     print("player ptDiffAvgByPct, " , playerStats["ptDiffAvgByPct"])
            #     print("player avg", playerStats["average"])
            #     print("player ptsTeamRatio", ptsScoredTeamRatio)

            # print(f"{teamName}: weightedScore = {teamStats["weightedScore"]}")
            playersList[playerName] = playerStats

    return playersList, currRanks, ptThreshold, posInput

def getProjPtsVsFutureOpp(p: Player, opp: str, week, proTeams):
    print(f"Get proj points for {p.getName()} vs {opp} in week {week}")
    print("Using WS3")

    # find ptsScoredTeamRatio
    playerAvgPts = p.getAvgPts()
    playersTeamAvg = proTeams[p.getProTeam].getAverage("scored", p.pos)
    ptsScoredTeamRatio = playerAvgPts / playersTeamAvg




