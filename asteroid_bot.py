import requests
import os
import json
import random
import time
from datetime import datetime

# ============================================================
# ⚙️ НАСТРОЙКИ
# ============================================================
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
NASA_API_KEY   = os.getenv('NASA_API_KEY') or "DEMO_KEY"
CHANNEL_NAME   = '@vladislav_space'
DB_FILE        = "last_asteroid_id.txt"

# Список проверенных фонов для постов
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

def get_asteroid_data():
    today = datetime.now().strftime('%Y-%m-%d')
    url = f"https://api.nasa.gov/neo/rest/v1/feed?start_date={today}&end_date={today}&api_key={NASA_API_KEY}"
    
    for attempt in range(1, 4):
        try:
            print(f"📡 Попытка {attempt}: Запрашиваю данные NASA...")
            res = requests.get(url, timeout=40)
            
            if res.status_code == 503:
                print("⚠️ NASA временно недоступна (503). Подождем...")
                time.sleep(10)
                continue
                
            data = res.json()
            asteroids = data['near_earth_objects'].get(today, [])
            
            if not asteroids:
                print("📭 Астероидов сегодня не обнаружено.")
                return None, None, None, None

            # Выбираем самый крупный астероид
            hero = max(asteroids, key=lambda x: x['estimated_diameter']['meters']['estimated_diameter_max'])
            ast_id = str(hero['neo_reference_id'])

            # Проверка памяти
            if os.path.exists(DB_FILE):
                with open(DB_FILE, 'r', encoding='utf-8') as f:
                    if ast_id in f.read():
                        print(f"✋ Астероид {ast_id} уже был опубликован.")
                        return None, None, None, None

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
                f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
            )

            keyboard = {"inline_keyboard": [[{"text": "👁 Орбита в 3D", "url": f"https://ssd.jpl.nasa.gov/tools/sbdb_lookup.html#/?sstr={ast_id}"}]]}
            return text, keyboard, random.choice(SPACE_PHOTOS), ast_id

        except Exception as e:
            print(f"❌ Ошибка в попытке {attempt}: {e}")
            time.sleep(5)
            
    return None, None, None, None

def send():
    text, keyb, photo, ast_id = get_asteroid_data()
    if text:
        payload = {
            'chat_id': CHANNEL_NAME,
            'photo': photo,
            'caption': text,
            'parse_mode': 'HTML',
            'reply_markup': json.dumps(keyb)
        }
        r = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto", data=payload)
        if r.status_code == 200:
            with open(DB_FILE, 'a', encoding='utf-8') as f:
                f.write(f"{ast_id}\n")
            print(f"✅ Астероид {ast_id} отправлен!")

if __name__ == '__main__':
    send()
