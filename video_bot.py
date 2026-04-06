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
    """Получает видео дня от NASA и делает идеальную ссылку"""
    url = f"https://api.nasa.gov/planetary/apod?api_key={NASA_API_KEY}"
    
    try:
        print("📡 Запрашиваю данные у NASA...")
        res = requests.get(url, timeout=20).json()
        
        if res.get('media_type') != 'video':
            print("ℹ️ Сегодня не видео. Пропускаю.")
            return None, None, None

        raw_url = res.get('url')
        
        # Вырезаем ID видео для YouTube
        video_id = ""
        if 'youtube.com/embed/' in raw_url:
            video_id = raw_url.split('/embed/')[1].split('?')[0]
        elif 'youtu.be/' in raw_url:
            video_id = raw_url.split('youtu.be/')[1].split('?')[0]
        elif 'v=' in raw_url:
            video_id = raw_url.split('v=')[1].split('&')[0]
        
        url_video = f"https://www.youtube.com/watch?v={video_id}" if video_id else raw_url

        title_ru = translator.translate(res.get('title', 'Космическое видео'))
        desc_en = res.get('explanation', '')
        desc_ru = translator.translate('. '.join(desc_en.split('.')[:4]) + '.')

        return url_video, title_ru, desc_ru
        
    except Exception as e:
        print(f"❌ Ошибка получения данных: {e}")
        return None, None, None

def send_to_telegram():
    url_video, title_ru, desc_ru = get_video_data()
    
    if not url_video:
        return

    # Текст сообщения. Ссылку на видео НЕ пишем, она уйдет в настройки превью.
    caption = (
        f"🎬 <b>ВИДЕО: {title_ru.upper()}</b>\n"
        f"─────────────────────\n\n"
        f"<b>О ЧЕМ РОЛИК:</b>\n"
        f"{desc_ru}\n\n"
        f"⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
        f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
    )

    print(f"📤 Отправляю в Telegram. Цель: {url_video}")
    
    # ФОРМИРУЕМ ПРАВИЛЬНЫЙ ПАКЕТ ДАННЫХ
    # Используем параметр link_preview_options, чтобы убить превью канала
    payload = {
        'chat_id': CHANNEL_NAME,
        'text': caption,
        'parse_mode': 'HTML',
        'link_preview_options': {
            'url': url_video,             # Показываем только ЭТУ ссылку
            'prefer_large_media': True,   # Окно видео будет большим
            'show_above_text': False,     # Окно будет ПОД текстом
            'is_disabled': False          # ПРОВЕРЯЕМ, что превью включено
        }
    }
    
    base_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    
    # ВАЖНО: отправляем как JSON, а не как обычные поля
    r = requests.post(base_url, json=payload)
    
    if r.status_code == 200:
        print("✅ Пост улетел! Теперь Телеграм просто обязан показать видео.")
    else:
        print(f"❌ Ошибка API: {r.text}")

if __name__ == '__main__':
    send_to_telegram()
