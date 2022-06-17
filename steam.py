import requests as rq
from dotenv import load_dotenv
from os import getenv

load_dotenv(override=True)


def call_csgo_api():
    req = rq.get(
        f'https://api.steampowered.com/ICSGOServers_730/GetGameServersStatus/v1/?key={getenv("STEAM_API_KEY")}').json()  # get info about servers by steam-web-api

    datacenters = req.get('result').get('datacenters')
    services = req.get('result').get('services')

    interesting_datacenters = ('EU East', 'EU West', 'EU North', 'Poland')
    info_interesting_datacenters = {datacenter: datacenters.get(  # sort info about interesting datacenters (location of each server)
        datacenter) for datacenter in interesting_datacenters}

    answer_string = '*Игровые сервера*\n'
    for server in info_interesting_datacenters:
        if info_interesting_datacenters.get(server).get('capacity') == 'full':
            answer_string += f'{server}: 🟢Online\n'
        else:
            answer_string += f'{server}: ❌Offline\n'

    answer_string += '\n*Сервисы Steam*\n'

    if services.get('SessionsLogon') == 'normal':
        answer_string += 'Система входа: 🟢Online\n'
    else:
        answer_string += 'Система входа: ❌Offline\n'

    if services.get('SteamCommunity') == 'normal':
        answer_string += 'Сообщество Steam: 🟢Online\n'
    else:
        answer_string += 'Сообщество Steam: ❌Offline\n'

    return answer_string


if __name__ == '__main__':
    print(call_csgo_api())
