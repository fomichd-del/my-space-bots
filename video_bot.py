import requests
import os
import json
from datetime import datetime
from deep_translator import GoogleTranslator

# ============================================================
# ⚙️ НАСТРОЙКИ
# ============================================================
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
NASA_API_KEY   = os.getenv('NASA_API_KEY') or "DEMO_KEY"
CHANNEL_NAME   = '@vladislav_space'

translator = GoogleTranslator(source='auto', target='ru')

def get_video_data():
    """Получает данные от NASA и формирует надежные ссылки"""
    url = f"https://api.nasa.gov/planetary/apod?api_key={NASA_API_KEY}"
    
    try:
        print("📡 Запрашиваю данные у NASA...")
        res = requests.get(url, timeout=20).json()
        
        if res.get('media_type') != 'video':
            print("ℹ️ Сегодня не видео. Пропускаю.")
            return None, None, None

        # Ссылка на само видео (может быть YouTube или .mp4)
        video_url = res.get('url', '')
        
        # МАГИЯ: Создаем ссылку на СТРАНИЦУ APOD. 
        # Telegram лучше всего делает "бары" именно со страниц.
        now = datetime.now()
        date_str = now.strftime("%y%m%d")
        page_url = f"https://apod.nasa.gov/apod/ap{date_str}.html"

        title_ru = translator.translate(res.get('title', 'Космическое видео'))
        desc_en = res.get('explanation', '')
        desc_ru = translator.translate('. '.join(desc_en.split('.')[:4]) + '.')

        return page_url, title_ru, desc_ru
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return None, None, None

def send_to_telegram():
    page_url, title_ru, desc_ru = get_video_data()
    
    if not page_url:
        return

    # Невидимая ссылка на СТРАНИЦУ NASA в самом начале.
    # Это заставит Telegram просканировать страницу и найти видео.
    invisible_link = f'<a href="{page_url}">&#8203;</a>'

    caption = (
        f"{invisible_link}🎬 <b>ВИДЕО: {title_ru.upper()}</b>\n"
        f"─────────────────────\n\n"
        f"<b>О ЧЕМ РОЛИК:</b>\n"
        f"{desc_ru}\n\n"
        f"⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
        f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
    )

    print(f"📤 Отправляю пост через страницу: {page_url}")
    
    # Используем современные настройки превью
    payload = {
        "chat_id": CHANNEL_NAME,
        "text": caption,
        "parse_mode": "HTML",
        "link_preview_options": {
            "url": page_url,              # Ссылка на страницу APOD
            "prefer_large_media": True,   # Большое окно видео
            "show_above_text": False      # Окно под текстом
        }
    }
    
    base_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    r = requests.post(base_url, json=payload)
    
    if r.status_code == 200:
        print("✅ ПОБЕДА! Видео должно появиться в канале.")
    else:
        print(f"❌ Ошибка Telegram: {r.text}")

if __name__ == '__main__':
    send_to_telegram()
