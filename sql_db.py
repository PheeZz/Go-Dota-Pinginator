import sqlite3 as sql
from loguru import logger
from typing import NoReturn, Union
from telebot import types


def dict_to_str(dict_: dict):
    result_str = str()
    for item in dict_.items():
        result_str += f"{item[0]} {item[1].upper()}, "
    result_str = result_str[:-2]
    return result_str


def create_table(table: str, column: dict, db='main'):
    colums = dict_to_str(column)
    try:
        with sql.connect(f'data/{db}.db') as con:
            cur = con.cursor()
            cur.execute(
                f"CREATE TABLE IF NOT EXISTS {table} ({colums})")
            logger.info(f"Table {table} created")
            return
    except Exception as e:
        logger.error(f"Table {table} not created cause {e}")
        return


def create_user_table():
    users = {
        'user_id': 'INTEGER PRIMARY KEY',
        'username': 'TEXT NOT NULL DEFAULT incognito',
        'lobby': 'TEXT',
        'active_preset': 'INTEGER DEFAULT 55555',
        'chat_id': 'TEXT DEFAULT NULL',
    }
    create_table(table=f'user', db='main', column=users)


def create_preset_table():
    presets = {
        'preset_id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
        'preset_author_id': 'INTEGER NOT NULL',
        'preset_name': 'TEXT NOT NULL DEFAULT SonOfMother',
        'preset_value': 'INTEGER NOT NULL DEFAULT 55555',
    }
    create_table(table='preset', db='main', column=presets)


def create_lobby_table():
    lobbies = {
        'lobby_id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
        'lobby_name': 'TEXT NOT NULL DEFAULT lobby',
        'chat_id': 'INTEGER NOT NULL',
        'author_id': 'INTEGER NOT NULL',
    }
    create_table(table='lobby', db='main', column=lobbies)


def create_lobby(message: types.Message):
    # message.text is lobby_name
    try:
        with sql.connect(f'data/main.db') as con:
            cur = con.cursor()
            cur.execute(
                f"INSERT INTO lobby VALUES (NULL,?,?,?)", (message.text, message.chat.id, message.from_user.id))
            logger.info(
                f"Lobby {message.text} in chat {message.chat.title} successfully created")

            cur.execute('SELECT lobby FROM user WHERE user_id = ?',
                        (message.from_user.id,))
            current_lobbies = cur.fetchone()[0]
            # if current_lobbies not NULL then add lobby_name to user's current lobbies
            if current_lobbies:
                cur.execute('UPDATE user SET lobby = ? WHERE user_id = ?',
                            (message.text+','+current_lobbies, message.from_user.id))
            else:
                cur.execute('UPDATE user SET lobby = ? WHERE user_id = ?',
                            (message.text, message.from_user.id))
            return f'Лобби {message.text} в чате {message.chat.title} успешно создано'
    except Exception as e:
        logger.error(
            f"Not created lobby {message.text} in {message.chat.title} cause {e}")
        return f'ОШИБКА: Не удалось создать лобби {message.text} в чате {message.chat.title}'


def get_chat_lobbies(message: types.Message) -> Union[str, None]:
    with sql.connect(f'data/main.db') as con:
        cur = con.cursor()
        cur.execute(
            f"SELECT lobby_name FROM lobby WHERE chat_id = ?", (message.chat.id,))
        logger.info(f"Succesfuly getted chat {message.chat.title} lobby")
        lobbies = cur.fetchall()
        if lobbies:
            answer = f'Список лобби в чате {message.chat.title}:\n'
            for lobby in lobbies:
                answer += f'{lobby[0]}\n'
        else:
            return f'В чате {message.chat.title} нет лобби'
        return answer


def get_user_lobbies(user_id: int) -> tuple:
    with sql.connect(f'data/main.db') as con:
        cur = con.cursor()
        cur.execute(
            f"SELECT lobby FROM user WHERE user_id = ?", (user_id,))
        logger.info(f"Succesfuly getted user {user_id} lobby")
        return cur.fetchone()


def invite_to_lobby(message: types.Message, lobby_name: str):
    users = message.text.replace('@', '').split()

    with sql.connect(f'data/main.db') as con:
        cur = con.cursor()
        for user in users:
            cur.execute(
                f"SELECT user_id FROM user WHERE username = ?", (user,))
            user_id = cur.fetchone()[0]
            cur.execute(
                f"SELECT lobby FROM user WHERE user_id = ?", (user_id,))
            current_lobbies = cur.fetchone()[0]
            if current_lobbies:
                if lobby_name not in current_lobbies:
                    cur.execute(
                        f"UPDATE user SET lobby = ? WHERE user_id = ?", (lobby_name+','+current_lobbies, user_id))
            else:
                cur.execute(
                    f"UPDATE user SET lobby = ? WHERE user_id = ?", (lobby_name, user_id))
            logger.info(f"Succesfuly invited {user} to {lobby_name}")
    return f'Пользователи {",".join(users)} приглашены в лобби {lobby_name}'


def delete_chat_lobbies(message: types.Message) -> str:
    with sql.connect(f'data/main.db') as con:
        cur = con.cursor()
        # select all lobby names from chat
        cur.execute(
            'SELECT lobby_name FROM lobby WHERE chat_id = ?', (message.chat.id,))
        lobby_names = cur.fetchall()

        # select all lobbies in user table
        cur.execute('SELECT user_id,lobby FROM user')
        users_lobbies = cur.fetchall()

        # delete current lobby from user table
        for user in users_lobbies:
            lobbies = str(user[1]).split(',')
            for lobby in lobby_names:
                if user[1] is not None and (lobby[0] in user[1]):
                    # lobby[0] is lobby name in str format
                    try:
                        lobbies.remove(lobby[0])
                    except Exception as e:
                        logger.error(f"Not deleted lobby {lobby[0]} cause {e}")
            lobbies = ','.join(lobbies)
            cur.execute(
                'UPDATE user SET lobby = ? WHERE user_id = ?', (lobbies, user[0]))

        # delete lobbies from lobby table with current chat.id
        cur.execute(
            f"DELETE FROM lobby WHERE chat_id = ?", (message.chat.id,))
        logger.info(
            f"Succesfuly deleted all lobbies in chat {message.chat.title}")
        return f'Лобби в чате {message.chat.title} успешно удалены'


def add_user_to_user_table(message: types.Message):
    filler = (message.from_user.id, message.from_user.username,
              None, None, message.chat.id)
    with sql.connect(f'data/main.db') as con:
        cur = con.cursor()
        cur.execute('INSERT INTO user VALUES (?,?,?,?,?)', filler)


def delete_user_from_user_table(message: types.Message):
    with sql.connect(f'data/main.db') as con:
        cur = con.cursor()
        cur.execute(
            f"DELETE FROM user WHERE user_id = ?", (message.from_user.id,))
        logger.info(f"Succesfuly deleted user {message.from_user.username}")
        return f'Пользователь {message.from_user.username} успешно удален из базы'


def update_user_info(message: types.Message):
    '''updates such info about user as username and current chat_id'''
    with sql.connect(f'data/main.db') as con:
        cur = con.cursor()
        chat_id_adder = str(message.chat.id)
        try:
            cur.execute(
                'SELECT chat_id FROM user WHERE user_id = ?', (message.from_user.id,))
            current_chat_ids = cur.fetchone()[0]
            if chat_id_adder in current_chat_ids:
                cur.execute('UPDATE user SET username = ? WHERE user_id = ?',
                            (message.from_user.username, message.from_user.id))
                logger.warning(
                    f"User {message.from_user.username} username updated, chat_id aleready exists")
            else:
                new_chat_id_data = f'{current_chat_ids},{chat_id_adder}'
                cur.execute(
                    f"UPDATE user SET username = ?, chat_id = ? WHERE user_id = ?", (message.from_user.username, new_chat_id_data, message.from_user.id))
                logger.info(
                    f"Succesfuly updated user {message.from_user.username} info")
        except TypeError:
            cur.execute('INSERT INTO user (user_id,username,chat_id) VALUES (?,?,?)',
                        (message.from_user.id, message.from_user.username, message.chat.id))
        return f'Информация о пользователе {message.from_user.username} успешно обновлена'


def utility_fill(table='user', db='main'):
    filler = {
        0: ('433364417', 'pheezz', 'zxc', '21345', None),
        1: ('601885807', 'opyatvtilte', 'zxc', '12435', None),
        2: ('1187419870', 'Nn1k1tos1k', 'zxc', '24135', None),
        3: ('1271768797', 'qweabuzr', None, None, None),
        4: ('1100933044', 'temaflex51', None, None, None),
    }
    try:
        with sql.connect(f'data/{db}.db') as con:
            cur = con.cursor()
            for value in filler:
                cur.execute(
                    f"INSERT INTO {table} VALUES (?,?,?,?,?)", filler.get(value))
            logger.info(f"Table {table} filled")
            return
    except Exception as e:
        logger.error(f"Table {table} not filled cause {e}")
        return


def create_preset(preset_name: str, preset_description: str, user_id: int) -> str:
    try:
        with sql.connect(f'data/main.db') as con:
            cur = con.cursor()
            cur.execute(
                f"INSERT INTO preset VALUES (NULL,?,?,?)", (user_id, preset_name, preset_description))
            logger.info(
                f"Row preset {preset_name} for user {user_id} successfully created")
            return f'Preset {preset_name} успешно создан'
    except Exception as e:
        return f'ОШИБКА: Не удалось создать пресет {preset_name}: {e}'


def get_preset_author_id(preset_id: str) -> Union[int, str]:
    try:
        with sql.connect(f'data/main.db') as con:
            cur = con.cursor()
            cur.execute(
                f"SELECT preset_author_id FROM preset WHERE preset_id = ?", (preset_id,))
            logger.info(f"Succesfuly getted preset {preset_id} author_id")
            return cur.fetchone()[0]
    except Exception as e:
        logger.error(f"Not getted preset {preset_id} author_id cause {e}")
        return f'ОШИБКА: Не удалось получить id автора пресета {preset_id}'


def update_preset(from_id: int, preset_name: str, preset_description: str) -> str:
    try:
        with sql.connect(f'data/main.db') as con:
            cur = con.cursor()
            cur.execute(
                f"UPDATE preset SET preset_description = ? WHERE preset_author_id = ? AND preset_name = ?", (preset_description, from_id, preset_name))
            logger.info(
                f"Table preset updated for {preset_name} -> {preset_description}")
            return f"Preset {preset_name} успешно изменен на {preset_description}"
    except Exception as e:
        logger.error(f"Table preset not updated cause {e}")
        return f"ОШИБКА: Preset {preset_name} не изменен, скорее всего он не существует"


def delete_preset(preset_id: str) -> str:
    try:
        with sql.connect(f'data/main.db') as con:
            cur = con.cursor()
            cur.execute(
                f"DELETE FROM preset WHERE preset_id = ?", (preset_id,))
            logger.info(f"preset_id {preset_id} in preset table deleted")
            return f'Preset успешно удален'
    except Exception as e:
        logger.error(f"Row {preset_id} not deleted cause {e}")
        return f'ОШИБКА: Preset {preset_id} не удален, скорее всего он не существует'


def get_all_active_presets(message: types.Message) -> str:
    """
    Args:
        message : telebot message object

    Returns:
        str: all active presets in chat
    """
    try:
        with sql.connect(f'data/main.db') as con:
            cur = con.cursor()
            cur.execute(
                f"SELECT username,active_preset FROM user where chat_id = ?", (message.chat.id,))
            logger.info(f"Succesfuly getted all active presets")
            user_and_active_preset_list = cur.fetchall()
            msg = 'Список активных пресетов в чате:\n\n'
            for item in user_and_active_preset_list:
                msg += f"{item[0]} - {item[1]}\n"
    except Exception as e:
        logger.error(f"Not getted all active presets cause {e}")
        return f'ОШИБКА: Не удалось получить все активные пресеты'


def get_user_preset(message: types.Message) -> str:
    """
    Args:
        message : telebot message object

    Returns:
        str: active user preset
    """
    try:
        with sql.connect(f'data/main.db') as con:
            cur = con.cursor()
            cur.execute(
                f"SELECT active_preset FROM user where username = ?", (message.from_user.username,))
            logger.info(f"Succesfuly getted user preset")
            return cur.fetchone()[0]
    except Exception as e:
        logger.error(f"Can't gett user preset cause {e}")
        return f'ОШИБКА: Не удалось получить пресет пользователя {message.from_user.username}:\n{e}'


def get_user_info(message: types.Message) -> str:
    ''' return all info about user
    such as username, active_preset, etc.'''
    with sql.connect(f'data/main.db') as con:
        cur = con.cursor()
        cur.execute(
            f"SELECT user_id,lobby,active_preset FROM user where username = ?", (message.from_user.username,))
        logger.info(
            f"Succesfuly getted {message.from_user.id} info from table user")
        user_data = cur.fetchone()

        info = f'Информация о пользователе {message.from_user.username}:\n\n'
        lobbies = get_user_lobbies(message.from_user.id)
        lobbies = '\n'.join(lobbies).replace(',', '\n')
        info += f'В каких лобби состоит:\n{lobbies}\n'
        info += f'\nАктивный пресет: {user_data[2]}\n'

        cur.execute(
            "SELECT preset_name, preset_value FROM preset WHERE preset_author_id = ?", (user_data[0],))
        presets = cur.fetchall()
        presets_str = ''
        for preset in presets:
            presets_str += f'{preset[0]} -> {preset[1]}\n'
        info += f'\nСписок пресетов:\n{presets_str}\n'

        return info


def setup_tables() -> NoReturn:
    """generate tables 'user', 'preset', 'lobby' in file main.db if not exist"""
    create_user_table()
    create_preset_table()
    create_lobby_table()


if __name__ == '__main__':
    setup_tables()
    utility_fill()
