import pandas as pd
import re
import numpy as np
from datetime import datetime
from data_manager import get_all_games, get_games_list, get_data_dragon_file

links = get_games_list()

def calculate_solo_kills_and_deaths(game_json):
    solo_kills_and_deaths = np.zeros((len(game_json['participants']),2))
    frames = game_json['timeline']['frames']
    for frame in frames:
        for event in frame['events']:
            if event["type"] == 'CHAMPION_KILL':
                if len(event["assistingParticipantIds"]) == 0:
                    solo_kills_and_deaths[event["killerId"]-1][0] +=1
                    solo_kills_and_deaths[event["victimId"]-1][1] +=1
    dataframe = pd.DataFrame(solo_kills_and_deaths)
    dataframe['gameId'] = game_json['gameId']
    dataframe['stats.participantId'] = range(1,11)
    dataframe.rename(columns = {0:'soloKills'}, inplace = True)
    dataframe.rename(columns = {1:'soloDeaths'}, inplace = True)
    dataframe = dataframe.astype({"soloDeaths": 'int', "soloKills": 'int'})
    return(dataframe)

def calculate_list_of_solo_kills_and_deaths(list_of_games):
    dataframes = list()
    for game in list_of_games:
        dataframes.append(calculate_solo_kills_and_deaths(game))
    print(pd.concat(dataframes))
    return pd.concat(dataframes)






games_acces = []
for i in links:
    # print(i)
    title_search = re.search(
        'https://matchhistory.na.leagueoflegends.com/en/#match-details/(.*)/(.*)\?gameHash=(.*)&tab=overview',
        i["link"])
    # print(f"{title_search.group(1)}\t{title_search.group(2)}\t{title_search.group(3)}\n")
    games_acces.append([title_search.group(1), title_search.group(2), title_search.group(3)])

all_games_data = get_all_games(games_acces)

solo_kills_and_deaths_dataframe = calculate_list_of_solo_kills_and_deaths(all_games_data)

participants_identities = pd.json_normalize(all_games_data, 'participantIdentities',
                                            ['gameId', 'platformId', 'gameCreation'])

participants_identities.to_csv('data/interm/participants_identities.csv')

game_dataframe = pd.json_normalize(all_games_data, 'participants', ['gameId',
                                                                    'platformId',
                                                                    'gameCreation',
                                                                    'gameDuration',
                                                                    'queueId',
                                                                    'mapId',
                                                                    'seasonId',
                                                                    'gameVersion',
                                                                    'gameMode',
                                                                    'gameType'])
game_dataframe.rename(columns={"championId": "banned_champion_id", "pickTurn": "bann_turn"}, inplace=True)
game_dataframe.replace({'win': {'Fail': 0, 'Win': 1}}, inplace=True)
game_dataframe.replace({'False': 0, 'True': 1}, inplace=True)
game_dataframe['gameDate'] = game_dataframe['gameCreation'].apply(lambda x: datetime.fromtimestamp(x // 1000))
temp_list = participants_identities['player.summonerName'].str.split(" ", 1, expand=True)
game_dataframe["summonerName"] = temp_list[1]
game_dataframe["teamName"] = temp_list[0]
game_dataframe = pd.merge(game_dataframe, solo_kills_and_deaths_dataframe, on=['gameId','stats.participantId'])

game_dataframe.to_csv('data/interm/game.csv')

for version in game_dataframe.gameVersion:
    get_data_dragon_file(version, 'champion')
    get_data_dragon_file(version, 'item')
    get_data_dragon_file(version, 'summoner')

teams_dataframe = pd.json_normalize(all_games_data, 'teams', ['gameId',
                                                              'platformId',
                                                              'gameCreation',
                                                              'gameDuration',
                                                              'queueId',
                                                              'mapId',
                                                              'seasonId',
                                                              'gameVersion',
                                                              'gameMode',
                                                              'gameType'])
teams_dataframe.replace({'win': {'Fail': 0, 'Win': 1}}, inplace=True)
teams_dataframe['gameDate'] = game_dataframe['gameCreation'].apply(lambda x: datetime.fromtimestamp(x // 1000))
teams_dataframe = pd.merge(teams_dataframe, game_dataframe[['gameId', 'teamId', 'teamName']].drop_duplicates(), on=['gameId', 'teamId'], how='inner')
teams_dataframe.replace({False: 0, True: 1}, inplace=True)

bans_dataframe = teams_dataframe.explode('bans', ignore_index=True)
print(bans_dataframe)
bans_dataframe = pd.concat([bans_dataframe, bans_dataframe.bans.apply(pd.Series)], axis='columns')
bans_dataframe.rename(columns={"championId": "banned_champion_id", "pickTurn": "bann_turn"}, inplace=True)
bans_dataframe.replace({'teamId': {100: 'Blue', 200: 'Red'}}, inplace=True)
bans_dataframe = bans_dataframe.drop('bans', axis=1)
bans_dataframe.rename(columns={"championId": "banned_champion_id", "pickTurn": "bann_turn"}, inplace=True)
teams_dataframe = teams_dataframe.drop('bans', axis=1)
teams_dataframe.to_csv('data/interm/teams.csv')
bans_dataframe.to_csv('data/interm/bans.csv')

print(bans_dataframe)

print(game_dataframe['soloKills'].sum())