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
    """Получает данные и определяет тип видео"""
    url = f"https://api.nasa.gov/planetary/apod?api_key={NASA_API_KEY}"
    
    try:
        print("📡 Запрашиваю данные у NASA...")
        res = requests.get(url, timeout=20).json()
        
        if res.get('media_type') != 'video':
            print("ℹ️ Сегодня не видео. Пропускаю.")
            return None, None, None, False

        raw_url = res.get('url', '')
        
        # Проверяем, YouTube это или прямой файл
        is_youtube = any(x in raw_url for x in ['youtube.com', 'youtu.be'])
        
        # Если YouTube, чистим ссылку
        if is_youtube:
            if 'embed/' in raw_url:
                video_id = raw_url.split('/embed/')[1].split('?')[0]
                final_url = f"https://www.youtube.com/watch?v={video_id}"
            else:
                final_url = raw_url
        else:
            final_url = raw_url # Оставляем прямую ссылку на .mp4

        title_ru = translator.translate(res.get('title', 'Космическое видео'))
        desc_en = res.get('explanation', '')
        desc_ru = translator.translate('. '.join(desc_en.split('.')[:4]) + '.')

        return final_url, title_ru, desc_ru, is_youtube
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return None, None, None, False

def send_to_telegram():
    video_url, title_ru, desc_ru, is_youtube = get_video_data()
    
    if not video_url:
        return

    # Формируем текст
    caption = (
        f"🎬 <b>ВИДЕО: {title_ru.upper()}</b>\n"
        f"─────────────────────\n\n"
        f"<b>О ЧЕМ РОЛИК:</b>\n"
        f"{desc_ru}\n\n"
        f"⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
        f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
    )

    base_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

    if is_youtube:
        # ВАРИАНТ ДЛЯ YOUTUBE (через ссылку и бар)
        print(f"📺 Отправляю YouTube плеер: {video_url}")
        payload = {
            "chat_id": CHANNEL_NAME,
            "text": caption,
            "parse_mode": "HTML",
            "link_preview_options": {
                "url": video_url,
                "prefer_large_media": True,
                "show_above_text": False  # Плеер под текстом
            }
        }
        r = requests.post(f"{base_url}/sendMessage", json=payload)
    else:
        # ВАРИАНТ ДЛЯ MP4 (загрузка файла напрямую)
        # show_caption_above_media=True делает текст СВЕРХУ, а видео СНИЗУ
        print(f"📹 Загружаю видеофайл напрямую: {video_url}")
        payload = {
            "chat_id": CHANNEL_NAME,
            "video": video_url,
            "caption": caption,
            "parse_mode": "HTML",
            "show_caption_above_media": True 
        }
        r = requests.post(f"{base_url}/sendVideo", data=payload)

    if r.status_code == 200:
        print("✅ ПОБЕДА! Видео в канале.")
    else:
        print(f"❌ Ошибка Telegram: {r.text}")

if __name__ == '__main__':
    send_to_telegram()
