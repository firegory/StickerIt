from rembg import remove
from PIL import Image

def remove_background(input_path, output_path):
    # Открываем входное изображение
    input_image = Image.open(input_path)

    # Удаляем фон
    output_image = remove(input_image)

    # Сохраняем результат
    output_image.save(output_path, "PNG")

remove_background('spidy.png ','spidy.webp')
