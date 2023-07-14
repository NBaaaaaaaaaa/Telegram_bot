from pymysql import connect, Error, cursors
from config_db import host, user, password, db_name
import traceback


# Процедура создания таблиц.
def crate_tables(connection):
    try:
        create_users_query = """
            CREATE TABLE IF NOT EXISTS `telegramBot`.`users` (
              `user_id` INT NOT NULL AUTO_INCREMENT,
              `user_name` VARCHAR(45) NOT NULL COMMENT 'Имя пользователя.',
              `chat_id` INT NULL COMMENT 'id чата с ботом.',
              PRIMARY KEY (`user_id`),
              UNIQUE INDEX `user_name_UNIQUE` (`user_name` ASC) VISIBLE,
              UNIQUE INDEX `chat_id_UNIQUE` (`chat_id` ASC) VISIBLE)
            ENGINE = InnoDB;
            """

        create_services_query = """
            CREATE TABLE IF NOT EXISTS `telegramBot`.`services` (
              `service_id` INT NOT NULL AUTO_INCREMENT,
              `service_name` VARCHAR(45) NOT NULL COMMENT 'Имя службы.',
              PRIMARY KEY (`service_id`),
              UNIQUE INDEX `service_name_UNIQUE` (`service_name` ASC) VISIBLE)
            ENGINE = InnoDB;       
            """

        connection.cursor().execute(create_users_query)
        connection.commit()
        print("Таблица пользователей успешно создана.")

        connection.cursor().execute(create_services_query)
        connection.commit()
        print("Таблица служб успешно создана.")

    except Error as e:
        print(e)


# Процедура создания базы данных.
def create_db():
    try:
        connection = connect(
            host=host,
            user=user,
            password=password
        )

        create_db_query = "CREATE DATABASE {db_name}".format(db_name=db_name)

        connection.cursor().execute(create_db_query)
        print("База данных успешно создана.")

        crate_tables(connection)

    except Error as e:
        print(e)


# Функция подключения к бд.
def connect_db():
    try:
        connection = connect(
            host=host,
            user=user,
            password=password,
            database=db_name,
            cursorclass=cursors.DictCursor
        )

        return connection

    except Error as e:
        if int(str(e)[1:5]) == 1049:
            create_db()
            connect_db()

        else:
            return str(e)


# Функция возвращает наличие пользователь в бд.
def user_in_db(message):
    connection = connect_db()

    if type(connection) == str:
        return {"stat": False, "comment": connection}

    try:
        select_user_query = """
                SELECT user_name FROM users
                WHERE user_name = '{user_name}' OR chat_id = {chat_id}
                """.format(user_name=message.from_user.username, chat_id=message.chat.id)

        cur = connection.cursor()
        cur.execute(select_user_query)
        if cur.fetchall():
            return {"stat": True}

        return {"stat": False, "comment": "У вас нет прав доступа."}

    except Error as e:
        return {"stat": False, "comment": str(e)}


# Функция добавления/удаления пользователя в/из бд.
def add_delete_user(mod, username):
    connection = connect_db()

    if type(connection) == str:
        return connection

    try:
        query = ""
        text = ""
        if mod == "add":
            username = username.split("@", 1)[1]

            query = """
                INSERT IGNORE INTO users (user_name)
                VALUES ("{username}")
                """.format(username=username)

            text = "Пользователь {u} успешно добавлен.".format(u=username)

        elif mod == "delete":
            query = """
                DELETE FROM users
                WHERE user_name='{user_name}'""".format(user_name=username)

            text = "Пользователь {u} успешно удален.".format(u=username)

        connection.cursor().execute(query)
        connection.commit()

        return text

    except Error as e:
        return str(e)


# Функция добавления id чата в бд.
def add_chat_id_db(message):
    connection = connect_db()

    if type(connection) == str:
        return {"stat": False, "comment": connection}

    try:
        select_user_query = """
            SELECT * FROM users
            WHERE user_name = '{user_name}'""".format(user_name=message.from_user.username)

        cur = connection.cursor()
        cur.execute(select_user_query)
        result = cur.fetchall()

        if not result[0]["chat_id"]:
            replace_tuple_query = """
                REPLACE INTO users 
                VALUES ({user_id}, '{user_name}', {chat_id});
                """.format(user_id=result[0]["user_id"], user_name=result[0]["user_name"], chat_id=message.chat.id)

            connection.cursor().execute(replace_tuple_query)
            connection.commit()

            return {"stat": True, "comment": "Id чата успешно внесен в таблицу."}

        return {"stat": True, "comment": None}

    except Error as e:
        return {"stat": False, "comment": str(e)}


# Функция возвращает словарь {"имя пользователя": "id чата", ...}.
def get_dict_username_id():
    connection = connect_db()

    if type(connection) == str:
        return {"stat": False, "comment": connection}

    try:
        select_user_query = "SELECT user_name, chat_id FROM users"

        cur = connection.cursor()
        cur.execute(select_user_query)
        result = cur.fetchall()

        send_dict = {}
        for user_data in result:
            send_dict[user_data["user_name"]] = user_data["chat_id"]

        return {"stat": True, "dict_users": send_dict}

    except Error as e:
        return {"stat": False, "comment": str(e)}


# Функция возваращает список имен служб в бд.
def get_list_services():
    connection = connect_db()

    if type(connection) == str:
        return {"stat": False, "comment": connection}

    try:
        select_user_query = "SELECT service_name FROM services"

        cur = connection.cursor()
        cur.execute(select_user_query)
        result = cur.fetchall()

        return {"stat": True, "list_services": list(service["service_name"] for service in result)}

    except Error as e:
        return {"stat": False, "comment": str(e)}


# Функция добавления/удаления имени службы в/из файл/а.
def add_delete_service(mod, service_name):
    connection = connect_db()

    if type(connection) == str:
        return connection

    try:
        query = ""
        text = ""
        if mod == "add":
            query = """
                    INSERT IGNORE INTO services (service_name)
                    VALUES ("{service_name}")
                    """.format(service_name=service_name)

            text = "Служба {s} успешно добавлена.".format(s=service_name)

        elif mod == "delete":
            query = """
                    DELETE FROM services
                    WHERE service_name='{service_name}'""".format(service_name=service_name)

            text = "Служба {s} успешно удалена.".format(s=service_name)

        connection.cursor().execute(query)
        connection.commit()

        return text

    except Error as e:
        return str(e)


if __name__ == "__main__":
    connect_db()
    your_username = "Ваше @имя_пользователя Telegram"
    add_delete_service("add", your_username)

