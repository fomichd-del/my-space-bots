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
    """Получает данные и защищен от пустых полей"""
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
        
        if is_youtube:
            if 'embed/' in raw_url:
                video_id = raw_url.split('/embed/')[1].split('?')[0]
                final_url = f"https://www.youtube.com/watch?v={video_id}"
            else:
                final_url = raw_url
        else:
            final_url = raw_url

        title_en = str(res.get('title') or "Космическое видео")
        desc_en = str(res.get('explanation') or "Описание сегодня не предоставлено.")

        print(f"📝 Перевожу заголовок...")
        title_ru = translator.translate(title_en)
        
        # Перевод описания
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

    # ТЕПЕРЬ ССЫЛКА НАВЕРХУ, А КАНАЛА ВНИЗУ НЕТ
    caption = (
        f"🎬 <b>ВИДЕО: {title_ru.upper()}</b>\n"
        f"🍿 <a href='{video_url}'><b>СМОТРЕТЬ РОЛИК</b></a>\n"
        f"─────────────────────\n\n"
        f"<b>О ЧЕМ РОЛИК:</b>\n"
        f"{desc_ru}"
    )

    base_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

    if is_youtube:
        # Для YouTube: текст СВЕРХУ, видео СНИЗУ (через бар)
        print(f"📺 Отправляю YouTube бар...")
        payload = {
            "chat_id": CHANNEL_NAME,
            "text": caption,
            "parse_mode": "HTML",
            "link_preview_options": {
                "url": video_url,
                "prefer_large_media": True,
                "show_above_text": True  # Текст над видео
            }
        }
        requests.post(f"{base_url}/sendMessage", json=payload)
    else:
        # Для файлов .mp4: отправляем как видеофайл
        print(f"📹 Пробую отправить файл: {video_url}")
        payload = {
            "chat_id": CHANNEL_NAME,
            "video": video_url,
            "caption": caption,
            "parse_mode": "HTML",
            "show_caption_above_media": True # Текст над видео
        }
        r = requests.post(f"{base_url}/sendVideo", data=payload)
        
        # Если файл не прошел, шлем просто текстом с баром
        if r.status_code != 200:
            payload_fallback = {
                "chat_id": CHANNEL_NAME,
                "text": caption,
                "parse_mode": "HTML",
                "link_preview_options": {
                    "url": video_url,
                    "prefer_large_media": True,
                    "show_above_text": True
                }
            }
            requests.post(f"{base_url}/sendMessage", json=payload_fallback)

if __name__ == '__main__':
    send_to_telegram()
