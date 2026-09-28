import json

def saveStatsToJson(allTeamStats, filename):
    filename = filename + ".json"
    with open(filename, "w") as file:
        json.dump(allTeamStats, file, indent=4)
    print("Saved to JSON file:", filename)

def loadStatsFromJson(filename):
    filename = filename + ".json"
    with open(filename, "r") as file:
        allTeamStats = json.load(file)
    print("Succesfully loaded team data from JSON file:", filename)
    return allTeamStats