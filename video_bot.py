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

def get_video_data():
    """Получает видео от NASA и анализирует ссылку"""
    url = f"https://api.nasa.gov/planetary/apod?api_key={NASA_API_KEY}"
    
    try:
        print("📡 Запрашиваю данные у NASA...")
        res = requests.get(url, timeout=20).json()
        
        if res.get('media_type') != 'video':
            print("ℹ️ Сегодня в APOD не видео, а фото. Бот пропускает запуск.")
            return None, None, None

        raw_url = res.get('url', '')
        print(f"🔗 ССЫЛКА ОТ NASA: {raw_url}") # Это поможет нам увидеть проблему в логах

        # Чистим YouTube ссылки (разные форматы)
        video_id = None
        if 'youtube.com' in raw_url or 'youtu.be' in raw_url:
            regex = r"(?:v=|\/embed\/|\/watch\?v=|\/vi\/|youtu\.be\/|\/shorts\/)([a-zA-Z0-9_-]{11})"
            match = re.search(regex, raw_url)
            if match:
                video_id = match.group(1)
        
        if video_id:
            url_video = f"https://www.youtube.com/watch?v={video_id}"
            is_direct_file = False
        else:
            url_video = raw_url
            # Проверяем, не прямая ли это ссылка на файл (mp4, mov)
            is_direct_file = any(raw_url.lower().endswith(ext) for ext in ['.mp4', '.mov', '.avi'])

        title_ru = translator.translate(res.get('title', 'Космическое видео'))
        desc_en = res.get('explanation', '')
        desc_ru = translator.translate('. '.join(desc_en.split('.')[:4]) + '.')

        return url_video, title_ru, desc_ru, is_direct_file
        
    except Exception as e:
        print(f"❌ Ошибка при получении данных: {e}")
        return None, None, None, False

def send_to_telegram():
    url_video, title_ru, desc_ru, is_direct_file = get_video_data()
    
    if not url_video:
        return

    caption = (
        f"🎬 <b>ВИДЕО: {title_ru.upper()}</b>\n"
        f"─────────────────────\n\n"
        f"<b>О ЧЕМ РОЛИК:</b>\n"
        f"{desc_ru}\n\n"
        f"⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
        f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
    )

    base_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

    if is_direct_file:
        # Если NASA дала прямую ссылку на файл — отправляем как ВИДЕО
        print(f"📹 Отправляю как прямой видеофайл: {url_video}")
        payload = {
            'chat_id': CHANNEL_NAME,
            'video': url_video,
            'caption': caption,
            'parse_mode': 'HTML'
        }
        r = requests.post(f"{base_url}/sendVideo", data=payload)
    else:
        # Если это YouTube — отправляем через sendMessage с жесткой настройкой превью
        print(f"📺 Отправляю как ссылку YouTube: {url_video}")
        payload = {
            'chat_id': CHANNEL_NAME,
            'text': caption,
            'parse_mode': 'HTML',
            'link_preview_options': json.dumps({
                'url': url_video,
                'prefer_large_media': True,
                'show_above_text': False
            })
        }
        r = requests.post(f"{base_url}/sendMessage", data=payload)
    
    if r.status_code == 200:
        print("✅ Пост успешно отправлен!")
    else:
        print(f"❌ Ошибка Telegram (код {r.status_code}): {r.text}")

if __name__ == '__main__':
    send_to_telegram()
