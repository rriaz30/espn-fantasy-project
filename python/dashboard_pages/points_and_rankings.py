import streamlit as dashboard

import espn_data
import constants
import config
import pandas as pd
from . import helper

def render(allTeamStats):
    dashboard.title("Points & Rankings")
    dashboard.write("View NFL positional rankings.")

    # submenu
    pointsMenu = dashboard.radio(
        "Select Report Type",
        [
            "Overall Points & Rankings",
            "Weekly Points & Rankings",
            "Filter Trailing Weeks Points & Rankings"
        ],
        horizontal=True
    )

    if pointsMenu == "Overall Points & Rankings":

        dashboard.metric("Latest Completed Week", config.currDataWeek)

        dashboard.subheader("Overall Positional Rankings")

        option = dashboard.selectbox(
            "Points Type",
            ["allowed", "scored"]
        )

        dataFrame = espn_data.getOverallPosRanks(allTeamStats, option)

        dataFrameLogo = dataFrame.copy()

        columnConfig, rowHeight, dataCol = helper.formatDF(dataFrameLogo)

        dashboard.dataframe(
            dataFrameLogo,
            row_height=rowHeight,
            hide_index=True,
            column_config=columnConfig
        )

    elif pointsMenu == "Weekly Points & Rankings":

        dashboard.metric("Weekly Breakdown - Latest Completed Week", config.currDataWeek)

        dashboard.subheader("Weekly Breakdown Positional Rankings")

        col1, col2 = dashboard.columns(2)

        with col1:
            pos = dashboard.selectbox(
                "Position",
                constants.POSITIONS,
                key="realPos"
            )

        with col2:
            option = dashboard.selectbox(
                "Points Type",
                ["allowed", "scored"]
            )

        dataFrame = espn_data.getWeeklyPosReportData(allTeamStats, option)

        dataFrameLogo = dataFrame[pos].copy()

        columnConfig, rowHeight, dataCol = helper.formatDF(dataFrameLogo)

        dataFrameLogo.columns = pd.MultiIndex.from_tuples([
            ("", "Team") if col[0] == "Team" else
            ("", "Logo") if col[0] == "Logo" else
            col
            for col in dataFrameLogo.columns
        ])

        dashboard.dataframe(
            dataFrameLogo,
            hide_index=True,
            width="stretch",
            row_height=rowHeight,
            column_config={
                2: dashboard.column_config.ImageColumn(
                    width=70
                )
            }
        )

    elif pointsMenu == "Filter Trailing Weeks Points & Rankings":

        dashboard.metric("Points & Ranks Filtered - Latest Completed Week", config.currDataWeek)

        dashboard.subheader("Filtered Positional Rankings")

        col1, col2, col3 = dashboard.columns(3)

        with col1:
            pos = dashboard.selectbox(
                "Position",
                constants.POSITIONS,
                key="realPos"
            )

        with col2:
            option = dashboard.selectbox(
                "Points Type",
                ["allowed", "scored"]
            )

        with col3:
            trailingWeeks = dashboard.selectbox(
                "Previous Weeks",
                [0] + list(range(1, config.currDataWeek + 1)),
                format_func=lambda x: "All Weeks" if x == 0 else f"Last {x}",
                key="realTrailingWeeks"
            )

        dataFrame = espn_data.getWeeklyPosReportData(allTeamStats, option, trailingWeeks)

        dataFrameLogo = dataFrame[pos].copy()

        columnConfig, rowHeight, dataCol = helper.formatDF(dataFrameLogo)

        dataFrameLogo.columns = pd.MultiIndex.from_tuples([
            ("", "Team") if col[0] == "Team" else
            ("", "Logo") if col[0] == "Logo" else
            col
            for col in dataFrameLogo.columns
        ])

        dashboard.dataframe(
            dataFrameLogo,
            hide_index=True,
            width="stretch",
            row_height=rowHeight,
            column_config={
                2: dashboard.column_config.ImageColumn(
                    width=70
                )
            }
        )