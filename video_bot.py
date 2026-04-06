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
    """Получает данные и защищен от отсутствующих полей (KeyError)"""
    url = f"https://api.nasa.gov/planetary/apod?api_key={NASA_API_KEY}"
    
    try:
        print("📡 Запрашиваю данные у NASA...")
        response = requests.get(url, timeout=25)
        res = response.json()
        
        # Проверка: если NASA вернула ошибку вместо данных
        if 'error' in res or response.status_code != 200:
            print(f"❌ Ошибка NASA API: {res.get('msg', 'Неизвестная ошибка')}")
            return None, None, None, False

        if res.get('media_type') != 'video':
            print("ℹ️ Сегодня не видео. Пропускаю.")
            return None, None, None, False

        raw_url = res.get('url', '')
        is_youtube = any(x in raw_url for x in ['youtube.com', 'youtu.be'])
        
        if is_youtube:
            if 'embed/' in raw_url:
                video_id = raw_url.split('/embed/')[1].split('?')[0]
                final_url = f"https://www.youtube.com/watch?v={video_id}"
            else:
                final_url = raw_url
        else:
            final_url = raw_url

        # Безопасно получаем заголовок и описание (без KeyError)
        title_en = res.get('title', 'Космическое видео дня')
        desc_en = res.get('explanation', 'Описание сегодня не предоставлено.')

        print(f"📝 Перевожу: {title_en}")
        title_ru = translator.translate(title_en)
        
        # Сокращаем описание
        sentences = desc_en.split('.')
        short_desc_en = '. '.join(sentences[:4]) + '.'
        desc_ru = translator.translate(short_desc_en)

        return final_url, title_ru, desc_ru, is_youtube
        
    except Exception as e:
        print(f"❌ Критическая ошибка в get_video_data: {e}")
        return None, None, None, False

def send_to_telegram():
    video_url, title_ru, desc_ru, is_youtube = get_video_data()
    
    if not video_url:
        print("📭 Нечего отправлять.")
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

    try:
        if is_youtube:
            print(f"📺 Отправляю YouTube: {video_url}")
            payload = {
                "chat_id": CHANNEL_NAME,
                "text": caption,
                "parse_mode": "HTML",
                "link_preview_options": {
                    "url": video_url,
                    "prefer_large_media": True,
                    "show_above_text": True  # Текст СВЕРХУ для YouTube превью
                }
            }
            r = requests.post(f"{base_url}/sendMessage", json=payload)
        else:
            print(f"📹 Отправляю видеофайл: {video_url}")
            payload = {
                "chat_id": CHANNEL_NAME,
                "video": video_url,
                "caption": caption,
                "parse_mode": "HTML",
                "show_caption_above_media": True # Текст СВЕРХУ для файла
            }
            r = requests.post(f"{base_url}/sendVideo", data=payload)

        if r.status_code == 200:
            print("✅ Успешно доставлено!")
        else:
            print(f"❌ Ошибка Telegram: {r.text}")
            
    except Exception as e:
        print(f"❌ Ошибка при отправке: {e}")

if __name__ == '__main__':
    send_to_telegram()
