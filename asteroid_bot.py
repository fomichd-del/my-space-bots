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

# Список фоновых изображений для постов
SPACE_PHOTOS = [
    "https://images.unsplash.com/photo-1446776811953-b23d57bd21aa?q=80&w=1200&auto=format&fit=crop",
    "https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=1200&auto=format&fit=crop",
    "https://images.unsplash.com/photo-1446776877081-d282a0f896e2?q=80&w=1200&auto=format&fit=crop",
    "https://images.unsplash.com/photo-1446947661719-71e4b03e6961?q=80&w=1200&auto=format&fit=crop"
]

def get_size_comparison(meters):
    """Сравнение размеров для наглядности (понятно детям)"""
    if meters < 15: return "🚌 Размером с автобус"
    elif meters < 40: return "🏠 Размером с большой дом"
    elif meters < 100: return "⚽️ Размером с футбольное поле"
    elif meters < 250: return "🏢 Размером с небоскреб"
    else: return "⛰ Размером с гору"

def get_asteroid_data():
    """Получает данные от NASA и формирует пост"""
    today = datetime.now().strftime('%Y-%m-%d')
    url = f"https://api.nasa.gov/neo/rest/v1/feed?start_date={today}&end_date={today}&api_key={NASA_API_KEY}"
    
    try:
        print(f"📡 Запрашиваю данные NASA на {today}...")
        response = requests.get(url, timeout=40)
        
        if response.status_code != 200:
            print(f"❌ Ошибка NASA API: {response.status_code}")
            return None, None, None, None

        data = response.json()
        asteroids = data['near_earth_objects'].get(today, [])
        
        if not asteroids:
            print("📭 Астероидов на сегодня не обнаружено.")
            return None, None, None, None

        # Выбираем самый крупный объект дня
        hero = max(asteroids, key=lambda x: x['estimated_diameter']['meters']['estimated_diameter_max'])
        ast_id = str(hero['neo_reference_id'])
        
        # Проверка памяти (чтобы не дублировать пост)
        if os.path.exists(DB_FILE):
            with open(DB_FILE, 'r', encoding='utf-8') as f:
                if ast_id in f.read():
                    print(f"✋ Астероид {ast_id} уже был опубликован сегодня. Пропускаю.")
                    return None, None, None, None

        # Данные астероида
        is_danger = hero['is_potentially_hazardous_asteroid']
        name = hero['name'].replace("(", "").replace(")", "").strip()
        size = round(hero['estimated_diameter']['meters']['estimated_diameter_max'])
        
        dist_km = float(hero['close_approach_data'][0]['miss_distance']['kilometers'])
        dist_ld = round(dist_km / 384400, 1)

        # Текст поста
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

        # Ссылка на 3D орбиту NASA
        orbit_url = f"https://ssd.jpl.nasa.gov/tools/sbdb_lookup.html#/?sstr={ast_id}"
        
        # Кнопка типа Web App (открывается прямо в Telegram)
        keyboard = {
            "inline_keyboard": [[
                {
                    "text": "👁 Орбита в 3D (Открыть плеер)", 
                    "web_app": {"url": orbit_url}
                }
            ]]
        }
        
        return text, keyboard, random.choice(SPACE_PHOTOS), ast_id

    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        return None, None, None, None

def send():
    """Отправка сообщения в канал"""
    text, keyb, photo, ast_id = get_asteroid_data()
    
    if text:
        print("📤 Отправляю сообщение в Telegram...")
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
            print(f"✅ Успешно! Астероид {ast_id} в канале.")
        else:
            print(f"❌ Ошибка Telegram: {r.text}")

if __name__ == '__main__':
    send()
