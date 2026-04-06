import requests
import os
import json
import re
from datetime import datetime
from deep_translator import GoogleTranslator

# ============================================================
# ⚙️ НАСТРОЙКИ
# ============================================================
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
NASA_API_KEY   = os.getenv('NASA_API_KEY') or "DEMO_KEY"
CHANNEL_NAME   = '@vladislav_space'

translator = GoogleTranslator(source='auto', target='ru')

def get_video_id(url):
    """Вытаскивает ID видео из любой ссылки YouTube"""
    # Ищем 11 символов ID видео (например, Z_YpL-nK6p0)
    regex = r"(?:v=|\/embed\/|\/watch\?v=|\/\d+\/|\/vi\/|youtu\.be\/|https:\/\/www\.youtube\.com\/shorts\/|&v=|^|[^a-zA-Z0-9_-])([a-zA-Z0-9_-]{11})(?:[^a-zA-Z0-9_-]|$)"
    match = re.search(regex, url)
    return match.group(1) if match else None

def get_video_data():
    """Получает видео от NASA и готовит данные"""
    url = f"https://api.nasa.gov/planetary/apod?api_key={NASA_API_KEY}"
    
    try:
        print("📡 Запрашиваю данные у NASA...")
        res = requests.get(url, timeout=20).json()
        
        if res.get('media_type') != 'video':
            print("ℹ️ Сегодня не видео. Пропускаю.")
            return None, None, None

        raw_url = res.get('url', '')
        video_id = get_video_id(raw_url)
        
        if not video_id:
            print(f"❌ Не смог найти ID видео в ссылке: {raw_url}")
            return None, None, None

        # Делаем максимально "вкусную" ссылку для Телеграма
        url_video = f"https://www.youtube.com/watch?v={video_id}"
        
        title_ru = translator.translate(res.get('title', 'Космическое видео'))
        desc_en = res.get('explanation', '')
        desc_ru = translator.translate('. '.join(desc_en.split('.')[:4]) + '.')

        return url_video, title_ru, desc_ru
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return None, None, None

def send_to_telegram():
    url_video, title_ru, desc_ru = get_video_data()
    
    if not url_video:
        return

    # В самом начале ставим невидимый символ и маленькую иконку со ссылкой.
    # Это заставит Телеграм нарисовать окно видео.
    # Ссылку на канал внизу пишем просто текстом-ссылкой.
    
    caption = (
        f"🎬 <b>ВИДЕО: {title_ru.upper()}</b> <a href='{url_video}'>📺</a>\n"
        f"─────────────────────\n\n"
        f"<b>О ЧЕМ РОЛИК:</b>\n"
        f"{desc_ru}\n\n"
        f"⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
        f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
    )

    print(f"📤 Отправляю пост. Ссылка на видео: {url_video}")
    
    # Пакет настроек для Телеграма
    payload = {
        "chat_id": CHANNEL_NAME,
        "text": caption,
        "parse_mode": "HTML",
        "link_preview_options": {
            "url": url_video,
            "prefer_large_media": True,
            "show_above_text": False
        }
    }
    
    base_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    
    # Отправляем именно как JSON (это важно для новых настроек)
    r = requests.post(base_url, json=payload)
    
    if r.status_code == 200:
        print("✅ Пост отправлен! Если видео нет — Телеграм блокирует превью этого ролика.")
    else:
        print(f"❌ Ошибка API: {r.text}")

if __name__ == '__main__':
    send_to_telegram()
