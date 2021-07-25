import pandas as pd
import numpy as np
from datetime import datetime
from data_manager import get_all_games, get_games_list, get_data_dragon_file, upload_to_big_query
import json
import logging
from data_procesing import calculate_kda, calculate_kp, calculate_list_of_solo_kills_and_deaths, \
    generate_timeline_player_dataframe, generate_champion_dataframe, replace_championId_with_champion_name

logging.basicConfig(filename='example.log', filemode='w', level=logging.DEBUG)
links = get_games_list()

all_games_data = get_all_games(links)
solo_kills_and_deaths_dataframe = calculate_list_of_solo_kills_and_deaths(all_games_data)

# Getting participant identities in order to use it later.
participants_identities = pd.json_normalize(all_games_data, 'participantIdentities',
                                            ['gameId', 'platformId', 'gameCreation'])

# Getting game information per player.
game_dataframe = pd.json_normalize(all_games_data, 'participants', ['gameId',
                                                                    'platformId',
                                                                    'gameCreation',
                                                                    'gameDuration',
                                                                    'queueId',
                                                                    'mapId',
                                                                    'seasonId',
                                                                    'gameVersion',
                                                                    'gameMode',
                                                                    'gameType',
                                                                    'tournament'])

# Drop timeline information that is not used
game_dataframe.drop(['timeline.participantId', 'timeline.creepsPerMinDeltas.10-20', 'timeline.creepsPerMinDeltas.0-10',
                     'timeline.creepsPerMinDeltas.30-end', 'timeline.creepsPerMinDeltas.20-30',
                     'timeline.xpPerMinDeltas.10-20', 'timeline.xpPerMinDeltas.0-10', 'timeline.xpPerMinDeltas.30-end',
                     'timeline.xpPerMinDeltas.20-30', 'timeline.goldPerMinDeltas.10-20',
                     'timeline.goldPerMinDeltas.0-10', 'timeline.goldPerMinDeltas.30-end',
                     'timeline.goldPerMinDeltas.20-30', 'timeline.damageTakenPerMinDeltas.10-20',
                     'timeline.damageTakenPerMinDeltas.0-10', 'timeline.damageTakenPerMinDeltas.30-end',
                     'timeline.damageTakenPerMinDeltas.20-30', 'timeline.role', 'timeline.lane'], axis=1, inplace=True)

# Replace win and fail with 0 and 1 for calculations
game_dataframe.replace({'win': {'Fail': 0, 'Win': 1}}, inplace=True)

# Replaces True and False with 1 and 0 for persentages and averages.
game_dataframe.replace({'False': 0, 'True': 1}, inplace=True)

# Rename teams to Blue and Red
game_dataframe.replace({'teamId': {100: 'Blue', 200: 'Red'}}, inplace=True)

# Transforme gameCreation to date format.
game_dataframe['gameDate'] = game_dataframe['gameCreation'].apply(lambda x: datetime.fromtimestamp(x // 1000))

# Split team name and player name from the ID.
participants_identities['player.summonerName'] = participants_identities['player.summonerName'].str.strip()
temp_list = participants_identities['player.summonerName'].str.split(" ", 1, expand=True)
game_dataframe["summonerName"] = temp_list[1]
game_dataframe["teamName"] = temp_list[0]

# Calculate solo kills and deaths and join them to the player.
game_dataframe = pd.merge(game_dataframe, solo_kills_and_deaths_dataframe, on=['gameId', 'stats.participantId'])

# Add role to players.
role_dataframe = pd.DataFrame(
    {'participantId': range(1, 11), 'role': ['TOP', 'JG', 'MID', 'ADC', 'SUPP', 'TOP', 'JG', 'MID', 'ADC', 'SUPP']})
game_dataframe = pd.merge(game_dataframe, role_dataframe, on='participantId', how='inner')

# Calculating KDA
game_dataframe = calculate_kda(game_dataframe)

# Calculating Kill Participation
game_dataframe = calculate_kp(game_dataframe)


# Sorting dataframe by game and player
game_dataframe = game_dataframe.sort_values(by=['gameCreation', 'participantId'], ignore_index=True)

# Add champion Names
game_dataframe.loc[:,'championName'] = replace_championId_with_champion_name(game_dataframe.championId, game_dataframe.gameVersion.iat[-1])
game_dataframe.columns = game_dataframe.columns.str.replace("\.", "_", regex=True)

# Saving the dataframe without index.
game_dataframe.to_csv('data/interm/game.csv', index=False)
upload_to_big_query(game_dataframe, "game")

# Get Data Dragon information for champions, items and summoner spells
for version in pd.unique(game_dataframe.gameVersion):
    get_data_dragon_file(version, 'champion')
    get_data_dragon_file(version, 'item')
    get_data_dragon_file(version, 'summoner')

# Normalize team information
teams_dataframe = pd.json_normalize(all_games_data, 'teams', ['gameId',
                                                              'platformId',
                                                              'gameCreation',
                                                              'gameDuration',
                                                              'queueId',
                                                              'mapId',
                                                              'seasonId',
                                                              'gameVersion',
                                                              'gameMode',
                                                              'gameType',
                                                              'tournament'])

# Rename teams to Blue and Red
teams_dataframe.replace({'teamId': {100: 'Blue', 200: 'Red'}}, inplace=True)

# Replaces True and False with 1 and 0 for persentages and averages.
teams_dataframe.replace({'win': {'Fail': 0, 'Win': 1}}, inplace=True)

# Replaces True and False with 1 and 0 for persentages and averages.
teams_dataframe.replace({False: 0, True: 1}, inplace=True)

# Transforme gameCreation to date format.
teams_dataframe['gameDate'] = teams_dataframe['gameCreation'].apply(lambda x: datetime.fromtimestamp(x // 1000))
teams_dataframe = pd.merge(teams_dataframe, game_dataframe[['gameId', 'teamId', 'teamName']].drop_duplicates(),
                           on=['gameId', 'teamId'], how='inner')

# Expand and deletes banns from team dataframe and rename columns for clarity.
bans_dataframe = teams_dataframe.explode('bans', ignore_index=True)
bans_dataframe = pd.concat([bans_dataframe, bans_dataframe.bans.apply(pd.Series)], axis='columns')
bans_dataframe.rename(columns={"championId": "banned_champion_id", "pickTurn": "ban_turn"}, inplace=True)
bans_dataframe = bans_dataframe.drop('bans', axis=1)

# Add champion Names
bans_dataframe.loc[:,'championName'] = replace_championId_with_champion_name(bans_dataframe.banned_champion_id, bans_dataframe.gameVersion.iat[-1])
bans_dataframe.columns = bans_dataframe.columns.str.replace("\.", "_", regex=True)

# Remove Banns from Team Dataframe.
teams_dataframe = teams_dataframe.drop('bans', axis=1)
teams_dataframe.columns = teams_dataframe.columns.str.replace("\.", "_", regex=True)


# Generate Timeline Dataframe
timeline_dataframe = generate_timeline_player_dataframe(all_games_data)

# Add Timeline Dataframe to players name
timeline_dataframe = pd.merge(timeline_dataframe, game_dataframe[
    ['gameId', 'stats_participantId', 'teamName', 'summonerName']].drop_duplicates(),
                              right_on=['gameId', 'stats_participantId'], left_on=['gameId', 'participantId'],
                              how='inner')

# Sort Dataframe by Game date, timestamp and participant ID
timeline_dataframe.sort_values(by=['gameCreation', 'timestamps', 'participantId'], inplace=True)
timeline_dataframe.columns = timeline_dataframe.columns.str.replace("\.", "_", regex=True)

# Save timeline to csv
timeline_dataframe.to_csv('data/interm/player_frames.csv', index=False)
upload_to_big_query(timeline_dataframe, "timeline")

champion_dataframe = generate_champion_dataframe(game_dataframe, bans_dataframe)

champion_dataframe.to_csv('data/interm/champion.csv', index=False)
upload_to_big_query(champion_dataframe, "champion")

# Save Teams to csv
teams_dataframe.to_csv('data/interm/teams.csv', index=False)
upload_to_big_query(teams_dataframe, "teams")

# Saves Banns to csv.
bans_dataframe.to_csv('data/interm/bans.csv', index=False)
upload_to_big_query(bans_dataframe, "bans")
