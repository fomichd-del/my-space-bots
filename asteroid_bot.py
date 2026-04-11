import requests
import os
import json
import random
from datetime import datetime

# ============================================================
# ⚙️ НАСТРОЙКИ
# ============================================================
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
NASA_API_KEY   = os.getenv('NASA_API_KEY') or "DEMO_KEY"
CHANNEL_NAME   = '@vladislav_space'
DB_FILE        = "last_asteroid_id.txt"

SPACE_PHOTOS = [
    "https://images.unsplash.com/photo-1446776811953-b23d57bd21aa?q=80&w=1200",
    "https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=1200",
    "https://images.unsplash.com/photo-1446776877081-d282a0f896e2?q=80&w=1200"
]

def get_size_comparison(meters):
    if meters < 15: return "🚌 Размером с автобус"
    elif meters < 40: return "🏠 Размером с большой дом"
    elif meters < 100: return "⚽️ Размером с футбольное поле"
    elif meters < 250: return "🏢 Размером с небоскреб"
    else: return "⛰ Размером с гору"

def get_asteroid_data():
    today = datetime.now().strftime('%Y-%m-%d')
    url = f"https://api.nasa.gov/neo/rest/v1/feed?start_date={today}&end_date={today}&api_key={NASA_API_KEY}"
    
    try:
        res = requests.get(url, timeout=40).json()
        asteroids = res['near_earth_objects'].get(today, [])
        if not asteroids: return None, None, None, None

        hero = max(asteroids, key=lambda x: x['estimated_diameter']['meters']['estimated_diameter_max'])
        ast_id = str(hero['neo_reference_id'])

        if os.path.exists(DB_FILE):
            with open(DB_FILE, 'r', encoding='utf-8') as f:
                if ast_id in f.read(): return None, None, None, None

        is_danger = hero['is_potentially_hazardous_asteroid']
        raw_name = hero['name'].replace("(", "").replace(")", "").strip()
        link_name = raw_name.replace(" ", "_")

        size = round(hero['estimated_diameter']['meters']['estimated_diameter_max'])
        dist_km = float(hero['close_approach_data'][0]['miss_distance']['kilometers'])
        dist_ld = round(dist_km / 384400, 1)

        # ТЕКСТ ПОСТА С ПОДСКАЗКАМИ
        text = (
            f"☄️ <b>АСТЕРОИДНЫЙ ПАТРУЛЬ</b>\n"
            f"─────────────────────\n\n"
            f"🛰 <b>Название:</b> {raw_name}\n"
            f"📏 <b>Размер:</b> ~{size} метров\n"
            f"👉 <i>{get_size_comparison(size)}</i>\n\n"
            f"🛣 <b>Дистанция:</b> {dist_ld} расстояний до Луны\n"
            f"{'⚠️' if is_danger else '✅'} <b>Статус: {'ОПАСЕН' if is_danger else 'БЕЗОПАСЕН'}</b>\n\n"
            f"📖 <b>ШПАРГАЛКА ДЛЯ 3D:</b>\n"
            f"▫️ <i>Distance</i> — расстояние\n"
            f"▫️ <i>Velocity</i> — скорость\n"
            f"▫️ <i>Diameter</i> — диаметр\n\n"
            f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
        )

        eyes_url = f"https://eyes.nasa.gov/apps/asteroids/#/asteroid/{link_name}"
        keyboard = {"inline_keyboard": [[{"text": "🚀 СМОТРЕТЬ В 3D (NASA EYES)", "url": eyes_url}]]}
        
        return text, keyboard, random.choice(SPACE_PHOTOS), ast_id
    except: return None, None, None, None

def send():
    text, keyb, photo, ast_id = get_asteroid_data()
    if text:
        payload = {'chat_id': CHANNEL_NAME, 'photo': photo, 'caption': text, 'parse_mode': 'HTML', 'reply_markup': json.dumps(keyb)}
        r = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto", data=payload)
        if r.status_code == 200:
            with open(DB_FILE, 'a', encoding='utf-8') as f: f.write(f"{ast_id}\n")

if __name__ == '__main__':
    send()
