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
    """Получает данные от NASA и готовит ссылки"""
    url = f"https://api.nasa.gov/planetary/apod?api_key={NASA_API_KEY}"
    
    try:
        print("📡 Запрашиваю данные у NASA...")
        res = requests.get(url, timeout=20).json()
        
        if res.get('media_type') != 'video':
            print("ℹ️ Сегодня не видео. Пропускаю.")
            return None, None, None

        raw_url = res.get('url', '')
        
        # Если это YouTube, делаем красивую ссылку
        if 'youtube.com' in raw_url or 'youtu.be' in raw_url:
            if 'embed/' in raw_url:
                video_id = raw_url.split('/embed/')[1].split('?')[0]
                video_url = f"https://www.youtube.com/watch?v={video_id}"
            else:
                video_url = raw_url
        else:
            # Если это прямой файл .mp4, даем ссылку на страницу NASA (она надежнее)
            now = datetime.now()
            date_str = now.strftime("%y%m%d")
            video_url = f"https://apod.nasa.gov/apod/ap{date_str}.html"

        title_ru = translator.translate(res.get('title', 'Космическое видео'))
        desc_en = res.get('explanation', '')
        desc_ru = translator.translate('. '.join(desc_en.split('.')[:4]) + '.')

        return video_url, title_ru, desc_ru
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return None, None, None

def send_to_telegram():
    video_url, title_ru, desc_ru = get_video_data()
    
    if not video_url:
        return

    # Текст сообщения без ссылок (чистый и красивый)
    caption = (
        f"🎬 <b>ВИДЕО: {title_ru.upper()}</b>\n"
        f"─────────────────────\n\n"
        f"<b>О ЧЕМ РОЛИК:</b>\n"
        f"{desc_ru}\n\n"
        f"⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
        f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
    )

    # Создаем кнопку под постом
    reply_markup = {
        "inline_keyboard": [[
            {
                "text": "СМОТРЕТЬ ВИДЕО 🚀", 
                "url": video_url
            }
        ]]
    }

    print(f"📤 Отправляю в Telegram с кнопкой: {video_url}")
    
    payload = {
        "chat_id": CHANNEL_NAME,
        "text": caption,
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
        "reply_markup": json.dumps(reply_markup) # Добавляем кнопку
    }
    
    base_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    r = requests.post(base_url, data=payload)
    
    if r.status_code == 200:
        print("✅ Пост с кнопкой опубликован!")
    else:
        print(f"❌ Ошибка: {r.text}")

if __name__ == '__main__':
    send_to_telegram()
