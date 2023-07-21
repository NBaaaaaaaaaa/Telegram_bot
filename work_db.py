import os
import traceback


# Функция возвращает список ["имя пользователя", "id чата"].
def split_username_id(string):
    list_string = list(string)

    for ind in range(len(list_string) - 1, -1, -1):
        if list_string[ind] == ";":
            username = "".join(list_string[:ind])
            chat_id = "".join(list_string[ind + 1:])

            return [username, chat_id]


# Функция возвращает словарь {"имя пользователя": "id чата", ...}.
def get_dict_username_id():
    try:
        with open("users/users_db.txt", "r") as file:
            return {"status": True,
                    "result": dict(split_username_id(string.replace("\n", "")) for string in file.readlines())}

    except Exception as e:
        return {"status": False, "result": traceback.format_exc()}


# Процедура перезаписи файла с пользователями.
def rewrite_db_file(dict_file):
    with open("users/users_db.txt", "w") as file:
        for username in sorted(dict_file.keys()):
            file.write("{n};{i}\n".format(n=username, i=dict_file[username]))


# Процедура добавления имени пользователя в файл.
def add_chat_user_db(username):
    try:
        result = get_dict_username_id()

        if result["status"]:
            # Получаем словарь {"имя пользователя": "id чата", ...}.
            dict_file = result["result"]

            # Запись в файл.
            if username not in dict_file:
                dict_file[username] = ""
                rewrite_db_file(dict_file)

                return "Пользователь {username} успешно добавлен.".format(username=username)

            return "Пользователь {username} уже есть.".format(username=username)

        else:
            return "Пользователь {username} не добавлен.\n{p}".format(username=username, p=result["result"])

    except Exception as e:
        return "Пользователь {username} не добавлен.\n{p}".format(username=username, p=traceback.format_exc())


# Процедура добавления id чата в файл.
def add_chat_id_db(message):
    try:
        result = get_dict_username_id()

        if result["status"]:
            # Получаем словарь {"имя пользователя": "id чата", ...}.
            dict_file = result["result"]

            # Добавляем id чата в словарь, если поле пустое.
            if message.from_user.username in dict_file:
                if dict_file[message.from_user.username] == "":
                    dict_file[message.from_user.username] = message.chat.id
                    # Создаем файл под запись id сообщений.
                    open("all_messages/{chat_id}".format(chat_id=message.chat.id), "w").close()
                    # Перезаписываем бд.
                    rewrite_db_file(dict_file)

                    return "Id чата успешно записан."

            return "Id чата уже записан."

        else:
            return "Id чата не записан.\n{p}".format(p=result["result"])

    except Exception as e:
        return "Id чата не записан.\n{p}".format(p=traceback.format_exc())


# Процедура удаления пользователя.
def delete_user(username):
    try:
        result = get_dict_username_id()

        if result["status"]:
            # Получаем словарь {"имя пользователя": "id чата", ...}.
            dict_file = result["result"]

            if username in dict_file:
                if dict_file[username] != "":
                    chat_id = int(dict_file[username])
                    # Удаляем файл предназначенный для id сообщений.
                    os.remove("all_messages/{chat_id}".format(chat_id=chat_id))
                # Удаляем пользователя из словаря.
                del dict_file[username]

            # Сохраняем изменения словаря.
            rewrite_db_file(dict_file)

            return "Пользователь {username} успешно удален.".format(username=username)

        else:
            return "Пользователь {username} не удален.\n{p}".format(username=username, p=result["result"])

    except Exception as e:
        return "Пользователь {username} не удален.\n{p}".format(username=username, p=traceback.format_exc())


# Функция возвращает имя пользователя по id чата. Необходима только для логов.
def get_username(chat_id):
    result = get_dict_username_id()

    if result["status"]:
        # Получаем словарь {"имя пользователя": "id чата", ...}.
        dict_file = result["result"]

        for username in dict_file:
            try:
                if int(dict_file[username]) == chat_id:
                    return username
            except ValueError:
                print("{n} не имеет id чата.".format(n=username))


# Функция возвращает есть ли пользователь в файле или нет.
def user_in_db(message):
    result = get_dict_username_id()

    if result["status"]:
        # Получаем словарь {"имя пользователя": "id чата", ...}.
        dict_file = result["result"]

        if str(message.chat.id) in dict_file.values() or message.from_user.username in dict_file:
            return {"status": True}

    return {"status": False, "result": result["result"]}


# Процедура создания и записи польователя в файл.
def create_users_db(username):
    if not os.path.isdir("users"):
        os.mkdir("users")

    with open("users/users_db.txt", "w") as file:
        file.write("{username};".format(username=username.split("@")[1]))


# Процедура создаия файла для служб.
def create_services_db():
    open("list_services.txt", "w").close()


# Запустить, если проект только был скачан.
if __name__ == "__main__":
    create_users_db("@имя_пользователя")
    create_services_db()
    os.mkdir("all_messages")
