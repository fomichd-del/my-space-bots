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
    """Получает данные и защищен от пустых полей (KeyError)"""
    url = f"https://api.nasa.gov/planetary/apod?api_key={NASA_API_KEY}"
    
    try:
        print("📡 Запрашиваю данные у NASA...")
        response = requests.get(url, timeout=25)
        res = response.json()
        
        if response.status_code != 200 or 'url' not in res:
            return None, None, None, False

        if res.get('media_type') != 'video':
            print("ℹ️ Сегодня не видео. Пропускаю.")
            return None, None, None, False

        raw_url = res.get('url', '')
        is_youtube = any(x in raw_url for x in ['youtube.com', 'youtu.be'])
        
        # Исправляем формат ссылки YouTube для лучшего превью
        if is_youtube:
            if 'embed/' in raw_url:
                video_id = raw_url.split('/embed/')[1].split('?')[0]
                final_url = f"https://www.youtube.com/watch?v={video_id}"
            else:
                final_url = raw_url
        else:
            # Для прямых ссылок .mp4 даем ссылку на страницу NASA (она лучше создает бар)
            now = datetime.now()
            date_str = now.strftime("%y%m%d")
            final_url = f"https://apod.nasa.gov/apod/ap{date_str}.html"

        # Безопасно получаем тексты
        title_en = str(res.get('title') or "Космическое видео дня")
        desc_en = str(res.get('explanation') or "Описание сегодня не предоставлено.")

        print(f"📝 Перевожу заголовок...")
        title_ru = translator.translate(title_en)
        
        # Перевод и обрезка описания
        sentences = desc_en.split('.')
        short_desc_en = '. '.join(sentences[:4]) + '.'
        desc_ru = translator.translate(short_desc_en)

        return final_url, title_ru, desc_ru, is_youtube
        
    except Exception as e:
        print(f"❌ Ошибка в обработке данных: {e}")
        return None, None, None, False

def send_to_telegram():
    video_url, title_ru, desc_ru, is_youtube = get_video_data()
    
    if not video_url:
        return

    # ФОРМИРУЕМ ПОСТ
    caption = (
        f"🎬 <b>ВИДЕО: {title_ru.upper()}</b>\n"
        f"🍿 <a href='{video_url}'><b>СМОТРЕТЬ РОЛИК</b></a>\n"
        f"─────────────────────\n\n"
        f"<b>О ЧЕМ РОЛИК:</b>\n"
        f"{desc_ru}\n\n"
        f"⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
        f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
    )

    print(f"📤 Отправляю в Telegram через ссылку: {video_url}")
    
    payload = {
        "chat_id": CHANNEL_NAME,
        "text": caption,
        "parse_mode": "HTML",
        "link_preview_options": {
            "url": video_url,             # Приоритет превью — видео
            "prefer_large_media": True,   # Большое окно
            "show_above_text": False      # Окно под текстом (как на твоем любимом варианте)
        }
    }
    
    base_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    r = requests.post(base_url, json=payload)
    
    if r.status_code == 200:
        print("✅ Пост опубликован!")
    else:
        print(f"❌ Ошибка: {r.text}")

if __name__ == '__main__':
    send_to_telegram()
