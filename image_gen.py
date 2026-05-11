from PIL import Image, ImageDraw, ImageFont
import io
import random
import time
from datetime import datetime
from neural_draw import get_cascade_image # 🟢 Подключаем каскадный генератор AI-фонов

def get_passport_prompt(rank_name):
    """Генерирует уникальный, улучшенный промпт для фона паспорта на основе ранга."""
    
    # Базовый, очень мощный и детализированный промпт
    base_prompt = (
        "macro photography of a realistic sci-fi futuristic Orion Academy identity card template, "
        "made of futuristic carbon and polished metal, incredibly complex detailed patterns, "
        "subtle blue glowing holographic projections of stars and constellations floating just above the surface, "
        "a small circular glowing emblem on the left with a stylized Orion constellation as a ship with wings (Orion Academy logo), "
        "no text on the template, blank space for details, cinematic lighting, 8k resolution, photorealistic."
    )
    
    # 🟢 Мои фишки: Меняем стиль промпта в зависимости от ранга!
    if "Рекрут" in rank_name or "Кадет" in rank_name:
        style_details = "theme of new beginnings, subtle blue and silver glowing colors."
    elif "Маршал" in rank_name or "Пилот" in rank_name:
        style_details = "theme of elitism and leadership, subtle gold and black glowing colors, expensive look."
    else:
        style_details = "theme of the space, deep space indigo and neon purple colors."
        
    return f"{base_prompt} {style_details}"

def generate_passport(user_name, rank_name, user_id):
    try:
        # === ЧАСТЬ 1: ГЕНЕРАЦИЯ AI-ФОНА (Каскад + Зерно по рангу) ===
        
        prompt = get_passport_prompt(rank_name)
        
        # 🟢 Самое важное: фиксируем зерно по рангу, чтобы фон был стабильным для звания
        seed = sum(ord(c) for c in rank_name) 
        
        # Запрашиваем изображение из AI (каскадом)
        image_bytes = get_cascade_image(prompt, seed)
        
        if not image_bytes:
            print("❌ ОШИБКА: Нейросеть не смогла сгенерировать фон паспорта!")
            return None
            
        # Конвертируем байты AI в Pillow Image
        img = Image.open(io.BytesIO(image_bytes))
        
        # === ЧАСТЬ 2: НАЛОЖЕНИЕ ТЕКСТА (Высший пилотаж Pillow) ===
        
        draw = ImageDraw.Draw(img)
        
        # Убедись, что файл лежит рядом со скриптом!
        font_path = "Roboto-Bold.ttf" 
        try:
            font_title = ImageFont.truetype(font_path, 40)
            font_text = ImageFont.truetype(font_path, 35)
            font_date = ImageFont.truetype(font_path, 25)
            font_id = ImageFont.truetype(font_path, 20)
        except IOError:
            print("⚠️ ОШИБКА: Шрифт Roboto-Bold.ttf не найден! Использую стандартный.")
            font_title = font_text = font_date = font_id = ImageFont.load_default()

        # Настраиваем координаты для правой светлой части
        start_x = int(img.width * 0.55)
        start_y = int(img.height * 0.3)
        
        current_date = datetime.now().strftime("%d.%m.%Y")
        # 🟢 Моя фишка: генерируем уникальный серийный ID на основе user_id и времени
        unique_id = f"ORION-ID_{user_id}_{int(time.time() / 3600)}" 

        # 🟢 Цвета с эффектом свечения (Тень + Текст)
        
        # Цвета для тени (более темные)
        shadow_color = (10, 10, 30)
        # Цвета для текста (светлые/неоновые)
        title_color = (200, 220, 255) # Светло-голубой
        date_color = (180, 180, 180)  # Серый
        rank_color = (180, 150, 255)  # Светло-фиолетовый

        # Впечатываем текст (сначала ТЕНЬ с отступом 2 пикселя, затем ТЕКСТ)
        
        # Текст: Пилот
        draw.text((start_x + 2, start_y + 2), f"ПИЛОТ: {user_name}", fill=shadow_color, font=font_title)
        draw.text((start_x, start_y), f"ПИЛОТ: {user_name}", fill=title_color, font=font_title)
        
        # Текст: Звание (тень не нужна, он серый)
        draw.text((start_x, start_y + 70), f"ЗВАНИЕ:", fill=date_color, font=font_date)
        
        # Текст: Название ранга
        draw.text((start_x + 2, start_y + 112), f"{rank_name}", fill=shadow_color, font=font_text)
        draw.text((start_x, start_y + 110), f"{rank_name}", fill=rank_color, font=font_text)
        
        # Текст: Дата
        draw.text((start_x, start_y + 200), f"ДАТА ВЫДАЧИ: {current_date}", fill=date_color, font=font_date)
        
        # 🟢 Текст: Серийный ID-номер в самом низу
        draw.text((start_x, img.height - 40), f"VALID: {unique_id}", fill=(100, 100, 100, 150), font=font_id)
        
        # === ЧАСТЬ 3: СОХРАНЕНИЕ И ОТПРАВКА ===
        
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        
        print(f"✅ Паспорт нового образца с AI-фоном для ранга '{rank_name}' успешно сгенерирован!")
        return img_byte_arr
        
    except Exception as e:
        print(f"🚨 КРИТИЧЕСКИЙ СБОЙ ПРИ ГЕНЕРАЦИИ ПАСПОРТА: {e}")
        return None
