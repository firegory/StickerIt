import aiosqlite

async def init_db():
    async with aiosqlite.connect('chat_messages.db') as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS chat_messages (
                chat_id INTEGER PRIMARY KEY,
                chat_title TEXT,
                messages TEXT,
                last_user_id INTEGER
            )
        ''')

# Функция для обновления сообщений в базе данных
async def update_messages(chat_id:int, chat_title:str, new_message:str, user_id:int):
    async with aiosqlite.connect('chat_messages.db') as db:
        # Проверяем, существует ли запись для данного чата
        async with db.execute("SELECT messages FROM chat_messages WHERE chat_id = ?", (chat_id,)) as cursor:
            row = await cursor.fetchone()
        async with db.execute("SELECT last_user_id FROM chat_messages WHERE chat_id = ?", (chat_id,)) as cursor:
            last_user_id=await cursor.fetchone()
        if row is None:
            new_message="-"+new_message
            # Если запись не существует, вставляем новую
            await db.execute("INSERT INTO chat_messages (chat_id, chat_title, messages, last_user_id) VALUES (?, ?, ?, ?)",
                             (chat_id, chat_title, new_message,user_id))
        else:
            # Если запись существует, обновляем сообщения
            existing_messages = row[0]  # Получаем существующие сообщения
            existing_messages=existing_messages.replace('\n',' \n')
            messages_list = existing_messages.split(' ') if existing_messages else []
            if last_user_id[0]!=user_id:
                new_message=' \n-'+new_message
            # Добавляем новое сообщение в список
            messages_list.extend(new_message.split(' '))
            # Оставляем только последние 200 слов из сообщений
            if len(messages_list) > 200:
                messages_list = messages_list[-200:]
            existing_messages=' '.join(messages_list).replace(" \n","\n")
            # Обновляем строку с новыми сообщениями и последним ID пользователя
            await db.execute("UPDATE chat_messages SET chat_title = ?, messages = ?, last_user_id = ? WHERE chat_id = ?",
                             (chat_title, existing_messages, user_id, chat_id))
        await db.commit()
    print("База данных обновлена")
#функция для получения сообщений из определнного чата
async def get_chat_messages_from_db(chat_id):
    async with aiosqlite.connect('chat_messages.db') as db:
        # Проверяем, существует ли запись для данного чата
        async with db.execute("SELECT messages FROM chat_messages WHERE chat_id = ?", (chat_id,)) as cursor:
            row = await cursor.fetchone()
            messages = row[0]
    return messages

