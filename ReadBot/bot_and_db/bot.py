from aiogram import Bot,Dispatcher
from asyncio import run
from dotenv import load_dotenv
from os import getenv

from db_manager import init_db
from handlers import router
load_dotenv()

async def main():
    bot = Bot(token=getenv('API_TOKEN'))
    dp = Dispatcher()
    dp.include_router(router)
    await init_db()  # Инициализация базы данных
    await dp.start_polling(bot)  # Запуск бота

if __name__ == '__main__':
    try:
        run(main())
    except KeyboardInterrupt:
        print('Exit')

