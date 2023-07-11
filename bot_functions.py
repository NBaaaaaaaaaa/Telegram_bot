import psutil
import win32com
import wmi
import pythoncom
import traceback


# Функция возваращает список имен служб записанных в файле.
def get_list_services():
    with open("list_of_services.txt", "r") as file:
        list_services = list()
        for service_name in file.readlines():
            list_services.append(service_name.replace("\n", ""))

        return list_services


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
#                               "cpu": "нагрузку на цп (cpu)"},
#                               "status": "статус службы", ...}
def get_data_services():
    # Создание пустого словаря.
    dict_data_services = dict()

    list_services = list(psutil.win_service_get(i) for i in get_list_services())

    # Перебираем все службы.
    for service in list_services:
        # Добавляем в словарь данные процесса.
        dict_data_services[service.name()] = {
            "uss": str(get_process_memory_usage(service.binpath().split("\\")[-1])) + " Мб",
            "cpu": None,
            "status": service.status()
        }

    # Возвращаем словарь данных  служб.
    return dict_data_services


# Функция запуска и остановки служб.
def on_off_services(mod, service_name=None):
    pythoncom.CoInitialize()
    c = wmi.WMI()

    dict_phrases = {"off":
                        {"status": ["paused", "running"],
                         "error_text": "Служба {name} не остановлена. Ошибка: {error}.\n",
                         "success_text": "Служба {name} успешно остановлена.\n",
                         "text": "Службы уже остановлены."},
                    "on":
                        {"status": ["stopped"],
                         "error_text": "Служба {name} не запущена. Ошибка: {error}.\n",
                         "success_text": "Служба {name} успешно запущена.\n",
                         "text": "Службы уже запущены."}
                    }

    if service_name:
        list_services = [service_name]
    else:
        # Получение списка необходимых имен сервисов.
        list_services = get_list_services()

    # Формируем строку для ответа.
    text = ""

    for service_name in list_services:
        if psutil.win_service_get(service_name).status() in dict_phrases[mod]["status"]:
            service = c.Win32_Service(Name=service_name)

            try:
                if mod == "off":
                    service[0].StopService()
                elif mod == "on":
                    service[0].StartService()

            except Exception as e:
                text += dict_phrases[mod]["error_text"].format(name=service_name, error=traceback.format_exc())

            else:
                text += dict_phrases[mod]["success_text"].format(name=service_name)

    if text == "":
        text = dict_phrases[mod]["text"]

    return text

