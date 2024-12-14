from aiogram import Router,types
from aiogram.filters import CommandStart,Command

from db import update_messages,get_chat_messages_from_db
from regex_patterns import preprocess_text

router=Router()

# обработчик команды /start
@router.message(CommandStart())
async def start_command(message: types.Message) -> None:
    await message.answer("Привет! Я бот для хранения сообщений чатов.")

# обработчик команды /get_messages, возвращает пользователю сохраняемую в бд историю чата
@router.message(Command("get_messages"))
async  def get_messages(message:types.Message) -> None:
    chat_id = message.chat.id
    messages=await get_chat_messages_from_db(chat_id)
    if messages:
        await message.answer(messages)
    else:
        await message.answer('В данном чате сообщений не найдено')

# обработчик всех входящих сообщений, сохраняет их в базу данных
@router.message()
async def process_messages(message: types.Message) -> None:
    chat_id:int = message.chat.id
    chat_title:str = message.chat.title or "Неизвестный чат"  # Используем название чата, если доступно
    user_id:int = message.from_user.id  # Получаем ID пользователя
    new_message:str = preprocess_text(message.text)
    # Обновляем сообщения в базе данных
    if message.text:
        await update_messages(chat_id, chat_title, new_message,user_id)
