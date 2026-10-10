# project imports
import espn_data
import constants
import pandas as pd

def rankFAandMyTeamPlayerVsCurrOppWIP(allTeamStats, players, nflSchedule, currentWeek):
    # experiment - calc 'real' def rank, maybe this could lead to more 
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
            currOpp = nflSchedule[teamName]["games"][(currentWeek)] # -1 because python is 0 based
            # handle bye week
            if (currOpp == "BYE"): continue
            playerStats["currOpp"] = currOpp
            playerStats["currOppRank"] = allTeamStats[currOpp]["averages"]["allowed"]
            currOppAvgAllowed = allTeamStats[currOpp]["averages"]["allowed"][pos]

            playerStats["weightedScore1"] = playerStats["average"]*0.5 + playerStats["ptDiffAverage"]*0.25 + currOppAvgAllowed*ptsScoredTeamRatio*0.25
            playerStats["weightedScore2"] = playerStats["average"]*0.5 + currOppAvgAllowed*ptsScoredTeamRatio*0.5*(1+playerStats["ptDiffAvgByPct"])

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