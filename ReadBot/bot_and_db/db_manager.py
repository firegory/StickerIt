import aiosqlite
from typing import Optional
from asyncio import Lock

lock=Lock()

# инициализация базы данных
async def init_db() -> None:
    async with aiosqlite.connect('chat_messages.db') as db:
        cursor:aiosqlite.Cursor = await db.cursor()
        await cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_messages (
                chat_id INTEGER PRIMARY KEY,
                chat_title TEXT,
                messages TEXT,
                last_user_id INTEGER
            )
        ''')
        await db.commit()

# функция для обновления сообщений в базе данных
async def update_messages(chat_id: int, chat_title: str, new_message: str, user_id: int) -> None:
    async with lock:
        async with aiosqlite.connect('chat_messages.db') as db:
            cursor:aiosqlite.Cursor = await db.cursor()
            # проверяем, существует ли запись для данного чата
            await cursor.execute("SELECT messages, last_user_id FROM chat_messages WHERE chat_id = ?", (chat_id,))
            row:Optional[tuple[Optional[str],Optional[int]]]= await cursor.fetchone()
            messages:Optional[str]; last_user_id:Optional[int]
            messages, last_user_id = row if row else (None, None)

            if messages is None:
                new_message:str = "-" + new_message
                # если запись не существует, вставляем новую
                await cursor.execute("INSERT INTO chat_messages (chat_id, chat_title, messages, last_user_id) VALUES (?, ?, ?, ?)",
                                     (chat_id, chat_title, new_message, user_id))
            else:
                # если запись существует, обновляем сообщения
                messages = messages.replace('\n', ' \n')
                messages_list:list = messages.split(' ') if messages else []
                if last_user_id != user_id:
                    new_message = ' \n-' + new_message
                # добавляем новое сообщение в список
                messages_list.extend(new_message.split(' '))
                # оставляем только последние 200 слов из сообщений
                if len(messages_list) > 200:
                    messages_list = messages_list[-200:]
                messages = ' '.join(messages_list).replace(" \n", "\n")
                # обновляем строку с новыми сообщениями и последним ID пользователя
                await cursor.execute("UPDATE chat_messages SET chat_title = ?, messages = ?, last_user_id = ? WHERE chat_id = ?",
                                     (chat_title, messages, user_id, chat_id))
            await db.commit()
        print("База данных обновлена")

# функция для получения сообщений из определённого чата в БД
async def get_chat_messages_from_db(chat_id: int) -> Optional[str]:
    async with aiosqlite.connect('chat_messages.db') as db:
        cursor:aiosqlite.Cursor = await db.cursor()
        # проверяем, существует ли запись для данного чата
        await cursor.execute("SELECT messages FROM chat_messages WHERE chat_id = ?", (chat_id,))
        row:Optional[tuple[Optional[str]]] = await cursor.fetchone()
        messages:Optional[str] = row[0] if row else None
    return messages
