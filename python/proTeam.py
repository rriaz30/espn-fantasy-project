

class ProTeam(object):

    def __init__(self, stats):

        self.name = stats["name"]
        self.weeks = stats["weeks"]
        self.totals = stats["totals"]
        self.averages = stats["averages"]
        self.gamesPlayed = stats["gamesPlayed"]

    def getTeamName(self):
         return self.name

    def getWeekStats(self, week):
        return self.weeks.get(str(week), {})

    def getOppByWeek(self, week):
        return self.getWeekStats(week).get("opp", "")

    def getStatsByWeek(self, week, type, pos):
        return self.getWeekStats(week).get(type, {}).get(pos, 0)

    def getTotals(self, type, pos):
        return self.totals.get(type, {}).get(pos, 0)

    def getAverage(self, type, pos):
            return self.averages.get(type, {}).get(pos, 0)       
