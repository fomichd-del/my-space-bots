from PIL import Image, ImageDraw, ImageFont
import io
from datetime import datetime

def generate_passport(user_name, rank_name):
    try:
        # 1. Открываем твой фон
        img = Image.open("passport_bg.png")
    except FileNotFoundError:
        print("❌ ОШИБКА: Файл passport_bg.png не найден на сервере!")
        return None

    draw = ImageDraw.Draw(img)
    
    # 2. Загружаем шрифт (убедись, что файл лежит рядом со скриптом)
    font_path = "Roboto-Bold.ttf" 
    try:
        font_title = ImageFont.truetype(font_path, 40)
        font_text = ImageFont.truetype(font_path, 35)
        font_date = ImageFont.truetype(font_path, 25)
    except IOError:
        print("⚠️ ОШИБКА: Файл шрифта не найден! Использую стандартный (возможны проблемы с русским языком).")
        font_title = ImageFont.load_default()
        font_text = ImageFont.load_default()
        font_date = ImageFont.load_default()

    # 3. Настраиваем координаты для правой светлой части
    # Ориентировочно: немного правее центра
    start_x = int(img.width * 0.55)
    start_y = int(img.height * 0.3)
    
    current_date = datetime.now().strftime("%d.%m.%Y")

    # 4. Впечатываем текст
    draw.text((start_x, start_y), f"ПИЛОТ: {user_name}", fill=(20, 30, 80), font=font_title)
    draw.text((start_x, start_y + 70), f"ЗВАНИЕ:", fill=(80, 80, 80), font=font_date)
    draw.text((start_x, start_y + 110), f"{rank_name}", fill=(100, 50, 150), font=font_text)
    draw.text((start_x, start_y + 200), f"ДАТА ВЫДАЧИ: {current_date}", fill=(100, 100, 100), font=font_date)
    
    # 5. Сохраняем в оперативную память для отправки
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    
    return img_byte_arr
