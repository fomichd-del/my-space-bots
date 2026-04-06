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

def clean_youtube_url(raw_url):
    """
    Превращает любую ссылку (embed, short, и т.д.) в стандартную.
    Именно это заставит Telegram показать плеер (окно видео).
    """
    video_id = None
    
    # 1. Если это формат embed (как на твоем скриншоте)
    if 'youtube.com/embed/' in raw_url:
        video_id = raw_url.split('embed/')[1].split('?')[0].split('/')[0]
    # 2. Если это короткая ссылка youtu.be
    elif 'youtu.be/' in raw_url:
        video_id = raw_url.split('youtu.be/')[1].split('?')[0]
    # 3. Если это обычная ссылка с v=
    elif 'v=' in raw_url:
        video_id = raw_url.split('v=')[1].split('&')[0]
        
    if video_id:
        return f"https://www.youtube.com/watch?v={video_id}"
    return raw_url

def get_video_data():
    """Получает данные от NASA и готовит их для поста"""
    url = f"https://api.nasa.gov/planetary/apod?api_key={NASA_API_KEY}"
    
    try:
        print("📡 Запрашиваю данные у NASA...")
        res = requests.get(url, timeout=20).json()
        
        if res.get('media_type') != 'video':
            print("ℹ️ Сегодня не видео. Пропускаю.")
            return None, None, None

        # ОЧИЩАЕМ ССЫЛКУ ТУТ
        url_video = clean_youtube_url(res.get('url', ''))
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

    # В тексте только описание и ссылка на канал.
    # Ссылку на видео мы НЕ пишем текстом, она пойдет "под капот" превью.
    caption = (
        f"🎬 <b>ВИДЕО: {title_ru.upper()}</b>\n"
        f"─────────────────────\n\n"
        f"<b>О ЧЕМ РОЛИК:</b>\n"
        f"{desc_ru}\n\n"
        f"⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
        f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
    )

    print(f"📤 Отправляю в Telegram с ПРАВИЛЬНОЙ ссылкой: {url_video}")
    
    # Мы ПРИНУДИТЕЛЬНО говорим Telegram: "Делай окно (бар) только для YouTube!"
    payload = {
        'chat_id': CHANNEL_NAME,
        'text': caption,
        'parse_mode': 'HTML',
        'link_preview_options': {
            'url': url_video,             # Ссылка на видео (теперь правильная!)
            'prefer_large_media': True,   # Делаем окно видео БОЛЬШИМ
            'show_above_text': False,     # Окно будет ПОД текстом
            'is_disabled': False          # ПРОВЕРЯЕМ, что превью не выключено
        }
    }
    
    base_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    r = requests.post(base_url, json=payload)
    
    if r.status_code == 200:
        print("✅ УРА! Пост отправлен успешно.")
    else:
        print(f"❌ Ошибка API: {r.text}")

if __name__ == '__main__':
    send_to_telegram()
