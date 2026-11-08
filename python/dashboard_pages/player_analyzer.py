import streamlit as dashboard

import analyzer
import config
from . import helper

def render(allTeamStats, players, nflSchedule):
    dashboard.title("Player Projections")
    dashboard.write("Compare players using weighted-score projections.")

    # User inputs
    col1, col2, col3, col4 = dashboard.columns(4)

    with col1:
        pos = dashboard.selectbox(
            "Position",
            ["QB", "RB", "WR", "TE", "K", "D/ST"]
        )

    with col2:
        trailingWeeks = dashboard.selectbox(
            "Previous Weeks",
            [0] + list(range(1, config.currDataWeek + 1)),
            format_func=lambda x: "All Weeks" if x == 0 else str(x)
        )

    with col3:
        futureWeek = dashboard.selectbox(
            "Future Week",
            [0] + list(range(config.currLiveWeek+1, 19)),
            format_func=lambda x: "Current Matchup" if x == 0 else f"Week {x}"
        )

    with col4:
        ptThreshold = dashboard.number_input(
            "Minimum Weighted Score",
            min_value=0.0,
            value=5.0,
            step=1.0
        )

    scoreType = dashboard.selectbox(
        "Weighted Score Algorithm",
        [
            "weightedScore1",
            "weightedScore2",
            "weightedScore3",
            "weightedScore4"
        ],
        index=2
    )

    # Calculate rankings using existing backend
    playersWSRanks = analyzer.getFAvsProjection(
        allTeamStats,
        players,
        nflSchedule,
        pos,
        trailingWeeks=trailingWeeks,
        futureWeek=futureWeek,
        ptThreshold=ptThreshold
    )

    # Select ranking table
    playerDF = playersWSRanks[scoreType]

    dashboard.subheader(f"{pos} Player Rankings")

    rankColumns = ["Team Rank", "Opp Rank"]

    coloredPlayerDF = playerDF.style.map(
        helper.colorRank,
        subset=rankColumns
    )

    dashboard.dataframe(
        coloredPlayerDF,
        hide_index=True,
        width="stretch",
        column_config={
            "Weighted Score": dashboard.column_config.NumberColumn(
                "Projected Points",
                format="%.1f"
            )
        }
    )