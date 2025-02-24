import subprocess
import sys

# Function to install a package using pip
def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

# List of required packages
packages = [
    "streamlit",
    "pandas",
    "mplsoccer",
    "numpy",
    "matplotlib",
    "seaborn",
    "statsbombpy"
]

# Install all required packages
for package in packages:
    try:
        install(package)
    except subprocess.CalledProcessError as e:
        print(f"Failed to install {package}: {e}")

# Import necessary libraries after installation
import streamlit as st
import pandas as pd
from mplsoccer import Pitch
import matplotlib.pyplot as plt
import seaborn as sns
from statsbombpy import sb

# Function to load match data
def load_match_data():
    # Fetch all competitions
    competitions = sb.competitions()

    # Fetch FIFA 2022 matches
    fifa22_matches = sb.matches(competition_id=43, season_id=106)

    # Filter Brazil matches
    brazil_matches = fifa22_matches[(fifa22_matches['home_team'] == 'Brazil') | (fifa22_matches['away_team'] == 'Brazil')]

    # Get match IDs
    match_ids = list(brazil_matches['match_id'])

    return competitions, fifa22_matches, brazil_matches, match_ids

# Function to fetch and preprocess event data for selected match
def fetch_event_data(selected_match_id):
    # Fetch event data for selected match
    event_data = sb.events(match_id=selected_match_id)

    # Convert location and pass_end_location to tuples
    event_data['location'] = event_data['location'].apply(tuple)
    event_data['pass_end_location'] = event_data['pass_end_location'].apply(tuple)

    # Filter events for selected match and sort by time
    event_data = event_data[event_data['match_id'] == selected_match_id].sort_values(by=['minute', 'second'])

    return event_data

# Function to visualize pass network
def visualize_pass_network(event_data, opp_team):
    # Filter pass events
    pass_events = event_data[event_data['type'] == 'Pass']

    # Filter successful passes
    successful_passes = pass_events[pass_events['pass_outcome'].isnull()]

    # Calculate average pass locations
    avg_locations = successful_passes.groupby('player')['location'].apply(lambda x: pd.Series(x.mean())).reset_index()
    avg_locations.columns = ['player', 'avg_location']

    # Plotting pass network
    pitch = Pitch(pitch_type='statsbomb', pitch_color='#22312b', line_color='#c7d5cc')
    fig, ax = pitch.draw(figsize=(16, 11), constrained_layout=True, tight_layout=False)
    fig.set_facecolor('#22312b')

    # Plot successful passes
    for i, row in successful_passes.iterrows():
        ax.plot([row['location'][0], row['pass_end_location'][0]], [row['location'][1], row['pass_end_location'][1]],
                color='#19AE47', zorder=2, alpha=0.8)

    # Plot average pass locations
    for i, row in avg_locations.iterrows():
        ax.scatter(row['avg_location'][0], row['avg_location'][1], color='#FFDC02', edgecolors='black', s=200, zorder=3)
        ax.text(row['avg_location'][0], row['avg_location'][1], row['player'], color='white', fontsize=12, ha='center', va='center', zorder=4)

    # Title and annotation
    ax.set_title(f'Brazil vs {opp_team}', color='white', fontsize=30, fontweight='bold', pad=20)
    ax.annotate('FIFA 2022 World Cup Match', xy=(0.5, 1), xytext=(0, 0), xycoords='axes fraction',
                textcoords='offset points', fontsize=20, color='black', va='top', ha='center')

    return fig, ax

# Main function to run Streamlit app
def main():
    st.title("Brazil FIFA 2022 World Cup Pass Network")

    # Load match data
    competitions, fifa22_matches, brazil_matches, match_ids = load_match_data()

    # Select a match
    selected_match_id = st.selectbox("Select a match ID:", options=match_ids)

    # Fetch event data for selected match
    event_data = fetch_event_data(selected_match_id)

    # Identify opposition team
    opp_team_mask = event_data['team'] != 'Brazil'
    opp_team = event_data[opp_team_mask]['team'].unique()[0]

    # Visualize pass network
    fig_pass_network, ax_pass_network = visualize_pass_network(event_data, opp_team)
    st.pyplot(fig_pass_network)

if __name__ == '__main__':
    main()

