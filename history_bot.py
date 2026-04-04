import requests
import os
import random
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
    
    months_ru = [
        "Января", "Февраля", "Марта", "Апреля", "Мая", "Июня",
        "Июля", "Августа", "Сентября", "Октября", "Ноября", "Декабря"
    ]
    date_display = f"{day} {months_ru[month-1]}"

    # API Википедии
    url = f"https://en.wikipedia.org/api/rest_v1/feed/onthisday/all/{month}/{day}"
    
    # ВАЖНО: Добавляем User-Agent, чтобы не было ошибки 403
    headers = {
        'User-Agent': 'MarsBotHistory/1.0 (contact: your-email@example.com) Python-requests'
    }
    
    try:
        print(f"🌐 Ищу мировые события на {date_display}...")
        response = requests.get(url, headers=headers, timeout=25)
        
        if response.status_code != 200:
            print(f"❌ Ошибка API Википедии: {response.status_code}")
            return None, None

        data = response.json()
        events = data.get('selected', []) + data.get('events', [])
        
        # Ключевые слова для космоса
        keywords = ['space', 'launch', 'orbit', 'rocket', 'moon', 'satellite', 'gagarin', 'soyuz', 'apollo', 'vostok', 'nasa', 'roscosmos', 'astronomy']
        
        space_events = [e for e in events if any(k in e.get('text', '').lower() for k in keywords)]
        
        if not space_events:
            print(f"📭 На {date_display} космических дат в базе нет.")
            return None, None

        # Выбираем случайное
        event = random.choice(space_events)
        year = event.get('year')
        text_en = event.get('text')
        
        # Картинка
        img_url = "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=1200"
        if 'pages' in event and event['pages']:
            for page in event['pages']:
                if 'thumbnail' in page:
                    img_url = page['thumbnail']['source']
                    break

        print(f"📝 Перевожу событие {year} года...")
        text_ru = translator.translate(text_en)

        # Прячем ссылку в невидимый символ
        invisible_link = f'<a href="{img_url}">\u200b</a>'

        caption = (
            f"{invisible_link}📜 <b>ЭТОТ ДЕНЬ В ИСТОРИИ: {date_display.upper()}</b>\n"
            f"─────────────────────\n\n"
            f"📅 <b>Год: {year}</b>\n\n"
            f"🚀 <b>Что произошло:</b>\n{text_ru}\n\n"
            f"⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
            f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
        )
        
        return img_url, caption
        
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        return None, None

def send_to_telegram():
    img_url, caption = get_global_history()
    
    if not img_url:
        return

    print("📤 Отправляю пост со звуком...")
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    payload = {
        'chat_id': CHANNEL_NAME,
        'photo': img_url,
        'caption': caption,
        'parse_mode': 'HTML',
        'disable_notification': False  # Звук всегда включен
    }
    
    r = requests.post(url, data=payload)
    if r.status_code == 200:
        print("✅ Успешно!")
    else:
        print(f"❌ Ошибка Telegram: {r.text}")

if __name__ == '__main__':
    send_to_telegram()
