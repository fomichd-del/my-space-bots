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
    """Получает видео от NASA и готовит лучшую ссылку для бара"""
    url = f"https://api.nasa.gov/planetary/apod?api_key={NASA_API_KEY}"
    
    try:
        print("📡 Запрашиваю данные у NASA...")
        res = requests.get(url, timeout=20).json()
        
        if res.get('media_type') != 'video':
            print("ℹ️ Сегодня не видео. Пропускаю.")
            return None, None, None

        raw_url = res.get('url', '')
        
        # Если это YouTube, чистим ссылку для лучшего превью
        if 'youtube.com' in raw_url or 'youtu.be' in raw_url:
            if 'embed/' in raw_url:
                video_id = raw_url.split('/embed/')[1].split('?')[0]
                url_for_preview = f"https://www.youtube.com/watch?v={video_id}"
            else:
                url_for_preview = raw_url
        else:
            # Для прямых файлов (как сегодня) лучше всего давать ссылку на страницу NASA
            # Телеграм идеально делает из неё "бар" с видео
            now = datetime.now()
            date_str = now.strftime("%y%m%d")
            url_for_preview = f"https://apod.nasa.gov/apod/ap{date_str}.html"

        title_ru = translator.translate(res.get('title', 'Космическое видео'))
        desc_en = res.get('explanation', '')
        desc_ru = translator.translate('. '.join(desc_en.split('.')[:4]) + '.')

        return url_for_preview, title_ru, desc_ru
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return None, None, None

def send_to_telegram():
    url_for_preview, title_ru, desc_ru = get_video_data()
    
    if not url_for_preview:
        return

    # Текст сообщения
    # Мы добавили "СМОТРЕТЬ РОЛИК", но основная красота будет в баре внизу
    caption = (
        f"🎬 <b>ВИДЕО: {title_ru.upper()}</b>\n"
        f"─────────────────────\n\n"
        f"🍿 <a href='{url_for_preview}'><b>СМОТРЕТЬ РОЛИК</b></a>\n\n"
        f"<b>О ЧЕМ ВИДЕО:</b>\n"
        f"{desc_ru}\n\n"
        f"⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
        f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
    )

    print(f"📤 Отправляю пост. Превью только для: {url_for_preview}")
    
    # КЛЮЧЕВОЙ МОМЕНТ:
    # Мы указываем конкретный URL для превью. Это УБИРАЕТ бар канала.
    payload = {
        "chat_id": CHANNEL_NAME,
        "text": caption,
        "parse_mode": "HTML",
        "link_preview_options": {
            "url": url_for_preview,       # Только это видео будет в баре
            "prefer_large_media": True,   # Сделать плеер большим
            "show_above_text": False      # Плеер будет внизу под текстом
        }
    }
    
    base_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    
    # Отправляем через JSON для точности настроек
    r = requests.post(base_url, json=payload)
    
    if r.status_code == 200:
        print("✅ Успешно! Проверь канал.")
    else:
        print(f"❌ Ошибка: {r.text}")

if __name__ == '__main__':
    send_to_telegram()
