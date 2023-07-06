import psutil
import win32com
import wmi
import pythoncom


# Функция возваращает словарь {"имя службы": "испольняющий файл"} записанных в файле.
def get_dict_services():
    with open("list_of_services.txt", "r") as file:
        dict_services = dict()
        for line in file.readlines():
            service_name, exe_name = line.replace("\n", "").split("/", 1)
            dict_services[service_name] = exe_name

        return dict_services


# Функция возвращает кол-во памяти (Мб), которое освободится после остановки службы.
def get_process_memory_usage(process_name):
    pythoncom.CoInitialize()
    wmi = win32com.client.GetObject("winmgmts:")
    process_list = wmi.ExecQuery("SELECT * FROM Win32_Process WHERE Name='{0}'".format(process_name))

    for process in process_list:
        process_id = process.Properties_('ProcessId').Value
        memory_usage = 0

        try:
            memory_stats = wmi.ExecQuery(
                "SELECT * FROM Win32_PerfRawData_PerfProc_Process WHERE IDProcess='{0}'".format(process_id))
            for stat in memory_stats:
                memory_usage = round(int(stat.WorkingSetPrivate) / 1024 / 1024, 2)

                break
        except Exception as e:
            print("Ошибка при получении информации о потреблении памяти:", str(e))

        return memory_usage

    return None


# Функция возвращает словарь {"имя службы": {                          данных служб.
#                               "uss": "физическая память",
#                               "cpu": "нагрузку на цп (cpu)"}, ...}
def get_data_services():
    # Создание пустого словаря.
    dict_data_services = dict()
    # Получение словаря необходимых служб
    dict_services = get_dict_services()

    list_services = list(psutil.win_service_get(i) for i in dict_services)

    # Перебираем все службы.
    for service in list_services:
        # Ищем запущенные процессы.
        process = psutil.Process(pid=service.pid())

        if process.status() == "running":
            # Добавляем в словарь данные запущенного процесса.
            dict_data_services[service.name()] = {
                "uss": str(get_process_memory_usage(dict_services[service.name()])) + " Мб",
                "cpu": None
            }

    # Возвращаем словарь данных  служб.
    return dict_data_services


# Процедура запуска службы.
def start_service(service_name):
    pythoncom.CoInitialize()
    c = wmi.WMI()
    service = c.Win32_Service(Name=service_name)
    if len(service) > 0:
        result = service[0].StartService()
        if result == (0, ):
            print("Служба", service_name, "успешно запущена.")
        else:
            print("Не удалось запустить службу", service_name, ". Код ошибки:", result)
    else:
        print("Служба", service_name, "не найдена.")


# Процедура остановки службы.
def stop_service(service_name):
    pythoncom.CoInitialize()
    c = wmi.WMI()
    service = c.Win32_Service(Name=service_name)
    if len(service) > 0:
        result = service[0].StopService()
        if result == (0, ):
            print("Служба", service_name, "успешно остановлена.")
        else:
            print("Не удалось остановить службу", service_name, ". Код ошибки:", result)
    else:
        print("Служба", service_name, "не найдена.")


# Процедура запуска и остановки служб.
def on_off_services(mod):
    # Получение списка необходимых имен сервисов.
    dict_services = get_dict_services()

    # Остановка запущенных служб.
    if mod == "off":
        for service_name in dict_services:
            if psutil.win_service_get(service_name).status() != "stopped":
                stop_service(service_name)

    # Запуск остановленных служб.
    elif mod == "on":
        for service_name in dict_services:
            if psutil.win_service_get(service_name).status() == "stopped":
                start_service(service_name)


# Функция возвращает словарь {"имя службы": "статус службы", ...}.
def get_services_status():
    # Получение словаря необходимых служб
    dict_services = get_dict_services()

    list_services = list(psutil.win_service_get(i) for i in dict_services)

    # Перебираем все службы.
    for service in list_services:
        dict_services[service.name()] = service.status()

    return dict_services

