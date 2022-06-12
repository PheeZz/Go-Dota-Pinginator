import telebot
from dotenv import load_dotenv
from loguru import logger
from os import getenv
import utility as util
from datetime import datetime
import random

load_dotenv(override=True)


def get_Datetime():
    now = datetime.now()
    pretty_str = now.strftime("%d.%m.%Y_%H.%M.%S")
    return pretty_str


# create logger
logger.add(f"logs/{get_Datetime()}.log", rotation='1 day', level="DEBUG")

# create a bot
bot = telebot.TeleBot(getenv("TOKEN"))

# /start command


@bot.message_handler(commands=["start"])
def start(message, res=False):
    bot.send_message(
        message.chat.id, 'Создайте чат и добавьте меня в него, затем добавьте всех в него всех пользователей для использования функционала!')


@bot.message_handler(content_types=["new_chat_members"])
def add_user_in_yaml(message):
    new_user = message.new_chat_members[0]
    chat_id = message.chat.id

    try:
        util.load_yaml(f'data/chat_users/{chat_id}.yaml')
    except FileNotFoundError:
        util.dump_yaml(f'data/chat_users/{chat_id}.yaml', {'chat id': chat_id})
    finally:
        data = util.load_yaml(f'data/chat_users/{chat_id}.yaml')
        if 'chat_id' in data:
            del data['chat_id']
        if new_user.username not in data:
            data.update({new_user.username: new_user.id})
        util.dump_yaml(f'data/chat_users/{chat_id}.yaml', data)


@bot.message_handler(content_types=["left_chat_members"])
def delete_user_from_yaml(message):
    left_user = message.left_chat_members[0]
    chat_id = message.chat.id
    data = util.load_yaml(f'data/chat_users/{chat_id}.yaml')

    try:
        del data[left_user.username]
        logger.warning(f'no key in yaml as {left_user.username}')
    except:
        del data[left_user.first_name]
        logger.warning(f'no key in yaml as {left_user.first_name}')
    finally:
        util.dump_yaml(f'data/chat_users/{chat_id}.yaml', data)


@bot.message_handler(content_types=["text"])
def pinger(message):
    if message.text == '?':
        ping_string = str()
        users = util.load_yaml(f'data/chat_users/{message.chat.id}.yaml')
        for user in users:
            ping_string += f'@{user} '

        pretty_adder = ('Го каточку, сладкие мои <3 ', 'Заебали, пошли в доту',
                        'ЭЭЭ ойбой', 'хочу сосать, пошли сосааааать')
        ping_string = f'\n{random.choice(pretty_adder)}\n{ping_string}'
        logger.info(
            f'ping string: {ping_string}\n chat id: {message.chat.id}\n')

        answer = bot.send_message(
            chat_id=message.chat.id, text=ping_string)
        util.create_timer_thread(message, answer, bot)

    elif message.text.lower() == 'roll':
        answer = bot.send_message(
            chat_id=message.chat.id, text=f'Ваш результат: {random.randint(1, 100)}')
        util.create_timer_thread(message, answer, bot)

    elif message.text.lower().startswith('try'):
        result = ('УСПЕШНО', 'НЕУДАЧНО')
        try_string = message.text.replace('try', '')
        answer = bot.send_message(
            chat_id=message.chat.id, text=f'{try_string}: *bold* {random.choice(result)}')


@logger.catch
def start_bot():  # Запускаем бота
    bot.polling(none_stop=True, interval=0)


start_bot()
