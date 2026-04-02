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

# Список проверенных фонов
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
    
    try:
        print(f"📡 Запрашиваю данные NASA на {today}...")
        res = requests.get(url, timeout=15).json()
        asteroids = res['near_earth_objects'].get(today, [])
        
        if not asteroids:
            print("📭 Астероидов сегодня не обнаружено.")
            return None, None, None

        hero = max(asteroids, key=lambda x: x['estimated_diameter']['meters']['estimated_diameter_max'])
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

        keyboard = {"inline_keyboard": [[{"text": "👁 Орбита в 3D", "url": f"https://ssd.jpl.nasa.gov/tools/sbdb_lookup.html#/?sstr={hero['neo_reference_id']}"}]]}
        photo_url = random.choice(SPACE_PHOTOS)

        return text, keyboard, photo_url
    except Exception as e:
        print(f"❌ Ошибка сбора данных: {e}")
        return None, None, None

def send_to_telegram(text, keyboard, photo_url):
    if not TELEGRAM_TOKEN:
        print("❌ ОШИБКА: TELEGRAM_TOKEN не найден в Secrets!")
        return

    print(f"📤 Отправляю фото в канал {CHANNEL_NAME}...")
    base_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    
    payload = {
        'chat_id': CHANNEL_NAME,
        'photo': photo_url,
        'caption': text,
        'parse_mode': 'HTML',
        'reply_markup': json.dumps(keyboard)
    }
    
    try:
        r = requests.post(base_url, data=payload, timeout=20)
        if r.status_code == 200:
            print("✅ СООБЩЕНИЕ УСПЕШНО ОТПРАВЛЕНО!")
        else:
            print(f"❌ ОШИБКА TELEGRAM API: {r.status_code}")
            print(f"📝 Текст ошибки: {r.text}")
    except Exception as e:
        print(f"❌ Ошибка сети при отправке: {e}")

if __name__ == '__main__':
    msg_text, msg_key, img_url = get_asteroid_data()
    if msg_text:
        send_to_telegram(msg_text, msg_key, img_url)
    else:
        print("📭 Нечего отправлять.")
