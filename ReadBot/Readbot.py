import sqlite3
from telebot import TeleBot
import re
import os
import gc

import torch
import numpy as np
import pandas as pd
from diffusers import DiffusionPipeline
from peft import PeftModel, PeftConfig
from transformers import AutoModelForCausalLM, AutoTokenizer, GenerationConfig

device = "cuda" if torch.cuda.is_available() else "cpu"

# Инициализация бота
API_TOKEN = '7941892229:AAF5kEUQSRA9beUfn6PMn4-EhJRffx3VYoc'  # Замените на ваш токен API
bot = TeleBot(API_TOKEN)


MODEL_NAME = "IlyaGusev/saiga_mistral_7b"
DEFAULT_MESSAGE_TEMPLATE = "<s>{role}\n{content}</s>"
DEFAULT_SYSTEM_PROMPT = "Ты генерируешь по набору диалогов связный промпт для последующей генерации картинок"

class Conversation:
    def __init__(
        self, messages,
        message_template=DEFAULT_MESSAGE_TEMPLATE,
    ):
        self.message_template = message_template
        self.messages = messages

    def add_user_message(self, message):
        self.messages.append({
            "role": "user",
            "content": message
        })

    def get_prompt(self, tokenizer):
        final_text = ""
        for message in self.messages:
            message_text = self.message_template.format(**message)
            final_text += message_text
        return final_text.strip()


def generate(model, tokenizer, prompt, generation_config):
    data = tokenizer(prompt, return_tensors="pt", add_special_tokens=False)
    data = {k: v.to(model.device) for k, v in data.items()}
    output_ids = model.generate(
        **data,
        generation_config=generation_config
    )[0]
    output_ids = output_ids[len(data["input_ids"][0]):]
    output = tokenizer.decode(output_ids, skip_special_tokens=True)
    return output.strip()

# Функция для очистки сообщения
def clean_message(message):
    # Удаляем ссылки
    message = re.sub(r'http[s]?://\S+', '', message)

    # Удаляем смайлы (пример для некоторых смайлов)
    message = re.sub(r'[\U0001F600-\U0001F64F'
                     r'\U0001F300-\U0001F5FF'
                     r'\U0001F680-\U0001F6FF'
                     r'\U0001F700-\U0001F77F'
                     r'\U0001F780-\U0001F7FF'
                     r'\U0001F800-\U0001F8FF'
                     r'\U0001F900-\U0001F9FF'
                     r'\U0001FA00-\U0001FAFF'
                     r'\U00002702-\U000027B0'
                     r'\U000024C2-\U0001F251]+', '', message)  # Удаляем все эмодзи

    # Удаляем команды для бота (предполагаем, что они начинаются с '/')
    message = re.sub(r'/\S+', '', message)

    # Возврат очищенного сообщения
    return message.strip()

# Функция для создания базы данных и таблицы, если еще не созданы
def create_database():
    conn = sqlite3.connect('chat_messages.db')
    c = conn.cursor()
    c.execute('''
    CREATE TABLE IF NOT EXISTS chat_history (
        chat_id INTEGER PRIMARY KEY,
        chat_title TEXT,
        last_words TEXT,
        last_user_id INTEGER
    )
    ''')
    conn.commit()
    conn.close()

# Функция для обновления последних сообщений в базе данных
def update_last_words(chat_id, chat_title, new_message, user_id):
    conn = sqlite3.connect('chat_messages.db')
    c = conn.cursor()

    # Очищаем новое сообщение
    cleaned_message = clean_message(new_message)

    # Если очищенное сообщение пустое, ничего не делаем
    if not cleaned_message:
        return

    # Получаем текущее значение last_words и last_user_id
    c.execute('SELECT last_words, last_user_id FROM chat_history WHERE chat_id = ?', (chat_id,))
    row = c.fetchone()

    # Извлекаем текущее значение и id последнего пользователя или начинаем с пустых значений
    if row and row[0]:
        last_words = row[0].strip().split('\n')  # Разделяем сообщения по переносам строк
        last_user_id = row[1]  # Сохраняем id последнего пользователя
    else:
        last_words = []
        last_user_id = None

    # Добавляем новое сообщение
    if last_user_id is not None and last_user_id != user_id:
        last_words.append("")  # Добавляем перенос строки для сообщения от другого пользователя

    # Определяем, как добавлять новое сообщение
    if last_user_id == user_id:
        last_words[-1] += f" {cleaned_message}"  # Добавляем сообщение к последнему, если от того же пользователя
    else:
        new_entry = f"- {cleaned_message}"  # Новый элемент с дефисом
        last_words.append(new_entry)  # Добавляем новое сообщение

    # Обрезаем до последних 200 строк (сообщений)
    if len(last_words) > 200:
        last_words = last_words[-200:]

    # Превращаем список сообщений обратно в строку с переносами между ними
    updated_last_words = '\n'.join(last_words)

    # Вставляем или обновляем запись в базе данных
    c.execute('''
    INSERT INTO chat_history (chat_id, chat_title, last_words, last_user_id) 
    VALUES (?, ?, ?, ?) 
    ON CONFLICT(chat_id) DO UPDATE SET 
        chat_title = excluded.chat_title, 
        last_words = excluded.last_words,
        last_user_id = excluded.last_user_id
    ''', (chat_id, chat_title, updated_last_words, user_id))

    conn.commit()
    conn.close()

# инициализация моделей
def model_init():
    df = pd.read_csv('ReadBot\dataset.csv')
    messages = [{"role": "system", "content": DEFAULT_SYSTEM_PROMPT}]
    for i, row in df[:30].iterrows():
        messages.append({"role": "user", "content": row['last_words']})
        messages.append({"role": "bot", "content": row['caption']})

    config = PeftConfig.from_pretrained(MODEL_NAME)
    model = AutoModelForCausalLM.from_pretrained(
        config.base_model_name_or_path,
        torch_dtype=torch.float16,
        device_map="auto"
    )
    model = PeftModel.from_pretrained(
        model,
        MODEL_NAME,
        torch_dtype=torch.float16
    )
    model.eval()

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, use_fast=False)
    generation_config = GenerationConfig.from_pretrained(MODEL_NAME)
    return tokenizer, model, generation_config, messages 

# Создаем базу данных при запуске скрипта
create_database()
tokenizer, model, generation_config, messages  = model_init()

def make_pred(inp, tokenizer, model, generation_config, messages):
    conversation = Conversation(messages)
    conversation.add_user_message(inp)
    prompt = conversation.get_prompt(tokenizer)

    output = generate(model, tokenizer, prompt, generation_config)
    return output


# Обработчик команды для получения последних 200 слов
@bot.message_handler(commands=['get_last_words'])
def get_last_words(message):
    chat_id = message.chat.id
    conn = sqlite3.connect('chat_messages.db')
    c = conn.cursor()

    c.execute('SELECT last_words FROM chat_history WHERE chat_id = ?', (chat_id,))
    row = c.fetchone()

    if row and row[0]:
        context = row[0]
        res = make_pred(context, tokenizer, model, generation_config, messages)

        bot.reply_to(message, f'Ваш готовый промпт для генерации  картинки:\n{res}')
    else:
        bot.reply_to(message, "Нет данных для этого чата.")

    conn.close()

# Обработчик сообщений
@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    chat_id = message.chat.id
    chat_title = message.chat.title if message.chat.title else "Неизвестный чат"
    message_text = message.text
    user_id = message.from_user.id  # Получаем уникальный id пользователя

    # Обновляем последние слова в БД
    update_last_words(chat_id, chat_title, message_text, user_id)

# Запуск бота
bot.polling(none_stop=True)
