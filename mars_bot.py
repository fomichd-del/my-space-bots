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
    """Ищет свежие фото, а если их нет — вытягивает из архива NASA."""
    active_rovers = ['perseverance', 'curiosity']
    
    # 1. Поиск за неделю
    for day_offset in range(7):
        target_date = (datetime.now() - timedelta(days=day_offset)).strftime('%Y-%m-%d')
        random.shuffle(active_rovers)
        for rover in active_rovers:
            print(f"🔍 Проверка {rover} за {target_date}...")
            url = f"https://api.nasa.gov/mars-photos/api/v1/rovers/{rover}/photos?earth_date={target_date}&api_key={NASA_API_KEY}"
            try:
                response = requests.get(url, timeout=15)
                if response.status_code == 200:
                    photos = response.json().get('photos', [])
                    if photos:
                        print(f"✅ Найдено свежее фото ровера {rover}!")
                        return random.choice(photos), False
            except Exception as e:
                print(f"⚠️ Ошибка при проверке {rover}: {e}")

    # 2. План Б: Latest Photos
    print("⏳ Свежих фото за неделю нет. Ищу в архиве последних снимков...")
    rover = random.choice(active_rovers)
    url = f"https://api.nasa.gov/mars-photos/api/v1/rovers/{rover}/latest_photos?api_key={NASA_API_KEY}"
    
    try:
        response = requests.get(url, timeout=15)
        print(f"📡 Запрос к архиву {rover}: Статус {response.status_code}")
        data = response.json()
        
        # Проверяем, есть ли фотографии в списке
        if 'latest_photos' in data and data['latest_photos']:
            print(f"📦 План Б сработал! Фото ровера {rover} получено.")
            return random.choice(data['latest_photos']), True
        else:
            print(f"📭 В архиве {rover} тоже пусто.")
    except Exception as e:
        print(f"❌ Ошибка в Плане Б: {e}")
                
    return None, False

def send_mars_post():
    photo, is_archive = get_mars_photo()
    
    if not photo:
        print("🛑 Сообщение не отправлено: фото не найдено ни в свежем, ни в архивном списке.")
        return

    # Данные снимка
    rover = photo['rover']['name']
    date = photo['earth_date']
    sol = photo['sol']
    cam = photo['camera']['full_name']
    
    # Исправляем ссылку (некоторые роверы присылают http вместо https)
    img = photo['img_src']
    if img.startswith('http://'):
        img = img.replace('http://', 'https://', 1)

    title = "📂 АРХИВНОЕ ФОТО" if is_archive else "🆕 СВЕЖИЙ КАДР С МАРСА"
    
    text = (
        f"🪐 <b>{title}</b>\n"
        f"─────────────────────\n\n"
        f"🤖 Ровер: <b>{rover}</b>\n"
        f"📸 Камера: <b>{cam}</b>\n"
        f"📅 Дата: <b>{date}</b> (Sol {sol})\n\n"
        f"⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
        f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
    )

    api_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    payload = {'chat_id': CHANNEL_NAME, 'photo': img, 'caption': text, 'parse_mode': 'HTML'}
    
    try:
        r = requests.post(api_url, data=payload)
        print(f"📡 Статус отправки в Telegram: {r.status_code}")
        if r.status_code != 200:
            print(f"📋 Ответ Telegram: {r.text}")
    except Exception as e:
        print(f"❌ Ошибка при отправке в Telegram: {e}")

if __name__ == '__main__':
    print("--- 🏁 Запуск Mars Bot ---")
    send_message = send_mars_post()
    print("--- 🏁 Работа завершена ---")
