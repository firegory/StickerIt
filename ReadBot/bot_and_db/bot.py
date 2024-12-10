from aiogram import Bot,Dispatcher,types
from os import getenv
import re
from aiogram.types import Message
from dotenv import load_dotenv
from asyncio import run
from aiogram.filters import CommandStart,Command
import aiosqlite
from db import init_db,update_messages

load_dotenv()
bot = Bot(token=getenv('TOKEN'))
dp = Dispatcher()

#функция для предобработки полученных сообщений
def preprocess_text(text:str):
    # Удаляем ссылки
    link_pattern:re.Pattern = re.compile(r'https?://\S+|www\.\S+')
    text = link_pattern.sub('', text)

    # Удаляем эмодзи
    emoji_pattern:re.Pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # Смiley
        "\U0001F300-\U0001F5FF"  # Symbols & Shapes
        "\U0001F680-\U0001F6FF"  # Transport & Map Symbols
        "\U0001F700-\U0001F7FF"  # Alchemical Symbols
        "\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
        "\U0001FA00-\U0001FAFF"  # Chess Symbols
        "\u2600-\u26FF"  # Miscellaneous Symbols
        "\u2700-\u27BF"  # Dingbats
        "]+", flags=re.UNICODE)
    text = emoji_pattern.sub('', text)

    # Удаляем лишние пробелы
    text = ' '.join(text.split())

    # Приводим текст к нижнему регистру
    text = text.lower()

    return text.strip()  # Удаляем пробелы по краям текста

@dp.message(CommandStart())
async def start_command(message: types.Message):
    await message.answer("Привет! Я бот для хранения сообщений чатов.")

@dp.message(Command("get_messages"))
async  def get_messages(message:types.Message):
    async with aiosqlite.connect('chat_messages.db') as db:
        # Проверяем, существует ли запись для данного чата
        chat_id=message.chat.id
        async with db.execute("SELECT messages FROM chat_messages WHERE chat_id = ?", (chat_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                # Если запись найдена, выводим сообщения
                messages = row[0]
                await message.answer(messages)
            else:
                # Если записи нет, отправляем соответствующее сообщение
                await message.answer("Нет сообщений для этого чата.")


@dp.message()
async def process_messages(message: types.Message):
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

