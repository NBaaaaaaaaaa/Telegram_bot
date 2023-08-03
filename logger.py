import os
from datetime import datetime


# Процедура логирования.
def logging(username, text):
    log_file = "{file}.{num}.txt"
    # Получение текущей даты.
    current_datetime = datetime.now()
    path = "logs/{y}/{m}/{d}/".format(y=current_datetime.year, m=current_datetime.month, d=current_datetime.day)

    # Создание директорий.
    os.makedirs(path, exist_ok=True)

    # Создание имени логу.
    list_files = os.listdir(path)
    # Если файлов нет в директории.
    if len(list_files) == 0:
        log_file = log_file.format(file=current_datetime.strftime("%d-%m-%Y"), num=0)

    # Если файлы есть в директории.
    else:
        # Получаем последний созданный файл.
        last_file = list_files[-1]

        # Если вес его >= 48 Мб
        if round(int(os.stat(path + last_file).st_size)/1024/1024, 2) >= 48:
            log_file = log_file.format(file=current_datetime.strftime("%d-%m-%Y"), num=int(last_file.split(".")[1]) + 1)

        # Если вес его < 48 Мб
        else:
            log_file = last_file

    # Запись в файл.
    with open(path + log_file, "a", encoding="utf-8") as file:
        file.write("{date} | {name} | {text}\n".format(date=current_datetime.strftime("%Y-%m-%d %H:%M:%S"),
                                                       name=username, text=text))


# Функция возвращает список имен файлов и папок в директории.
def get_directory_data(path=None):
    path_logs = "logs/"

    if path:
        path_logs += "{path}/".format(path=path)

    return os.listdir(path_logs)
