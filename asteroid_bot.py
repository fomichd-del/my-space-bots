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

# Красивые фоны для карточки
BACKGROUND_URLS = [
    "https://w.forfun.com/fetch/f6/f67584100c82fb61b369986326e5a4ed.jpeg",
    "https://w.forfun.com/fetch/5a/5a4b76df87fbff8d2543920678d8a55d.jpeg",
    "https://w.forfun.com/fetch/31/3141fbe14c8f53347b702da19f7902ba.jpeg",
    "https://w.forfun.com/fetch/10/104191d966e3fb2427a133481a53b53f.jpeg"
]

def get_size_comparison(meters):
    if meters < 5: return "🚗 Размером с автомобиль"
    elif meters < 15: return "🚌 Размером с автобус"
    elif meters < 40: return "🏠 Размером с большой дом"
    elif meters < 100: return "⚽️ Размером с футбольное поле"
    elif meters < 250: return "🏢 Размером с небоскреб"
    else: return "⛰ Размером с гору"

def generate_asteroid_card(asteroid_name):
    """Генерация фото-карточки с названием"""
    try:
        bg_url = random.choice(BACKGROUND_URLS)
        response = requests.get(bg_url, timeout=10)
        img = Image.open(BytesIO(response.content)).convert("RGB")
        img = img.resize((1280, 720), Image.Resampling.LANCZOS)
        
        draw = ImageDraw.Draw(img)
        
        # Поиск шрифта в системе
        font_main = None
        for p in ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"]:
            if os.path.exists(p):
                font_main = ImageFont.truetype(p, 90)
                font_small = ImageFont.truetype(p, 45)
                break
        
        if not font_main:
            font_main = ImageFont.load_default()
            font_small = font_main

        # Рисуем плашку и текст
        draw.rectangle([0, 320, 1280, 480], fill=(0, 0, 0, 160))
        draw.text((80, 350), f"ОБЪЕКТ: {asteroid_name}", font=font_main, fill=(255, 215, 0))
        draw.text((80, 60), "☄️ АСТЕРОИДНЫЙ ПАТРУЛЬ", font=font_small, fill=(255, 255, 255))

        img_io = BytesIO()
        img.save(img_io, 'JPEG', quality=90)
        img_io.seek(0)
        return img_io
    except: return None

def get_asteroid_data():
    today = datetime.now().strftime('%Y-%m-%d')
    url = f"https://api.nasa.gov/neo/rest/v1/feed?start_date={today}&end_date={today}&api_key={NASA_API_KEY}"
    
    try:
        res = requests.get(url, timeout=15).json()
        asteroids = res['near_earth_objects'].get(today, [])
        if not asteroids: return None, None, None

        hero = max(asteroids, key=lambda x: x['estimated_diameter']['meters']['estimated_diameter_max'])
        is_danger = hero['is_potentially_hazardous_asteroid']
        name = hero['name'].replace("(", "").replace(")", "").strip()
        size = round(hero['estimated_diameter']['meters']['estimated_diameter_max'])
        
        # Дистанция
        dist_km = float(hero['close_approach_data'][0]['miss_distance']['kilometers'])
        dist_ld = round(dist_km / 384400, 1) # Переводим в расстояния до Луны
        
        # Формируем понятную подпись для дистанции
        if dist_ld < 1:
            dist_phrase = f"⚠️ ОЧЕНЬ БЛИЗКО! ({dist_ld} до Луны)"
        else:
            dist_phrase = f"{dist_ld} расстояний до Луны"

        text = (
            f"☄️ <b>АСТЕРОИДНЫЙ ПАТРУЛЬ</b>\n"
            f"─────────────────────\n\n"
            f"🛰 <b>Название:</b> {name}\n"
            f"📏 <b>Размер:</b> ~{size} метров\n"
            f"👉 <i>{get_size_comparison(size)}</i>\n\n"
            f"🛣 <b>Дистанция:</b> {dist_phrase}\n"
            f"<i>({round(dist_km / 1_000_000, 1)} млн км от нас)</i>\n\n"
            f"{'⚠️' if is_danger else '✅'} <b>Статус: {'ОПАСЕН' if is_danger else 'БЕЗОПАСЕН'}</b>\n\n"
            f"⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
            f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
        )

        keyboard = {"inline_keyboard": [[{"text": "👁 Орбита в 3D", "url": f"https://ssd.jpl.nasa.gov/tools/sbdb_lookup.html#/?sstr={hero['neo_reference_id']}"}]]}
        photo = generate_asteroid_card(name)
        return text, keyboard, photo
    except: return None, None, None

def send_to_telegram(text, keyboard, photo):
    base_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
    if photo:
        files = {'photo': ('asteroid.jpg', photo, 'image/jpeg')}
        requests.post(f"{base_url}/sendPhoto", files=files, data={'chat_id': CHANNEL_NAME, 'caption': text, 'parse_mode': 'HTML', 'reply_markup': json.dumps(keyboard)})
    else:
        requests.post(f"{base_url}/sendMessage", data={'chat_id': CHANNEL_NAME, 'text': text, 'parse_mode': 'HTML', 'reply_markup': json.dumps(keyboard)})

if __name__ == '__main__':
    msg_text, msg_key, msg_photo = get_asteroid_data()
    if msg_text:
        send_to_telegram(msg_text, msg_key, msg_photo)
