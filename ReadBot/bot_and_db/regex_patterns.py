import re
# компилируем регулярные выражения
link_pattern:re.Pattern= re.compile(r'https?://\S+|www\.\S+')
emoji_pattern:re.Pattern = re.compile(
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

#функция для предобработки полученных сообщений
def preprocess_text(text:str) -> str :
    # удаляем==заменяем на пустую строку

    # удаляем ссылки
    text = link_pattern.sub('', text)

    # удаляем эмодзи
    text = emoji_pattern.sub('', text)

    # удаляем лишние пробелы
    text = ' '.join(text.split())

    # приводим текст к нижнему регистру
    text = text.lower()

    return text.strip()  # удаляем пробелы по краям текста
