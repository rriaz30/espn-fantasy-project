import streamlit as dashboard

import analyzer
import constants
import config
from . import helper
import pandas as pd

def render(allTeamStats, players, fantasyTeams):
    dashboard.title("Real Position Rankings")
    dashboard.write("Rank NFL players by actual fantasy points per game.")

    if config.currDataWeek < 1:
        dashboard.warning("No completed weeks are available to rank yet.")
    else:
        col1, col2, col3, col4 = dashboard.columns(4)

        with col1:
            pos = dashboard.selectbox(
                "Position",
                constants.POSITIONS,
                key="realPos"
            )

        with col2:
            trailingWeeks = dashboard.selectbox(
                "Previous Weeks",
                [0] + list(range(1, config.currDataWeek + 1)),
                format_func=lambda x: "All Weeks" if x == 0 else f"Last {x}",
                key="realTrailingWeeks"
            )

        maxGames = trailingWeeks if trailingWeeks else config.currDataWeek

        with col3:
            minGames = dashboard.number_input(
                "Minimum Games",
                min_value=1,
                max_value=maxGames,
                value=min(3, maxGames),
                step=1,
                key="realMinGames"
            )

        with col4:
            minPtsThreshold = dashboard.number_input(
                "Minimum Average Points",
                min_value=0.0,
                value=7.0,
                step=0.5,
                key="realMinPts"
            )

        # Backend computes DataFrames for all positions; select the requested one.
        realPosRanksDF = analyzer.getRealPosRanks(
            allTeamStats,
            players,
            fantasyTeams,
            minPtsThreshold=minPtsThreshold,
            minGames=minGames,
            trailingWeeks=trailingWeeks
        )
        playerDF = realPosRanksDF[pos].copy()

        playerDF["Opp Rank"] = pd.to_numeric(
            playerDF["Opp Rank"],
            errors = "coerce"
        ).astype("Int64")

        dashboard.subheader(f"Top {pos} Players")
        dashboard.caption(
            f"Based on {'all completed weeks' if trailingWeeks == 0 else f'the last {trailingWeeks} weeks'}"
            f" · Minimum {minGames} game(s) · Average above {minPtsThreshold:g} PPG"
        )

        if playerDF.empty:
            dashboard.info("No players match the selected criteria.")
        else:
            # A BYE is text, so do not pass it directly to colorRank().
            def colorOpponentRank(rank):
                if rank == "BYE":
                    return "background-color: #64748b; color: white"
                try:
                    return helper.colorRank(int(rank))
                except (TypeError, ValueError, OverflowError):
                    return ""

            coloredPlayerDF = playerDF.style.map(
                colorOpponentRank,
                subset=["Opp Rank"]
            )

            dashboard.dataframe(
                coloredPlayerDF,
                hide_index=True,
                width="stretch",
                column_config={
                    "Average": dashboard.column_config.NumberColumn(
                        "Average PPG", format="%.2f"
                    )
                }
            )

            dashboard.download_button(
                "Download rankings (CSV)",
                data=playerDF.to_csv(index=False).encode("utf-8"),
                file_name=f"RealPosRanks-{pos.replace('/', '_')}-week-{config.currLiveWeek}.csv",
                mime="text/csv"
            )