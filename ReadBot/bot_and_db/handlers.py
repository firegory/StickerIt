from typing import Optional
from aiogram.types import FSInputFile
from aiogram import Router,types,F
from aiogram.types import BotCommand
from aiogram.filters import CommandStart,Command
import os
# импортируем модели для генерации изображений и текстов
from image_generator import ImageGenerator
from text_model import CaptionGenerator

from db_manager import update_messages,get_chat_messages_from_db
from regex_patterns import preprocess_text

# создаем список команд
Commands=[BotCommand(command='start',description='начинаем, можете сгенерировать стикер'),
          BotCommand(command='get_messages',description='текущий контекст'),
          BotCommand(command='generate_sticker',description='сгенерируем стикер'),
          BotCommand(command='help',description='получить список команд')]
# создаем экземпляр роутера для управления обработчиками сообщений
router:Router=Router()

# инициализируем модели для генерации изображений и текста
image_model, text_model = ImageGenerator(), CaptionGenerator()

# обработчик команды /start
@router.message(CommandStart())
async def start_command(message: types.Message) -> None:
    await message.answer("Привет! Я бот для хранения сообщений чатов и генерации контекстуальных стикеров.\n Ознакомьтесь со списком команд с помощью /help")

@router.message(Command("help"))
async def send_help(message: types.Message):
    help_text = (
        "Доступные команды:\n"
        "/start - Начинаем, можете сгенерировать стикер\n"
        "/get_messages - Текущий контекст\n"
        "/generate_sticker - Сгенерируем стикер\n"
    )
    await message.answer(help_text)

# обработчик команды /get_messages, возвращает пользователю сохраняемую в бд историю чата
@router.message(Command("get_messages"))
async  def get_messages(message:types.Message) -> None:
    chat_id:int = message.chat.id
    messages:Optional[str]=await get_chat_messages_from_db(chat_id) # извлекаем сообщения из БД(если есть)
    if messages:
        await message.answer(messages)
    else:
        await message.answer('В данном чате сообщений не найдено')

# обработчик команды /generate_sticker для генерации стикера
@router.message(Command("generate_sticker"))
async def generate_sticker(message:types.Message):
        chat_id: int = message.chat.id
        context: Optional[str] = await get_chat_messages_from_db(chat_id) # получаем сообщения из бд
        if context:
            generated_caption = text_model.generate(context) # получаем описание сообщений(промпт) для генерации стикера
            save_path = image_model.generate(generated_caption, chat_id)
            # сгенерируем стикер и отправим в нужный чат
            sticker_file = FSInputFile(save_path)

            await message.answer_sticker(sticker_file)

            # удаляем файл после отправки
            if os.path.exists(save_path):
                os.remove(save_path)
        else:
            await message.answer(f'Нет данных для этого!')

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