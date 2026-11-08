import constants
import streamlit as dashboard

# Helper functions

def colorRank(rank):
    if 1 <= rank <= 10:
        color = constants.GREEN_COLORS[rank - 1]

    elif 23 <= rank <= 32:
        color = constants.RED_COLORS[rank - 23]

    else:
        return ""

    textColor = "white" if rank <= 3 or rank >= 30 else "black"

    return f"background-color: #{color}; color: {textColor}"

def formatDF(dataFrame):

    rowHeight = 45

    dataFrame.insert(
        0,
        "Team",
        dataFrame.index
    )

    dataFrame.insert(
        1,
        "Logo",
        [constants.TEAM_LOGOS.get(team, "") for team in dataFrame.index]
    )

    columnConfig = {
        "Team": dashboard.column_config.TextColumn(
            "Team",
            width=50,
            pinned=True,
            alignment="center"
        ),
        "Logo": dashboard.column_config.ImageColumn(
            "Logo",
            width=65,
            pinned=True
        )
    }

    dataColumns = dataFrame.columns[2:]

    # for data in dataColumns:
    #     columnConfig[data] = dashboard.column_config.TextColumn(
    #         str(data),
    #         width=70,
    #         alignment="center"
    #     )

    return columnConfig, rowHeight, dataColumns

