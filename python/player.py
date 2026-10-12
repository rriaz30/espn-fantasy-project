

class Player(object):

    def __init__(self, stats):

        self.name = stats["name"]
        self.proTeam = stats["proTeam"]
        self.fantasyTeam = stats["onTeamId"]
        self.pos = stats["position"]

        self.stats = stats["stats"]
        self.schedule = stats["schedule"]

    def getPtsForWeek(self, week):
        return self.stats.get(str(week), {}).get("points", 0)

    def getAvgPts(self, start, end):

        totalPts = 0
        gamesPlayed = 0
        for i in range(start, end+1):
            totalPts += self.getPtsForWeek(i)
            if self.stats.get(str(i), {}).get("breakdown", {}):
                gamesPlayed += 1

        return round(totalPts/gamesPlayed, 1), gamesPlayed

    def getOppByWeek(self, week):
        return self.schedule.get(str(week), {}).get("team", "")