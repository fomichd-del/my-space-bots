import requests
import os
import json
import random
from datetime import datetime, timezone
from zoneinfo import ZoneInfo 

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

# Словари для перевода на русский
MONTHS_RU = {
    1: "января", 2: "февраля", 3: "марта", 4: "апреля", 5: "мая", 6: "июня",
    7: "июля", 8: "августа", 9: "сентября", 10: "октября", 11: "ноября", 12: "декабря"
}

ORBIT_MAP = {
    "Apollo": "Аполлоны (пересекают орбиту Земли)",
    "Amor": "Амуры (подлетают близко к Земле)",
    "Aten": "Атоны (внутри земной орбиты, пересекают её)",
    "Atira": "Атиры (полностью внутри орбиты Земли)",
    "Parabolic": "Параболическая (пришелец из глубин космоса)",
    "Hyperbolic": "Гиперболическая (пролетит мимо один раз)"
}

def format_date_ru(date_str):
    """Превращает 2004-03-23 в 23 марта 2004 года"""
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return f"{dt.day} {MONTHS_RU[dt.month]} {dt.year} года"
    except:
        return date_str

def get_size_comparison(meters):
    if meters < 15: return "🚌 Автобус"
    elif meters < 40: return "🏠 Большой дом"
    elif meters < 100: return "⚽️ Футбольное поле"
    elif meters < 250: return "🏢 Небоскреб"
    else: return "⛰ Гора"

def get_asteroid_data():
    now_local = datetime.now(ZoneInfo("Europe/Kyiv"))
    today_str = now_local.strftime('%Y-%m-%d')
    
    feed_url = f"https://api.nasa.gov/neo/rest/v1/feed?start_date={today_str}&end_date={today_str}&api_key={NASA_API_KEY}"
    
    try:
        res = requests.get(feed_url, timeout=40).json()
        asteroids = res['near_earth_objects'].get(today_str, [])
        if not asteroids: return None, None, None, None

        # Выбираем самый крупный астероид дня
        hero = max(asteroids, key=lambda x: x['estimated_diameter']['meters']['estimated_diameter_max'])
        ast_id = str(hero['neo_reference_id'])

        # Проверка памяти
        if os.path.exists(DB_FILE):
            with open(DB_FILE, 'r', encoding='utf-8') as f:
                if ast_id in f.read(): return None, None, None, None

        # Детальный запрос для досье
        details_url = f"https://api.nasa.gov/neo/rest/v1/neo/{ast_id}?api_key={NASA_API_KEY}"
        details = requests.get(details_url, timeout=30).json()
        
        discovery_date_raw = details.get('orbital_data', {}).get('first_observation_date', "Неизвестно")
        discovery_date_ru = format_date_ru(discovery_date_raw)
        
        orbit_type = details.get('orbital_data', {}).get('orbit_class', {}).get('orbit_class_type', "Околоземный")
        orbit_desc_ru = ORBIT_MAP.get(orbit_type, "Редкий тип орбиты")

        name = hero['name'].replace("(", "").replace(")", "").strip()
        link_name = name.replace(" ", "_")
        size = round(hero['estimated_diameter']['meters']['estimated_diameter_max'])
        is_danger = hero['is_potentially_hazardous_asteroid']
        
        approach = hero['close_approach_data'][0]
        dist_km = float(approach['miss_distance']['kilometers'])
        velocity = float(approach['relative_velocity']['kilometers_per_hour'])
        
        timestamp_ms = approach['epoch_date_close_approach']
        approach_dt = datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc).astimezone(ZoneInfo("Europe/Kyiv"))

        danger_text = "⚠️ Потенциально опасен" if is_danger else "✅ Не представляет угрозы"
        interest_reason = "Крупный размер" if size > 100 else "Очень близкий пролет" if dist_km < 1000000 else "Высокая скорость"

        # ТЕКСТ ПОСТА (С двойным заголовком)
        text = (
            f"☄️ <b>АСТЕРОИДНЫЙ ПАТРУЛЬ: ДОСЬЕ ОБЪЕКТА {name}</b>\n"
            f"─────────────────────\n\n"
            f"⏰ <b>Пик сближения:</b> {approach_dt.strftime('%H:%M')}\n"
            f"🗓 <b>Впервые замечен:</b> {discovery_date_ru}\n\n"
            f"📏 <b>Размер:</b> ~{size} м ({get_size_comparison(size)})\n"
            f"🚀 <b>Скорость:</b> {int(velocity):,} км/ч\n"
            f"🛣 <b>Дистанция:</b> {round(dist_km / 1_000_000, 2)} млн км\n\n"
            f"🛰 <b>Группа:</b> {orbit_desc_ru}\n"
            f"🛡 <b>Статус:</b> {danger_text}\n"
            f"🧐 <b>Интересно:</b> {interest_reason}\n"
            f"Отличный снимок, Командор! 🚀 Если хочешь узнать больше об этом астероиде, можешь <a href="https://t.me/Marty_Help_Bot?start=channel_post">Спросить эксперта!</a>\n"         
            f"─────────────────────\n"
            f"📍 <b>ГДЕ ИСКАТЬ:</b> Нажми кнопку ниже. В 3D-плеере разверни камеру на Землю — астероид будет подлетать с освещенной (день) или ночной стороны.\n\n"
            f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
        )

        eyes_url = f"https://eyes.nasa.gov/apps/asteroids/#/asteroid/{link_name}"
        button_text = f"✨ СМОТРЕТЬ ТРАЕКТОРИЮ В 3D ✨"
        keyboard = {"inline_keyboard": [[{"text": button_text, "url": eyes_url}]]}
        
        return text, keyboard, random.choice(SPACE_PHOTOS), ast_id
    except Exception as e:
        print(f"❌ Ошибка досье: {e}")
        return None, None, None, None

def send():
    text, keyb, photo, ast_id = get_asteroid_data()
    if text:
        payload = {'chat_id': CHANNEL_NAME, 'photo': photo, 'caption': text, 'parse_mode': 'HTML', 'reply_markup': json.dumps(keyb)}
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto", data=payload)
        with open(DB_FILE, 'a', encoding='utf-8') as f: f.write(f"{ast_id}\n")

if __name__ == '__main__':
    send()
