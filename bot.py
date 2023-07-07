import telebot
from telebot import types
from func_about_services import *
import time


bot = telebot.TeleBot(open("TOKEN.txt", "r").read())


# Функция добавления id чата в файл.
def add_chat_id_db(chat_id):
    chat_id = str(chat_id)

    with open("all_chat_id.txt", "r+") as file:
        if file.read().find(chat_id, 1) == -1:
            file.write(chat_id + ";")


# Функция отправки стартового сообщения.
def send_start_message(chat_id):
    # Создание поля для вставки кнопок.
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)

    # Добавление стартовых кнопок.
    markup.add(
        types.KeyboardButton("Данные служб"),
        types.KeyboardButton("Запустить службы"),
        types.KeyboardButton("Остановить службы"),
        types.KeyboardButton("Список служб"),
        types.KeyboardButton("Перезапустить бота")
    )

    # Вывод сообщения и кнопок.
    bot.send_message(chat_id, "Жми на кнопки", reply_markup=markup)


# Функция начала работы с ботом.
@bot.message_handler(commands=['start'])
def start(message):
    add_chat_id_db(message.chat.id)
    send_start_message(message.chat.id)


# Функция отправки сообщений всем пользователям о перезапуске бота.
def send_message_after_restart():
    with open("all_chat_id.txt", "r+") as file:
        list_chat_id = list(map(int, file.read().split(";")[:-1]))
        for chat_id in list_chat_id:
            bot.send_message(chat_id, "Бот запущен")
            send_start_message(chat_id)


# Функция возвращает список ["имя службы: статус службы", ...].
def get_list_services():
    services_status = get_services_status()
    return list(": ".join([service, services_status[service]]) for service in sorted(services_status.keys()))


# Функция получения статуса работы бота. Необходимо для перезапуска бота.
def get_status():
    global status
    return status


# Функция вывода запущенных служб в формате кнопок.
def output_button_service_stat(message):
    list_services = get_list_services()

    markup = types.InlineKeyboardMarkup(row_width=1)
    # Заполяем поле кнопками.
    for service in list_services:
        markup.add(types.InlineKeyboardButton(service, callback_data=service))

    bot.send_message(message.chat.id, "Список служб:", reply_markup=markup)


# Функция обработки нажажатия кнопок со встроенной клавиатуры.
@bot.callback_query_handler(func=lambda message: True)
def callback_query(call):
    if call.message:
        # Получаем список служб и их статуса.
        list_call_data = get_list_services()

        if call.data in list_call_data:
            markup = types.InlineKeyboardMarkup(row_width=1)

            service_name, service_status = call.data.replace(" ", "").split(":")

            # Формируем строку для ответа.
            text = ""
            # Остановка службы.
            if service_status != "stopped":
                text = "Остановить сервис {name}?".format(name=service_name)
                # Добавление кнопки для остановки службы.
                markup.add(types.InlineKeyboardButton("Остановить",
                                                      callback_data="Stop_service:{name}".format(name=service_name)))

            # Запуск службы.
            else:
                text = "Запустить сервис {name}?".format(name=service_name)
                # Добавление кнопки для запуска службы.
                markup.add(types.InlineKeyboardButton("Запустить",
                                                      callback_data="Start_service:{name}".format(name=service_name)))

            # Добавление кнопки для возврата назад.
            markup.add(types.InlineKeyboardButton("Назад", callback_data="Back"))

            # Вывод сообщения с кнопками.
            bot.send_message(call.message.chat.id, text, reply_markup=markup)

        # Обработка запроса по остановке службы.
        elif call.data.split(":", 1)[0] == "Stop_service":
            stop_service(call.data.split(":", 1)[1])
            output_button_service_stat(call.message)

        # Обработка запроса по запуску службы.
        elif call.data.split(":", 1)[0] == "Start_service":
            start_service(call.data.split(":", 1)[1])
            # Пауза, чтобы служба успела запуститься.
            time.sleep(1)
            output_button_service_stat(call.message)

        # Обработка запроса вернуться назад.
        elif call.data == "Back":
            bot.delete_message(call.message.chat.id, call.message.message_id)

        # Обработка запроса перезапуска бота.
        elif call.data == "Restart":
            global status
            # Меняем значение глобальной переменной на "Restart".
            status = call.data

            # Увираем кнопки с клавиатуры.
            no_buttons = telebot.types.ReplyKeyboardRemove()
            # Отправляем сообщение.
            bot.send_message(call.message.chat.id, "Бот перезапускается ...", reply_markup=no_buttons)
            # Завершаем процесс опроса Telegram серверов на предмет новых сообщений.
            bot.stop_polling()


# Функция, обслуживающая отправленные сообщения.
@bot.message_handler(content_types=["text"])
def buttons_events(message):
    # Обработка запроса "Данные служб".
    if message.text == "Данные служб":
        # Получаем словарь данных служб.
        dict_services = get_data_services()

        # Формируем строку для ответа.
        all_data = ""
        if len(dict_services) != 0:
            for service in sorted(dict_services.keys()):
                string_to_send = "; ".join([service, dict_services[service]["uss"]]) #, dict_services[service]["cpu"]
                all_data += string_to_send + "\n"
        else:
            all_data = "Сервисы не запущенны"

        bot.send_message(message.chat.id, all_data)

    # Обработка запроса "Запустить службы".
    elif message.text == "Запустить службы":
        on_off_services("on")
        bot.send_message(message.chat.id, "on")

    # Обработка запроса "Остановить службы".
    elif message.text == "Остановить службы":
        on_off_services("off")
        bot.send_message(message.chat.id, "off")

    # Обработка запроса "Список служб".
    elif message.text == "Список служб":
        output_button_service_stat(message)

    # Обработка запроса "Перезапустить бота".
    elif message.text == "Перезапустить бота":
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton("Перезапустить", callback_data="Restart"),
            types.InlineKeyboardButton("Назад", callback_data="Back")
        )
        bot.send_message(message.chat.id, "Перезапустить бота?", reply_markup=markup)


# Процедура запуска бота.
def start_bot():
    # Запускаем процесс опроса Telegram серверов на предмет новых сообщений.
    bot.polling(none_stop=True)


if __name__ == "__main__":
    start_bot()

# Переменная. Необходима для перезапуска бота.
status = ""
