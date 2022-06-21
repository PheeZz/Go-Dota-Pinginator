from itertools import count
from unittest import result
import requests as rq
from dotenv import load_dotenv
from os import getenv, mkdir, listdir
from loguru import logger
import yaml
import json
from random import randint
from telebot import types

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


def register_role_priority(message):
    '''
    функция, задающая значение приоритетности (по убыванию) ролей пользователя для авторолла
    '''
    only_digits = ''.join(filter(str.isdigit, message.text))
    if len(set(only_digits)) < 5:  # защита от хитрожопых пользователей
        digits = set(only_digits)
        only_digits = ''.join(digits)
        while len(only_digits) < 5:
            only_digits += '5'

    user_roles = {message.from_user.username: only_digits}

    try:
        with open(f'data/role_priority/{message.chat.id}.yaml', 'r') as stream:
            role_priority = yaml.full_load(stream)
    except FileNotFoundError:
        role_priority = dict()
        logger.error(f'File {message.chat.id} for roles priority not found')
    role_priority.update(user_roles)

    yaml.dump(user_roles, open(
        f'data/role_priority/{message.chat.id}.yaml', 'w'))
    logger.info(f'{message.from_user.username} registered role priority {only_digits} for chat {message.chat.id} in file: data/role_priority/{message.chat.id}.yaml')


def get_user_priority(message) -> str | None:
    try:
        with open(f'data/role_priority/{message.chat.id}.yaml', 'r') as stream:
            roles_priority_dict = yaml.full_load(stream)
        user_roles = roles_priority_dict.get(message.from_user.username)
        return user_roles
    except FileNotFoundError:
        return None


def show_my_priority(message, bot):
    user_roles = get_user_priority(message)
    if user_roles is None:
        bot.send_message(chat_id=message.chat.id,
                         text='Вы не зарегистрированы в системе\nИспользуйте команду /setpriority для регистрации')
    else:
        bot.send_message(chat_id=message.chat.id,
                         text=f'{message.from_user.first_name}, ваша приоритетность ролей:\n{user_roles}')


def show_all_priority(message, bot):
    '''
    вывод обработанного списка ролей из файла чата /data/role_priority/{message.chat.id}.yaml
    '''
    try:
        with open(f'data/role_priority/{message.chat.id}.yaml', 'r') as stream:
            roles_priority_dict = yaml.full_load(stream)
        roles_priority_string = json.dumps(roles_priority_dict)

        chars_for_delete = ('{', '}', '"')
        for char in chars_for_delete:
            roles_priority_string = roles_priority_string.replace(
                char, '')

        bot.send_message(chat_id=message.chat.id,
                         text=f'Все приоритеты ролей:\n{roles_priority_string}')
    except FileNotFoundError:
        bot.send_message(chat_id=message.chat.id,
                         text='Еще никто из данного чата не зарегистрированы в системе\nИспользуйте команду /setpriority для регистрации')


def create_lobby(message, bot):
    '''
    создание лобби из для проведения авторолла и распределения по ролям
    если лобби уже существует, то оно перезаписывается
    '''
    try:
        # создание папки чата для всех лобби внутри него
        mkdir(f'data/lobby/{message.chat.id}')
        logger.info(f'Создана папка лобби для чата {message.chat.id}')
    except FileExistsError:
        logger.warning(f'Папка уже существует {message.chat.id}')

    user_roles = get_user_priority(message)
    user_and_roles = {message.from_user.username: user_roles}

    if user_roles is None:
        logger.error(
            f'{message.from_user.username} not registered in role priority')
        answer = bot.send_message(chat_id=message.chat.id,
                                  text='Вы не зарегистрированы в системе\nИспользуйте команду /setpriority для регистрации')
        return answer

    try:
        with open(f'data/lobby/{message.chat.id}/{message.text}.yaml', 'w') as stream:
            logger.info(f'Lobby {message.text} created')
            yaml.dump(user_and_roles, stream)
        answer = bot.send_message(
            chat_id=message.chat.id, text=f'Лобби {message.text} создано')
        return answer
    except:
        logger.error(f'Lobby {message.text} not created')
        answer = bot.send_message(chat_id=message.chat.id,
                                  text='Лобби не создано\nПочему? Неизвестно хиихихихихихихиихих')
        return answer


def users_lobbies(message) -> list:
    '''
    возвращает список лобби в которых находится пользователь
    '''
    lobby_list = listdir(f'data/lobby/{message.chat.id}')
    users_lobby_list = list()

    for lobby in lobby_list:
        with open(f'data/lobby/{message.chat.id}/{lobby}', 'r') as stream:
            lobby_dict = yaml.full_load(stream)
            if message.from_user.username in lobby_dict.keys():
                users_lobby_list.append(lobby)

    users_lobby_list = [lobby.replace('.yaml', '')
                        for lobby in users_lobby_list]

    return users_lobby_list


def roll_roles(message, bot):
    '''
    генерация ролей из лобби и отправка в чат
    '''

    try:
        with open(f'data/lobby/{message.chat.id}/{message.text}.yaml', 'r') as stream:
            users_roles = yaml.full_load(stream)
    except FileNotFoundError:
        logger.error(f'Lobby {message.text} not found')
        answer = bot.send_message(chat_id=message.chat.id,
                                  text='Лобби не найдено')
        return answer

    # генерация /roll значений от 1 до 100
    roll_result = {user: randint(1, 100) for user in users_roles.keys()}
    logger.info(f'Roll result: {roll_result}')
    roll_result_numbers = sorted(
        roll_result.items(), key=lambda x: x[1], reverse=True)
    roll_result = sorted(roll_result, key=roll_result.get, reverse=True)

    result_dict = dict()
    for user in roll_result:  # перебор пользователей по приоритету
        result_dict.update({user: users_roles[user][0]})
        current_pos = users_roles[user][0]
        del users_roles[user]
        for check in users_roles:
            # удаление занятой позиции из списков оставшихся пользователей
            if current_pos in users_roles[check]:
                users_roles.update(
                    {check: users_roles[check].replace(current_pos, '')+'5'})

    pretty_str = '*РАСПРЕДЕЛЕНИЕ*\n'
    counter = 0
    for user in result_dict:
        pretty_str += f'{result_dict[user]}pos - {user} - roll: *{roll_result_numbers[counter][1]}*\n'
        counter += 1
    del counter
    logger.info(f'Roles fill result: {pretty_str}')

    bot.send_message(chat_id=message.chat.id,
                     text=pretty_str, parse_mode='Markdown', reply_markup=types.ReplyKeyboardRemove())


if __name__ == '__main__':
    pass
