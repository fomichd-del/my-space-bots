import requests
import os
import json
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
    """Получает видео дня от NASA и делает ссылку понятной для Telegram"""
    url = f"https://api.nasa.gov/planetary/apod?api_key={NASA_API_KEY}"
    
    try:
        print("📡 Запрашиваю данные у NASA...")
        res = requests.get(url, timeout=20).json()
        
        if res.get('media_type') != 'video':
            print("ℹ️ Сегодня не видео. Пропускаю.")
            return None, None, None

        raw_url = res.get('url')
        
        # Превращаем техническую ссылку (embed) в стандартную ссылку YouTube
        # Это критично для того, чтобы плеер ("бар") появился внизу
        if 'youtube.com/embed/' in raw_url:
            video_id = raw_url.split('/')[-1].split('?')[0]
            url_video = f"https://www.youtube.com/watch?v={video_id}"
        else:
            url_video = raw_url

        title_en = res.get('title', 'Космическое видео')
        desc_en = res.get('explanation', '')

        print(f"📝 Перевожу заголовок...")
        title_ru = translator.translate(title_en)
        
        # Берем 4 предложения для описания
        sentences = desc_en.split('.')
        short_desc_en = '. '.join(sentences[:4]) + '.'
        desc_ru = translator.translate(short_desc_en)

        return url_video, title_ru, desc_ru
        
    except Exception as e:
        print(f"❌ Ошибка получения данных: {e}")
        return None, None, None

def send_to_telegram():
    url_video, title_ru, desc_ru = get_video_data()
    
    if not url_video:
        return

    # МАГИЯ: Используем специальный невидимый код &#8203; 
    # Мы ставим его в самом начале. Telegram увидит ссылку и создаст "бар", 
    # но в тексте поста ссылки НЕ БУДЕТ видно.
    invisible_link = f'<a href="{url_video}">&#8203;</a>'

    caption = (
        f"{invisible_link}🎬 <b>ВИДЕО: {title_ru.upper()}</b>\n"
        f"─────────────────────\n\n"
        f"<b>О ЧЕМ РОЛИК:</b>\n"
        f"{desc_ru}\n\n"
        f"⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
        f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
    )

    print(f"📤 Отправляю в Telegram...")
    base_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    
    payload = {
        'chat_id': CHANNEL_NAME,
        'text': caption,
        'parse_mode': 'HTML',
        'disable_web_page_preview': False  # Это ОБЯЗАТЕЛЬНО должно быть False
    }
    
    r = requests.post(base_url, data=payload)
    if r.status_code == 200:
        print("✅ Пост опубликован! Проверь плеер внизу.")
    else:
        print(f"❌ Ошибка Telegram: {r.text}")

if __name__ == '__main__':
    send_to_telegram()
