from PIL import Image, ImageDraw, ImageFont
import io
from datetime import datetime

def generate_passport(user_name, rank_name):
    # 1. Открываем твой фон с GitHub
    img = Image.open("passport_bg.png")
    draw = ImageDraw.Draw(img)
    
    # 2. Загружаем шрифт (УБЕДИСЬ, ЧТО ИМЯ ФАЙЛА СОВПАДАЕТ)
    font_path = "Roboto-Bold.ttf" 
    try:
        font_title = ImageFont.truetype(font_path, 50)
        font_text = ImageFont.truetype(font_path, 40)
    except IOError:
        print("⚠️ ОШИБКА: Файл шрифта не найден! Использую стандартный.")
        font_title = ImageFont.load_default()
        font_text = ImageFont.load_default()

    # 3. Настраиваем координаты для правой светлой части
    # Берем ширину картинки, делим пополам и немного сдвигаем вправо
    start_x = (img.width // 2) + 50 
    start_y = 250 # Отступ сверху
    
    current_date = datetime.now().strftime("%d.%m.%Y")

    # 4. Впечатываем текст (темно-синим космическим цветом)
    draw.text((start_x, start_y), f"ПИЛОТ: {user_name}", fill=(20, 30, 80), font=font_title)
    draw.text((start_x, start_y + 80), f"ЗВАНИЕ: {rank_name}", fill=(100, 50, 150), font=font_text)
    draw.text((start_x, start_y + 180), f"ДАТА: {current_date}", fill=(80, 80, 80), font=font_text)
    
    # 5. Сохраняем в оперативную память (чтобы сразу отправить в ТГ)
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    
    return img_byte_arr
