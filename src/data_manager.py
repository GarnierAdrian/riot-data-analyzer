import json
import requests
import os

base_match_history_stats_url = "https://acs.leagueoflegends.com/v1/stats/game/{}/{}?gameHash={}"
base_match_history_stats_timeline_url = "https://acs.leagueoflegends.com/v1/stats/game/{}/{}/timeline?gameHash={}"
cookies = "ajs_group_id=null; ajs_user_id=null; PVPNET_LANG=en_US; ping_session_id=7c9995f1-f223-449a-a0d8-ba61b5c7ac90; _ga=GA1.2.485594807.1613081309; _gid=GA1.2.1457282448.1613081309; PVPNET_TOKEN_LAN=eyJkYXRlX3RpbWUiOjE2MTMwODEzMjQ0MjgsImdhc19hY2NvdW50X2lkIjoyMDAwNjI3MDYsInB2cG5ldF9hY2NvdW50X2lkIjoyMDAwNjI3MDYsInN1bW1vbmVyX25hbWUiOiJFcmFvIiwidm91Y2hpbmdfa2V5X2lkIjoiOTAzNDc1MmIyYjQ1NjA0NGFlODdmMjU5ODJkYWQwN2QiLCJzaWduYXR1cmUiOiJtQllZQUx2M01IVXU2NUlRVWhOOVFFcXlEUHRRUXcranArek9QbEM0dkVrL1hIV1phbjRxdnE1TEpmQ2l4dnpEaWhHSGtmM09jVkhuYzU1a3RUZHZ2VlY5NEVOdjQyU0trS1U1UFNKckVDZzhaajJmVDRsQXFsVjRBMGRwMUZ2eXBVUnNJNUtDNjJTdEU1alFyL0xWY0lrL1dsZ251U1o0UW1EKzExSDAvTGs9In0%3D; PVPNET_ACCT_LAN=Erao; PVPNET_ID_LAN=200062706; PVPNET_REGION=lan; id_token=eyJraWQiOiJzMSIsImFsZyI6IlJTMjU2In0.eyJzdWIiOiIxNjk0YmRiZi0xZjg5LTViYTYtOTg5ZC0wNTIxZjhlOGNiM2YiLCJjb3VudHJ5IjoiY3JpIiwicGxheWVyX3Bsb2NhbGUiOiJlbi1VUyIsImFtciI6WyJwYXNzd29yZCJdLCJpc3MiOiJodHRwczpcL1wvYXV0aC5yaW90Z2FtZXMuY29tIiwibG9sIjpbeyJjdWlkIjoyMDAwNjI3MDYsImNwaWQiOiJMQTEiLCJ1aWQiOjM4NTU4NzEzLCJ1bmFtZSI6IkVyYW9MaXZlbm94MSIsInB0cmlkIjpudWxsLCJwaWQiOiJOQSIsInN0YXRlIjoiRU5BQkxFRCJ9XSwibG9jYWxlIjoiZW5fVVMiLCJhdWQiOiJyc28td2ViLWNsaWVudC1wcm9kIiwiYWNyIjoidXJuOnJpb3Q6YnJvbnplIiwicGxheWVyX2xvY2FsZSI6ImVuLVVTIiwiZXhwIjoxNjEzMTY3NzIyLCJpYXQiOjE2MTMwODEzMjIsImFjY3QiOnsiZ2FtZV9uYW1lIjoiRXJhbyIsInRhZ19saW5lIjoiTEFOIn0sImp0aSI6Im5ia0IwNVhiOHAwIiwibG9naW5fY291bnRyeSI6ImNyaSJ9.XJCDrXFeooSAzrSCY9PBZiph5MpSBXwnODvdHpS0DOrt9gp2wVQt2vt_BqDhiXOQnoYpf2OhdIfStSjMocbRApC840Cp74EuxGdIHio8RSi8eRVrrxa1R0A84eNcVXWxPq78b3gUswu081vlC11w_pmrZoiQUDTDebT8GXS6Fm0; id_hint=sub%3D1694bdbf-1f89-5ba6-989d-0521f8e8cb3f%26lang%3Den%26game_name%3DErao%26tag_line%3DLAN%26id%3D200062706%26summoner%3DErao%26region%3DLA1%26tag%3Dlan; __cfduid=d014fa502ba7f667ec60e0fe86e2d11881613081326"


def get_games_list():
    with open('data/input_data/games.json', 'r') as links_file:
        data = links_file.read()
    return json.loads(data)['links']


def get_all_games(game_list):
    all_games_data = []
    for i in game_list:
        game_data = get_game_data(i[0], i[1], i[2])
        all_games_data.append(game_data)
    return all_games_data


def get_game_data(server, game_id, game_hash):
    if is_file_downloaded(f'data/cache/game_files/{server}{game_id}{game_hash}.json'):
        game_data = load_game_file(server, game_id, game_hash)
    else:
        game_data = request_game_data(server, game_id, game_hash)
    return game_data


def load_game_file(server, game_id, game_hash):
    with open(f'data/input_data/game_files/{server}{game_id}{game_hash}.json', 'r') as links_file:
        data = links_file.read()
    game_data = json.loads(data)
    # print("File Opened")
    return game_data


def request_game_data(server, game_id, game_hash):
    game_url = base_match_history_stats_url.format(server, game_id, game_hash)
    game_timeline_url = base_match_history_stats_timeline_url.format(server, game_id, game_hash)
    this_game_data = requests.get(game_url,
                                  cookies={c.split("=")[0]: c.split("=")[1] for c in cookies.split(";")}).json()
    this_game_data["timeline"] = requests.get(game_timeline_url,
                                              cookies={c.split("=")[0]: c.split("=")[1] for c in
                                                       cookies.split(";")}).json()
    print(this_game_data["timeline"])
    with open(f'data/input_data/game_files/{server}{game_id}{game_hash}.json', 'w', encoding='utf8') as json_file:
        json.dump(this_game_data, json_file, allow_nan=True)
    # print('File writen')
    return this_game_data


def download_url(url, save_path, chunk_size=128):
    r = requests.get(url, stream=True)
    with open(save_path, 'wb') as fd:
        for chunk in r.iter_content(chunk_size=chunk_size):
            fd.write(chunk)


def get_data_dragon_file(version, file, game_lang='en_US'):
    splinted_version = version.split('.')
    dd_version = f'{splinted_version[0]}.{splinted_version[1]}.1'
    path = f'data/cache/data_dragon/{dd_version}'
    if not os.path.isdir(path):
        os.mkdir(path)
    path += f'/{game_lang}'
    if not os.path.isdir(path):
        os.mkdir(path)
    path += f'/{file}.json'
    if not is_file_downloaded(path):
        download_data_dragon(dd_version, file, path, game_lang)
    with open(path, 'r') as f:
        data = json.load(f)
    return data


def download_data_dragon(version, file, path, game_lang='en_US', chunk_size=128):
    url = f"http://ddragon.leagueoflegends.com/cdn/{version}/data/{game_lang}/{file}.json"
    print(url)
    download_url(url, path, chunk_size)


def is_file_downloaded(path):
    try:
        open(path)
        return True
    except IOError:
        return False
