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
    """Ищет свежие фото за последние 7 дней или берет последние доступные."""
    active_rovers = ['perseverance', 'curiosity']
    
    # 1. Основной поиск: за последнюю неделю
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
                        return random.choice(photos), False
            except: continue

    # 2. План Б: Загрузка самых последних фото из архива
    print("⏳ Свежих фото нет. Беру последние доступные снимки...")
    rover = random.choice(active_rovers)
    url = f"https://api.nasa.gov/mars-photos/api/v1/rovers/{rover}/latest_photos?api_key={NASA_API_KEY}"
    try:
        res = requests.get(url, timeout=15).json()
        return random.choice(res['latest_photos']), True
    except: return None, False

def send_mars_post():
    """Формирует пост без дополнительных фактов и отправляет в Telegram."""
    photo, is_archive = get_mars_photo()
    if not photo: return

    # Данные снимка
    rover = photo['rover']['name']
    date = photo['earth_date']
    sol = photo['sol']
    cam = photo['camera']['full_name']
    img = photo['img_src']

    # Метка для архива
    title = "📂 АРХИВНОЕ ФОТО" if is_archive else "🆕 СВЕЖИЙ КАДР С МАРСА"
    
    # Лаконичный текст поста
    text = (
        f"🪐 <b>{title}</b>\n"
        f"─────────────────────\n\n"
        f"🤖 Ровер: <b>{rover}</b>\n"
        f"📸 Камера: <b>{cam}</b>\n"
        f"📅 Дата: <b>{date}</b> (Sol {sol})\n\n"
        f"⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
        f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
    )

    # Отправка фото
    requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto", 
                  data={'chat_id': CHANNEL_NAME, 'photo': img, 'caption': text, 'parse_mode': 'HTML'})

if __name__ == '__main__':
    print("--- 🏁 Запуск Mars Bot (Minimal) ---")
    send_mars_post()
    print("--- 🏁 Работа завершена ---")
