from typing import Optional
from aiogram.types import FSInputFile
from aiogram import Router,types,F
from aiogram.filters import CommandStart,Command

from image_generator import ImageGenerator
from text_model import CaptionGenerator

from db_manager import update_messages,get_chat_messages_from_db
from regex_patterns import preprocess_text

router:Router=Router()

# обработчик команды /start
@router.message(CommandStart())
async def start_command(message: types.Message) -> None:
    image_model, text_model = ImageGenerator(), CaptionGenerator()
    await message.answer("Привет! Я бот для хранения сообщений чатов.")

# обработчик команды /get_messages, возвращает пользователю сохраняемую в бд историю чата
@router.message(Command("get_messages"))
async  def get_messages(message:types.Message) -> None:
    chat_id:int = message.chat.id
    messages:Optional[str]=await get_chat_messages_from_db(chat_id)
    if messages:
        await message.answer(messages)
    else:
        await message.answer('В данном чате сообщений не найдено')

@router.message(Command("generate_image"))
async def generate_image(message:types.Message):
    chat_id: int = message.chat.id
    context: Optional[str] = await get_chat_messages_from_db(chat_id)
    if context:
        generated_caption = text_model.generate(context)
        save_path = image_model.generate(generated_caption, chat_id)
        sticker_file = FSInputFile(save_path)        
        
        await message.answer_sticker(sticker_file)
    else:
        await message.answer(f'Нет данных для этого!')

# @router.message(Command("generate_sticker"))
# async def generate_sticker(message:types.Message):
#     sticker_path = "lol.webp"  # Путь к стикеру

#     # Создаем экземпляр FSInputFile
#     sticker_file = FSInputFile(sticker_path)

#     # Отправка стикера пользователю
#     await message.answer_sticker(sticker_file)

# обработчик всех входящих текстовых сообщений, сохраняет их в базу данных
@router.message(F.text)
async def process_messages(message: types.Message) -> None:
    chat_id:int = message.chat.id
    chat_title:str = message.chat.title or "Неизвестный чат"  # Используем название чата, если доступно
    user_id:int = message.from_user.id  # Получаем ID пользователя
    new_message:str = preprocess_text(message.text)
    # Обновляем сообщения в базе данных
    if new_message:
        await update_messages(chat_id, chat_title, new_message,user_id)