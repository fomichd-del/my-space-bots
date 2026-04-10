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
DB_FILE        = "last_video_date.txt" # Файл памяти

translator = GoogleTranslator(source='auto', target='ru')

def get_video_data():
    """Получает данные о видео дня от NASA"""
    url = f"https://api.nasa.gov/planetary/apod?api_key={NASA_API_KEY}"
    
    try:
        print("📡 Запрашиваю данные у NASA...")
        response = requests.get(url, timeout=25)
        res = response.json()
        
        if response.status_code != 200 or 'url' not in res:
            return None, None, None, False, None

        # Проверяем тип контента
        if res.get('media_type') != 'video':
            print("ℹ️ Сегодня не видео. Пропускаю.")
            return None, None, None, False, None

        current_date = res.get('date')

        # --- ПРОВЕРКА НА ПОВТОРЫ ---
        if os.path.exists(DB_FILE):
            with open(DB_FILE, 'r', encoding='utf-8') as f:
                if f.read().strip() == current_date:
                    print(f"✋ Видео за {current_date} уже было опубликовано.")
                    return None, None, None, False, None

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
            # Для прямых ссылок .mp4 даем ссылку на страницу NASA
            now = datetime.now()
            date_str = now.strftime("%y%m%d")
            final_url = f"https://apod.nasa.gov/apod/ap{date_str}.html"

        # Получаем и переводим тексты
        title_en = str(res.get('title') or "Космическое видео дня")
        desc_en = str(res.get('explanation') or "Описание сегодня не предоставлено.")

        print(f"📝 Перевожу заголовок...")
        title_ru = translator.translate(title_en)
        
        # Перевод и обрезка описания (первые 4 предложения)
        sentences = desc_en.split('.')
        short_desc_en = '. '.join(sentences[:4]) + '.'
        desc_ru = translator.translate(short_desc_en)

        return final_url, title_ru, desc_ru, is_youtube, current_date
        
    except Exception as e:
        print(f"❌ Ошибка в обработке данных: {e}")
        return None, None, None, False, None

def send_to_telegram():
    video_url, title_ru, desc_ru, is_youtube, video_date = get_video_data()
    
    if not video_url:
        return

    # ФОРМИРУЕМ ПОСТ (без бара)
    caption = (
        f"🎬 <b>ВИДЕО: {title_ru.upper()}</b>\n"
        f"🍿 <a href='{video_url}'><b>СМОТРЕТЬ РОЛИК</b></a>\n"
        f"─────────────────────\n\n"
        f"<b>О ЧЕМ РОЛИК:</b>\n"
        f"{desc_ru}\n\n"
        f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
    )

    print(f"📤 Отправляю в Telegram: {video_url}")
    
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
        # Записываем дату в память только после успешной отправки
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            f.write(video_date)
        print("✅ Пост опубликован и дата сохранена!")
    else:
        print(f"❌ Ошибка: {r.text}")

if __name__ == '__main__':
    send_to_telegram()
