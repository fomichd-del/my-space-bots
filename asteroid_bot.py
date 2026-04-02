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

# Красивые фоны для карточки (высокое качество)
BACKGROUND_URLS = [
    "https://w.forfun.com/fetch/f6/f67584100c82fb61b369986326e5a4ed.jpeg", # Deep Space
    "https://w.forfun.com/fetch/5a/5a4b76df87fbff8d2543920678d8a55d.jpeg", # Planet & Meteor
    "https://w.forfun.com/fetch/31/3141fbe14c8f53347b702da19f7902ba.jpeg", # Blue Nebula
    "https://w.forfun.com/fetch/10/104191d966e3fb2427a133481a53b53f.jpeg"  # Asteroid Field
]

def get_size_comparison(meters):
    """Сравнивает размер астероида с понятными вещами"""
    if meters < 5: return "🚗 Размером с легковой автомобиль"
    elif meters < 15: return "🚌 Размером с автобус"
    elif meters < 40: return "🏠 Размером с большой дом"
    elif meters < 100: return "⚽️ Размером с футбольное поле"
    elif meters < 250: return "🏢 Размером с небоскреб"
    else: return "⛰ Размером с гору"

def generate_asteroid_card(asteroid_name):
    """Генерирует уникальную картинку с именем астероида. Супер-надежный режим."""
    try:
        print(f"🎨 Генерирую карточку для: {asteroid_name}...")
        # 1. Скачиваем случайный фон
        bg_url = random.choice(BACKGROUND_URLS)
        response = requests.get(bg_url, timeout=10)
        img = Image.open(BytesIO(response.content))
        
        # 2. Обрезка под формат Telegram (16:9) и ресайз
        img = img.convert("RGB") # Гарантируем формат RGB
        width, height = img.size
        img = img.resize((1280, 720), Image.Resampling.LANCZOS)
        width, height = img.size
        
        # 3. Подготовка к рисованию
        draw = ImageDraw.Draw(img)
        
        # Загружаем шрифт. По умолчанию на Linux есть этот шрифт.
        # Я добавил поиск по стандартному пути в Ubuntu.
        font_main = None
        paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
        ]
        for p in paths:
            if os.path.exists(p):
                # Нашли, используем красивый жирный шрифт
                font_main = ImageFont.truetype(p, 100)
                font_small = ImageFont.truetype(p, 50)
                break
        
        if not font_main:
            # Резервный шрифт, если не нашли DejaVu
            print("⚠️ Шрифты DejaVu/Liberation не найдены, использую стандартный.")
            font_main = ImageFont.load_default()
            font_small = font_main

        # 4. Рисуем плашку и текст
        # Рисуем простую подложку для читаемости по центру
        draw.rectangle([0, 320, 1280, 480], fill=(0, 0, 0, 160))
        
        # Название астероида (золотым цветом)
        draw.text((80, 350), f"ОБЪЕКТ: {asteroid_name}", font=font_main, fill=(255, 215, 0)) # Золотой

        # Заголовок (белым цветом сверху)
        draw.text((80, 60), "☄️ АСТЕРОИДНЫЙ ПАТРУЛЬ", font=font_small, fill=(255, 255, 255))

        # 5. Сохраняем в память
        img_io = BytesIO()
        img.save(img_io, 'JPEG', quality=90)
        img_io.seek(0)
        return img_io

    except Exception as e:
        print(f"❌ Ошибка генерации картинки: {e}")
        return None

def get_asteroid_data():
    """Получает данные и формирует Фото + Текст."""
    today = datetime.now().strftime('%Y-%m-%d')
    url = f"https://api.nasa.gov/neo/rest/v1/feed?start_date={today}&end_date={today}&api_key={NASA_API_KEY}"
    
    try:
        print(f"📡 Запрос данных от NASA...")
        response = requests.get(url, timeout=15)
        
        if response.status_code != 200:
            print(f"❌ Ошибка API: {response.status_code}")
            return None, None, None

        data = response.json()
        asteroids = data['near_earth_objects'].get(today, [])
        
        print(f"✅ Данные получены. Обнаружено объектов: {len(asteroids)}")
        
        if not asteroids:
            return "☄️ <b>АСТЕРОИДНЫЙ ПАТРУЛЬ</b>\n\nСегодня в окрестностях Земли спокойно. ✨", None, None

        # Выбор "героя" дня
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
        # Расстояние в "Лунах"
        dist_ld = dist_km / 384400
        
        speed = float(hero['close_approach_data'][0]['relative_velocity']['kilometers_per_hour'])

        # Текст
        comparison = get_size_comparison(avg_size)
        status_icon = "⚠️" if is_danger else "✅"
        status_text = "ПОТЕНЦИАЛЬНО ОПАСЕН" if is_danger else "БЕЗОПАСЕН"

        text = (
            f"☄️ <b>АСТЕРОИДНЫЙ ПАТРУЛЬ: ОБЪЕКТ ДНЯ</b>\n"
            f"─────────────────────\n\n"
            f"🛰 <b>Название:</b> {name}\n"
            f"📏 <b>Размер:</b> ~{avg_size} метров\n"
            f"👉 <i>{comparison}</i>\n\n"
            f"🚀 <b>Скорость:</b> {round(speed):,} км/ч\n"
            f"🛣 <b>Дистанция:</b> {round(dist_ld, 1)} LD (расстояний до Луны)\n"
            f"<i>({round(dist_km / 1_000_000, 1)} млн км от Земли)</i>\n\n"
            f"{status_icon} <b>Статус NASA: {status_text}</b>"
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
    """Отправляет Фото + Текст (sendPhoto). Это уберет нижний блок."""
    base_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
    
    if not photo:
        # Резервный вариант, если картинка не сгенерировалась
        print("⚠️ Шлю только текст, так как фото нет.")
        url = f"{base_url}/sendMessage"
        payload = {
            'chat_id': CHANNEL_NAME,
            'text': text,
            'parse_mode': 'HTML',
            'reply_markup': json.dumps(keyboard),
            'disable_web_page_preview': True # Это уберет нижний блок, если шлем только текст
        }
        requests.post(url, data=payload)
    else:
        # Шлем ФОТО с подписью. Telegram сам уберет превью ссылки.
        print("📡 Отправляю фото-карточку в Telegram...")
        url = f"{base_url}/sendPhoto"
        files = {'photo': ('asteroid.jpg', photo, 'image/jpeg')}
        payload = {
            'chat_id': CHANNEL_NAME,
            'caption': text,
            'parse_mode': 'HTML',
            'reply_markup': json.dumps(keyboard)
        }
        requests.post(url, files=files, data=payload)

if __name__ == '__main__':
    msg_text, msg_key, msg_photo = get_asteroid_data()
    if msg_text:
        send_to_telegram(msg_text, msg_key, msg_photo)
