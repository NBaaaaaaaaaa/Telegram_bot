import telebot
from telebot import types
from func_about_services import *
import time
from datetime import datetime
import os

bot = telebot.TeleBot(open("TOKEN.txt", "r").read())


# Процедура записи id сообщения в соответствующий файл.
def writing_message_id(message):
    with open("all_messages/{chat_id}".format(chat_id=message.chat.id), "a+") as file:
        file.write(str(message.message_id) + ";")


# Процедура удаления переписки с ботом.
def delete_all_messages(chat_id):
    with open("all_messages/{chat_id}".format(chat_id=chat_id), "r+") as file:
        # Получаем список id сообщений в чате.
        list_messages_id = list(map(int, file.read().split(";")[:-1]))
        min_id, max_id = min(list_messages_id), max(list_messages_id)

        for message_id in range(min_id, max_id + 3):
            try:
                bot.delete_message(chat_id, message_id)
            except Exception as e:
                print("Ошибка при удалении сообщения с id: {mes_id}".format(mes_id=message_id))

        # Очищаем файл.
        open("all_messages/{chat_id}".format(chat_id=chat_id), "w")


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
    with open("users/users_db.txt", "r") as file:
        return dict(split_username_id(string.replace("\n", "")) for string in file.readlines())


# Процедура перезаписи файла, если место id чата было пустое.
def rewrite_db_file(dict_file):
    with open("users/users_db.txt", "w") as file:
        for username in sorted(dict_file.keys()):
            file.write("{n};{i}\n".format(n=username, i=dict_file[username]))


# Процедура добавления имени пользователя в файл.
def add_chat_user_db(username):
    # Получаем словарь {"имя пользователя": "id чата", ...}.
    dict_file = get_dict_username_id()
    # Запись в файл.
    if username not in dict_file:
        dict_file[username[1:]] = ""
        rewrite_db_file(dict_file)


# Процедура добавления id чата в файл.
def add_chat_id_db(message):
    # Получаем словарь {"имя пользователя": "id чата", ...}.
    dict_file = get_dict_username_id()

    # Добавляем id чата в словарь, если поле пустое.
    if message.from_user.username in dict_file:
        if dict_file[message.from_user.username] == "":
            dict_file[message.from_user.username] = message.chat.id
            # Создаем файл под запись id сообщений.
            open("all_messages/{chat_id}".format(chat_id=message.chat.id), "w").close()
            # Перезаписываем бд.
            rewrite_db_file(dict_file)


# Процедура удаления пользователя.
def delete_user(username):
    # Получаем словарь {"имя пользователя": "id чата", ...}.
    dict_file = get_dict_username_id()

    if username in dict_file:
        if dict_file[username] != "":
            chat_id = int(dict_file[username])
            # Удаляем файл предназначенный для id сообщений.
            os.remove("all_messages/{chat_id}".format(chat_id=chat_id))

        # Удаляем пользователя из словаря.
        del dict_file[username]

    # Сохраняем изменения словаря.
    rewrite_db_file(dict_file)


# Функция возвращает имя пользователя по id чата.
def get_username(chat_id):
    # Получаем словарь {"имя пользователя": "id чата", ...}.
    dict_file = get_dict_username_id()

    for username in dict_file:
        try:
            if int(dict_file[username]) == chat_id:
                return username
        except ValueError:
            print("{n} не имеет id чата.".format(n=username))


# Функция возвращает есть ли пользователь в файле или нет.
def user_in_db(message):
    # Получаем словарь {"имя пользователя": "id чата", ...}.
    dict_file = get_dict_username_id()

    if str(message.chat.id) in dict_file.values() or message.from_user.username in dict_file:
        return True

    return False


# Процедура логирования.
def logging(username, text):
    log_file = "log.{num}.txt"
    # Получение текущей даты.
    current_datetime = datetime.now()
    path = "logs/{y}/{m}/{d}/".format(y=current_datetime.year, m=current_datetime.month, d=current_datetime.day)

    # Создание директорий.
    os.makedirs(path, exist_ok=True)

    # Создание имени логу.
    list_files = os.listdir(path)
    # Если файлов нет в директории.
    if len(list_files) == 0:
        log_file = log_file.format(num=0)

    # Если файлы есть в директории.
    else:
        # Получаем последний созданный файл.
        last_file = list_files[-1]

        # Если вес его >= 48 Мб
        if round(int(os.stat(path + last_file).st_size)/1024/1024, 2) >= 48:
            log_file = log_file.format(num=int(last_file.split(".")[1]) + 1)

        # Если вес его < 48 Мб
        else:
            log_file = last_file

    # Запись в файл.
    with open(path + log_file, "a", encoding="utf-8") as file:
        file.write("{date} | {name} | {text}\n".format(date=current_datetime.strftime("%Y-%m-%d %H:%M:%S"),
                                                       name=username, text=text))


# Функция отправки стартового сообщения.
def send_start_message(mod, chat_id):
    dict_text = {"start": "Привет.\n" +
                          "Бот позволяет мониторить, зпускать и останавливать сервисы на сервере.\n" +
                          "Для управления используй кнопки.",
                 "restart": "Бот перезапущен.\n" +
                            "Для управления используй кнопки.",
                 "after_admin": "Режим пользователя."}

    # Создание поля для вставки кнопок.
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)

    # Добавление стартовых кнопок.
    markup.add(
        types.KeyboardButton("📊 Мониторинг"),
        types.KeyboardButton("🧹 Очистить чат"),
        types.KeyboardButton("🔴 Остановить службы"),
        types.KeyboardButton("🟢 Запустить службы"),
        types.KeyboardButton("🔁 Перезапустить бота"),
        types.KeyboardButton("🫅 Админ")
    )

    # Логирование.
    logging("dhadhfabot", dict_text[mod].replace("\n", " "))

    # Вывод сообщения и кнопок.
    bot.send_message(chat_id, dict_text[mod], reply_markup=markup)


# Функция отправки сообщений всем пользователям о перезапуске бота.
def send_message_after_restart():
    # Получаем словарь {"имя пользователя": "id чата", ...}.
    dict_file = get_dict_username_id()

    for username in dict_file:
        try:
            send_start_message("restart", int(dict_file[username]))
        except ValueError:
            print("{n} не получил сообщение о рестарте, так как не имеет id чата.".format(n=username))


# Функция начала работы с ботом.
@bot.message_handler(commands=['start'])
def start(message):
    # Проверка доступа пользователя.
    if user_in_db(message):
        # Логирование.
        logging(message.from_user.username, message.text)
        # Записываем id чата в файл.
        add_chat_id_db(message)
        # Выводим стартовове сообщение.
        send_start_message("start", message.chat.id)
        # Записываем id сообщения.
        writing_message_id(message)


# Функция добавления пользователя.
@bot.message_handler(commands=['add'])
def add_command(message):
    # Проверка доступа пользователя.
    if user_in_db(message):
        try:
            # Логирование.
            logging(message.from_user.username, message.text)
            # Записываем id чата в файл.
            add_chat_user_db(message.text.split(" ", 1)[1].replace(" ", ""))

        except IndexError:
            print("Неверно ведена команда /add: '{c}'".format(c=message.text))


# Функция получения статуса работы бота. Необходимо для перезапуска бота.
def get_status():
    global status
    return status


# Функция вывода служб в формате кнопок.
def output_button_service_stat(message):
    dict_services = get_data_services()

    # Логирование.
    logging("dhadhfabot", "Мониторинг:")

    markup = types.InlineKeyboardMarkup(row_width=1)
    # Заполяем поле кнопками.
    for service in sorted(dict_services.keys()):
        text = "; ".join(
            [service, dict_services[service]["uss"],
             dict_services[service]["status"]])  # , dict_services[service]["cpu"]

        markup.add(types.InlineKeyboardButton(text, callback_data=service))

        # Логирование.
        logging("dhadhfabot", text)

    bot.send_message(message.chat.id, "Мониторинг:", reply_markup=markup)


# Функция вывода пользователей в формате кнопок.
def output_button_users(message):
    dict_users = get_dict_username_id()

    # Логирование.
    logging("dhadhfabot", "Пользователи:")

    markup = types.InlineKeyboardMarkup(row_width=1)
    # Заполяем поле кнопками.
    for username in sorted(dict_users.keys()):
        markup.add(types.InlineKeyboardButton(username, callback_data=username))

        # Логирование.
        logging("dhadhfabot", username)

    bot.send_message(message.chat.id, "Пользователи:", reply_markup=markup)


# Функция обработки нажажатия кнопок со встроенной клавиатуры.
@bot.callback_query_handler(func=lambda message: True)
def callback_query(call):
    if call.message:
        # Проверка доступа пользователя.
        if user_in_db(call.message):
            # Записываем id сообщения.
            writing_message_id(call.message)

            # Получаем словарь служб с их данными.
            dict_services = get_data_services()
            # Получаем словарь пользователей.
            list_users = list(get_dict_username_id())

            if call.data in dict_services:
                markup = types.InlineKeyboardMarkup(row_width=1)

                service_name, service_status = call.data, dict_services[call.data]["status"]

                # Формируем строку для ответа.
                text = ""
                # Остановка службы.
                if service_status != "stopped":
                    text = "Остановить сервис {name}?".format(name=service_name)

                    # Добавление кнопки для остановки службы.
                    markup.add(types.InlineKeyboardButton("🔴 Остановить",
                                                          callback_data="Stop_service:{name}:{mes_id}".
                                                          format(name=service_name, mes_id=call.message.message_id)))

                # Запуск службы.
                else:
                    text = "Запустить сервис {name}?".format(name=service_name)

                    # Добавление кнопки для запуска службы.
                    markup.add(types.InlineKeyboardButton("🟢 Запустить",
                                                          callback_data="Start_service:{name}:{mes_id}".
                                                          format(name=service_name, mes_id=call.message.message_id)))

                # Добавление кнопки для возврата назад.
                markup.add(types.InlineKeyboardButton("🔙 Назад", callback_data="Back"))

                # Логирование.
                logging("dhadhfabot", text)

                # Вывод сообщения с кнопками.
                bot.send_message(call.message.chat.id, text, reply_markup=markup)

            # Обработка запроса по остановке службы.
            elif call.data.split(":", 2)[0] == "Stop_service":
                result = on_off_services("off", call.data.split(":", 2)[1])

                # Удаляем 2 пердыдущих сообщения.
                bot.delete_message(call.message.chat.id, call.data.split(":", 2)[2])
                bot.delete_message(call.message.chat.id, call.message.message_id)

                # Логирование.
                logging(get_username(call.message.chat.id), "Остановить")
                logging("dhadhfabot", result.replace("\n", " "))

                bot.send_message(call.message.chat.id, result)
                output_button_service_stat(call.message)

            # Обработка запроса по запуску службы.
            elif call.data.split(":", 2)[0] == "Start_service":
                result = on_off_services("on", call.data.split(":", 2)[1])

                # Удаляем 2 пердыдущих сообщения.
                bot.delete_message(call.message.chat.id, call.data.split(":", 2)[2])
                bot.delete_message(call.message.chat.id, call.message.message_id)

                # Логирование.
                logging(get_username(call.message.chat.id), "Запустить")
                logging("dhadhfabot", result.replace("\n", " "))

                bot.send_message(call.message.chat.id, result)
                # Пауза, чтобы служба успела запуститься.
                time.sleep(1)
                output_button_service_stat(call.message)

            # Если было передано значение равное имени пользователя.
            elif call.data in list_users:
                markup = types.InlineKeyboardMarkup(row_width=1)

                text = "Удалить пользователя {name}?".format(name=call.data)

                # Добавление кнопки удаления пользователя.
                markup.add(types.InlineKeyboardButton("🧹 Удалить",
                                                      callback_data="Delete:{name}:{mes_id}".
                                                      format(name=call.data, mes_id=call.message.message_id)))

                # Добавление кнопки для возврата назад.
                markup.add(types.InlineKeyboardButton("🔙 Назад", callback_data="Back"))

                # Логирование.
                logging("dhadhfabot", text)

                # Вывод сообщения с кнопками.
                bot.send_message(call.message.chat.id, text, reply_markup=markup)

            # Обработка запроса по удалению пользователя.
            elif call.data.split(":", 2)[0] == "Delete":
                delete_user(call.data.split(":", 2)[1])

                # Удаляем 2 пердыдущих сообщения.
                bot.delete_message(call.message.chat.id, call.data.split(":", 2)[2])
                bot.delete_message(call.message.chat.id, call.message.message_id)

                # Логирование.
                logging(get_username(call.message.chat.id), "Удалить")

                # Пауза, чтобы служба успела запуститься.
                output_button_users(call.message)

            # Обработка запроса вернуться назад.
            elif call.data == "Back":
                # Логирование.
                logging(get_username(call.message.chat.id), "Назад")

                bot.delete_message(call.message.chat.id, call.message.message_id)

            # Обработка запроса перезапуска бота.
            elif call.data == "Restart":
                # Логирование.
                logging(get_username(call.message.chat.id), "Перезапустить")

                global status
                # Меняем значение глобальной переменной на "Restart".
                status = call.data

                # Увираем кнопки с клавиатуры.
                no_buttons = telebot.types.ReplyKeyboardRemove()

                # Логирование.
                logging("dhadhfabot", "Бот перезапускается ...")

                # Удаление предыдущего сообщения.
                bot.delete_message(call.message.chat.id, call.message.message_id)

                # Отправляем сообщение.
                bot.send_message(call.message.chat.id, "Бот перезапускается ...", reply_markup=no_buttons)
                # Завершаем процесс опроса Telegram серверов на предмет новых сообщений.
                bot.stop_polling()


# Функция, обслуживающая отправленные сообщения.
@bot.message_handler(content_types=["text"])
def buttons_events(message):
    # Проверка доступа пользователя.
    if user_in_db(message):
        # Записываем id сообщения.
        writing_message_id(message)
        # Логирование.
        logging(message.from_user.username, message.text)

        # Обработка запроса "📊 Мониторинг".
        if message.text == "📊 Мониторинг":
            output_button_service_stat(message)

        # Обработка запроса "🧹 Очистить чат".
        elif message.text == "🧹 Очистить чат":
            delete_all_messages(message.chat.id)

        # Обработка запроса "🟢 Запустить службы".
        elif message.text == "🟢 Запустить службы":
            result = on_off_services("on")

            # Логирование.
            logging("dhadhfabot", result.replace("\n", " "))

            bot.send_message(message.chat.id, result)

        # Обработка запроса "🔴 Остановить службы".
        elif message.text == "🔴 Остановить службы":
            result = on_off_services("off")

            # Логирование.
            logging("dhadhfabot", result.replace("\n", " "))

            bot.send_message(message.chat.id, result)

        # Обработка запроса "🔁 Перезапустить бота".
        elif message.text == "🔁 Перезапустить бота":
            markup = types.InlineKeyboardMarkup(row_width=1)
            markup.add(
                types.InlineKeyboardButton("🔁 Перезапустить", callback_data="Restart"),
                types.InlineKeyboardButton("🔙 Назад", callback_data="Back")
            )

            # Логирование.
            logging("dhadhfabot", "Перезапустить бота?")

            bot.send_message(message.chat.id, "Перезапустить бота?", reply_markup=markup)

        # Обработка запроса "🫅 Админ".
        elif message.text == "🫅 Админ":
            # Создание поля для вставки кнопок.
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)

            # Добавление стартовых кнопок.
            markup.add(
                types.KeyboardButton("👨 Добавить пользователя"),
                types.KeyboardButton("📖 Cписок пользователей"),
                types.KeyboardButton("🔙 Назад")
            )

            # Логирование.
            logging("dhadhfabot", "Режим администратора.")

            bot.send_message(message.chat.id, "Режим администратора.", reply_markup=markup)

        # Обработка запроса "👨 Добавть пользователя".
        elif message.text == "👨 Добавить пользователя":
            # Логирование.
            logging("dhadhfabot", "Испоользуй команду: /add *'@имя_пользователя'*")

            bot.send_message(message.chat.id, "Испоользуй команду: /add *'@имя_пользователя'*", parse_mode="Markdown")

        # Обработка запроса "📖 Cписок пользователей".
        elif message.text == "📖 Cписок пользователей":
            output_button_users(message)

        # Обработка запроса "🔙 Назад".
        elif message.text == "🔙 Назад":
            send_start_message("after_admin", message.chat.id)


# Процедура запуска бота.
def start_bot():
    # Запускаем процесс опроса Telegram серверов на предмет новых сообщений.
    bot.polling(none_stop=True)


if __name__ == "__main__":
    start_bot()

# Переменная. Необходима для перезапуска бота.
status = ""
