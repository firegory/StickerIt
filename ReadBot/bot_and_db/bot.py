from aiogram import Bot,Dispatcher,types
from asyncio import run

from dotenv import load_dotenv
from os import getenv

#import logging

from db_manager import init_db
from handlers import router,Commands

# Загружаем переменные окружения из файла .env
load_dotenv()

async def main():
    # создаем экземпляры бота и диспетчера
    bot = Bot(token=getenv('API_TOKEN'))
    dp = Dispatcher()
    # подключаем роутер с обработчиками к диспетчеру
    dp.include_router(router)
    await init_db()  # Инициализация базы данных
    # установка команд для частных чатов
    await  bot.set_my_commands(commands=Commands, scope= types.BotCommandScopeAllPrivateChats())
    await bot.delete_webhook(drop_pending_updates=True) # удаляем обновления, которые пришли когда бот был выключен, чтобы их не обрабатывать
    await dp.start_polling(bot,allowed_updates=dp.resolve_used_update_types())  # Запуск бота

if __name__ == '__main__':
    #logging.basicConfig(level=logging.INFO)
    try:
        run(main())
    except KeyboardInterrupt:
        print('Exit')

