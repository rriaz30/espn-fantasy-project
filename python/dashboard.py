import streamlit as dashboard
from pathlib import Path
import data_service
from dashboard_pages import (
    nfl_schedules, 
    points_and_rankings, 
    home, 
    player_analyzer, 
    player_search, 
    real_pos_rankings
)


projectDir = Path(__file__).resolve().parent.parent
dataDir = projectDir / "data"

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
        "NFL Schedules",
        "Points & Rankings",
        "Player Projections",
        "Player Search",
        "Real Position Rankings"
    ]
)

dashboard.set_page_config(
    page_title=f"{menu} | ESPN Fantasy Analyzer"
)

# Display the selected page
if menu == "Home":
    home.render(dataDir)

elif menu == "NFL Schedules":
    nfl_schedules.render(allTeamStats, nflSchedule)

elif menu == "Points & Rankings":
    points_and_rankings.render(allTeamStats)

elif menu == "Player Projections":
    player_analyzer.render(allTeamStats, players, nflSchedule)

elif menu == "Player Search":
    player_search.render(players)

elif menu == "Real Position Rankings":
    real_pos_rankings.render(allTeamStats, players, fantasyTeams)