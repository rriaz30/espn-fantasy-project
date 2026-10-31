import streamlit as dashboard
from pathlib import Path

import data_service
import espn_data
import config
import analyzer
import constants
import excel_util
from player import Player
import pandas as pd


projectDir = Path(__file__).resolve().parent.parent
dataDir = projectDir / "data"

#####################################################

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

#######################################################

# Load saved data
allTeamStats, nflSchedule, players, fantasyTeams = (
    data_service.loadJsonData(dataDir)
)

dashboard.title("ESPN Fantasy Analyzer")

if not allTeamStats:
    dashboard.error("No saved ESPN data found.")
    dashboard.stop()

dashboard.set_page_config(
    page_title="ESPN Fantasy Analyzer",
    page_icon="🏈",
    layout="wide"
)

# Sidebar main menu
dashboard.sidebar.title("🏈 ESPN Fantasy Analyzer")

menu = dashboard.sidebar.radio(
    "Main Menu",
    [
        "Home",
        "Points & Rankings",
        "NFL Schedules",
        "Player Analyzer",
        "Player Search",
        "Real Position Rankings"
    ]
)

# Display the selected page
#########################################
####################  HOME ##############
#########################################
if menu == "Home":
    dashboard.title("Home")
    dashboard.write("Welcome to your fantasy football analytics dashboard!")

########################################
################ Points Rankings  ######
########################################
elif menu == "Points & Rankings":
    dashboard.title("Points & Rankings")
    dashboard.write("View NFL positional rankings.")

    dashboard.metric("Latest Completed Week", config.currDataWeek)

    dashboard.subheader("Overall Positional Rankings")

    option = dashboard.selectbox(
        "Points Type",
        ["allowed", "scored"]
    )

    dataFrame = espn_data.getOverallPosRanks(allTeamStats, option)

    dataFrameLogo = dataFrame.copy()

    dataFrameLogo.insert(
        0,
        "Team",
        dataFrameLogo.index
    )

    dataFrameLogo.insert(
        1,
        "Logo",
        [constants.TEAM_LOGOS.get(team, "") for team in dataFrameLogo.index]
    )

    dashboard.dataframe(
        dataFrameLogo,
        hide_index=True,
        column_config={"Logo": dashboard.column_config.ImageColumn("Logo", width="small")}
    )

#######################################
############### NFL Schedules    ######
#######################################
elif menu == "NFL Schedules":
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

    ##### formatting 
    nflScheduleLogoDF.insert(
        0,
        "Team",
        nflScheduleLogoDF.index
    )

    nflScheduleLogoDF.insert(
        1,
        "Logo",
        [constants.TEAM_LOGOS.get(team, "") for team in nflScheduleLogoDF.index]
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

    weekColumns = nflScheduleLogoDF.columns[2:]

    for week in weekColumns:
        columnConfig[week] = dashboard.column_config.TextColumn(
            str(week),
            width=70,
            alignment="center"
        )
    ##### done formatting

    if scheduleMenu == "Regular Schedule":
        dashboard.subheader("NFL Regular Season Schedule")

        currentWeek = str(config.currLiveWeek)

        styledSchedule = nflScheduleLogoDF.style

        if currentWeek in weekColumns:
            styledSchedule = styledSchedule.map(
                lambda value: "font-weight: bold",
                subset=[currentWeek]
            )

        dashboard.dataframe(
            styledSchedule,
            row_height=45,
            hide_index=True,
            column_config=columnConfig
        )

    elif scheduleMenu == "Positional Heat Map":
        dashboard.subheader("NFL Schedule Heat Map")

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
            row_height=45,
            hide_index=True,
            column_config=columnConfig
        )

#########################################
################# Player Analyzer  ######
#########################################
elif menu == "Player Analyzer":
    dashboard.title("Player Analyzer")
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
        colorRank,
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

##########################################
################## Player Search    ######
##########################################
elif menu == "Player Search":
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

##########################################
################## Real Pos Rankings #####
##########################################
elif menu == "Real Position Rankings":
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
                    return colorRank(int(rank))
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