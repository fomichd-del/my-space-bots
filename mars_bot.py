import requests
import os
import random
import json
from datetime import datetime, timedelta

# ============================================================
# ⚙️ НАСТРОЙКИ
# ============================================================
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
NASA_API_KEY   = os.getenv('NASA_API_KEY') or "DEMO_KEY"
CHANNEL_NAME   = '@vladislav_space'

def get_mars_photo():
    """Ищет свежие фото, перебирая последние 7 дней и активные роверы."""
    # Используем только те марсоходы, которые работают сейчас
    active_rovers = ['perseverance', 'curiosity']
    
    # Проверяем последние 7 дней (NASA нужно время на обработку снимков)
    for day_offset in range(7):
        target_date = (datetime.now() - timedelta(days=day_offset)).strftime('%Y-%m-%d')
        
        # Перемешиваем роверы, чтобы контент был разным
        random.shuffle(active_rovers)
        
        for rover in active_rovers:
            print(f"🔍 Проверка {rover.capitalize()} за {target_date}...")
            url = f"https://api.nasa.gov/mars-photos/api/v1/rovers/{rover}/photos?earth_date={target_date}&api_key={NASA_API_KEY}"
            
            try:
                response = requests.get(url, timeout=15)
                if response.status_code == 200:
                    photos = response.json().get('photos', [])
                    if photos:
                        print(f"✅ Ура! Найдено {len(photos)} фото.")
                        return random.choice(photos)
            except Exception as e:
                print(f"⚠️ Ошибка сети: {e}")
                
    return None

def send_mars_post():
    """Формирует пост в стиле '3 факта' и отправляет в Telegram."""
    photo_data = get_mars_photo()
    
    if not photo_data:
        print("📭 Увы, за последнюю неделю новых фото не поступало.")
        return

    # Извлекаем данные
    img_url = photo_data.get('img_src')
    rover_name = photo_data['rover']['name']
    camera_name = photo_data['camera']['full_name']
    sol = photo_data['sol']
    earth_date = photo_data['earth_date']

    # 📋 ФОРМИРУЕМ 3 ФАКТА
    fact_1 = f"🤖 Марсоход: <b>{rover_name}</b>"
    fact_2 = f"📸 Камера: <b>{camera_name}</b>"
    fact_3 = f"☀️ День на Марсе (Sol): <b>{sol}</b>"

    text = (
        f"🪐 <b>ПРИВЕТ С КРАСНОЙ ПЛАНЕТЫ!</b>\n"
        f"─────────────────────\n\n"
        f"<b>ИНФОРМАЦИЯ:</b>\n\n"
        f"🔹 {fact_1}\n\n"
        f"🔹 {fact_2}\n\n"
        f"🔹 {fact_3}\n\n"
        f"📅 <i>Дата снимка: {earth_date}</i>\n\n"
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
    
    try:
        r = requests.post(api_url, data=payload)
        print(f"📡 Статус отправки в Telegram: {r.status_code}")
        if r.status_code != 200:
            print(f"📋 Ошибка: {r.text}")
    except Exception as e:
        print(f"❌ Критическая ошибка при отправке: {e}")

if __name__ == '__main__':
    print("--- 🏁 Запуск Mars Bot ---")
    send_mars_post()
    print("--- 🏁 Работа завершена ---")
