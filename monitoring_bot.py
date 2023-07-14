import telebot
from telebot import types
import time
from bot_functions import *
from logger import logging
from TOKEN import TOKEN
from work_db import add_delete_user, user_in_db, add_chat_id_db, get_dict_username_id, add_delete_service


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

        for message_id in range(min_id, max_id + 3):
            try:
                bot.delete_message(chat_id, message_id)
            except Exception as e:
                print("Ошибка при удалении сообщения с id: {mes_id}".format(mes_id=message_id))

        # Очищаем файл.
        open("all_messages/{chat_id}".format(chat_id=chat_id), "w")


# Функция возвращает имя пользователя по id чата. Необходима только для логов.
def get_username(chat_id):
    # Получаем словарь {"имя пользователя": "id чата", ...}.
    dict_file = get_dict_username_id()

    for username in dict_file:
        try:
            if int(dict_file[username]) == chat_id:
                return username
        except ValueError:
            print("{n} не имеет id чата.".format(n=username))


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
        except TypeError:
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
@bot.message_handler(commands=['addUser'])
def add_command(message):
    # Проверка доступа пользователя.
    if user_in_db(message):
        try:
            # Логирование.
            logging(message.from_user.username, message.text)
            # Записываем пользователя в бд.
            add_delete_user("add", message.text.split(" ", 1)[1].replace(" ", ""))

        except IndexError:
            print("Неверно ведена команда /addUser: {c}".format(c=message.text))


# Функция добавления службы.
@bot.message_handler(commands=['addService'])
def add_command(message):
    # Проверка доступа пользователя.
    if user_in_db(message):
        try:
            # Логирование.
            logging(message.from_user.username, message.text)
            # Записываем id чата в файл.
            add_delete_service("add", message.text.split(" ", 1)[1])

        except IndexError:
            print("Неверно ведена команда /addService: {c}".format(c=message.text))


# Функция получения статуса работы бота. Необходимо для перезапуска бота.
def get_status():
    global status
    return status


# Функция вывода данных служб в формате кнопок.
def output_button_service_stat(message):
    dict_services = get_data_services()

    # Логирование.
    logging("dhadhfabot", "Мониторинг:")

    markup = types.InlineKeyboardMarkup(row_width=1)
    # Заполяем поле кнопками.
    for service in sorted(dict_services.keys()):
        text = "; ".join(
            [service, dict_services[service]["uss"],
             dict_services[service]["status"]])

        markup.add(types.InlineKeyboardButton(text, callback_data=service))

        # Логирование.
        logging("dhadhfabot", text)

    bot.send_message(message.chat.id, "Мониторинг:", reply_markup=markup)


# Функция вывода имен служб в формате кнопок.
def output_button_service(message):
    list_services = get_list_services()

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
            # Получаем список имен служб.
            list_services = get_list_services()

            # Обработка запроса по нажатию на inline кнопки, содержащую данные службы.
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
                add_delete_service("delete", call.data.split(":", 2)[1])

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
                add_delete_user("delete", call.data.split(":", 2)[1])

                # Удаляем 2 пердыдущих сообщения.
                bot.delete_message(call.message.chat.id, call.data.split(":", 2)[2])
                bot.delete_message(call.message.chat.id, call.message.message_id)

                # Логирование.
                logging(get_username(call.message.chat.id), "Удалить")

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
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)

            # Добавление стартовых кнопок.
            markup.add(
                types.KeyboardButton("👨 Добавить пользователя"),
                types.KeyboardButton("📖 Cписок пользователей"),
                types.KeyboardButton("🟢 Добавить службу"),
                types.KeyboardButton("📖 Cписок служб"),
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
