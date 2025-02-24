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
import numpy as np
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
    brazil_matches = fifa22_matches[
        (fifa22_matches['home_team'] == 'Brazil') | (fifa22_matches['away_team'] == 'Brazil')
    ]

    # Get match IDs
    match_ids = list(brazil_matches['match_id'])

    return competitions, fifa22_matches, brazil_matches, match_ids

# Helper function to safely convert a value to a tuple
def safe_convert(x):
    try:
        # Only convert if the value is not null, is iterable, and not a string/bytes
        if pd.notnull(x) and hasattr(x, '__iter__') and not isinstance(x, (str, bytes)):
            return tuple(x)
    except Exception:
        pass
    return None

# Function to fetch and preprocess event data for selected match
def fetch_event_data(selected_match_id):
    # Fetch event data for selected match
    event_data = sb.events(match_id=selected_match_id)

    # Safely convert 'location' and 'pass_end_location' to tuples
    event_data['location'] = event_data['location'].apply(safe_convert)
    event_data['pass_end_location'] = event_data['pass_end_location'].apply(safe_convert)

    # Filter events for selected match and sort by time
    event_data = event_data[event_data['match_id'] == selected_match_id].sort_values(by=['minute', 'second'])

    return event_data

# Function to compute average location from a series of tuples
def average_tuple(locs):
    # Remove any None values before averaging
    valid_locs = [loc for loc in locs if loc is not None]
    if valid_locs:
        # Convert to numpy array and calculate mean along each coordinate
        locs_array = np.array(valid_locs)
        return tuple(locs_array.mean(axis=0))
    return None

# Function to visualize pass network
def visualize_pass_network(event_data, opp_team):
    # Filter pass events
    pass_events = event_data[event_data['type'] == 'Pass']

    # Filter successful passes (i.e. passes with no outcome indicating a problem)
    successful_passes = pass_events[pass_events['pass_outcome'].isnull()]

    # Calculate average pass locations per player
    avg_locations = (
        successful_passes.groupby('player')['location']
        .apply(average_tuple)
        .reset_index()
        .rename(columns={'location': 'avg_location'})
    )

    # Plotting pass network using mplsoccer's Pitch
    pitch = Pitch(pitch_type='statsbomb', pitch_color='#22312b', line_color='#c7d5cc')
    fig, ax = pitch.draw(figsize=(16, 11), constrained_layout=True, tight_layout=False)
    fig.set_facecolor('#22312b')

    # Plot each successful pass as a line between start and end locations
    for i, row in successful_passes.iterrows():
        start = row['location']
        end = row['pass_end_location']
        # Only plot if both start and end locations are valid
        if start is not None and end is not None:
            ax.plot(
                [start[0], end[0]],
                [start[1], end[1]],
                color='#19AE47',
                zorder=2,
                alpha=0.8
            )

    # Plot average pass locations for each player
    for i, row in avg_locations.iterrows():
        avg_loc = row['avg_location']
        if avg_loc is not None:
            ax.scatter(avg_loc[0], avg_loc[1], color='#FFDC02', edgecolors='black', s=200, zorder=3)
            ax.text(
                avg_loc[0],
                avg_loc[1],
                row['player'],
                color='white',
                fontsize=12,
                ha='center',
                va='center',
                zorder=4
            )

    # Title and annotation
    ax.set_title(f'Brazil vs {opp_team}', color='white', fontsize=30, fontweight='bold', pad=20)
    ax.annotate(
        'FIFA 2022 World Cup Match',
        xy=(0.5, 1),
        xytext=(0, 0),
        xycoords='axes fraction',
        textcoords='offset points',
        fontsize=20,
        color='black',
        va='top',
        ha='center'
    )

    return fig, ax

# Main function to run Streamlit app
def main():
    st.title("Brazil FIFA 2022 World Cup Pass Network")

    # Load match data
    competitions, fifa22_matches, brazil_matches, match_ids = load_match_data()

    # Select a match
    selected_match_id = st.selectbox("Select a match ID:", options=match_ids)

    # Fetch event data for the selected match
    event_data = fetch_event_data(selected_match_id)

    # Identify the opposition team (i.e. team that is not Brazil)
    opp_team_mask = event_data['team'] != 'Brazil'
    if opp_team_mask.any():
        opp_team = event_data[opp_team_mask]['team'].unique()[0]
    else:
        opp_team = "Unknown"

    # Visualize pass network
    fig_pass_network, ax_pass_network = visualize_pass_network(event_data, opp_team)
    st.pyplot(fig_pass_network)

if __name__ == '__main__':
    main()
