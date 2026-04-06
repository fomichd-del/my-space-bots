import requests
import os
from datetime import datetime, timedelta
from deep_translator import GoogleTranslator

# ============================================================
# ⚙️ НАСТРОЙКИ
# ============================================================
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
NASA_API_KEY   = os.getenv('NASA_API_KEY') or "DEMO_KEY"
CHANNEL_NAME   = '@vladislav_space'

translator = GoogleTranslator(source='auto', target='ru')

def get_video_data():
    """Получает видео дня от NASA и очищает ссылку"""
    url = f"https://api.nasa.gov/planetary/apod?api_key={NASA_API_KEY}"
    
    try:
        print("📡 Запрашиваю данные у NASA...")
        res = requests.get(url, timeout=20).json()
        
        if res.get('media_type') != 'video':
            print("ℹ️ Сегодня не видео. Пропускаю.")
            return None, None, None

        raw_url = res.get('url')
        
        # Вырезаем ID видео и делаем стандартную ссылку YouTube
        video_id = ""
        if 'youtube.com/embed/' in raw_url:
            video_id = raw_url.split('/embed/')[1].split('?')[0]
        elif 'youtu.be/' in raw_url:
            video_id = raw_url.split('youtu.be/')[1].split('?')[0]
        elif 'v=' in raw_url:
            video_id = raw_url.split('v=')[1].split('&')[0]
        
        if video_id:
            # Стандартная ссылка, которую Telegram понимает на 100%
            url_video = f"https://www.youtube.com/watch?v={video_id}"
        else:
            url_video = raw_url

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

    # 1. Ссылка на видео прячется в невидимый символ &#8203; в самом начале
    # 2. Ссылку на канал внизу мы делаем так, чтобы Telegram её игнорировал (без превью)
    
    invisible_link = f'<a href="{url_video}">&#8203;</a>'

    caption = (
        f"{invisible_link}🎬 <b>ВИДЕО: {title_ru.upper()}</b>\n"
        f"─────────────────────\n\n"
        f"<b>О ЧЕМ РОЛИК:</b>\n"
        f"{desc_ru}\n\n"
        f"⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
        f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
    )

    print(f"📤 Отправляю в Telegram. Ссылка для плеера: {url_video}")
    base_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    
    # Мы используем классический метод, но с жестким указанием не делать превью для канала
    payload = {
        'chat_id': CHANNEL_NAME,
        'text': caption,
        'parse_mode': 'HTML',
        'disable_web_page_preview': False # Разрешаем превью (для видео)
    }
    
    r = requests.post(base_url, data=payload)
    if r.status_code == 200:
        print("✅ Пост опубликован!")
    else:
        print(f"❌ Ошибка Telegram: {r.text}")

if __name__ == '__main__':
    send_to_telegram()
