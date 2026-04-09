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
HISTORY_FILE   = 'last_asteroid_id.txt'

SPACE_PHOTOS = [
    "https://images.unsplash.com/photo-1446776811953-b23d57bd21aa?q=80&w=1200&auto=format&fit=crop",
    "https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=1200&auto=format&fit=crop",
    "https://images.unsplash.com/photo-1446776877081-d282a0f896e2?q=80&w=1200&auto=format&fit=crop"
]

def get_size_comparison(meters):
    if meters < 15: return "🚌 Размером с автобус"
    elif meters < 40: return "🏠 Размером с большой дом"
    elif meters < 100: return "⚽️ Размером с футбольное поле"
    elif meters < 250: return "🏢 Размером с небоскреб"
    else: return "⛰ Размером с гору"

def is_already_sent(asteroid_id):
    """Проверяет память, чтобы не было дублей"""
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r') as f:
            return asteroid_id in f.read()
    return False

def get_asteroid_data():
    # NASA использует время UTC, поэтому берем его
    today = datetime.utcnow().strftime('%Y-%m-%d')
    url = f"https://api.nasa.gov/neo/rest/v1/feed?start_date={today}&end_date={today}&api_key={NASA_API_KEY}"
    
    try:
        print(f"📡 Запрашиваю данные NASA на {today}...")
        response = requests.get(url, timeout=15)
        res = response.json()
        
        # БЕЗОПАСНАЯ ПРОВЕРКА: Если ключа нет, бот не упадет, а просто напишет ошибку
        neo_data = res.get('near_earth_objects', {})
        asteroids = neo_data.get(today, [])
        
        if not asteroids:
            print(f"📭 Астероидов в данных NASA на {today} не найдено. Ответ: {res}")
            return None, None, None, None

        # Фильтруем те, что уже были
        new_asteroids = [a for a in asteroids if not is_already_sent(a['neo_reference_id'])]
        
        if not new_asteroids:
            print("✅ Все астероиды на сегодня уже опубликованы.")
            return None, None, None, None

        # Выбираем самый крупный
        hero = max(new_asteroids, key=lambda x: x['estimated_diameter']['meters']['estimated_diameter_max'])
        ast_id = hero['neo_reference_id']
        is_danger = hero['is_potentially_hazardous_asteroid']
        name = hero['name'].replace("(", "").replace(")", "").strip()
        size = round(hero['estimated_diameter']['meters']['estimated_diameter_max'])
        
        dist_km = float(hero['close_approach_data'][0]['miss_distance']['kilometers'])
        dist_ld = round(dist_km / 384400, 1)

        text = (
            f"☄️ <b>АСТЕРОИДНЫЙ ПАТРУЛЬ</b>\n"
            f"─────────────────────\n\n"
            f"🛰 <b>Название:</b> {name}\n"
            f"📏 <b>Размер:</b> ~{size} метров\n"
            f"👉 <i>{get_size_comparison(size)}</i>\n\n"
            f"🛣 <b>Дистанция:</b> {dist_ld} расстояний до Луны\n"
            f"<i>({round(dist_km / 1_000_000, 1)} млн км от нас)</i>\n\n"
            f"{'⚠️' if is_danger else '✅'} <b>Статус: {'ОПАСЕН' if is_danger else 'БЕЗОПАСЕН'}</b>\n\n"
            f"⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
            f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
        )

        keyboard = {"inline_keyboard": [[{"text": "👁 Орбита в 3D", "url": f"https://ssd.jpl.nasa.gov/tools/sbdb_lookup.html#/?sstr={ast_id}"}]]}
        photo_url = random.choice(SPACE_PHOTOS)

        return text, keyboard, photo_url, ast_id
        
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        return None, None, None, None

def send_to_telegram(text, keyboard, photo_url, ast_id):
    base_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    payload = {
        'chat_id': CHANNEL_NAME,
        'photo': photo_url,
        'caption': text,
        'parse_mode': 'HTML',
        'reply_markup': json.dumps(keyboard)
    }
    
    r = requests.post(base_url, data=payload, timeout=20)
    if r.status_code == 200:
        print("✅ Пост отправлен!")
        # Записываем в память
        with open(HISTORY_FILE, 'a') as f:
            f.write(f"{ast_id}\n")
    else:
        print(f"❌ Ошибка TG: {r.text}")

if __name__ == '__main__':
    msg_text, msg_key, img_url, ast_id = get_asteroid_data()
    if msg_text and ast_id:
        send_to_telegram(msg_text, msg_key, img_url, ast_id)
    else:
        print("📭 Нечего отправлять.")
