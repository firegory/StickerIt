import asyncio
from dotenv import load_dotenv
from time import sleep
from telethon import TelegramClient
from telethon.tl.types import *
from telethon.tl.functions.messages import GetHistoryRequest
import re
from fnmatch import fnmatch
import csv
import os
load_dotenv()
api_id = int(os.getenv('api_id'))
api_hash = os.getenv('api_hash')
phone = os.getenv('phone')  # Укажите номер телефона с '+', например, +71234567890
# Создаем клиент с указанным именем сессии
client = TelegramClient('session_name', api_id, api_hash,device_model='blabla',system_version="10.0 (Windows 11)")
mymessages=[]
stickers_folder = 'stickers'
os.makedirs(stickers_folder, exist_ok=True)

#функция для предобработки полученных сообщений
def preprocess_text(text):
    # Удаляем ссылки
    link_pattern = re.compile(r'http[s]?://\S+|www\.\S+')
    text = link_pattern.sub('', text)

    # Удаляем эмодзи
    emoji_pattern = re.compile(
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
#показывает доступные чаты и их id
async def get_dialog():
    async with client:
        dialogs=await client.get_dialogs()
        print('доступные чаты')
        for dialog in dialogs:
            print((dialog.title,dialog.entity.id))


#по id чата и макс кол-ву сообщ(должно быть кратно 100) получит эти сообщения из чата
#расчитано на многократное количество запусков, каждый раз в отдельном файле
#сохраняется информация про последнее полученное сообщение, так что можно продолжить
#парсить с того же места, где закончили в прошлый раз(только для одного и того же чата работает)
#чтобы начать парсить другие чаты удалите (csv,stickers,txt файлики)
async def parser(chat_id,max_messages:int):
    file_path = "lastmessage_id.txt"

    if os.path.exists(file_path):  # Проверяем существование файла
        with open(file_path, 'r') as file:  # Открываем файл для чтения
            lines = file.readlines()  # Читаем все строки
            lines=list(map(int,lines))
            last_offset_id,counter,last_user_id=lines

    else:
        last_offset_id=0
        counter = 1
        last_user_id=0

    async with client:
        chat=await client.get_entity(chat_id)
        for i in range(max_messages//100):
            mymessagespart=[]
            history = await client(GetHistoryRequest(
                peer=chat,
                limit=100,
                offset_id=last_offset_id,
                offset_date=None,
                add_offset=0,
                max_id=0,
                min_id=0,
                hash=0
            ))
            for message in history.messages[::-1]:
                if message.message:
                    msg=message.message
                    if message.from_id:  # Если от пользователя
                        now_user = message.from_id.user_id
                    elif message.peer_id and isinstance(message.peer_id,
                                                        PeerUser):  # Если от пользователя (в контексте чата)
                        now_user = message.peer_id.user_id
                    else:
                        now_user = 0  # В случае, если не удалось определить
                    if len(preprocess_text(msg))==0:
                        continue
                    if now_user is not None and now_user != last_user_id and len(mymessagespart) != 0:
                        last_user_id=now_user
                        msg='\n-'+preprocess_text(msg)
                        #print(msg,message.id)
                    elif len(mymessagespart)==0:
                        msg='-'+preprocess_text(msg)

                    else:
                        msg = " "+preprocess_text(msg)
                    mymessagespart.append(msg)
                elif message.sticker:
                    sticker_filename = f'sticker_{counter}.webp'
                    counter += 1
                    mymessagespart.append(sticker_filename)
                    mymessages.extend(mymessagespart)
                    mymessagespart=[]
                    sticker_path = os.path.join(stickers_folder, sticker_filename)
                    await client.download_media(message, file=sticker_path)
            if len(history.messages)>0:
                last_offset_id = history.messages[-1].id
            else:
                break
            print(last_offset_id)
            sleep(2)
        with open("lastmessage_id.txt", 'w') as file:
            file.write(str(last_offset_id)+'\n')
            file.write(str(counter)+'\n')
            file.write(str(last_user_id))
#осуществляет запись/дозапись данных в csv файл
def write_to_csv(stick_names_list:list,last_word_list:list):
    filename = 'output.csv'
    mode = 'a' if os.path.exists(filename) else 'w'
    with open('output.csv', mode, newline='', encoding='utf-16') as csvfile:
        writer = csv.writer(csvfile)

        # Запись заголовков столбцов
        if mode == 'w':
            writer.writerow(['Last Words', 'Sticker Name'])

        # Запись данных
        for last_word, sticker_name in zip(last_word_list, stick_names_list):
            writer.writerow([last_word, sticker_name])

client.start()  # Подключаемся и аутентифицируемся

async def main():
    await get_dialog()
    print("Введите id чата")
    chat_id=int(input())
    max_messages=1000
    await parser(chat_id,max_messages)
    sticker_names_list=[]
    last_words_list=[]
    last_words=""
    for msg in mymessages:
        if fnmatch(msg,'sticker*.webp'):
            if len(last_words)>0:
                last_words=" ".join(last_words.split(' ')[-500::])
                last_words_list.append(last_words)
                sticker_names_list.append(msg)
                last_words=""
        else:
            last_words+=msg
    write_to_csv(sticker_names_list,last_words_list)
if __name__ == "__main__":
    client.loop.run_until_complete(main())
