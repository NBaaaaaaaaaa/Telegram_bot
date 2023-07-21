import psutil
import win32com
import wmi
import pythoncom
import traceback


# Функция возваращает список имен служб записанных в файле.
def get_list_services():
    try:
        with open("list_services.txt", "r") as file:
            list_services = list()
            for service_name in file.readlines():
                list_services.append(service_name.replace("\n", ""))

            return {"status": True, "result": list_services}

    except Exception as e:
        return {"status": False, "result": traceback.format_exc()}


# Процедура перезаписи файла со службами.
def rewrite_services(list_services):
    with open("list_services.txt", "w") as file:
        for service_name in list_services:
            file.write("{n}\n".format(n=service_name))


# Процедура добавления/удаления имени службы в/из файл/а.
def add_delete_service(mod, service_name):
    # Перобразуем имя службы. Удаляем лишние пробелы справа и слева.
    service_name = " ".join([_ for _ in service_name.split(" ") if len(_) > 0])

    # Получаем список всех записанных служб.
    result = get_list_services()

    if result["status"]:
        try:
            list_sevices = result["result"]
            # Добавляем имя службы.
            if mod == "add" and service_name not in list_sevices:
                list_sevices.append(service_name)
            # Удаляем имя службы.
            elif mod == "delete" and service_name in list_sevices:
                list_sevices.remove(service_name)

            # Сохраняем изменения.
            rewrite_services(list_sevices)

            return {"status": True}

        except Exception as e:
            return {"status": False, "result": traceback.format_exc()}

    else:
        return {"status": False, "result": result["result"]}


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
            return None

        return memory_usage

    return None


# Функция возвращает нагрузку службы на ЦП.
def get_cpu_load(pid):
    if pid:
        try:
            process = psutil.Process(pid)
            cpu_percent = process.cpu_percent(interval=1.0)
            num_cores = psutil.cpu_count()
            total_cpu_load = round(float(cpu_percent) / num_cores, 2)

            return total_cpu_load

        except Exception as e:
            print("Ошибка при получении информации о нагрузки на ЦП:", str(e))
            return None

    else:
        return None


# Функция возвращает словарь {"имя службы": {                          данных служб.
#                               "uss": "физическая память",
#                               "cpu": ""
#                               "status": "статус службы", ...}
def get_data_services():
    pythoncom.CoInitialize()
    c = wmi.WMI()

    # Создание пустого словаря.
    dict_data_services = dict()

    list_services = list()

    result = get_list_services()

    if result["status"]:
        for service_name in result["result"]:
            try:
                list_services.append(c.Win32_Service(Name=service_name)[0])
            except Exception as e:
                print(e)

        # Перебираем все службы.
        for service in list_services:
            # Добавляем в словарь данные процесса.
            dict_data_services[service.Name] = {
                "uss": str(get_process_memory_usage(service.PathName.split("\\")[-1])) + " Мб",
                "cpu": str(get_cpu_load(service.ProcessId)) + "%",
                "status": service.State
            }

        # Возвращаем словарь данных служб.
        return {"status": True, "result": dict_data_services}

    else:
        return {"status": False, "result": result["result"]}


# Функция запуска и остановки служб.
def on_off_services(mod, service_name=None):
    pythoncom.CoInitialize()
    c = wmi.WMI()

    dict_phrases = {"off":
                        {"status": ["Paused", "Running"],
                         "error_text": "Служба {name} не остановлена. Ошибка: {error}.\n",
                         "success_text": "Служба {name} успешно остановлена.\n",
                         "text": "Службы уже остановлены."},
                    "on":
                        {"status": ["Stopped"],
                         "error_text": "Служба {name} не запущена. Ошибка: {error}.\n",
                         "success_text": "Служба {name} успешно запущена.\n",
                         "text": "Службы уже запущены."}
                    }

    if service_name:
        result = {"status": True, "result": [service_name]}
    else:
        # Получение списка необходимых имен сервисов.
        result = get_list_services()

    if result["status"]:
        list_services = result["result"]
        # Формируем строку для ответа.
        text = ""
        for service_name in list_services:
            if c.Win32_Service(Name=service_name)[0].State in dict_phrases[mod]["status"]:
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

    else:
        return result["result"]

