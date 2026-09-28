import pandas as pd
from openpyxl.styles import Font, Alignment
from openpyxl.styles import PatternFill
from openpyxl.utils import get_column_letter
from openpyxl import load_workbook

from constants import POSITIONS, NFL_TEAMS

# Green range
darkGreen = "006100"
lightGreen = "C6EFCE"

# Red range
lightRed = "FFC7CE"
darkRed = "9C0006"

# excel functions
def interpolateColor(startColor, endColor, percent):
    start = tuple(int(startColor[i:i+2], 16) for i in (0, 2, 4))
    end = tuple(int(endColor[i:i+2], 16) for i in (0, 2, 4))

    rgb = tuple(
        round(start[j] + (end[j] - start[j]) * percent)
        for j in range(3)
    )

    return "".join(f"{value:02X}" for value in rgb)

def printOverallPosRankToExcel(allTeamStats, excelFile: str):
    # load points allowed by pos for each team
    print("Calculating points allowed by position for each team")

    excelFile = excelFile.with_suffix(".xlsx")
    teamAverageStats = {}

    for team in NFL_TEAMS:
        # print(team)
        teamAverageStats[team] = allTeamStats[team]['averages']

    # create excel sheet for pts allowed

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
    # print(df)
    # try:
    #     df.to_excel("avgPtsAllowed.xlsx")
    # except PermissionError:
    #     print("ERROR: Close open excel file and try again.")
    print("Finished creating Points Allowed excel file:", excelFile)

    with pd.ExcelWriter(excelFile, engine="openpyxl") as writer:

        # Start the table on row 3, leaving room for the title
        df.to_excel(
            writer,
            sheet_name="Points Allowed",
            startrow=2
        )

        ws = writer.sheets["Points Allowed"]

        # Merge the title across all table columns
        last_col = df.shape[1] + 1
        ws.merge_cells(
            start_row=1,
            start_column=1,
            end_row=1,
            end_column=last_col
        )

        # Add and format the title
        title = ws.cell(row=1, column=1)
        title.value = "Points Allowed By Position"
        title.font = Font(size=20, bold=True)
        title.alignment = Alignment(horizontal="center")

        # Increase the title row's height
        ws.row_dimensions[1].height = 35

        headerRow = 3
        firstDataRow = 4
        lastDataRow = firstDataRow + len(df) - 1

        for col in range(2, ws.max_column + 1):

            header = ws.cell(row=headerRow, column=col).value

            # Only format columns like "QB Rank", "RB Rank", etc.
            if header and "Rank" in str(header):

                for row in range(firstDataRow, lastDataRow + 1):

                    cell = ws.cell(row=row, column=col)
                    rank = cell.value

                    if rank is None:
                        continue

                    # Rank 1-10 = green
                    if 1 <= rank <= 10:

                        percent = (rank - 1) / 9

                        color = interpolateColor(
                            darkGreen,
                            lightGreen,
                            percent
                        )

                        cell.fill = PatternFill(
                            fill_type="solid",
                            fgColor=color
                        )

                    # Rank 22-32 = red
                    elif 22 <= rank <= 32:

                        percent = (rank - 22) / 10

                        color = interpolateColor(
                            lightRed,
                            darkRed,
                            percent
                        )

                        cell.fill = PatternFill(
                            fill_type="solid",
                            fgColor=color
                        )

def createPositionDataFrame(ptsByWeek):
    rows = {}

    for team, weeks in ptsByWeek.items():
        rows[team] = {}

        for week, stats in weeks.items():
            weekLabel = f"Week {week}"

            rows[team][(weekLabel, "Pts")] = stats[0]
            rows[team][(weekLabel, "Running Avg")] = stats[1]
            rows[team][(weekLabel, "Rank")] = stats[2]

    df = pd.DataFrame.from_dict(rows, orient="index")

    df.index.name = "Team"
    df.columns = pd.MultiIndex.from_tuples(df.columns)

    return df

def writePositionSheet(writer, df, pos, title):
    sheetName = pos.replace("/", "_")

    df.to_excel(writer, sheet_name=sheetName, startrow=1)

    ws = writer.sheets[sheetName]

    # Remove the extra row pandas creates
    ws.delete_rows(4)
    ws["A2"] = "Team"
    writeTitle(ws, title)
    ws.freeze_panes = "B4"

def colorRankings(filePath):

    wb = load_workbook(filePath)

    greenColors = [
        "147D39", "208A43", "31994E", "49A75F",
        "62B674", "7CC48B", "96D2A3", "B1DFBB",
        "CCEBD3", "E5F5E9"
    ]

    redColors = [
        "FDE8E8", "FBDADA", "F8CACA", "F4B6B6",
        "EE9D9D", "E88080", "DF6262", "D54747",
        "C92F2F", "B91F1F", "991B1B"
    ]

    # Loop through every worksheet
    for ws in wb.worksheets:

        # Find every column with a Rank header
        for cell in ws[3]:

            if cell.value != "Rank":
                continue

            rankCol = cell.column

            # Color each rank in that column
            for row in range(4, ws.max_row + 1):

                rankCell = ws.cell(row=row, column=rankCol)
                rank = rankCell.value

                if not isinstance(rank, (int, float)):
                    continue

                rank = int(rank)

                if 1 <= rank <= 10:
                    color = greenColors[rank - 1]

                elif 22 <= rank <= 32:
                    color = redColors[rank - 22]

                else:
                    continue

                if 1 <= rank <=3 or 30 <= rank <= 32:
                    rankCell.font = Font(
                        bold=True,
                        color="FFFFFF"
                )

                rankCell.fill = PatternFill(
                    fill_type="solid",
                    fgColor=color
                )



    wb.save(filePath)


def writeTitle(ws, title):
    ws.merge_cells(
        start_row=1,
        start_column=1,
        end_row=1,
        end_column=ws.max_column
    )

    cell = ws["A1"]
    cell.value = title

    cell.font = Font(
        size=20,
        bold=True,
        color="FFFFFF"
    )

    cell.fill = PatternFill(
        fill_type="solid",
        fgColor="183B31"
    )

    cell.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 28