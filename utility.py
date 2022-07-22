import requests
from random import choice
from fake_useragent import UserAgent
from typing import NoReturn
from loguru import logger
import yaml
from dataclasses import dataclass
import time as t
from threading import Thread
from telebot import types


def load_yaml(file):
    try:
        with open(file, 'r') as f:
            return yaml.full_load(f)
    except FileNotFoundError:
        return dict()


def dump_yaml(file, data: dict):
    with open(file, 'w') as f:
        yaml.dump(data, f)


@dataclass
class message_timer:
    chat_id: int
    user_message_id: int
    bot_answer_id: int
    time_stamp: float


def create_clean_timer(message_timer, bot):
    while True:
        if t.time() - message_timer.time_stamp >= 300:
            try:
                bot.delete_message(chat_id=message_timer.chat_id,
                                   message_id=message_timer.bot_answer_id)
                bot.delete_message(chat_id=message_timer.chat_id,
                                   message_id=message_timer.user_message_id)
                del message_timer
                break
            except Exception as e:
                logger.error(
                    f'error: {e} in create_clean_timer: message not found')
                break


def create_timer_thread(message, answer, bot) -> NoReturn:
    timer = message_timer(
        chat_id=message.chat.id, user_message_id=message.message_id, bot_answer_id=answer.message_id, time_stamp=t.time())
    Thread(target=create_clean_timer, args=(timer, bot)).start()


def lauch_roll_timer(message, bot, duration=15) -> NoReturn:
    announcement = bot.send_message(
        chat_id=message.chat.id, text=f'Участники, проверьте правильность активных пресетов ролей в течение *{duration}* секунд', parse_mode='Markdown')
    while(duration > 1):
        t.sleep(5)
        duration -= 5
        bot.edit_message_text(chat_id=message.chat.id, message_id=announcement.message_id,
                              text=f'Участники, проверьте правильность активных пресетов ролей в течение *{duration}* секунд', parse_mode='Markdown')
    bot.delete_message(chat_id=message.chat.id,
                       message_id=announcement.message_id)
    bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)

    Thread(target=lauch_roll_timer, args=(message, duration, bot)).start()


def filter_digits(message: types.Message):
    only_digits = ''.join(filter(str.isdigit, message.text))
    if len(set(only_digits)) < 5:  # защита от хитрожопых пользователей
        digits = set(only_digits)
        only_digits = ''.join(digits)
        while len(only_digits) < 5:
            only_digits += '5'
    return only_digits


def ruslan(text: str) -> str:

    headers = {
        'Accept': '*/*',
        'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
        'Connection': 'keep-alive',
        'Content-Type': 'text/plain;charset=UTF-8',
        'Origin': 'https://porfirevich.ru',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'cross-site',
        'User-Agent': UserAgent().random,
        'sec-ch-ua': '".Not/A)Brand";v="99", "Google Chrome";v="103", "Chromium";v="103"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
    }
    data = '{"prompt":"' + text + '","length":50}'

    response = requests.post(
        'https://pelevin.gpt.dobro.ai/generate/', headers=headers, data=data.encode('utf-8')).json()
    return text + choice(response.get('replies'))


def buttons_row_split(buttons: list, row_length: int) -> list:
    buttons_row = []
    for i in range(0, len(buttons), row_length):
        buttons_row.append(tuple(buttons[i:i + row_length]))
    return buttons_row


if __name__ == '__main__':
    pass
