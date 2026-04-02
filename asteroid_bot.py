import requests
import os
import json
import random
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

# ============================================================
# ⚙️ НАСТРОЙКИ
# ============================================================
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
NASA_API_KEY   = os.getenv('NASA_API_KEY') or "DEMO_KEY"
CHANNEL_NAME   = '@vladislav_space'

# Список красивых фонов для генерации карточки (высокое качество)
BACKGROUND_URLS = [
    "https://w.forfun.com/fetch/f6/f67584100c82fb61b369986326e5a4ed.jpeg", # Deep Space
    "https://w.forfun.com/fetch/5a/5a4b76df87fbff8d2543920678d8a55d.jpeg", # Planet & Meteor
    "https://w.forfun.com/fetch/31/3141fbe14c8f53347b702da19f7902ba.jpeg", # Blue Nebula
    "https://w.forfun.com/fetch/10/104191d966e3fb2427a133481a53b53f.jpeg"  # Asteroid Field
]

# Координаты для Telegram в Лунах (LD = 384 400 км)
LD_DISTANCE = 384400

def get_size_comparison(meters):
    if meters < 5: return "🚗 Размером с легковой автомобиль"
    elif meters < 15: return "🚌 Размером с автобус"
    elif meters < 40: return "🏠 Размером с большой дом"
    elif meters < 100: return "⚽️ Размером с футбольное поле"
    elif meters < 250: return "🏢 Размером с небоскреб"
    else: return "⛰ Размером с гору"

def generate_asteroid_card(asteroid_name):
    """Генерирует уникальную картинку с именем астероида."""
    try:
        print(f"🎨 Генерирую карточку для: {asteroid_name}...")
        # 1. Скачиваем случайный фон
        bg_url = random.choice(BACKGROUND_URLS)
        response = requests.get(bg_url, timeout=10)
        img = Image.open(BytesIO(response.content))
        
        # 2. Делаем обрезку под формат Telegram (16:9)
        width, height = img.size
        target_ratio = 16 / 9
        current_ratio = width / height
        
        if current_ratio > target_ratio:
            # Слишком широкая, режем бока
            new_width = int(height * target_ratio)
            left = (width - new_width) // 2
            img = img.crop((left, 0, left + new_width, height))
        else:
            # Слишком высокая, режем верх/низ
            new_height = int(width / target_ratio)
            top = (height - new_height) // 2
            img = img.crop((0, top, width, top + new_height))
            
        img = img.resize((1280, 720), Image.Resampling.LANCZOS)
        width, height = img.size
        
        # 3. Подготовка к рисованию
        draw = ImageDraw.Draw(img, 'RGBA')
        
        # Загружаем шрифт. По умолчанию на Linux/GitHub Actions есть этот шрифт.
        # Если шрифта нет, он упадет, поэтому в реальном проекте .ttf лучше хранить в репо.
        try:
            # Пытаемся загрузить красивый жирный шрифт
            font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
            font_title = ImageFont.truetype(font_path, 80)
            font_name = ImageFont.truetype(font_path, 110)
            font_logo = ImageFont.truetype(font_path, 40)
        except:
            # Резервный шрифт, если не нашли DejaVu
            print("⚠️ Шрифты DejaVu не найдены, использую стандартный. Карточка будет некрасивой.")
            font_title = ImageFont.load_default()
            font_name = font_title
            font_logo = font_title

        # 4. Рисуем текст с подложкой (тенью) для читаемости
        shadow_color = (0, 0, 0, 180) # Полупрозрачный черный
        text_color = (255, 255, 255, 255) # Белый

        # Заголовок
        title_text = "☄️ АСТЕРОИДНЫЙ ПАТРУЛЬ"
        _, _, tw, th = draw.textbbox((0, 0), title_text, font=font_title)
        x_title = (width - tw) // 2
        
        draw.text((x_title + 3, 100 + 3), title_text, font=font_title, fill=shadow_color) # Тень
        draw.text((x_title, 100), title_text, font=font_title, fill=text_color)

        # Название астероида (самое главное)
        _, _, nw, nh = draw.textbbox((0, 0), asteroid_name, font=font_name)
        x_name = (width - nw) // 2
        y_name = (height - nh) // 2 + 50
        
        # Эффект обводки (рисуем 8 черных текстов вокруг белого)
        stroke_width = 4
        for x_offset in range(-stroke_width, stroke_width + 1):
            for y_offset in range(-stroke_width, stroke_width + 1):
                if x_offset == 0 and y_offset == 0: continue
                draw.text((x_name + x_offset, y_name + y_offset), asteroid_name, font=font_name, fill=(0,0,0,200))

        draw.text((x_name, y_name), asteroid_name, font=font_name, fill=(255, 215, 0, 255)) # Золотой цвет

        # Логотип канала (внизу справа)
        logo_text = "🛰 vladislav_space"
        _, _, lw, lh = draw.textbbox((0, 0), logo_text, font=font_logo)
        draw.text((width - lw - 40 + 2, height - lh - 40 + 2), logo_text, font=font_logo, fill=(0,0,0,150)) # Тень
        draw.text((width - lw - 40, height - lh - 40), logo_text, font=font_logo, fill=(255, 255, 255, 180))

        # 5. Сохраняем в память
        img_io = BytesIO()
        img.save(img_io, 'JPEG', quality=85)
        img_io.seek(0)
        return img_io

    except Exception as e:
        print(f"❌ Ошибка генерации картинки: {e}")
        return None

def get_asteroid_data():
    today = datetime.now().strftime('%Y-%m-%d')
    url = f"https://api.nasa.gov/neo/rest/v1/feed?start_date={today}&end_date={today}&api_key={NASA_API_KEY}"
    
    try:
        response = requests.get(url, timeout=15)
        if response.status_code != 200: return None, None, None

        data = response.json()
        asteroids = data['near_earth_objects'].get(today, [])
        
        if not asteroids:
            return "☄️ <b>АСТЕРОИДНЫЙ ПАТРУЛЬ</b>\n\nСегодня в окрестностях Земли всё спокойно. ✨", None, None

        # Выбираем самого крупного или опасного
        hazardous = [a for a in asteroids if a['is_potentially_hazardous_asteroid']]
        if hazardous:
            hero = max(hazardous, key=lambda x: x['estimated_diameter']['meters']['estimated_diameter_max'])
            is_danger = True
        else:
            hero = max(asteroids, key=lambda x: x['estimated_diameter']['meters']['estimated_diameter_max'])
            is_danger = False

        # Данные
        name = hero['name'].replace("(", "").replace(")", "").strip()
        size_min = round(hero['estimated_diameter']['meters']['estimated_diameter_min'])
        size_max = round(hero['estimated_diameter']['meters']['estimated_diameter_max'])
        avg_size = (size_min + size_max) // 2
        
        dist_km = float(hero['close_approach_data'][0]['miss_distance']['kilometers'])
        dist_ld = dist_km / LD_DISTANCE # В дистанциях до Луны
        
        speed = float(hero['close_approach_data'][0]['relative_velocity']['kilometers_per_hour'])

        # Текст
        comparison = get_size_comparison(avg_size)
        status_icon = "⚠️" if is_danger else "✅"
        status_text = "ПОТЕНЦИАЛЬНО ОПАСЕН" if is_danger else "БЕЗОПАСЕН"

        text = (
            f"☄️ <b>АСТЕРОИДНЫЙ ПАТРУЛЬ: ОБЪЕКТ ДНЯ</b>\n"
            f"─────────────────────\n\n"
            f"📏 <b>Размер:</b> ~{avg_size} метров\n"
            f"👉 <i>{comparison}</i>\n\n"
            f"🚀 <b>Скорость:</b> {round(speed):,} км/ч\n"
            f"🛣 <b>Дистанция:</b> {round(dist_ld, 1)} LD (расстояний до Луны)\n"
            f"<i>({round(dist_km / 1_000_000, 1)} млн км от Земли)</i>\n\n"
            f"{status_icon} <b>Статус NASA: {status_text}</b>\n\n"
            f"⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
            f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
        )

        keyboard = {
            "inline_keyboard": [[{
                "text": "👁 Посмотреть орбиту в 3D",
                "url": f"https://ssd.jpl.nasa.gov/tools/sbdb_lookup.html#/?sstr={hero['neo_reference_id']}"
            }]]
        }

        # Генерируем карточку
        photo = generate_asteroid_card(name)

        return text, keyboard, photo

    except Exception as e:
        print(f"⚠️ Ошибка: {e}")
        return None, None, None

def send_to_telegram(text, keyboard, photo):
    """Отправляет Фото + Текст (sendPhoto)."""
    base_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
    
    if not photo:
        # Если картинка не сгенерировалась, шлем только текст
        print("⚠️ Шлю только текст, так как фото нет.")
        url = f"{base_url}/sendMessage"
        payload = {'chat_id': CHANNEL_NAME, 'text': text, 'parse_mode': 'HTML', 'reply_markup': json.dumps(keyboard)}
        requests.post(url, data=payload)
    else:
        # Шлем ФОТО с подписью
        print("📡 Отправляю фото-карточку в Telegram...")
        url = f"{base_url}/sendPhoto"
        files = {'photo': ('asteroid.jpg', photo, 'image/jpeg')}
        payload = {'chat_id': CHANNEL_NAME, 'caption': text, 'parse_mode': 'HTML', 'reply_markup': json.dumps(keyboard)}
        requests.post(url, files=files, data=payload)

if __name__ == '__main__':
    msg_text, msg_key, msg_photo = get_asteroid_data()
    if msg_text:
        send_to_telegram(msg_text, msg_key, msg_photo)
