import logging
import numpy as np
import pandas as pd
import json
from data_manager import get_data_dragon_file


def calculate_list_of_solo_kills_and_deaths(list_of_games):
    logging.debug("Calculating all solo Kills and Deaths:")
    dataframes = list()
    for game in list_of_games:
        dataframes.append(calculate_solo_kills_and_deaths(game))
    result_dataframe = pd.concat(dataframes)
    logging.debug(f"Average Solo Kills per player {result_dataframe.soloKills.mean()}.")
    return pd.concat(dataframes)


def calculate_solo_kills_and_deaths(game_json):
    solo_kills_and_deaths = np.zeros((len(game_json['participants']), 2))
    frames = game_json['timeline']['frames']
    for frame in frames:
        for event in frame['events']:
            if event["type"] == 'CHAMPION_KILL':
                if len(event["assistingParticipantIds"]) == 0:
                    solo_kills_and_deaths[event["killerId"] - 1][0] += 1
                    solo_kills_and_deaths[event["victimId"] - 1][1] += 1
    dataframe = pd.DataFrame(solo_kills_and_deaths)
    dataframe['gameId'] = game_json['gameId']
    dataframe['stats.participantId'] = range(1, 11)
    dataframe.rename(columns={0: 'soloKills'}, inplace=True)
    dataframe.rename(columns={1: 'soloDeaths'}, inplace=True)
    dataframe = dataframe.astype({"soloDeaths": 'int', "soloKills": 'int'})
    return dataframe


def calculate_kda(dataframe):
    logging.debug("Calculating all players KDA:")
    dataframe['kda'] = (dataframe['stats.kills'] + dataframe['stats.assists']) / dataframe['stats.deaths'].apply(
        lambda x: 1 if x == 0 else x)
    logging.debug(f"Average KDA = {dataframe.kda.mean()}")
    return dataframe


def calculate_kp(dataframe):
    logging.debug("Calculating all players KP:")
    team_kills = dataframe[['gameId', 'teamId', 'stats.kills']].groupby(['gameId', 'teamId']).sum()
    merged_dataframe = dataframe.merge(team_kills, on=['gameId', 'teamId'], suffixes=('', '.team')).sort_values(
        by=['gameCreation', 'participantId'], ignore_index=True)
    dataframe = dataframe.sort_values(by=['gameCreation', 'participantId'], ignore_index=True)
    dataframe['kp'] = (dataframe['stats.kills'] + dataframe['stats.assists']) / merged_dataframe['stats.kills.team']
    logging.debug(f"Average KP = {dataframe.kp.mean()}")
    return dataframe


def generate_timeline_player_dataframe(games_data):
    res = pd.read_json(json.dumps(games_data))
    res = res.drop(['participants', 'participantIdentities', 'teams'], axis=1)
    res['frames'] = res['timeline'].apply(lambda x: x['frames'])
    res = res.drop('timeline', axis=1)
    res = res.explode('frames', ignore_index=True)
    res['participantFrames'] = res['frames'].apply(lambda x: x['participantFrames'])
    res['timestamps'] = res['frames'].apply(lambda x: x['timestamp'])
    res = res.drop('frames', axis=1)
    res['participantFramesPlayer'] = res['participantFrames'].apply(lambda x: [x[k] for k in x.keys()])
    res = res.drop('participantFrames', axis=1)
    res = res.explode('participantFramesPlayer', ignore_index=True)
    res['participantId'] = res['participantFramesPlayer'].apply(lambda x: x['participantId'])
    res['currentGold'] = res['participantFramesPlayer'].apply(lambda x: x['currentGold'])
    res['totalGold'] = res['participantFramesPlayer'].apply(lambda x: x['totalGold'])
    res['level'] = res['participantFramesPlayer'].apply(lambda x: x['level'])
    res['xp'] = res['participantFramesPlayer'].apply(lambda x: x['xp'])
    res['minionsKilled'] = res['participantFramesPlayer'].apply(lambda x: x['minionsKilled'])
    res['jungleMinionsKilled'] = res['participantFramesPlayer'].apply(lambda x: x['jungleMinionsKilled'])
    res['position_x'] = res['participantFramesPlayer'].apply(lambda x: x['position']['x'])
    res['position_y'] = res['participantFramesPlayer'].apply(lambda x: x['position']['y'])
    res = res.drop('participantFramesPlayer', axis=1)
    res['teamId'] = res.apply(lambda x: 'Blue' if x['participantId'] <= 5 else 'Red', axis=1)
    return res


def generate_timeline_event_dataframe(games_data):
    res = pd.read_json(json.dumps(games_data))
    res = res.drop(['participants', 'participantIdentities', 'teams'], axis=1)
    res['frames'] = res['timeline'].apply(lambda x: x['frames'])
    res = res.drop('timeline', axis=1)
    res = res.explode('frames', ignore_index=True)
    res['events'] = res['frames'].apply(lambda x: x['events'])
    res = res.explode('events', ignore_index=True)
    print(res)
    # TODO HACER EVENTOS


def generate_champion_dataframe(game_dataframe, ban_dataframe):
    reduced_game_dataframe = game_dataframe[
        ['gameId','teamId', 'gameDate', 'gameVersion', 'championId', 'championName', 'stats_win', 'teamName', 'role', 'tournament']].copy()
    reduced_game_dataframe.loc[:, 'participationType'] = 'Pick'
    reduced_game_dataframe.rename(columns={"stats_win": "win"}, inplace=True)
    reduced_ban_dataframe = ban_dataframe[['gameId','teamId', 'gameDate', 'gameVersion', 'banned_champion_id', 'championName', 'win', 'teamName', 'tournament']].copy()
    reduced_ban_dataframe.loc[:, 'role'] = 'Ban'
    reduced_ban_dataframe.loc[:, 'participationType'] = 'Ban'
    reduced_ban_dataframe.rename(columns={"banned_champion_id": "championId"}, inplace=True)
    champion_dataframe = pd.concat([reduced_ban_dataframe, reduced_game_dataframe])
    champion_dataframe.sort_values(by=['gameDate', 'teamName'], ignore_index=True, inplace=True)
    return champion_dataframe


def replace_championId_with_champion_name(series, game_version, language='en_US'):
    champions = get_data_dragon_file(game_version, "champion", game_lang=language)
    champion_dict = dict()
    for champion_info in champions['data'].values():
        champion_dict[int(champion_info["key"])] = champion_info["name"]
    return series.replace(champion_dict)
