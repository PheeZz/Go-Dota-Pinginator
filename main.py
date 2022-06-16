import telebot
from telebot import types
from dotenv import load_dotenv
from loguru import logger
from os import getenv
import utility as util
from datetime import datetime
import random
import steam

load_dotenv(override=True)


def get_Datetime():
    now = datetime.now()
    pretty_str = now.strftime("%d.%m.%Y_%H.%M.%S")
    return pretty_str


    # create logger
logger.add(f"logs/{get_Datetime()}.log", rotation='1 day',
           level="DEBUG", compression='zip')

# create a bot
bot = telebot.TeleBot(getenv('TOKEN'))

bot.set_my_commands(
    commands=[types.BotCommand(command='/help', description='show help message'),
              types.BotCommand(
                  command='/dice', description='roll a 1 to 6 dice'),
              types.BotCommand(
                  command='/roll', description='roll random 1 to 100 number'),
              types.BotCommand(command='/keyboard',
                               description='update fast answer keyboard'),
              types.BotCommand(command='/status',
                               description='show Steam servers status'),
              types.BotCommand(command='/bomber',
                               description="admin's little secret😈"),
              types.BotCommand(command='/admins', description="show list of admins"), ])


def create_ping_msg(message):
    ping_string = str()
    users = util.load_yaml(f'data/chat_users/{message.chat.id}.yaml')
    for user in users:
        ping_string += f'@{user} '

    pretty_adder = ('Го каточку, сладкие мои <3 🤍🖤', 'Заебали, пошли в доту🍺',
                    'ЭЭЭ ойбой🙈🙉🙊', 'Хочу сосать, пошли сосааааать👺', 'Пошли в доту😈', 'Может в жопу?👉🏽💦')
    ping_string = f'\n{random.choice(pretty_adder)}\n{ping_string}'
    logger.info(
        f'ping string: {ping_string} created\n chat id: {message.chat.id}\n')
    return ping_string


@bot.message_handler(commands=["start"])
def start(message, res=False):
    bot.send_message(
        message.chat.id, 'Создайте чат и добавьте меня в него, затем добавьте всех в него всех пользователей для использования функционала!')


@bot.message_handler(commands=["admins"])
def send_list_of_admins(message):
    admins = list(
        admin.user.username for admin in bot.get_chat_administrators(message.chat.id))
    admins_string = '\n@'.join(admins)
    bot.send_message(
        message.chat.id, f'Администраторы:\n{admins_string}')


@bot.message_handler(commands=["bomber"])
def bomber(message):
    if message.from_user.username in tuple(admin.user.username for admin in bot.get_chat_administrators(message.chat.id)):
        for _ in range(5):
            ping_string = create_ping_msg(message)
            answer = bot.send_message(
                chat_id=message.chat.id, text=ping_string)
            util.create_timer_thread(message, answer, bot)

    else:
        answer = bot.send_message(
            chat_id=message.chat.id, text='ихихихиххи\nАдминки то нет😢')
        util.create_timer_thread(message, answer, bot)


@bot.message_handler(commands=["status"])
def send_steam_status(message):
    loading = bot.send_message(
        chat_id=message.chat.id, text='Подождите немного...')
    answer = bot.send_message(chat_id=message.chat.id,
                              text=steam.call_csgo_api())
    bot.delete_message(chat_id=message.chat.id, message_id=loading.message_id)
    util.create_timer_thread(message, answer, bot)


@bot.message_handler(commands=["dice"])
def dice(message):
    util.create_timer_thread(message, bot.send_dice(message.chat.id), bot)


@bot.message_handler(commands=["roll"])
def roll(message):
    util.create_timer_thread(message, bot.send_message(
        chat_id=message.chat.id, text=f'Ваш результат: {random.randint(1, 100)}'), bot)


@bot.message_handler(commands=["keyboard"])
def show_keyboard(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = (types.KeyboardButton('?'),
               types.KeyboardButton('/roll'),
               )
    for button in buttons:
        markup.add(button)
    bot.send_message(
        message.chat.id, text='⌨️', reply_markup=markup)


@bot.message_handler(commands=["help"])
def show_help(message):
    help_msg = "/dice - бросить кубик\n/roll - получить рандомное число от 1 до 100\n/keyboard - показать клавиатуру c быстрыми сообщениями\n/status - показать статус серверов steam\n/help - показать справку\n\ntry <действие> - проверка на успех действия\n\nmade by @pheezz"
    util.create_timer_thread(message, bot.send_message(
        message.chat.id, help_msg), bot)


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


@bot.message_handler(content_types=["left_chat_member"])
def delete_user_from_yaml(message):
    left_user = message.left_chat_member
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
def pinger_answer(message):
    if message.text == '?':
        ping_string = create_ping_msg(message)
        answer = bot.send_message(
            chat_id=message.chat.id, text=ping_string)
        util.create_timer_thread(message, answer, bot)

    elif message.text.lower().startswith('try'):
        result = ('УСПЕШНО', 'НЕУДАЧНО')
        try_string = message.text.lower().replace('try', '')
        util.create_timer_thread(message, bot.send_message(
            chat_id=message.chat.id, text=f'{try_string}: *{random.choice(result)}*', parse_mode='Markdown'), bot)


@logger.catch
def start_bot():  # Запускаем бота
    bot.polling(none_stop=True, interval=0)


start_bot()
