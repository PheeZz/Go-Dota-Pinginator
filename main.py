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
import sql_db

load_dotenv(override=True)


def get_Datetime():
    now = datetime.now()
    pretty_str = now.strftime("%d.%m.%Y_%H.%M.%S")
    return pretty_str


# create logger
logger.add(f"logs/{get_Datetime()}.log", rotation='1 day',
           level="DEBUG", compression='zip')

# create a bot
# bot = telebot.TeleBot(getenv('TOKEN'))
bot = telebot.TeleBot('5586335425:AAGYIF0OBrwpPqwl_w8O3x9ETboum9c1qvs')

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
                  command='/create_preset', description="create your own role priority preset for autoroll"),
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
              types.BotCommand(command='/set_priority',
                               description="set your autoroll priority"),
              types.BotCommand(
                  command='/update_me', description="update your username and current chat id"),
              types.BotCommand(command='/delete_chat_lobbies',
                               description="delete all lobbies in current chat, only for admin"),
              types.BotCommand(
                  command='/me', description="show all bot's info about you"),
              ])


def create_ping_msg(message: types.Message):
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


def from_admin(message: types.Message):
    if message.from_user.username in tuple(admin.user.username for admin in bot.get_chat_administrators(message.chat.id)):
        return True
    else:
        answer = bot.send_message(
            chat_id=message.chat.id, text='ихихихиххи\nАдминки то нет😢')
        util.create_timer_thread(message, answer, bot)
        return False


@ bot.message_handler(commands=["start"])
def start(message: types.Message):
    bot.send_message(
        message.chat.id, 'Создайте чат и добавьте меня в него, затем добавьте всех в него всех пользователей для использования функционала!')


@ bot.message_handler(commands=["setup"])
def setup_tables():
    sql_db.setup_tables()


@ bot.message_handler(commands=["admins"])
def send_list_of_admins(message: types.Message):
    admins = list(
        admin.user.username for admin in bot.get_chat_administrators(message.chat.id))
    admins_string = '\n@'.join(admins)
    answer = bot.send_message(
        message.chat.id, f'Администраторы:\n{admins_string}')
    util.create_timer_thread(message, answer, bot)


@ bot.message_handler(commands=["lobby_list"])
def lobby_list(message: types.Message):
    bot.send_message(chat_id=message.chat.id,
                     text=sql_db.get_chat_lobbies(message))


@ bot.message_handler(commands=["delete_chat_lobbies"])
def delete_chat_lobbies(message: types.Message):
    if from_admin(message):
        bot.send_message(chat_id=message.chat.id,
                         text=sql_db.delete_chat_lobbies(message))


@ bot.message_handler(commands=["create_preset"])
def create_preset(message: types.Message):
    answer = bot.send_message(message.chat.id, 'Введите название пресета')
    bot.register_next_step_handler(answer, create_preset_name)
    util.create_timer_thread(message, answer, bot)


def create_preset_name(message: types.Message):
    preset_name = message.text
    roles = [1, 2, 3, 4, 5]
    random.shuffle(roles)
    only_digits = ''.join(filter(str.isdigit, str(roles)))
    answer = bot.send_message(
        message.chat.id, f'Чел ты.. ну ладно, тут у всех по 2 отца в лучшем случае\nВведите приоритет ролей для авто-ролла\nПример: {only_digits}')
    bot.register_next_step_handler(
        answer, register_roles_for_preset, preset_name)


def register_roles_for_preset(message: types.Message, preset_name: str):
    message.text = util.filter_digits(message)
    result = sql_db.create_preset(
        preset_name, preset_description=message.text, user_id=message.from_user.id)
    bot.send_message(message.chat.id, result)


@ bot.message_handler(commands=["show_my_priority"])
def show_my_priority(message: types.Message):
    steam.show_my_priority(message, bot)


@ bot.message_handler(commands=["show_all_priority"])
def show_all_roles(message: types.Message):
    bot.send_message(chat_id=message.chat.id,
                     text=sql_db.get_all_active_presets(message))


@ bot.message_handler(commands=["me"])
def show_info_about_me(message: types.Message):
    bot.send_message(chat_id=message.chat.id,
                     text=sql_db.get_user_info(message))


@ bot.message_handler(commands=["update_me"])
def update_user(message: types.Message):
    bot.send_message(chat_id=message.chat.id,
                     text=sql_db.update_user_info(message))


@ bot.message_handler(commands=["create_lobby"])
def create_lobby(message: types.Message):
    answer = bot.send_message(message.chat.id, 'Введите название лобби')
    bot.register_next_step_handler(answer, create_lobby_name)
    util.create_timer_thread(message, answer, bot)


def create_lobby_name(message: types.Message):
    bot.send_message(chat_id=message.chat.id,
                     text=sql_db.create_lobby(message))


@ bot.message_handler(commands=["invite"])
def show_info_message(message: types.Message):
    lobby_list = sql_db.get_user_lobbies(message.from_user.id)
    lobby_list = ','.join(lobby_list).split(',')
    if lobby_list:
        pretty_str = 'В какое лобби приглашаете?\n\nСписок доступных лобби:\n'
        pretty_str += '\n'.join(lobby_list)
        buttons = [types.InlineKeyboardButton(
            text=lobby, callback_data=f'invite_to_{lobby}') for lobby in lobby_list]
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        # FIXME настроить количество кнопок в ряду, мб использовать pip install keyboa
        for button in buttons:
            keyboard.add(button)
        answer = bot.send_message(
            message.chat.id, pretty_str, reply_markup=keyboard)
        util.create_timer_thread(message, answer, bot)
    else:
        pretty_str = 'Вы не состоите ни в одном лобби☹️'


@bot.callback_query_handler(func=lambda message: True)
def inline_logic(call):
    if call.data.startswith('invite_to_'):
        lobby_name = call.data.split('_')[2]
        bot.send_message(chat_id=call.message.chat.id,
                         text='Теперь пингани одним сообщением всех, кого хочешь пригласить')
        bot.register_next_step_handler(
            call.message, invite_to_lobby, lobby_name)


def invite_to_lobby(message: types.Message, lobby_name: str):
    bot.send_message(chat_id=message.chat.id,
                     text=sql_db.invite_to_lobby(message, lobby_name))


def choose_lobby(message: types.Message):
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


def choose_users_for_invite(message: types.Message):
    lobby = message.text
    print(lobby)
    print(type(lobby))
    bot.send_message(
        message.chat.id, 'Пинганите пользователей одним сообщением для приглашения', reply_markup=types.ReplyKeyboardRemove())

    bot.register_next_step_handler(
        message, create_invites_from_message, lobby)


def create_invites_from_message(message: types.Message, lobby):
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


@ bot.message_handler(commands=["bomber"])
def bomber(message: types.Message):
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


@ bot.message_handler(commands=["timer"])
def roll_timer(message: types.Message):
    util.lauch_roll_timer(message, bot)


@ bot.message_handler(commands=["status"])
def send_steam_status(message: types.Message):
    loading = bot.send_message(
        chat_id=message.chat.id, text='Подождите немного...')
    answer = bot.send_message(chat_id=message.chat.id,
                              text=steam.call_steamstatus(), parse_mode='Markdown')
    bot.delete_message(chat_id=message.chat.id,
                       message_id=loading.message_id)
    util.create_timer_thread(message, answer, bot)


@ bot.message_handler(commands=["dice"])
def dice(message: types.Message):
    util.create_timer_thread(message, bot.send_dice(message.chat.id), bot)


@ bot.message_handler(commands=["roll"])
def roll(message: types.Message):
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


@ bot.message_handler(commands=["keyboard"])
def show_keyboard(message: types.Message):
    question_btn = types.KeyboardButton('?')
    roll_btn = types.KeyboardButton('/roll')
    markup = types.ReplyKeyboardMarkup(
        resize_keyboard=True).row(question_btn, roll_btn)

    bot.send_message(
        message.chat.id, text='⌨️', reply_markup=markup)


@ bot.message_handler(commands=["help"])
def show_help(message: types.Message):
    help_msg = "Gaming\n/dice - бросить кубик\n/roll - получить рандомное число от 1 до 100\n\
/keyboard - показать клавиатуру c быстрыми сообщениями\n/status - показать статус серверов steam\n\n\
Lobby\n/create_preset - создать пресет для авто-ролла\n/show_all_priority - показать приоритетность\
ролей всех пользователей чата\n/show_my_priority - показать вашу приоритетность авто-ролла\n\
/help - показать справку\n\ntry <действие> - проверка на успех действия (успех\провал)\n\nmade by @pheezz"
    util.create_timer_thread(message, bot.send_message(
        message.chat.id, help_msg), bot)


@ bot.message_handler(content_types=["new_chat_members"])
def add_user_in_yaml(message: types.Message):
    sql_db.add_user_to_user_table(message)


@ bot.message_handler(content_types=["left_chat_member"])
def delete_user_from_yaml(message: types.Message):
    sql_db.delete_user(message.left_chat_member.id)


@ bot.message_handler(content_types=["text"])
def pinger_answer(message: types.Message):
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
    elif message.text.lower().startswith('руслан'):
        message.text = message.text.lower().replace('руслан', '')
        bot.send_message(chat_id=message.chat.id,
                         text=util.ruslan(message.text))


@ logger.catch
def start_bot():  # Запускаем бота
    bot.infinity_polling()


if __name__ == '__main__':
    start_bot()
