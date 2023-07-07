import threading
from bot import start_bot, get_status, send_message_after_restart


def worker():
    global status
    # Запускаем бота.
    start_bot()
    # Получаем статус работы бота.
    status = get_status()

    print('Нормальный конец работы')
    # Уведомляем wait что можно больше не блокировать основной поток.
    finished.set()


if __name__ == "__main__":
    status = "Start"

    while True:
        if status == "Start" or status == "Restart":
            finished = threading.Event()

            # Создаем поток. В нем будет запущен бот.
            p = threading.Thread(
                target=worker,
                daemon=False,
                name="worker",
                args=[]
            )
            # Запуск потока.
            p.start()

            # Оповещает всех пользователей, что бот перезапущен.
            if status == "Restart":
                send_message_after_restart()

            # Ожидаем завершения недемонического рабочего потока.
            if finished.wait():
                print('Поток закончен.')
                continue

