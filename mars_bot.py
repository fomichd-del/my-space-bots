import requests
import os
import random
from datetime import datetime, timedelta

# ============================================================
# ⚙️ НАСТРОЙКИ
# ============================================================
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
NASA_API_KEY   = os.getenv('NASA_API_KEY') or "DEMO_KEY"
CHANNEL_NAME   = '@vladislav_space'

def get_mars_photo():
    """Ищет фото с марсоходов, проверяя последние несколько дней."""
    # Список марсоходов
    rovers = ['curiosity', 'perseverance', 'opportunity']
    
    # Пробуем найти фото за последние 3 дня (на случай задержки данных)
    for day_offset in range(4):
        target_date = (datetime.now() - timedelta(days=day_offset)).strftime('%Y-%m-%d')
        rover = random.choice(rovers)
        
        url = f"https://api.nasa.gov/mars-photos/api/v1/rovers/{rover}/photos?earth_date={target_date}&api_key={NASA_API_KEY}"
        
        print(f"🔍 Проверка {rover.capitalize()} за {target_date}...")
        response = requests.get(url)
        
        if response.status_code == 200:
            photos = response.json().get('photos', [])
            if photos:
                print(f"✅ Найдено фото: {len(photos)}")
                return random.choice(photos)
    
    return None

def send_mars_post():
    photo_data = get_mars_photo()
    
    if not photo_data:
        print("📭 Фотографий за последние дни не найдено.")
        return

    img_url = photo_data.get('img_src')
    rover_name = photo_data['rover']['name']
    camera_name = photo_data['camera']['full_name']
    sol = photo_data['sol']
    earth_date = photo_data['earth_date']

    # 📋 ФОРМИРУЕМ 3 ФАКТА В НАШЕМ СТИЛЕ
    fact_1 = f"🤖 Марсоход: <b>{rover_name}</b>"
    fact_2 = f"📸 Камера: <b>{camera_name}</b>"
    fact_3 = f"☀️ День миссии (Sol): <b>{sol}</b> (Дата: {earth_date})"

    text = (
        f"🪐 <b>ПРИВЕТ С МАРСА!</b>\n"
        f"─────────────────────\n\n"
        f"<b>ИНФОРМАЦИЯ:</b>\n\n"
        f"🔹 {fact_1}\n\n"
        f"🔹 {fact_2}\n\n"
        f"🔹 {fact_3}\n\n"
        f"⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
        f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
    )

    # Отправка в Telegram
    api_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    payload = {
        'chat_id': CHANNEL_NAME,
        'photo': img_url,
        'caption': text,
        'parse_mode': 'HTML'
    }
    
    r = requests.post(api_url, data=payload)
    print(f"📡 Статус отправки в Telegram: {r.status_code}")

if __name__ == '__main__':
    send_mars_post()
