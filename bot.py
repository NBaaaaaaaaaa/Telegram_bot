import telebot
from telebot import types
from func_about_services import get_data_services, on_off_services


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

    # Добавление кнопок.
    markup.add(data_services)
    markup.add(on_services)
    markup.add(off_services)

    # Вывод сообщения и кнопок.
    bot.send_message(message.chat.id, "Press the buttons", reply_markup=markup)


# Функция, обслуживающая нажатие кнопок.
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


# Постоянная работа бота.
bot.polling(none_stop=True)
