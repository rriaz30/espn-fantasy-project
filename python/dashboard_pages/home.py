
import os
from pathlib import Path

import streamlit as dashboard
from dotenv import load_dotenv

import config
import espn_data
import data_service


def render(dataDir):

    dashboard.title("Home")
    dashboard.write("Manage your ESPN Fantasy Football data.")

    dataDir = Path(dataDir)
    projectDir = dataDir.parent

    load_dotenv(projectDir / ".env")

    year = int(os.environ["ESPN_YEAR"])
    espn_s2 = os.environ["ESPN_S2"]
    swid = os.environ["ESPN_SWID"]

    # Display currently loaded data
    dashboard.subheader("Currently Loaded Data")

    fetchInfoPath = dataDir / "FetchInfo.txt"

    if fetchInfoPath.exists():
        with open(fetchInfoPath, "r", encoding="utf-8") as file:
            dashboard.text(file.read())
    else:
        dashboard.info("No fetch information available.")

    dashboard.divider()
    dashboard.subheader("Change League or Fantasy Team")

    # Select league from config.py
    leagueChoice = dashboard.selectbox(
        "Select Fantasy League",
        list(config.leagues.keys()),
        format_func=lambda key: config.leagues[key][1]
    )

    league_id = config.leagues[leagueChoice][0]

    # Track loaded roster for each selected league
    if "homeLeagueId" not in dashboard.session_state:
        dashboard.session_state.homeLeagueId = None

    if "homeTeamOptions" not in dashboard.session_state:
        dashboard.session_state.homeTeamOptions = {}

    if dashboard.button("Load League Teams"):

        try:
            with dashboard.spinner("Loading fantasy teams..."):

                teamOptions = espn_data.getFantasyTeamOptions(
                    league_id,
                    year,
                    espn_s2,
                    swid
                )

            dashboard.session_state.homeLeagueId = league_id
            dashboard.session_state.homeTeamOptions = teamOptions

        except Exception as error:
            dashboard.error(f"Unable to load league: {error}")

    # Only display teams associated with this league
    if dashboard.session_state.homeLeagueId == league_id:

        teamOptions = dashboard.session_state.homeTeamOptions

        if teamOptions:

            fantasyTeamNum = dashboard.selectbox(
                "Select Your Fantasy Team",
                list(teamOptions.keys()),
                format_func=lambda key: teamOptions[key]
            )

            dashboard.write(
                f"Selected: {teamOptions[fantasyTeamNum]}"
            )

            if dashboard.button(
                "Fetch ESPN Data",
                type="primary"
            ):

                try:
                    with dashboard.spinner(
                        "Fetching and calculating ESPN data..."
                    ):

                        data_service.fetchESPNdata(
                            dataDir,
                            league_id,
                            year,
                            espn_s2,
                            swid,
                            fantasyTeamNum=fantasyTeamNum
                        )

                    dashboard.success(
                        "ESPN data fetched successfully."
                    )

                    dashboard.rerun()

                except Exception as error:
                    dashboard.error(
                        f"Unable to fetch ESPN data: {error}"
                    )
