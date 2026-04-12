import requests
import os
import json
import time
from datetime import datetime
from deep_translator import GoogleTranslator

# ============================================================
# ⚙️ НАСТРОЙКИ
# ============================================================
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
NASA_API_KEY   = os.getenv('NASA_API_KEY') or "DEMO_KEY"
CHANNEL_NAME   = '@vladislav_space'
DB_FILE        = "db_video.txt" # НОВОЕ ИМЯ ПАМЯТИ

translator = GoogleTranslator(source='auto', target='ru')

def get_video_data():
    url = f"https://api.nasa.gov/planetary/apod?api_key={NASA_API_KEY}"
    
    # ПЫТАЕМСЯ ДОСТУЧАТЬСЯ 3 РАЗА
    for attempt in range(3):
        try:
            print(f"📡 Запрос к NASA (Попытка {attempt + 1})...")
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                res = response.json()
                if res.get('media_type') != 'video':
                    print("ℹ️ Сегодня не видео. Пропускаю.")
                    return None, None, None, False, None
                
                current_date = res.get('date')

                # Проверка памяти
                if os.path.exists(DB_FILE):
                    with open(DB_FILE, 'r', encoding='utf-8') as f:
                        if f.read().strip() == current_date:
                            print(f"✋ Видео за {current_date} уже было.")
                            return None, None, None, False, None
                
                return res, current_date
            
            print(f"⚠️ NASA ответила ошибкой {response.status_code}. Ждем...")
            time.sleep(5) # Пауза перед следующей попыткой
            
        except Exception as e:
            print(f"❌ Ошибка при попытке {attempt + 1}: {e}")
            time.sleep(5)
            
    print("❌ Все попытки исчерпаны. Сервер NASA не отвечает.")
    return None, None

def send_to_telegram():
    res_data, video_date = get_video_data()
    
    if not res_data:
        return

    raw_url = res_data.get('url', '')
    is_youtube = any(x in raw_url for x in ['youtube.com', 'youtu.be'])
    
    # Формирование ссылки без бэкслешей внутри f-строк
    if is_youtube:
        if 'embed/' in raw_url:
            v_id = raw_url.split('/embed/')[1].split('?')[0]
            final_url = f"https://www.youtube.com/watch?v={v_id}"
        else:
            final_url = raw_url
    else:
        # Для других видео берем ссылку на страницу APOD
        clean_date = video_date[2:].replace('-', '')
        final_url = f"https://apod.nasa.gov/apod/ap{clean_date}.html"

    # Перевод
    title_en = res_data.get('title', 'Космическое видео дня')
    title_ru = translator.translate(title_en)
    
    desc_en = res_data.get('explanation', '')
    short_desc_en = '. '.join(desc_en.split('.')[:4]) + '.'
    desc_ru = translator.translate(short_desc_en)

    caption = (
        f"🎬 <b>ВИДЕО: {title_ru.upper()}</b>\n"
        f"🍿 <a href='{final_url}'><b>СМОТРЕТЬ РОЛИК</b></a>\n"
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
            "url": final_url, 
            "prefer_large_media": True
        }
    }
    
    r = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", json=payload)
    
    if r.status_code == 200:
        # Сохраняем дату в файл памяти
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            f.write(video_date)
        print("✅ Пост опубликован!")
    else:
        print(f"❌ Ошибка Telegram: {r.text}")

if __name__ == '__main__':
    send_to_telegram()
