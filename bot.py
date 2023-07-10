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


# Процедура добавления id чата в файл.
def add_chat_id_db(chat_id):
    chat_id = str(chat_id)

    with open("all_chat_id.txt", "r+") as file:
        if file.read().find(chat_id) == -1:
            # Записываем id чата в файл.
            file.write(chat_id + ";")
            # Создаем файл под запись id сообщений.
            open("all_messages/{chat_id}".format(chat_id=chat_id), "w").close()


# Процедура записи никнейма пользователя в файл.
def add_username_db(username):
    with open("users/users_db.txt", "r+") as file:
        if file.read().find(username) == -1:
            # Записываем id чата в файл.
            file.write(username + ";")


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
        file.write("{date} | {name} | {text}\n".format(date=current_datetime, name=username, text=text))


# Функция отправки стартового сообщения.
def send_start_message(mod, chat_id):
    dict_text = {"start": "Привет.\n" +
                          "Бот позволяет мониторить, зпускать и останавливать сервисы на сервере.\n" +
                          "Для управления используй кнопки.",
                 "restart": "Бот перезапущен.\n" +
                            "Для управления используй кнопки."}

    # Создание поля для вставки кнопок.
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)

    # Добавление стартовых кнопок.
    markup.add(
        types.KeyboardButton("Мониторинг"),
        types.KeyboardButton("Очистить чат"),
        types.KeyboardButton("Остановить службы"),
        types.KeyboardButton("Запустить службы"),
        types.KeyboardButton("Перезапустить бота")
    )

    # Логирование.
    logging("dhadhfabot", dict_text[mod].replace("\n", " "))

    # Вывод сообщения и кнопок.
    bot.send_message(chat_id, dict_text[mod], reply_markup=markup)


# Функция начала работы с ботом.
@bot.message_handler(commands=['start'])
def start(message):
    # Логирование.
    logging(message.from_user.username, message.text)
    # Записываем id чата в файл.
    add_chat_id_db(message.chat.id)
    # Записываем ние пользователя в файл.
    add_username_db(message.from_user.username)
    # Выводим стартовове сообщение.
    send_start_message("start", message.chat.id)
    # Записываем id сообщения.
    writing_message_id(message)


# Функция отправки сообщений всем пользователям о перезапуске бота.
def send_message_after_restart():
    with open("all_chat_id.txt", "r+") as file:
        list_chat_id = list(map(int, file.read().split(";")[:-1]))
        for chat_id in list_chat_id:
            send_start_message("restart", chat_id)


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


# Функция обработки нажажатия кнопок со встроенной клавиатуры.
@bot.callback_query_handler(func=lambda message: True)
def callback_query(call):
    if call.message:
        # Записываем id сообщения.
        writing_message_id(call.message)

        # Получаем список служб и их статуса.
        dict_services = get_data_services()

        if call.data in dict_services:
            markup = types.InlineKeyboardMarkup(row_width=1)

            service_name, service_status = call.data, dict_services[call.data]["status"]

            # Формируем строку для ответа.
            text = ""
            # Остановка службы.
            if service_status != "stopped":
                text = "Остановить сервис {name}?".format(name=service_name)

                # Добавление кнопки для остановки службы.
                markup.add(types.InlineKeyboardButton("Остановить",
                                                      callback_data="Stop_service:{name}:{mes_id}".
                                                      format(name=service_name, mes_id=call.message.message_id)))

            # Запуск службы.
            else:
                text = "Запустить сервис {name}?".format(name=service_name)

                # Добавление кнопки для запуска службы.
                markup.add(types.InlineKeyboardButton("Запустить",
                                                      callback_data="Start_service:{name}:{mes_id}".
                                                      format(name=service_name, mes_id=call.message.message_id)))

            # Добавление кнопки для возврата назад.
            markup.add(types.InlineKeyboardButton("Назад", callback_data="Back"))

            # Логирование.
            logging("dhadhfabot", text)

            # Вывод сообщения с кнопками.
            bot.send_message(call.message.chat.id, text, reply_markup=markup)

        # Обработка запроса по остановке службы.
        elif call.data.split(":", 2)[0] == "Stop_service":
            # Логирование.
            logging(call.message.from_user.username, call.message.text)

            result = on_off_services("off", call.data.split(":", 2)[1])

            # Удаляем 2 пердыдущих сообщения.
            bot.delete_message(call.message.chat.id, call.data.split(":", 2)[2])
            bot.delete_message(call.message.chat.id, call.message.message_id)

            # Логирование.
            logging("dhadhfabot", result)

            bot.send_message(call.message.chat.id, result)
            output_button_service_stat(call.message)

        # Обработка запроса по запуску службы.
        elif call.data.split(":", 2)[0] == "Start_service":
            # Логирование.
            logging(call.message.from_user.username, call.message.text)

            result = on_off_services("on", call.data.split(":", 2)[1])

            # Удаляем 2 пердыдущих сообщения.
            bot.delete_message(call.message.chat.id, call.data.split(":", 2)[2])
            bot.delete_message(call.message.chat.id, call.message.message_id)

            # Логирование.
            logging("dhadhfabot", result)

            bot.send_message(call.message.chat.id, result)
            # Пауза, чтобы служба успела запуститься.
            time.sleep(1)
            output_button_service_stat(call.message)

        # Обработка запроса вернуться назад.
        elif call.data == "Back":
            bot.delete_message(call.message.chat.id, call.message.message_id)

        # Обработка запроса перезапуска бота.
        elif call.data == "Restart":
            # Логирование.
            logging(call.message.from_user.username, call.message.text)

            global status
            # Меняем значение глобальной переменной на "Restart".
            status = call.data

            # Увираем кнопки с клавиатуры.
            no_buttons = telebot.types.ReplyKeyboardRemove()

            # Логирование.
            logging("dhadhfabot", "Бот перезапускается ...")

            # Отправляем сообщение.
            bot.send_message(call.message.chat.id, "Бот перезапускается ...", reply_markup=no_buttons)
            # Завершаем процесс опроса Telegram серверов на предмет новых сообщений.
            bot.stop_polling()


# Функция, обслуживающая отправленные сообщения.
@bot.message_handler(content_types=["text"])
def buttons_events(message):
    # Записываем id сообщения.
    writing_message_id(message)
    # Логирование.
    logging(message.from_user.username, message.text)

    # Обработка запроса "Мониторинг".
    if message.text == "Мониторинг":
        output_button_service_stat(message)

    # Обработка запроса "Очистить чат".
    elif message.text == "Очистить чат":
        delete_all_messages(message.chat.id)

    # Обработка запроса "Запустить службы".
    elif message.text == "Запустить службы":
        result = on_off_services("on")

        # Логирование.
        logging("dhadhfabot", result.replace("\n", " "))

        bot.send_message(message.chat.id, result)

    # Обработка запроса "Остановить службы".
    elif message.text == "Остановить службы":
        result = on_off_services("off")

        # Логирование.
        logging("dhadhfabot", result.replace("\n", " "))

        bot.send_message(message.chat.id, result)

    # Обработка запроса "Перезапустить бота".
    elif message.text == "Перезапустить бота":
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton("Перезапустить", callback_data="Restart"),
            types.InlineKeyboardButton("Назад", callback_data="Back")
        )

        # Логирование.
        logging("dhadhfabot", "Перезапустить бота?")

        bot.send_message(message.chat.id, "Перезапустить бота?", reply_markup=markup)


# Процедура запуска бота.
def start_bot():
    # Запускаем процесс опроса Telegram серверов на предмет новых сообщений.
    bot.polling(none_stop=True)


if __name__ == "__main__":
    start_bot()

# Переменная. Необходима для перезапуска бота.
status = ""
