from loguru import logger
import yaml
from dataclasses import dataclass
import time as t
from threading import Thread


def load_yaml(file):
    try:
        with open(file, 'r') as f:
            return yaml.full_load(f)
    except FileNotFoundError:
        return dict()


def dump_yaml(file, data):
    with open(file, 'w+') as f:
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
                return False
            except:
                logger.error(f'error in create_clean_timer: message not found')


def create_timer_thread(message, answer, bot):
    timer = message_timer(
        chat_id=message.chat.id, user_message_id=message.message_id, bot_answer_id=answer.message_id, time_stamp=t.time())
    Thread(target=create_clean_timer, args=(timer, bot)).start()
