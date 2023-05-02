import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from google_module.google_module import check_1_url
import time, json
from threading import Thread
from datetime import datetime, timedelta, time
from aiogram.exceptions import AiogramError, TelegramForbiddenError

# Чтение конфига
with open("config.json", "r") as read_file:
    config = json.load(read_file)

# Включаем логирование, чтобы не пропустить важные сообщения
logging.basicConfig(level=logging.INFO)
# root_logger= logging.getLogger()
# root_logger.setLevel(logging.WARNING) # or whatever
# handler = logging.FileHandler('app.log', 'a', 'utf-8') # or whatever
# handler.setFormatter(logging.Formatter('%(name)s %(message)s - %(asctime)s')) # or whatever
# root_logger.addHandler(handler)

# logging.basicConfig(level=logging.WARNING, filename='app.log', filemode='a', format='%(name)s - %(levelname)s - %(message)s {'+ str(time.time()) +'}', encoding="utf-8")

# Объект бота
bot = Bot(token=config["TG_TOKEN"])
# Пришлось создать отдельный объект бота для второго потока
bt = Bot(token=config["TG_TOKEN"])
# Диспетчер
dp = Dispatcher()


# Хэндлер на команду /start
@dp.message(commands=["start"])
async def cmd_start(message: types.Message):
    # print(message)
    return await message.answer(f"Привет! Я всё ещё работую.\nПроверка таблиц: {th.is_alive()}")


# Запуск процесса поллинга новых апдейтов
async def main():
    while True:
        try:
            await dp.start_polling(bot)
        except:
            await asyncio.sleep(5)


async def sending_messages(id:int,text:str):
    """
    Функция для отправки сообщений. На сервере заказчика интернет не очень, так что для безопасности
    """
    while True:
        try:
            await bt.send_message(id, text, parse_mode="HTML")
            break
        except TelegramForbiddenError as e:
            logging.warning(e)
            break
        except  AiogramError as e:
            logging.warning(e)
            await asyncio.sleep(20)


# Просмотр изменений в таблицах
async def get_updates():
    '''
    Получаем таблицу, проходимся по контракткам, смотрим те, что подойдут под условие
    '''  
    while True:
        try:
            if config["URL_FOR_TABLE_1"] == "" or config["CHAT_FOR_URL_1"] == "":
                raise Exception("Отсутствует первая ссылка")
            
            ### Смотрим первую таблицу
            resp = check_1_url(config["URL_FOR_TABLE_1"])
            
            # Если появились новые строки для извещения
            if resp["texts_to_send"] != []:            
                # Отсылаем пользователю все тексты
                tasks = [asyncio.ensure_future(sending_messages(config["CHAT_FOR_URL_1"], i)) for i in resp["texts_to_send"]]
                logging.warning(f"Sending messages. Len = {len(tasks)}")
                if tasks != []:
                    await asyncio.wait(tasks)
        
        except BaseException as e:
            logging.warning(e)

        # Засыпаем до 10 утра следующего дня
        time_to_sleep = (datetime.combine((datetime.today() + timedelta(days=1)).date(), time(10)) - datetime.today()).seconds
        print(time_to_sleep)
        await asyncio.sleep(time_to_sleep)


def sec_thread_start():
    asyncio.run(get_updates())


if __name__ == "__main__":
    # Запуск запросов в таблицу
    th = Thread(target=sec_thread_start, daemon=True)#, args=(i, ))
    th.start()
    # Запуск тг бота
    asyncio.run(main())