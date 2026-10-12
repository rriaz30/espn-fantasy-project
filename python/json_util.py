import json
from pathlib import Path
from datetime import datetime

def loadDataFromJson(filename):
    with open(filename, "r") as file:
        stats = json.load(file)
    return stats

def jsonConverter(obj):

    if isinstance(obj, datetime):
        return obj.isoformat()

    if hasattr(obj, "__dict__"):
        return vars(obj)

    raise TypeError(
        f"Object of type {type(obj).__name__} is not JSON serializable"
    )


def saveDataToJson(data, filePath):

    with open(filePath, "w") as file:
        json.dump(
            data,
            file,
            indent=4,
            default=jsonConverter
        )

    print(f"Saved to JSON file: {filePath}")