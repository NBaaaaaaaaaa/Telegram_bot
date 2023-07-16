from pymysql import connect, Error, cursors
from config_db import host, user, password, db_name


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
        return str(e)


# Функция возвращает наличие пользователь в бд.
def user_in_db(message):
    connection = connect_db()

    if type(connection) == str:
        return {"stat": False, "comment": connection}

    try:
        select_user_query = """
                CALL show_user('{user_name}', {chat_id})
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
            query = "CALL add_user('{user_name}')".format(user_name=username)

            text = "Пользователь {u} успешно добавлен.".format(u=username)

        elif mod == "delete":
            query = "CALL delete_user('{user_name}')".format(user_name=username)

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
        select_user_query = "CALL get_user_data('{user_name}')".format(user_name=message.from_user.username)

        cur = connection.cursor()
        cur.execute(select_user_query)
        result = cur.fetchall()

        if not result[0]["chat_id"]:
            try:
                replace_tuple_query = """
                    CALL replace_user_data({user_id}, '{user_name}', {chat_id})
                    """.format(user_id=result[0]["user_id"], user_name=result[0]["user_name"], chat_id=message.chat.id)

                connection.cursor().execute(replace_tuple_query)
                connection.commit()

                return {"stat": True, "comment": "Id чата успешно внесен в таблицу."}

            except Error as e:
                return {"stat": False, "comment": str(e)}

        return {"stat": True, "comment": None}

    except Error as e:
        return {"stat": False, "comment": str(e)}


# Функция возвращает словарь {"имя пользователя": "id чата", ...}.
def get_dict_username_id():
    connection = connect_db()

    if type(connection) == str:
        return {"stat": False, "comment": connection}

    try:
        select_user_query = "CALL get_users_data()"

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
        select_user_query = "CALL get_services_name()"

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
            query = "CALL add_service('{service_name}')".format(service_name=service_name)

            text = "Служба {s} успешно добавлена.".format(s=service_name)

        elif mod == "delete":
            query = "CALL delete_service('{service_name}')".format(service_name=service_name)

            text = "Служба {s} успешно удалена.".format(s=service_name)

        connection.cursor().execute(query)
        connection.commit()

        return text

    except Error as e:
        return str(e)


if __name__ == "__main__":
    your_username = "@имя_пользователя"
    add_delete_user("add", your_username)

