import pandas as pd
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl import load_workbook
from openpyxl.worksheet.worksheet import Worksheet
import win32com.client
from pathlib import Path

from constants import POSITIONS, NFL_TEAMS, GREEN_COLORS, RED_COLORS
import config

greenColors = [
    "147D39", "208A43", "31994E", "49A75F",
    "62B674", "7CC48B", "96D2A3", "B1DFBB",
    "CCEBD3", "E5F5E9"
]

redColors = [
    "FBDADA", "F8CACA", "F4B6B6", "EE9D9D",
    "E88080", "DF6262", "D54747", "C92F2F",
    "B91F1F", "991B1B"
]

# Borders
thin = Side(style="thin")
thick = Side(style="thick")

# excel helper functions functions
def interpolateColor(startColor, endColor, percent):
    start = tuple(int(startColor[i:i+2], 16) for i in (0, 2, 4))
    end = tuple(int(endColor[i:i+2], 16) for i in (0, 2, 4))

    rgb = tuple(
        round(start[j] + (end[j] - start[j]) * percent)
        for j in range(3)
    )

    return "".join(f"{value:02X}" for value in rgb)

def addFilter(ws):
    # Add filters to every column
    for row in ws.iter_rows():
        if any("Rank" in str(cell.value) for cell in row):
            headerRow = row[0].row

            # Add filters
            ws.auto_filter.ref = (
                f"A{headerRow}:"
                f"{ws.cell(ws.max_row, ws.max_column).coordinate}"
            )

            # Freeze header row and all rows above it
            ws.freeze_panes = f"A{headerRow + 1}"

            break

def colorRankings(filePath):

    wb = load_workbook(filePath)

    greenColors = [
        "147D39", "208A43", "31994E", "49A75F",
        "62B674", "7CC48B", "96D2A3", "B1DFBB",
        "CCEBD3", "E5F5E9"
    ]

    redColors = [
        "FBDADA", "F8CACA", "F4B6B6", "EE9D9D",
        "E88080", "DF6262", "D54747", "C92F2F",
        "B91F1F", "991B1B"
    ]

    # Loop through every worksheet
    for ws in wb.worksheets:

        # Find row containing "Rank"
        for row in ws.iter_rows():
            if any("Rank" in str(cell.value) for cell in row):
                rankRow = row[0].row + 1

                # Find every column with a Rank header
                for cell in row:

                    if cell.value == "Running Avg":
                        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
                        
                    # if cell.value != "Rank":
                    if "Rank" not in str(cell.value):
                        continue

                    rankCol = cell.column

                    # Color each rank in that column
                    for row in range(rankRow, ws.max_row + 1):
                            
                        rankCell = ws.cell(row=row, column=rankCol)
                        rank = rankCell.value

                        if not isinstance(rank, (int, float)):
                            continue

                        rank = int(rank)

                        if 1 <= rank <= 10:
                            color = greenColors[rank - 1]

                        elif 23 <= rank <= 32:
                            color = redColors[rank - 23]

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

#########################
## main excelfunctions ##
#########################

def exportOverallPosRanks(df, option, excelFile):

    if option == "allowed":
        optionTitle = "Allowed"
    else: optionTitle = "Scored"
    print(f"Finished creating Points {optionTitle} excel file: {excelFile}")

    with pd.ExcelWriter(excelFile, engine="openpyxl") as writer:

        # Start the table on row 3, leaving room for the title
        df.to_excel(
            writer,
            sheet_name="Points " + optionTitle,
            startrow=1
        )

        ws = writer.sheets["Points " + optionTitle]

        formatCells(ws)

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
        title.value = f"Points {optionTitle} By Position"
        title.font = Font(size=20, bold=True)
        title.alignment = Alignment(horizontal="center", vertical="center")

        # Increase the title row's height
        ws.row_dimensions[1].height = 35

        addFilter(ws)

    # Color rankings in excel
    colorRankings(excelFile)

    return excelFile

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

def exportWeeklyPosReport(excelFile, weeklyPosReportData, option):

    with pd.ExcelWriter(excelFile, engine="openpyxl") as writer:

        for pos in POSITIONS:

            df = createPositionDataFrame(weeklyPosReportData[pos])

            title = pos + f" - Points {option.capitalize()} By Week"
            writePositionSheet(writer, df, pos, title)

    # Color rankings in excel
    colorRankings(excelFile)

    print(f"Saved Excel file to {excelFile}")

    return excelFile

def writePositionSheet(writer, df, pos, title):
    sheetName = pos.replace("/", "_")

    df.to_excel(writer, sheet_name=sheetName, startrow=1, index=False)

    ws = writer.sheets[sheetName]

    formatCells(ws)

    # Remove the extra row pandas creates
    ws.delete_rows(4)
    ws["A2"] = "PLayer Rank"
    writeTitle(ws, title)

    addFilter(ws)

    return ws    

def writePositionSheetColorSched(writer, df, pos):
    sheetName = pos.replace("/", "_")

    df.to_excel(writer, sheet_name=sheetName)

    ws = writer.sheets[sheetName]

    return ws 

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

def exportNflSSchedule(df, excelFile):
    # Name the left-most index
    df.index.name = "Team"

    # Write to Excel
    df.to_excel(excelFile, sheet_name="NFL Schedule")

    # formatting
    wb = load_workbook(excelFile)
    ws = wb["NFL Schedule"]
    formatCells(ws)
    formatScheduleSheet(ws, config.currLiveWeek)

    wb.save(excelFile)

    return excelFile

def colorScheduleByPosition(schedule, filePath, pos, currentWeek):

    wb = load_workbook(filePath)
    ws = wb["NFL Schedule"]

    formatCells(ws)

    for row in range(2, ws.max_row + 1):

        for col in range(2, ws.max_column + 1):

            cell = ws.cell(row=row, column=col)
            opponent = cell.value
            opponent = opponent.replace("*","")

            if opponent == "BYE":
                continue

            rank = schedule[opponent]["ranks"][pos]

            # Rank 1-10 = green
            if rank <= 10:
                color = greenColors[rank - 1]
                cell.fill = PatternFill(
                    fill_type="solid",
                    fgColor=color
                )

            # Rank 23-32 = red
            elif rank >= 23:
                color = redColors[rank - 23]
                cell.fill = PatternFill(
                    fill_type="solid",
                    fgColor=color
                )

    formatScheduleSheet(ws, currentWeek)

    wb.save(filePath)

def exportColorNflSSchedule(df, schedule, excelFile, currentWeek):

    with pd.ExcelWriter(excelFile, engine="openpyxl") as writer:

        for pos in POSITIONS:

            ws = writePositionSheetColorSched(writer, df, pos)

            formatCells(ws)

            for row in range(2, ws.max_row + 1):

                for col in range(2, ws.max_column + 1):

                    cell = ws.cell(row=row, column=col)
                    opponent = cell.value
                    opponent = opponent.replace("*","")

                    if opponent == "BYE":
                        continue

                    rank = schedule[opponent]["ranks"][pos]

                    # Rank 1-10 = green
                    if rank <= 10:
                        color = greenColors[rank - 1]
                        cell.fill = PatternFill(
                            fill_type="solid",
                            fgColor=color
                        )

                    # Rank 23-32 = red
                    elif rank >= 23:
                        color = redColors[rank - 23]
                        cell.fill = PatternFill(
                            fill_type="solid",
                            fgColor=color
                        )

            formatScheduleSheet(ws, currentWeek)

    print(f"Saved Excel file to {excelFile}")

    return excelFile

def formatCells(ws: Worksheet):
    for row in ws.iter_rows():
        ws.row_dimensions[row[0].row].height = 34

        for cell in row:
            cell.alignment = Alignment(horizontal="center", vertical="center")

def formatScheduleSheet(ws: Worksheet, currentWeek):

    # Row 1
    for cell in ws[1]:
        cell.border = Border(bottom=thin)

    # Column 1
    for row in range(1, ws.max_row + 1):

        cell = ws.cell(row=row, column=1)

        if row == 1:
            cell.border = Border(
                bottom=thin,
                right=thin
            )
        else:
            cell.border = Border(right=thin)

    currentWeekCol = currentWeek + 1

    for row in range(1, ws.max_row + 1):

        cell = ws.cell(row=row, column=currentWeekCol)

        cell.font = Font(bold=True)

        if row == 1:
            cell.border = Border(
                left=thick,
                right=thick,
                top=thick,
                bottom=thin
            )

        elif row == ws.max_row:
            cell.border = Border(
                left=thick,
                right=thick,
                bottom=thick
            )

        else:
            cell.border = Border(
                left=thick,
                right=thick
            )

def printWeightedScoresToExcel(playersList, filePath, ptThreshold=0):

    scoreTypes = [
        "weightedScore1",
        "weightedScore2",
        "weightedScore3",
        "weightedScore4"
    ]

    with pd.ExcelWriter(filePath, engine="openpyxl") as writer:

        for scoreType in scoreTypes:

            # Sort players by weighted score (highest first)
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

            # Write to separate worksheet
            sheetName = scoreType.replace("weightedScore", "WS")
            df.to_excel(
                writer,
                sheet_name=sheetName,
                index=False
            )

            ws = writer.sheets[sheetName]

            # Add Excel filters
            ws.auto_filter.ref = ws.dimensions

            # Freeze header row
            ws.freeze_panes = "A2"

            # Adjust column widths
            for col in ws.columns:
                maxLength = max(
                    len(str(cell.value))
                    if cell.value is not None else 0
                    for cell in col
                )

                ws.column_dimensions[col[0].column_letter].width = maxLength + 2

            formatCells(ws)

    colorRankings(filePath)
    print(f"Weighted Score report saved to {filePath}")

def exportWeightedScores(playersWSRanks, filePath):

    with pd.ExcelWriter(filePath, engine="openpyxl") as writer:

        for scoreType, df in playersWSRanks.items():

            # Write to separate worksheet
            sheetName = scoreType.replace("weightedScore", "WS")
            df.to_excel(
                writer,
                sheet_name=sheetName,
                index=False
            )

            ws = writer.sheets[sheetName]

            # Add Excel filters
            ws.auto_filter.ref = ws.dimensions

            # Freeze header row
            ws.freeze_panes = "A2"

            # Adjust column widths
            for col in ws.columns:
                maxLength = max(
                    len(str(cell.value))
                    if cell.value is not None else 0
                    for cell in col
                )

                ws.column_dimensions[col[0].column_letter].width = maxLength + 2

            formatCells(ws)

    colorRankings(filePath)
    print(f"Weighted Score report saved to {filePath}")

    return filePath
    
def exportRealPosRanks(realPosRanksDF, excelFile):

    with pd.ExcelWriter(excelFile, engine="openpyxl") as writer:

        for pos, df in realPosRanksDF.items():

            sheetName = pos.replace("/", "_")

            df.to_excel(
                writer,
                sheet_name=sheetName,
                index=False
            )

            ws = writer.sheets[sheetName]

            # Add Excel filters
            ws.auto_filter.ref = ws.dimensions

            # Freeze header row
            ws.freeze_panes = "A2"

            # Adjust column widths
            for col in ws.columns:
                maxLength = max(
                    len(str(cell.value))
                    if cell.value is not None else 0
                    for cell in col
                )

                ws.column_dimensions[
                    col[0].column_letter
                ].width = maxLength + 2

            formatCells(ws)

    colorRankings(excelFile)

    print(f"Saved Excel file to {excelFile}")

    return excelFile 

def closeExcelFile(filePath):

    fileName = Path(filePath).name

    try:
        excel = win32com.client.GetActiveObject("Excel.Application")
        workbooks = excel.Workbooks
    except Exception:
        return

    for workbook in workbooks:

        if workbook.Name.lower() == fileName.lower():
            workbook.Close(SaveChanges=False)
            return