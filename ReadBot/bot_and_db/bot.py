from aiogram import Bot,Dispatcher
from asyncio import run

from dotenv import load_dotenv
from os import getenv
import logging

from db_manager import init_db
from handlers import router

load_dotenv()

async def main():
    bot = Bot(token=getenv('API_TOKEN'))
    dp = Dispatcher()
    dp.include_router(router)
    await init_db()  # Инициализация базы данных
    await bot.delete_webhook(drop_pending_updates=True) #удаляем обновления, которые пришли когда бот был выключен, чтобы их не обрабатывать
    await dp.start_polling(bot)  # Запуск бота

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    try:
        run(main())
    except KeyboardInterrupt:
        print('Exit')

