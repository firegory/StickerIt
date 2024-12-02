import sqlite3
from telebot import TeleBot
import re

# Инициализация бота
API_TOKEN = '7941892229:AAF5kEUQSRA9beUfn6PMn4-EhJRffx3VYoc'  # Замените на ваш токен API
bot = TeleBot(API_TOKEN)

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

# Создаем базу данных при запуске скрипта
create_database()

# Обработчик команды для получения последних 200 слов
@bot.message_handler(commands=['get_last_words'])
def get_last_words(message):
    chat_id = message.chat.id
    conn = sqlite3.connect('chat_messages.db')
    c = conn.cursor()

    c.execute('SELECT last_words FROM chat_history WHERE chat_id = ?', (chat_id,))
    row = c.fetchone()

    if row and row[0]:
        bot.reply_to(message, f'Последние 200 слов чата:\n{row[0]}')
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
