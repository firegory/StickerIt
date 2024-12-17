import re
import csv
import os

# компилируем регулярные выражения для поиска ссылок и эмодзи
link_pattern:re.Pattern = re.compile(r'https?://\S+|www\.\S+')
emoji_pattern:re.Pattern= re.compile(
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

# функция для предобработки полученных сообщений
def preprocess_text(text:str):
    # удаляем == заменяем на пустую строку
    # удаляем ссылки
    text = link_pattern.sub('', string=text)

    # удаляем эмодзи
    text = emoji_pattern.sub('', text)

    # удаляем лишние пробелы
    text = ' '.join(text.split())

    # приводим текст к нижнему регистру
    text = text.lower()

    return text.strip()  # удаляем пробелы по краям текста

# шаблон для файлов 'sticker*.webp', где * - одна или более цифр
stick_pattern:re.Pattern=re.compile(r'sticker_\d+\.webp$')

# получаем столбцы для записи потом в csv файл
def get_columns(messages_we_have:list[str]):
    sticker_names_list:list[str] = []
    last_words_list:list[str] = []
    last_words:str = ''
    for msg in messages_we_have:
        if stick_pattern.match(msg):
            if len(last_words) > 0:
                last_words = last_words.replace('\n', ' \n')
                last_words = last_words.split(' ')
                last_words:list
                len_last_words:int = 0
                new_last_words = []
                for ms in last_words[::-1]:
                    if ms[:2] == '\n':
                        len_last_words -= 2
                    len_last_words += len(ms)
                    new_last_words = [ms] + new_last_words
                    if len_last_words > 500:
                        break
                new_last_words = ' '.join(new_last_words)
                last_words = new_last_words
                new_last_words = new_last_words.replace(' \n', '\n')
                last_words_list.append(new_last_words)
                sticker_names_list.append(msg)
        else:
            last_words += msg
    return sticker_names_list,last_words_list

# осуществляет запись/дозапись данных в csv файл
def write_to_csv(stick_names_list:list,last_word_list:list):
    filename = 'output.csv'
    mode:str = 'a' if os.path.exists(filename) else 'w'
    with open('output.csv', mode, newline='', encoding='utf-16') as csvfile:
        writer = csv.writer(csvfile)

        # Запись заголовков столбцов
        if mode == 'w':
            writer.writerow(['Last Words', 'Sticker Name'])

        # Запись данных
        for last_word, sticker_name in zip(last_word_list, stick_names_list):
            writer.writerow([last_word, sticker_name])

