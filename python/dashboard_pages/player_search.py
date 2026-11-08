import streamlit as dashboard

import analyzer
import config
from player import Player

def render(players):
    dashboard.title("Player Search")
    dashboard.write("Search for NFL players and analyze their performance.")

    # Search input
    searchInput = dashboard.text_input(
        "Search Player",
        placeholder="Enter player name (e.g. Josh Allen)"
    )

    if searchInput.strip():

        playerFound, matchList = analyzer.playerSearchMatches(
            searchInput,
            players
        )

        if not playerFound:
            dashboard.warning("No matching players found.")

        else:
            dashboard.success(f"Found {len(matchList)} matching players")

            # Select player from search results
            selectedIndex = dashboard.selectbox(
                "Select Player",
                range(len(matchList)),
                format_func=lambda i: (
                    f"{matchList[i][0]['name']} "
                    f"({matchList[i][1]:.1%} Match)"
                )
            )

            # Construct Player object
            selectedPlayer = Player(matchList[selectedIndex][0])

            dashboard.divider()
            dashboard.subheader(selectedPlayer.name)

            # Player information
            col1, col2, col3 = dashboard.columns(3)

            with col1:
                dashboard.metric(
                    "Position",
                    selectedPlayer.pos
                )

            with col2:
                dashboard.metric(
                    "NFL Team",
                    selectedPlayer.getProTeam()
                )

            with col3:
                avgPts, gamesPlayed = selectedPlayer.getAvgPts(
                    1,
                    config.currDataWeek
                )

                dashboard.metric(
                    "Average Points",
                    f"{avgPts:.1f}"
                )

            dashboard.write(f"Games Played: {gamesPlayed}")

            dashboard.divider()

            # Player stat options
            statMenu = dashboard.radio(
                "Select Analysis",
                [
                    "Weekly Points",
                    "Average Points"
                ],
                horizontal=True
            )

            if statMenu == "Weekly Points":

                week = dashboard.selectbox(
                    "Select Week",
                    range(1, config.currDataWeek + 1)
                )

                pts = selectedPlayer.getPtsForWeek(week)

                dashboard.metric(
                    f"Week {week} Points",
                    f"{pts:.1f}"
                )

            elif statMenu == "Average Points":

                col1, col2 = dashboard.columns(2)

                with col1:
                    startWeek = dashboard.selectbox(
                        "Start Week",
                        range(1, config.currDataWeek + 1)
                    )

                with col2:
                    endWeek = dashboard.selectbox(
                        "End Week",
                        range(startWeek, config.currDataWeek + 1),
                        index=config.currDataWeek - startWeek
                    )

                avgPts, gamesPlayed = selectedPlayer.getAvgPts(
                    startWeek,
                    endWeek
                )

                dashboard.metric(
                    "Average Points",
                    f"{avgPts:.1f}"
                )

                dashboard.write(
                    f"Games Played: {gamesPlayed}"
                )