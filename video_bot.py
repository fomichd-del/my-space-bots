import requests
import os
import json
from datetime import datetime
from deep_translator import GoogleTranslator

# ============================================================
# ⚙️ НАСТРОЙКИ
# ============================================================
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
# Приоритет всегда твоему ключу из Secrets
NASA_API_KEY   = os.getenv('NASA_API_KEY')
CHANNEL_NAME   = '@vladislav_space'
DB_FILE        = "last_video_date.txt"

translator = GoogleTranslator(source='auto', target='ru')

def get_video_data():
    """Получает данные и обрабатывает ошибки сервера"""
    if not NASA_API_KEY:
        print("⚠️ ВНИМАНИЕ: NASA_API_KEY не найден в Secrets. Использую DEMO_KEY.")
        api_key = "DEMO_KEY"
    else:
        api_key = NASA_API_KEY

    url = f"https://api.nasa.gov/planetary/apod?api_key={api_key}"
    
    try:
        print("📡 Запрашиваю данные у NASA...")
        response = requests.get(url, timeout=30)
        
        # Проверяем статус-код (200 - успех)
        if response.status_code != 200:
            print(f"❌ Ошибка сервера NASA: Код {response.status_code}")
            print(f"📝 Ответ сервера: {response.text[:100]}")
            return None, None, None, False, None

        # Проверяем, не пустой ли ответ
        if not response.text.strip():
            print("❌ Ошибка: Сервер NASA прислал пустой ответ.")
            return None, None, None, False, None

        try:
            res = response.json()
        except json.JSONDecodeError as e:
            print(f"❌ Ошибка декодирования JSON: {e}")
            print(f"📝 Содержимое ответа: {response.text[:200]}")
            return None, None, None, False, None

        # Проверяем тип контента
        if res.get('media_type') != 'video':
            print("ℹ️ Сегодня в APOD не видео. Пропускаю.")
            return None, None, None, False, None

        current_date = res.get('date')

        # --- ПРОВЕРКА НА ПОВТОРЫ ---
        if os.path.exists(DB_FILE):
            with open(DB_FILE, 'r', encoding='utf-8') as f:
                if f.read().strip() == current_date:
                    print(f"✋ Видео за {current_date} уже опубликовано.")
                    return None, None, None, False, None

        raw_url = res.get('url', '')
        is_youtube = any(x in raw_url for x in ['youtube.com', 'youtu.be'])
        
        # Исправляем формат ссылки YouTube
        if is_youtube:
            if 'embed/' in raw_url:
                video_id = raw_url.split('/embed/')[1].split('?')[0]
                final_url = f"https://www.youtube.com/watch?v={video_id}"
            else:
                final_url = raw_url
        else:
            now = datetime.now()
            date_str = now.strftime("%y%m%d")
            final_url = f"https://apod.nasa.gov/apod/ap{date_str}.html"

        # Перевод
        title_ru = translator.translate(res.get('title', 'Космическое видео'))
        desc_en = res.get('explanation', '')
        sentences = desc_en.split('.')
        short_desc_en = '. '.join(sentences[:4]) + '.'
        desc_ru = translator.translate(short_desc_en)

        return final_url, title_ru, desc_ru, is_youtube, current_date
        
    except Exception as e:
        print(f"❌ Критическая ошибка в обработке: {e}")
        return None, None, None, False, None

def send_to_telegram():
    video_url, title_ru, desc_ru, is_youtube, video_date = get_video_data()
    
    if not video_url:
        return

    caption = (
        f"🎬 <b>ВИДЕО: {title_ru.upper()}</b>\n"
        f"🍿 <a href='{video_url}'><b>СМОТРЕТЬ РОЛИК</b></a>\n"
        f"─────────────────────\n\n"
        f"<b>О ЧЕМ РОЛИК:</b>\n"
        f"{desc_ru}\n\n"
        f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
    )

    payload = {
        "chat_id": CHANNEL_NAME,
        "text": caption,
        "parse_mode": "HTML",
        "link_preview_options": {
            "url": video_url,
            "prefer_large_media": True,
            "show_above_text": False
        }
    }
    
    base_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    r = requests.post(base_url, json=payload)
    
    if r.status_code == 200:
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            f.write(video_date)
        print("✅ Пост опубликован!")
    else:
        print(f"❌ Ошибка Telegram: {r.text}")

if __name__ == '__main__':
    send_to_telegram()
