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
    
    # Форматируем дату с ведущими нулями (04/04), иначе Википедия выдает 404
    month_padded = now.strftime("%m")
    day_padded = now.strftime("%d")
    
    months_ru = [
        "Января", "Февраля", "Марта", "Апреля", "Мая", "Июня",
        "Июля", "Августа", "Сентября", "Октября", "Ноября", "Декабря"
    ]
    date_display = f"{now.day} {months_ru[now.month-1]}"

    # Ссылка на API с правильным форматом MM/DD
    url = f"https://en.wikipedia.org/api/rest_v1/feed/onthisday/all/{month_padded}/{day_padded}"
    
    # ВАЖНО: Википедия ТРЕБУЕТ уникальный User-Agent, иначе выдает 403
    headers = {
        'User-Agent': 'VladSpaceBot/1.0 (https://t.me/vladislav_space; contact: admin@example.com)'
    }
    
    try:
        print(f"🌐 Запрашиваю события на {date_display} ({month_padded}/{day_padded})...")
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code != 200:
            print(f"❌ Ошибка API Википедии: {response.status_code}. Текст: {response.text[:100]}")
            return None, None

        data = response.json()
        # Собираем все типы событий в один список
        all_events = data.get('selected', []) + data.get('events', []) + data.get('births', [])
        
        # Ключевые слова для поиска космических событий
        keywords = [
            'space', 'launch', 'orbit', 'rocket', 'moon', 'satellite', 'gagarin', 
            'soyuz', 'apollo', 'vostok', 'nasa', 'roscosmos', 'astronomy', 'planet', 'telescope'
        ]
        
        space_events = [e for e in all_events if any(k in e.get('text', '').lower() for k in keywords)]
        
        if not space_events:
            print(f"📭 На {date_display} специфических космических дат нет. Беру самое интересное событие дня.")
            # Если про космос ничего нет, берем самое важное общее событие
            if data.get('selected'):
                event = random.choice(data['selected'])
            else:
                return None, None
        else:
            event = random.choice(space_events)

        year = event.get('year')
        text_en = event.get('text')
        
        # Ищем картинку
        img_url = "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=1200"
        if 'pages' in event and event['pages']:
            for page in event['pages']:
                if 'thumbnail' in page:
                    img_url = page['thumbnail']['source']
                    break

        print(f"📝 Перевожу событие {year} года...")
        text_ru = translator.translate(text_en)

        # Прячем ссылку в невидимый символ для чистоты текста
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
        print(f"❌ Ошибка: {e}")
        return None, None

def send_to_telegram():
    img_url, caption = get_global_history()
    
    if not img_url:
        print("📭 Нечего отправлять.")
        return

    print("📤 Отправляю в Telegram со звуком...")
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    payload = {
        'chat_id': CHANNEL_NAME,
        'photo': img_url,
        'caption': caption,
        'parse_mode': 'HTML',
        'disable_notification': False  # ЗВУК ВКЛЮЧЕН
    }
    
    r = requests.post(url, data=payload)
    if r.status_code == 200:
        print("✅ Пост успешно опубликован!")
    else:
        print(f"❌ Ошибка Telegram: {r.text}")

if __name__ == '__main__':
    send_to_telegram()
