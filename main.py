import telebot
from telebot import types
from dotenv import load_dotenv
from loguru import logger
from os import getenv, listdir, remove
import utility as util
from datetime import datetime
import random
import steam
import yaml


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
                  command='/roll', description='roll autofill for current lobby'),
              types.BotCommand(command='/keyboard',
                               description='update fast answer keyboard'),
              types.BotCommand(command='/status',
                               description='show Steam servers status'),
              types.BotCommand(command='/bomber',
                               description="admin's little secret😈"),
              types.BotCommand(command='/admins',
                               description="show list of admins"),
              types.BotCommand(
                  command='/set_priority', description="set your own role priority for autoroll"),
              types.BotCommand(command='/show_my_priority',
                               description="shows your registered autoroll role priority"),
              types.BotCommand(command='/show_all_priority',
                               description="shows all users registered autoroll roles priority"),
              types.BotCommand(command='/create_lobby',
                               description="create an autoroll lobby"),
              types.BotCommand(command='/invite',
                               description="invite someone to lobby"),
              types.BotCommand(command='/lobby_list',
                               description="shows exist lobby list"),
              types.BotCommand(command='/delete_all_lobbies',
                               description="only for admin"),
              types.BotCommand(command='/set_priority', description="set your autoroll priority"), ])


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


def from_admin(message):
    if message.from_user.username in tuple(admin.user.username for admin in bot.get_chat_administrators(message.chat.id)):
        return True
    else:
        answer = bot.send_message(
            chat_id=message.chat.id, text='ихихихиххи\nАдминки то нет😢')
        util.create_timer_thread(message, answer, bot)
        return False


@bot.message_handler(commands=["start"])
def start(message, res=False):
    bot.send_message(
        message.chat.id, 'Создайте чат и добавьте меня в него, затем добавьте всех в него всех пользователей для использования функционала!')


@bot.message_handler(commands=["admins"])
def send_list_of_admins(message):
    admins = list(
        admin.user.username for admin in bot.get_chat_administrators(message.chat.id))
    admins_string = '\n@'.join(admins)
    answer = bot.send_message(
        message.chat.id, f'Администраторы:\n{admins_string}')
    util.create_timer_thread(message, answer, bot)


@bot.message_handler(commands=["lobby_list"])
def lobby_list(message):
    lobbys = listdir(f'data/lobby/{message.chat.id}')
    if 'empty.yaml' in lobbys:
        lobbys.remove('empty.yaml')

    for lobby in range(len(lobbys)):
        lobbys[lobby] = lobbys[lobby].replace('.yaml', '')

    lobby_str = '\t\t'.join(lobbys)
    if lobbys:
        answer = bot.send_message(
            message.chat.id, f'Существующие лобби:\n{lobby_str}')
        util.create_timer_thread(message, answer, bot)
    else:
        answer = bot.send_message(
            message.chat.id, f'На данный момент нет ни одного существующего лобби')
        util.create_timer_thread(message, answer, bot)


@bot.message_handler(commands=["set_priority"])
def help_msg_setroles(message):
    roles = [1, 2, 3, 4, 5]
    random.shuffle(roles)
    only_digits = ''.join(filter(str.isdigit, str(roles)))
    answer = bot.send_message(chat_id=message.chat.id,
                              text=f'Введите приоритет ролей для авто-ролла\nПример: {only_digits}')

    bot.register_next_step_handler(answer, register_roles_for_user)
    util.create_timer_thread(message, answer, bot)


def register_roles_for_user(message):
    steam.register_role_priority(message)


@bot.message_handler(commands=["show_my_priority"])
def show_my_priority(message):
    steam.show_my_priority(message, bot)


@bot.message_handler(commands=["show_all_priority"])
def show_all_roles(message):
    steam.show_all_priority(message, bot)


@bot.message_handler(commands=["create_lobby"])
def create_lobby(message):
    answer = bot.send_message(message.chat.id, 'Введите название лобби')
    bot.register_next_step_handler(answer, create_lobby_name)
    util.create_timer_thread(message, answer, bot)


def create_lobby_name(message):
    answer = steam.create_lobby(message, bot)
    util.create_timer_thread(message, answer, bot)


@bot.message_handler(commands=["invite"])
def start_invite(message):
    lobby_count = len(listdir(f'data/lobby/{message.chat.id}'))
    bot.send_message(chat_id=message.chat.id,
                     text=f'Количество созданных лобби: {lobby_count}')

    if lobby_count == 0:
        answer = bot.send_message(
            message.chat.id, f'Нет ни одного существующего лобби, используйте /create_lobby')
        util.create_timer_thread(message, answer, bot)

    else:
        choose_lobby(message)


def choose_lobby(message):
    lobbys = listdir(f'data/lobby/{message.chat.id}')
    if 'empty.yaml' in lobbys:
        lobbys.remove('empty.yaml')
    for lobby in range(len(lobbys)):
        lobbys[lobby] = lobbys[lobby].replace('.yaml', '')

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True,
                                       one_time_keyboard=True)
    for lobby in lobbys:
        markup.add(lobby)
    answer = bot.send_message(
        message.chat.id, 'Выберите лобби для приглашения:', reply_markup=markup)
    util.create_timer_thread(message, answer, bot)
    bot.register_next_step_handler(answer, choose_users_for_invite)


def choose_users_for_invite(message):
    lobby = message.text
    print(lobby)
    print(type(lobby))
    bot.send_message(
        message.chat.id, 'Пинганите пользователей одним сообщением для приглашения', reply_markup=types.ReplyKeyboardRemove())

    bot.register_next_step_handler(
        message, create_invites_from_message, lobby)


def create_invites_from_message(message, lobby):
    '''
    создание инвайтов в лобби из сообщения
    '''
    invites = message.text.replace(' ', '').split('@')
    users = [invite for invite in invites if invite != '']

    with open(f'data/role_priority/{message.chat.id}.yaml', 'r') as stream:
        users_roll_priority = yaml.full_load(stream)
    with open(f'data/lobby/{message.chat.id}/{lobby}.yaml', 'r') as stream:
        lobby_data = yaml.full_load(stream)

    for user in users:

        if user in users_roll_priority:
            logger.info(f'{user} added to lobby {lobby}')
            lobby_data.update({user: users_roll_priority[user]})
            bot.send_message(chat_id=message.chat.id,
                             text=f'{user} добавлен в лобби {lobby}🤡')

        else:
            logger.error(f'{user} not registered in role priority')
            bot.send_message(
                chat_id=message.chat.id, text=f'{user} не зарегистрирован в системе авторолла')

    # recreate lobby file (remove old one because func open(... 'w') in this case will create new file)
    remove(f'data/lobby/{message.chat.id}/{lobby}.yaml')
    with open(f'data/lobby/{message.chat.id}/{lobby}.yaml', 'w') as stream:
        yaml.dump(lobby_data, stream)


@bot.message_handler(commands=["bomber"])
def bomber(message):
    if from_admin(message):
        spam = list()
        for _ in range(10):
            ping_string = create_ping_msg(message)
            answer = bot.send_message(
                chat_id=message.chat.id, text=ping_string)
            spam.append(answer)
        for _ in range(len(spam)):
            bot.delete_message(message.chat.id, spam.pop().message_id)

        try:
            bot.delete_message(message.chat.id, message.message_id)
        except Exception as e:
            logger.error(f'{e}')


@bot.message_handler(commands=["status"])
def send_steam_status(message):
    loading = bot.send_message(
        chat_id=message.chat.id, text='Подождите немного...')
    answer = bot.send_message(chat_id=message.chat.id,
                              text=steam.call_steamstatus(), parse_mode='Markdown')
    bot.delete_message(chat_id=message.chat.id,
                       message_id=loading.message_id)
    util.create_timer_thread(message, answer, bot)


@bot.message_handler(commands=["dice"])
def dice(message):
    util.create_timer_thread(message, bot.send_dice(message.chat.id), bot)


@bot.message_handler(commands=["delete_all_lobbies"])
def delete_lobbies(message):
    if from_admin(message):
        lobbies = listdir(f'data/lobby/{message.chat.id}')
        for lobby in lobbies:
            remove(f'data/lobby/{message.chat.id}/{lobby}')
        bot.send_message(chat_id=message.chat.id,
                         text='Все лобби успешно удалены')


@bot.message_handler(commands=["roll"])
def roll(message):
    lobbies = steam.users_lobbies(message)
    if not lobbies:
        bot.send_message(chat_id=message.chat.id,
                         text='Вы не состоите ни в одном лобби!')
        return
    markup = types.ReplyKeyboardMarkup(
        resize_keyboard=True, one_time_keyboard=True)
    for lobby in lobbies:
        markup.add(lobby)
    bot.send_message(chat_id=message.chat.id,
                     text=f'Выберите лобби для авторолла:', reply_markup=markup)
    bot.register_next_step_handler(message, steam.roll_roles, bot)


@bot.message_handler(commands=["keyboard"])
def show_keyboard(message):
    question_btn = types.KeyboardButton('?')
    roll_btn = types.KeyboardButton('/roll')
    markup = types.ReplyKeyboardMarkup(
        resize_keyboard=True).row(question_btn, roll_btn)

    bot.send_message(
        message.chat.id, text='⌨️', reply_markup=markup)


@bot.message_handler(commands=["help"])
def show_help(message):
    help_msg = "Gaming\n/dice - бросить кубик\n/roll - получить рандомное число от 1 до 100\n\
/keyboard - показать клавиатуру c быстрыми сообщениями\n/status - показать статус серверов steam\n\n\
Lobby\n/set_priority - установить приоритет для авто-ролла\n/show_all_priority - показать приоритетность\
ролей всех пользователей чата\n/show_my_priority - показать вашу приоритетность авто-ролла\n\
/help - показать справку\n\ntry <действие> - проверка на успех действия (успех\провал)\n\nmade by @pheezz"
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
    bot.infinity_polling()


start_bot()
