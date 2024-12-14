from aiogram import Bot,Dispatcher,types
from os import getenv
from dotenv import load_dotenv
from asyncio import run
from aiogram.filters import CommandStart,Command
from db import init_db,update_messages,get_chat_messages_from_db
from utils import preprocess_text
load_dotenv()
bot = Bot(token=getenv('API_TOKEN'))
dp = Dispatcher()

# обработчик команды /start
@dp.message(CommandStart())
async def start_command(message: types.Message):
    await message.answer("Привет! Я бот для хранения сообщений чатов.")

# обработчик команды /get_messages, возвращает пользователю сохраняемую в бд историю чата
@dp.message(Command("get_messages"))
async  def get_messages(message:types.Message):
    chat_id = message.chat.id
    messages=await get_chat_messages_from_db(chat_id)
    if messages:
        await message.answer(messages)
    else:
        await message.answer('В данном чате сообщений не найдено')

# обработчик всех входящих сообщений, сохраняет их в базу данных
@dp.message()
async def process_messages(message: types.Message) -> None:
    chat_id:int = message.chat.id
    chat_title:str = message.chat.title or "Неизвестный чат"  # Используем название чата, если доступно
    user_id:int = message.from_user.id  # Получаем ID пользователя
    new_message:str = preprocess_text(message.text)
    # Обновляем сообщения в базе данных
    if message.text:
        await update_messages(chat_id, chat_title, new_message,user_id)

if __name__ == '__main__':
    async def main():
        await init_db()  # Инициализация базы данных
        await dp.start_polling(bot)  # Запуск бота

    try:
        run(main())
    except KeyboardInterrupt:
        print('Exit')

