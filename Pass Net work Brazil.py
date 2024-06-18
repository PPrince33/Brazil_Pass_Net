#Libraries 
from statsbombpy import sb
import pandas as pd
from mplsoccer import Pitch
import seaborn as sns
import matplotlib.pyplot as plt
import streamlit as st

#Competition Data Frame
competition=sb.competitions()

#FIFA Matches
fifa22=sb.matches(competition_id=43,season_id=106)
fifa18=sb.matches(competition_id=43,season_id=3)

#Brazil Data Frame
brazil22=fifa22[(fifa22['home_team']=='Brazil')|(fifa22['away_team']=='Brazil')]

#Brazil Match IDs
brazil22_match_id_list=list(brazil22['match_id'])
brazil_match_ids=brazil22_match_id_list

#Select Brazil Match
st.title("Brazil FIFA 2022 World Cup Pass Network")
selected_match_id=st.selectbox("Select a match ID:",options=brazil_match_ids)

#Event Data Frame
event = sb.events(match_id=selected_match_id)

#Opposition Team
opp_team_mask = event['team'] != 'Brazil'
opp_team = event[opp_team_mask]['team'].unique()[0]


#Locations
def convert_to_tuple(x):
    if isinstance(x,list):
        return tuple(x)
    return x

event['location']=event['location'].apply(convert_to_tuple)
event['pass_end_location']=event['pass_end_location'].apply(convert_to_tuple)

#Setting Event Data Frame
event=event[event['match_id']==selected_match_id].sort_values(by=['minute','second'])
event=event[[ 'id','match_id','team', 'team_id',
 'minute','second','type','location','pass_end_location',
 'pass_angle',
 'pass_body_part',
 'pass_height',
 'pass_length','player','player_id',
 'pass_recipient','pass_recipient_id',
 'pass_type',
 'period',
 'play_pattern',
 'position','pass_outcome',
 'possession_team']]

#Pass Event
pass_event=event[event['type']=='Pass']
pass_event['x'] = pass_event['location'].apply(lambda loc: loc[0])
pass_event['endx'] = pass_event['pass_end_location'].apply(lambda loc: loc[0])
pass_event['y'] = pass_event['location'].apply(lambda loc: loc[1])
pass_event['endy'] = pass_event['pass_end_location'].apply(lambda loc: loc[1])
pass_event=pass_event[pass_event['possession_team']=='Brazil']

#Successful Pass
successful=pass_event[pass_event['pass_outcome'].isnull()]

#First Substitution
subs=event[(event['type']=='Substitution')&(event['team']=="Brazil")]
sub_palyers=subs[[ 'minute','second','player']]
st.subheader("Brazil Substitutions")
st.dataframe(sub_palyers)
firstsub=subs[ 'minute'].min()

#Pass Network Before First Substitution
successful=successful[successful['minute']<firstsub]

#Line-up Data Frame
lineup=sb.lineups(match_id=selected_match_id)["Brazil"]
jersey_data=lineup[['player_nickname','player_id','jersey_number']]
st.subheader("Brazil Line-up")
st.dataframe(jersey_data)

#Adding Jersey Number To Successful Passes
successful=pd.merge(successful,jersey_data,on='player_id')
successful.rename(columns={'player_id':'passer_id','player_nickname':'passer_nickname','jersey_number':'passer_jersey_no'},inplace=True)
jersey_data.rename(columns={'player_id':'pass_recipient_id'},inplace=True)
successful=pd.merge(successful,jersey_data,on='pass_recipient_id')
successful.rename(columns={'player_nickname':'recipient_nickname','jersey_number':'recipient_jersey_no'},inplace=True)

#Average Location
avg_locations=successful.groupby('passer_jersey_no').agg({'x':['mean'],'y':['mean','count']})
avg_locations.columns=['x','y','count']

#Pass B/W Players
pass_between=successful.groupby(['passer_jersey_no','recipient_jersey_no']).id.count().reset_index()
pass_between.rename(columns={'id':'pass_count'},inplace=True)
pass_between=pd.merge(pass_between,avg_locations,on='passer_jersey_no')
avg_locations=avg_locations.rename_axis('recipient_jersey_no')
pass_between=pd.merge(pass_between,avg_locations,on='recipient_jersey_no',suffixes=['','_end'])
# pass_between=pass_between[pass_between['pass_count']>3]

#Plotting 
##Set up the pitch
pitch = Pitch(pitch_type='statsbomb', pitch_color='#FFDC02', line_color='black')
fig, ax = pitch.draw(figsize=(16, 11), constrained_layout=True, tight_layout=False)
fig.set_facecolor("black")

##Plot the passing lines
pass_lines = pitch.lines(pass_between['x'], pass_between['y'],
                         pass_between['x_end'], pass_between['y_end'],
                         lw=0.7 * pass_between['pass_count'],
                         color="#193375", zorder=0.7, ax=ax)

##Plot the average locations
pass_nodes = pitch.scatter(avg_locations['x'], avg_locations['y'],
                           s=30 * avg_locations['count'].values,
                           color='#19AE47', edgecolors='black', linewidth=1, ax=ax)

##Annotate the plot
for index, row in avg_locations.iterrows():
    pitch.annotate(index, xy=(row['x'], row['y']), c='#161A30',
                   fontweight='light', va='center', ha='center', size=15, ax=ax)

ax.set_title(f'Brazil vs {opp_team}', color='white', va='center', ha='center',
             fontsize=30, fontweight='bold', pad=20)

ax.annotate('FIFA 2022 World Cup Match', xy=(0.5, 1), xytext=(0, 0),
            xycoords='axes fraction', textcoords='offset points',
            fontsize=20, color='black', va='top', ha='center')

##Display the plot in Streamlit
st.pyplot(fig)

