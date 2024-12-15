from telethon import TelegramClient
from telethon.tl.functions.messages import GetHistoryRequest
from telethon.tl.types import DocumentAttributeFilename,PeerUser,PeerChannel
from telethon.helpers import TotalList

from asyncio import sleep
from dotenv import load_dotenv
import os

from helper_func import preprocess_text, write_to_csv,get_columns

# Загружаем переменные окружения из файла .env и авторизуемся
load_dotenv()
api_id:int = int(os.getenv('api_id'))
api_hash:str = os.getenv('api_hash')
phone:str = os.getenv('phone')  # Укажите номер телефона с '+', например, +71234567890
# Создаем клиент с указанным именем сессии
client:TelegramClient = TelegramClient('my_session_name2.session', api_id, api_hash,device_model='NewLaptop',system_version="10.0 (Windows 11)")
mymessages:list[str]=[]

# создаем папку stickers если ее не существует
stickers_folder:str = 'stickers'
os.makedirs(stickers_folder, exist_ok=True)

# показывает доступные чаты и их id
async def get_dialog() -> None:
    async with client:
        dialogs:TotalList=await client.get_dialogs()
        print('доступные чаты')
        for dialog in dialogs:
            print((dialog.title,dialog.entity.id))

# по id чата и макс кол-ву сообщений(должно быть кратно 100) получит эти сообщения из чата
# рассчитано на многократное количество запусков, каждый раз в отдельном файле
# сохраняется информация про последнее полученное сообщение, так что можно продолжить
# парсить с того же места, где закончили в прошлый раз(только для одного и того же чата)
async def parser(chat_id:int,max_messages:int)->None:
    allmessages:list=[]

    file_path:str = "lastmessage_id.txt"

    if os.path.exists(file_path):  # проверяем существование файла
        with open(file_path, 'r') as file:  # открываем файл для чтения
            lines:list[str] = file.readlines()
            lines:list[int]=list(map(int,lines))
            last_offset_id,counter=lines

    else:
        last_offset_id=0
        counter = 1

    async with client:
        chat=await client.get_entity(chat_id)
        for zapros in range(max_messages//100):
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
            if len(history.messages)==0:
                break
            else:
                last_offset_id=history.messages[-1].id
            allmessages.extend(history.messages)
            if zapros%2==0:
                await sleep(1) # нужны задержки между запросами
        mymessagespart: list[str] = []
        last_user_id = 0
        for message in allmessages[::-1]:
            if message.message:
                msg:str=message.message
                if len(preprocess_text(msg))==0:
                    continue

                if message.from_id:
                    if isinstance(message.from_id, PeerUser):
                        # Если это пользователь
                        now_user = message.from_id.user_id

                    elif isinstance(message.from_id, PeerChannel):
                        # Если это канал
                        now_user = message.from_id.channel_id

                else:
                    now_user = 505  # В случае, если не удалось определить

                if len(mymessagespart)==0 or last_user_id==0:
                    msg='-'+preprocess_text(msg)
                    last_user_id=now_user

                elif last_user_id==now_user:
                    msg = " " + preprocess_text(msg)

                elif now_user not in [None,0,505]  and now_user != last_user_id:
                    last_user_id=now_user
                    msg='\n-'+preprocess_text(msg)
                    #print(msg,message.id)
                else:
                    msg = " "+preprocess_text(msg)
                    last_user_id=now_user
                mymessagespart.append(msg)
            elif message.sticker:
                attr=message.sticker.attributes
                for at in attr:
                    if isinstance(at, DocumentAttributeFilename):
                        file_name = at.file_name
                        if file_name=='sticker.webp':
                            sticker_filename = f'sticker_{counter}.webp'
                            counter += 1
                            mymessagespart.append(sticker_filename)
                            mymessages.extend(mymessagespart)
                            mymessagespart = []
                            sticker_path = os.path.join(stickers_folder, sticker_filename)
                            await client.download_media(message, file=sticker_path)

        if len(allmessages)==0:
            print("ВСЁ")
        else:
            last_offset_id = allmessages[-1].id
        print(last_offset_id)
        with open("lastmessage_id.txt", 'w') as file:
            file.write(str(last_offset_id)+'\n')
            file.write(str(counter)+'\n')


async def main():
    await get_dialog()
    print("Введите id чата")
    #chat_id =int(input()) при нескольких запусках для парсинга одного и того же чата можете указать напрямую
    chat_id=2151011041
    max_messages:int=1000 # сколько сообщений из чата хотите получить(кратно 100)
    await parser(chat_id,max_messages)
    sticker_names_list,last_words_list=get_columns(mymessages)
    write_to_csv(sticker_names_list,last_words_list)
if __name__ == "__main__":
    client.loop.run_until_complete(main())
