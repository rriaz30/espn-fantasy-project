import json
from pathlib import Path

def saveDataToJson(allTeamStats, filename):
    with open(filename, "w") as file:
        json.dump(allTeamStats, file, indent=4)
    print("Saved to JSON file:", filename)

def loadDataFromJson(filename):
    with open(filename, "r") as file:
        allTeamStats = json.load(file)
    print("Succesfully loaded team data from JSON file:", filename)
    return allTeamStats