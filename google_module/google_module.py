# Подключаем библиотеки
import httplib2 
import apiclient.discovery
from oauth2client.service_account import ServiceAccountCredentials	
import google_module.google_config as conf
from datetime import datetime, date

CREDENTIALS_FILE = 'google_module/token.json'  # Имя файла с закрытым ключом, вы должны подставить свое

# Читаем ключи из файла
credentials = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])

# Запрос к таблице
def get(spreadsheetId:str, range_g):
    httpAuth = credentials.authorize(httplib2.Http()) # Авторизуемся в системе
    service = apiclient.discovery.build('sheets', 'v4', http = httpAuth) # Выбираем работу с таблицами и 4 версию API 

    resp = service.spreadsheets().values().get(spreadsheetId=spreadsheetId, range=range_g).execute()
    return resp


def check_1_url(url:str):
    """
    Получаем из таблицы данные, ищем те договоры, которые истекают сегодня/через неделю/через 2 недели
    """
    answer = {
        "texts_to_send":[]
    }

    try:
        resp = get(url, f"'ведение машин по граниту'!A1:V100000")
    except BaseException as e:
        print(e)
        return answer

    if "values" not in resp:
        return answer

    if resp["values"] != []:
        for i in resp["values"]:
            # Добавим стоблцов, чтобы их можно было проверить дальше если что
            if len(i) < 23:
                i += ["" for j in range(23-len(i))]

            # Проверка обязательных полей
            if i[0] == "" or i[21] == "" or i[17].lower() not in conf.url_1_R:
                continue

            # Пытаемся дату спарсить
            date = ""
            try:
                date = datetime.strptime(i[21], "%d.%m.%Y").date()
            except:
                continue

            # Номер договора
            text = i[0]
            text = text.replace("&","&amp;")
            text = text.replace("<","&lt;")
            text = text.replace(">","&gt;")

            # Информация о клиенте
            client = i[18]
            client = client.replace("&","&amp;")
            client = client.replace("<","&lt;")
            client = client.replace(">","&gt;")
            
            if (date - date.today()).days == 14:
                answer["texts_to_send"].append(f"Просьба – обновите договор.\n\n<b>Договор:</b> <code>{text}</code>\n<b>Клиент:</b> <code>{client}</code>\n<b>Осталось</b>: <u>2 недели</u>.\n<b>Дата окончания:</b> {date}\n==========================")
            elif (date - date.today()).days == 7:
                answer["texts_to_send"].append(f"Срочно обновите договор!\n\n<b>Договор:</b> <code>{text}</code>\n<b>Клиент:</b> <code>{client}</code>\n<b>Осталась</b>: <u>1 неделя</u>.\n<b>Дата окончания:</b> {date}\n==========================")
            elif (date.today() -  date).days == 0:
                answer["texts_to_send"].append(f"<b>!Немедленно обновите договор!</b>\n\n<b>Договор:</b> <code>{text}</code>\n<b>Клиент:</b> <code>{client}</code>\n<b>Осталось</b>: <u>несколько часов</u>.\n<b>Дата окончания:</b> {date}\n==========================")


    return answer
