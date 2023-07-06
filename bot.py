import telebot
from telebot import types
from func_about_services import *
import time


bot = telebot.TeleBot(open("TOKEN.txt", "r").read())


# Функция начала работы с ботом.
@bot.message_handler(commands=['start', 'help'])
def start(message):
    # Создание поля для вставки кнопок.
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    # Создание кнопок.
    data_services = types.KeyboardButton("Данные служб")
    on_services = types.KeyboardButton("Запустить службы")
    off_services = types.KeyboardButton("Остановить службы")
    list_serices = types.KeyboardButton("Список служб")

    # Добавление кнопок.
    markup.add(data_services)
    markup.add(on_services)
    markup.add(off_services)
    markup.add(list_serices)

    # Вывод сообщения и кнопок.
    bot.send_message(message.chat.id, "Жми на кнопки", reply_markup=markup)


# Функция возвращает список ["имя службы: статус службы", ...].
def get_list_services():
    services_status = get_services_status()
    return list(": ".join([service, services_status[service]]) for service in services_status)


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
        # Получаем список сервисов и их статуса.
        list_call_data = get_list_services()

        if call.data in list_call_data:
            markup = types.InlineKeyboardMarkup(row_width=1)

            service_name, service_status = call.data.replace(" ", "").split(":")

            text = ""
            if service_status != "stopped":
                text = "Остановить сервис {name}?".format(name=service_name)
                markup.add(types.InlineKeyboardButton("Остановить",
                                                      callback_data="Stop_service:{name}".format(name=service_name)))
            else:
                text = "Запустить сервис {name}?".format(name=service_name)
                markup.add(types.InlineKeyboardButton("Запустить",
                                                      callback_data="Start_service:{name}".format(name=service_name)))

            markup.add(types.InlineKeyboardButton("Назад", callback_data="Back"))

            bot.send_message(call.message.chat.id, text, reply_markup=markup)

        # Обработка запроса по остановке сервиса.
        elif call.data.split(":", 1)[0] == "Stop_service":
            stop_service(call.data.split(":", 1)[1])
            output_button_service_stat(call.message)

        # Обработка запроса по запуску сервиса.
        elif call.data.split(":", 1)[0] == "Start_service":
            start_service(call.data.split(":", 1)[1])
            # Пауза, чтобы служба успела запуститься.
            time.sleep(1)
            output_button_service_stat(call.message)

        # Обработка запроса вернуться назад.
        elif call.data == "Back":
            bot.delete_message(call.message.chat.id, call.message.message_id)


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


# Постоянная работа бота.
bot.polling(none_stop=True)
