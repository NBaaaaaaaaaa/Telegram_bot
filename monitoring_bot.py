import telebot
from telebot import types
import time
from bot_functions import *
from logger import *
from TOKEN import TOKEN
from work_db import *

bot = telebot.TeleBot(TOKEN)


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

        for message_id in range(min_id - 15, max_id + 15):
            try:
                bot.delete_message(chat_id, message_id)
            except Exception as e:
                print("Ошибка при удалении сообщения с id: {mes_id}".format(mes_id=message_id))

        # Очищаем файл.
        open("all_messages/{chat_id}".format(chat_id=chat_id), "w")


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
    result = get_dict_username_id()

    if result["status"]:
        # Получаем словарь {"имя пользователя": "id чата", ...}.
        dict_file = result["result"]

        for username in dict_file:
            try:
                send_start_message("restart", int(dict_file[username]))

            except ValueError:
                print("{n} не получил сообщение о рестарте, так как не имеет id чата.".format(n=username))

    else:
        print(result["result"])


# Функция начала работы с ботом.
@bot.message_handler(commands=['start'])
def start(message):
    # Логирование.
    logging(message.from_user.username, message.text)

    # Проверка доступа пользователя.
    result = user_in_db(message)

    if result["status"]:
        # Создаем файл для записи id сообщений.
        if not os.path.exists("all_messages/{chat_id}".format(chat_id=message.chat.id)):
            open("all_messages/{chat_id}".format(chat_id=message.chat.id), "w").close()

        # Записываем id сообщения.
        writing_message_id(message)

        # Записываем id чата в файл.
        result = add_chat_id_db(message)

        bot.send_message(message.chat.id, result)
        # Логирование.
        logging("dhadhfabot", result)

        # Выводим стартовове сообщение.
        send_start_message("start", message.chat.id)

    else:
        if result["result"] != "NoUser":
            # Логирование.
            logging("dhadhfabot", result["result"])

            # Выводим стартовове сообщение.
            bot.send_message(message.chat.id, result["result"])


# Функция добавления пользователя.
@bot.message_handler(commands=['addUser'])
def add_command(message):
    # Логирование.
    logging(message.from_user.username, message.text)

    # Проверка доступа пользователя.
    result = user_in_db(message)

    if result["status"]:
        try:
            # Записываем id чата в файл.
            result = add_chat_user_db(message.text.split(" ", 1)[1].replace(" ", "").split("@", 1)[1])

            # Логирование.
            logging("dhadhfabot", result)

            bot.send_message(message.chat.id, result)

        except IndexError:
            result = "Неверно ведена команда /addUser: {c}".format(c=message.text)

            # Логирование.
            logging("dhadhfabot", result)

            bot.send_message(message.chat.id, result)

    else:
        if result["result"] != "NoUser":
            # Логирование.
            logging("dhadhfabot", result["result"])

            # Выводим стартовове сообщение.
            bot.send_message(message.chat, id, result["result"])


# Функция добавления службы.
@bot.message_handler(commands=['addService'])
def add_command(message):
    # Логирование.
    logging(message.from_user.username, message.text)

    # Проверка доступа пользователя.
    result = user_in_db(message)

    if result["status"]:
        try:
            # Записываем службу в файл.
            result = add_delete_service("add", message.text.split(" ", 1)[1])

            if result["status"]:
                text = "Служба {service} успешно добавлена.".format(service=message.text.split(" ", 1)[1])

            else:
                text = result["result"]

            # Логирование.
            logging("dhadhfabot", text)

            bot.send_message(message.chat.id, text)

        except IndexError:
            text = "Неверно ведена команда /addService: {c}".format(c=message.text)

            # Логирование.
            logging("dhadhfabot", text)

            bot.send_message(message.chat.id, text)

    else:
        if result["result"] != "NoUser":
            # Логирование.
            logging("dhadhfabot", result["result"])

            # Выводим стартовове сообщение.
            bot.send_message(message.chat, id, result["result"])


# Функция получения статуса работы бота. Необходимо для перезапуска бота.
def get_status():
    global status
    return status


# Функция вывода данных служб в формате кнопок.
def output_button_service_stat(message):
    result = get_data_services()
    # Логирование.
    logging("dhadhfabot", "Мониторинг:")

    if result["status"]:
        dict_services = result["result"]

        markup = types.InlineKeyboardMarkup(row_width=1)
        # Заполяем поле кнопками.
        for service in sorted(dict_services.keys()):
            text = "; ".join(
                [service, dict_services[service]["uss"], dict_services[service]["cpu"],
                 dict_services[service]["status"]])

            markup.add(types.InlineKeyboardButton(text, callback_data=service))

            # Логирование.
            logging("dhadhfabot", text)

        bot.send_message(message.chat.id, "Мониторинг:", reply_markup=markup)

    else:
        # Логирование.
        logging("dhadhfabot", result["result"])

        bot.send_message(message.chat.id, result["result"])


# Функция вывода имен служб в формате кнопок.
def output_button_service(message):
    result = get_list_services()

    if result["status"]:
        list_services = result["result"]

        # Логирование.
        logging("dhadhfabot", "Службы:")

        markup = types.InlineKeyboardMarkup(row_width=1)
        # Заполяем поле кнопками.
        for service in sorted(list_services):
            text = service

            markup.add(types.InlineKeyboardButton(text, callback_data="list_{s}".format(s=service)))

            # Логирование.
            logging("dhadhfabot", text)

        bot.send_message(message.chat.id, "Службы:", reply_markup=markup)

    else:
        # Логирование.
        logging("dhadhfabot", result["result"])

        bot.send_message(message.chat.id, result["result"])


# Функция вывода пользователей в формате кнопок.
def output_button_users(message):
    result = get_dict_username_id()

    # Логирование.
    logging("dhadhfabot", "Пользователи:")

    if result["status"]:
        dict_users = result["result"]

        markup = types.InlineKeyboardMarkup(row_width=1)
        # Заполяем поле кнопками.
        for username in sorted(dict_users.keys()):
            markup.add(types.InlineKeyboardButton(username, callback_data=username))

            # Логирование.
            logging("dhadhfabot", username)

        bot.send_message(message.chat.id, "Пользователи:", reply_markup=markup)

    else:
        # Логирование.
        logging("dhadhfabot", result["result"])

        bot.send_message("dhadhfabot", result["result"])


# Функция вывода логов в формате кнопок.
def output_button_logs(message, path=None):
    # В переменной path содержится путь с id сообщений, что потом необходимо будет удалить.
    copy_path = path

    text = ""
    if path:
        # Отделяем путь и id сообщений.
        path, mes_id = path.split("?", 1)
        text = "Содержимое папки '{path}'".format(path=path)

    else:
        text = "Логи:"

    # Получаем список содержимого в папке.
    list_contents = get_directory_data(path)

    # Логирование.
    logging("dhadhfabot", text)

    markup = types.InlineKeyboardMarkup(row_width=1)
    # Заполяем поле кнопками.
    for content in sorted(list_contents):
        if path:
            path = copy_path

        markup.add(types.InlineKeyboardButton(content, callback_data="log:{content}:{path}".format(content=content,
                                                                                                   path=path)))

        # Логирование.
        logging("dhadhfabot", content)

    # Добавление кнопки для возврата назад.
    markup.add(types.InlineKeyboardButton("🔙 Назад", callback_data="Back"))

    bot.send_message(message.chat.id, text, reply_markup=markup)


# Функция обработки нажажатия кнопок со встроенной клавиатуры.
@bot.callback_query_handler(func=lambda message: True)
def callback_query(call):
    if call.message:
        # Проверка доступа пользователя.
        result = user_in_db(call.message)

        if result["status"]:
            # Записываем id сообщения.
            writing_message_id(call.message)

            result_us = get_dict_username_id()
            result_se = get_list_services()
            result_da = get_data_services()

            if result_us["status"] and result_se["status"] and result_da["status"]:
                # Получаем словарь служб с их данными.
                dict_services = result_da["result"]
                # Получаем словарь пользователей.
                list_users = list(result_us["result"])
                # Получаем список имен служб.
                list_services = result_se["result"]

                # Обработка запроса по нажатию на inline кнопки, содержащую данные службы.
                if call.data in dict_services:
                    markup = types.InlineKeyboardMarkup(row_width=1)

                    service_name, service_status = call.data, dict_services[call.data]["status"]

                    # Формируем строку для ответа.
                    text = ""
                    # Остановка службы.
                    if service_status != "Stopped":
                        text = "Остановить сервис {name}?".format(name=service_name)

                        # Добавление кнопки для остановки службы.
                        markup.add(types.InlineKeyboardButton("🔴 Остановить",
                                                              callback_data="Stop_service:{name}:{mes_id}".format(
                                                                  name=service_name, mes_id=call.message.message_id)))

                    # Запуск службы.
                    else:
                        text = "Запустить сервис {name}?".format(name=service_name)

                        # Добавление кнопки для запуска службы.
                        markup.add(types.InlineKeyboardButton("🟢 Запустить",
                                                              callback_data="Start_service:{name}:{mes_id}".format(
                                                                  name=service_name, mes_id=call.message.message_id)))

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

                    # Пауза, чтобы служба успела запуститься.
                    time.sleep(3)

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

                    # Пауза, чтобы служба успела запуститься.
                    time.sleep(3)

                    bot.send_message(call.message.chat.id, result)
                    output_button_service_stat(call.message)

                # Обработка запроса по нажатию на inline кнопки, содержащую имя службы.
                elif call.data in list("list_{s}".format(s=_) for _ in list_services):
                    markup = types.InlineKeyboardMarkup(row_width=1)

                    service_name = call.data.split("_", 1)[1]
                    text = "Удалить службу {name}?".format(name=service_name)

                    # Добавление кнопки для удаления службы.
                    markup.add(types.InlineKeyboardButton("🔴 Удалить",
                                                          callback_data="Delete_service:{name}:{mes_id}".
                                                          format(name=service_name, mes_id=call.message.message_id)))

                    # Добавление кнопки для возврата назад.
                    markup.add(types.InlineKeyboardButton("🔙 Назад", callback_data="Back"))

                    # Логирование.
                    logging("dhadhfabot", text)

                    # Вывод сообщения с кнопками.
                    bot.send_message(call.message.chat.id, text, reply_markup=markup)

                # Обработка запроса по удалению службы.
                elif call.data.split(":", 2)[0] == "Delete_service":
                    result = add_delete_service("delete", call.data.split(":", 2)[1])

                    if result["status"]:
                        text = "Служба {service} успешно удалена.".format(service=call.data.split(":", 2)[1])

                    else:
                        text = result["result"]

                    # Логирование.
                    logging("dhadhfabot", text)

                    bot.send_message(call.message.chat.id, text)

                    # Удаляем 2 пердыдущих сообщения.
                    bot.delete_message(call.message.chat.id, call.data.split(":", 2)[2])
                    bot.delete_message(call.message.chat.id, call.message.message_id)

                    # Логирование.
                    logging(get_username(call.message.chat.id), "Удалить")

                    output_button_service(call.message)

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
                    result = delete_user(call.data.split(":", 2)[1])

                    # Удаляем 2 пердыдущих сообщения.
                    bot.delete_message(call.message.chat.id, call.data.split(":", 2)[2])
                    bot.delete_message(call.message.chat.id, call.message.message_id)

                    # Логирование.
                    logging(get_username(call.message.chat.id), "Удалить")
                    logging("dhadhfabot", result)

                    bot.send_message(call.message.chat.id, result)

                    # Вывод сообщения с кнопками.
                    output_button_users(call.message)

                # Обработка запроса по нажатию на inline кнопки, содержащую контент логов.
                elif call.data.split(":", 1)[0] == "log":
                    content = call.data.split(":")[1]

                    path = call.data.split(":")[2]
                    if path != "None":
                        path = "{path}/{content}?{mes_id}".format(path=path.split("?", 1)[0],
                                                                  content=content,
                                                                  mes_id=path.split("?", 1)[1])

                    else:
                        path = content

                    path += "?{mes_id}".format(mes_id=call.message.message_id)

                    if ".txt" in content:
                        path, str_mes_id = path.split("?", 1)
                        # Отправляем файл.
                        bot.send_document(call.message.chat.id, open("logs/" + path, 'rb'))

                        # Удаляем предыдущие сообщения.
                        for mes_id in str_mes_id.split("?"):
                            bot.delete_message(call.message.chat.id, mes_id)

                    else:
                        # Выводим содержимое директории.
                        output_button_logs(call.message, path)

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

            else:
                if not result_se["status"]:
                    # Логирование.
                    logging("dhadhfabot", result_se["result"])

                    bot.send_message(call.message.chat.id, result_se["result"])

                elif not result_us["status"]:
                    # Логирование.
                    logging("dhadhfabot", result_us["result"])

                    bot.send_message(call.message.chat.id, result_us["result"])

                else:
                    # Логирование.
                    logging("dhadhfabot", result_da["result"])

                    bot.send_message(call.message.chat.id, result_da["result"])

        else:
            # Логирование.
            logging("dhadhfabot", result["result"])

            # Выводим стартовове сообщение.
            bot.send_message(call.message.chat, id, result["result"])


# Функция, обслуживающая отправленные сообщения.
@bot.message_handler(content_types=["text"])
def buttons_events(message):
    # Логирование.
    logging(message.from_user.username, message.text)

    # Проверка доступа пользователя.
    result = user_in_db(message)

    if result["status"]:

        # Записываем id сообщения.
        writing_message_id(message)

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
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)

            # Добавление стартовых кнопок.
            markup.add(
                types.KeyboardButton("👨 Добавить пользователя"),
                types.KeyboardButton("📖 Cписок пользователей"),
                types.KeyboardButton("🟢 Добавить службу"),
                types.KeyboardButton("📖 Cписок служб"),
                types.KeyboardButton("🧾 Логи"),
                types.KeyboardButton("🔙 Назад")
            )

            # Логирование.
            logging("dhadhfabot", "Режим администратора.")

            bot.send_message(message.chat.id, "Режим администратора.", reply_markup=markup)

        # Обработка запроса "👨 Добавть пользователя".
        elif message.text == "👨 Добавить пользователя":
            # Логирование.
            logging("dhadhfabot", "Используй команду: /addUser *@имя_пользователя*")

            bot.send_message(message.chat.id, "Используй команду:\n/addUser *@имя_пользователя*", parse_mode="Markdown")

        # Обработка запроса "📖 Cписок пользователей".
        elif message.text == "📖 Cписок пользователей":
            output_button_users(message)

        # Обработка запроса "📖 Cписок служб".
        elif message.text == "📖 Cписок служб":
            output_button_service(message)

        # Обработка запроса "🟢 Добавить службу".
        elif message.text == "🟢 Добавить службу":
            # Логирование.
            logging("dhadhfabot", "Используй команду: /addService *имя_службы*")

            bot.send_message(message.chat.id, "Используй команду:\n/addService *имя_службы*", parse_mode="Markdown")

        # Обработка запроса "🧾 Логи".
        elif message.text == "🧾 Логи":
            output_button_logs(message)

        # Обработка запроса "🔙 Назад".
        elif message.text == "🔙 Назад":
            send_start_message("after_admin", message.chat.id)

    else:
        if result["result"] != "NoUser":
            # Логирование.
            logging("dhadhfabot", result["result"])

            # Выводим стартовове сообщение.
            bot.send_message(message.chat, id, result["result"])


# Процедура запуска бота.
def start_bot():
    # Запускаем процесс опроса Telegram серверов на предмет новых сообщений.
    bot.polling(none_stop=True)


# Переменная. Необходима для перезапуска бота.
status = ""
