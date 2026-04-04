import requests
import os
import random
import json
from datetime import datetime
from deep_translator import GoogleTranslator

# ============================================================
# ⚙️ НАСТРОЙКИ
# ============================================================
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHANNEL_NAME   = '@vladislav_space'

translator = GoogleTranslator(source='auto', target='ru')

def get_global_history():
    """Ищет мировые космические события через Wikipedia API"""
    now = datetime.now()
    month = now.month
    day = now.day
    
    # Месяцы для заголовка
    months_ru = [
        "Января", "Февраля", "Марта", "Апреля", "Мая", "Июня",
        "Июля", "Августа", "Сентября", "Октября", "Ноября", "Декабря"
    ]
    date_display = f"{day} {months_ru[month-1]}"

    # API Википедии "В этот день" (на английском данных больше, поэтому берем оттуда и переводим)
    url = f"https://en.wikipedia.org/api/rest_v1/feed/onthisday/all/{month}/{day}"
    
    try:
        print(f"🌐 Ищу мировые события на {date_display}...")
        res = requests.get(url, timeout=20).json()
        events = res.get('selected', []) + res.get('events', [])
        
        # Ключевые слова для фильтрации космических событий
        space_keywords = [
            'space', 'launch', 'orbit', 'rocket', 'moon', 'planet', 'satellite', 
            'cosmonaut', 'astronaut', 'soyuz', 'apollo', 'vostok', 'nasa', 'esa', 
            'roscosmos', 'station', 'astronomy', 'telescope', 'gagarin'
        ]
        
        space_events = []
        for e in events:
            text = e.get('text', '').lower()
            if any(key in text for key in space_keywords):
                space_events.append(e)
        
        if not space_events:
            print(f"📭 Космических событий на {date_display} не найдено.")
            return None, None

        # Выбираем одно случайное событие
        event = random.choice(space_events)
        year = event.get('year')
        text_en = event.get('text')
        
        # Пытаемся достать фото из события, если оно есть
        img_url = "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=1200" # Запасное фото
        if 'pages' in event and event['pages']:
            for page in event['pages']:
                if 'thumbnail' in page:
                    img_url = page['thumbnail']['source']
                    break

        # Перевод
        print(f"📝 Перевожу событие из мировой истории...")
        text_ru = translator.translate(text_en)

        # Невидимая ссылка для чистоты
        invisible_link = f'<a href="{img_url}">\u200b</a>'

        caption = (
            f"{invisible_link}📜 <b>ЭТОТ ДЕНЬ В ИСТОРИИ: {date_display.upper()}</b>\n"
            f"─────────────────────\n\n"
            f"📅 <b>Год: {year}</b>\n\n"
            f"🚀 <b>Событие:</b>\n{text_ru}\n\n"
            f"⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
            f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
        )
        
        return img_url, caption
        
    except Exception as e:
        print(f"❌ Ошибка получения истории: {e}")
        return None, None

def send_to_telegram():
    img_url, caption = get_global_history()
    
    if not img_url:
        return

    print("📤 Отправляю мировой исторический пост...")
    base_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    
    payload = {
        'chat_id': CHANNEL_NAME,
        'photo': img_url,
        'caption': caption,
        'parse_mode': 'HTML',
        'disable_notification': False  # ВСЕГДА СО ЗВУКОМ
    }
    
    r = requests.post(base_url, data=payload)
    if r.status_code == 200:
        print("✅ Пост опубликован!")
    else:
        print(f"❌ Ошибка Telegram: {r.text}")

if __name__ == '__main__':
    send_to_telegram()
