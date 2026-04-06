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
    """Получает видео от NASA (любого формата)"""
    url = f"https://api.nasa.gov/planetary/apod?api_key={NASA_API_KEY}"
    
    try:
        print("📡 Запрашиваю данные у NASA...")
        res = requests.get(url, timeout=20).json()
        
        if res.get('media_type') != 'video':
            print("ℹ️ Сегодня не видео. Пропускаю.")
            return None, None, None

        # Берем ссылку как есть (mp4 или youtube)
        url_video = res.get('url', '')
        
        # Если это YouTube в формате /embed/, чуть подправим для Telegram
        if 'youtube.com/embed/' in url_video:
            video_id = url_video.split('/embed/')[1].split('?')[0]
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

    # Делаем чистое сообщение без видимых ссылок
    caption = (
        f"🎬 <b>ВИДЕО: {title_ru.upper()}</b>\n"
        f"─────────────────────\n\n"
        f"<b>О ЧЕМ РОЛИК:</b>\n"
        f"{desc_ru}\n\n"
        f"⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
        f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
    )

    print(f"📤 Отправляю в Telegram: {url_video}")
    
    # Используем настройки превью, чтобы видео всегда было внизу в окошке
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
    r = requests.post(base_url, json=payload)
    
    if r.status_code == 200:
        print("✅ Пост отправлен!")
    else:
        print(f"❌ Ошибка: {r.text}")

if __name__ == '__main__':
    send_to_telegram()
