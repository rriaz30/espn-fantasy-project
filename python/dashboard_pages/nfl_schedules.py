import streamlit as dashboard

import analyzer
import espn_data
import excel_util
import constants
import config
from . import helper

def render(allTeamStats, nflSchedule):

    dashboard.title("NFL Schedules")
    dashboard.write("Analyze upcoming NFL matchups.")

    # submenu
    scheduleMenu = dashboard.radio(
        "Select Schedule Type",
        [
            "Regular Schedule",
            "Positional Heat Map"
        ],
        horizontal=True
    )

    # get nfl schedule data into data frame
    nflScheduleDF = espn_data.getNflScheduleDF(nflSchedule)
    nflScheduleLogoDF = nflScheduleDF.copy()

    columnConfig, rowHeight, weekColumns = helper.formatDF(nflScheduleLogoDF)

    if scheduleMenu == "Regular Schedule":
        dashboard.subheader(f"NFL Regular Season Schedule - Current Week - {config.currLiveWeek}")

        currentWeek = str(config.currLiveWeek)

        styledSchedule = nflScheduleLogoDF.style

        if currentWeek in weekColumns:
            styledSchedule = styledSchedule.map(
                lambda value: "font-weight: bold",
                subset=[currentWeek]
            )

        dashboard.dataframe(
            styledSchedule,
            row_height=rowHeight,
            hide_index=True,
            column_config=columnConfig
        )

    elif scheduleMenu == "Positional Heat Map":
        dashboard.subheader(f"NFL Schedule Heat Map - Current Week - {config.currLiveWeek}")

        pos = dashboard.selectbox(
            "Select Position",
            ["QB", "RB", "WR", "TE", "K", "D/ST"]
        )

        option = dashboard.selectbox(
            "Points Type",
            ["allowed", "scored"]
        )

        nflScheduleRanks = analyzer.getPosRanks(allTeamStats, nflSchedule, option)

        def colorGame(opponent):
            # Remove away-game marker
            team = str(opponent).replace("*", "")

            if team == "BYE":
                return "background-color: #64748b; color: white"

            rank = nflScheduleRanks[team]["ranks"][pos]

            if 1 <= rank <= 10:
                color = excel_util.greenColors[rank - 1]

            elif 23 <= rank <= 32:
                color = excel_util.redColors[rank - 23]

            else:
                return ""

            # White text on the darkest colors
            if rank <= 3 or rank >= 30:
                return f"background-color: #{color}; color: white"

            return f"background-color: #{color}; color: black"

        coloredSchedule = nflScheduleLogoDF.style.map(colorGame, subset=weekColumns)

        currentWeek = str(config.currLiveWeek)

        if currentWeek in weekColumns:
            coloredSchedule = coloredSchedule.map(
                lambda value: "font-weight: bold",
                subset=[currentWeek]
            )

        dashboard.dataframe(
            coloredSchedule,
            row_height=rowHeight,
            hide_index=True,
            column_config=columnConfig
        )