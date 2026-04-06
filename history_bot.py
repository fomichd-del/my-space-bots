import requests
import os
from datetime import datetime
from deep_translator import GoogleTranslator

# ============================================================
# ⚙️ НАСТРОЙКИ
# ============================================================
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHANNEL_NAME   = '@vladislav_space'

translator = GoogleTranslator(source='auto', target='ru')

# 🌌 МАКСИМАЛЬНЫЙ КОСМИЧЕСКИЙ ПОИСК
SPACE_KEYWORDS = [
    'space', 'nasa', 'rocket', 'satellite', 'planet', 'star', 'astronomer',
    'pioneer', 'voyager', 'apollo', 'soyuz', 'shuttle', 'iss', 'orbit',
    'launch', 'telescope', 'hubble', 'galaxy', 'cosmos', 'comet', 'nebula',
    'asteroid', 'discovery', 'observed', 'moon', 'mars', 'jupiter', 'saturn',
    'supernova', 'observatory', 'cosmic', 'cosmology', 'spacewalk'
]

# 🚫 ФИЛЬТР АГРЕССИИ И ПОЛИТИКИ
STOP_WORDS = [
    'war', 'military', 'army', 'battle', 'killed', 'politics', 'weapon',
    'война', 'военный', 'армия', 'битва', 'убит', 'оружие', 'база', 'штаб'
]

def get_space_history():
    now = datetime.now()
    # Используем самую полную базу - английскую Wikipedia All
    url = f"https://en.wikipedia.org/api/rest_v1/feed/onthisday/all/{now.month}/{now.day}"
    
    print(f"📡 Сканирую историю Вселенной за {now.day}/{now.month}...")
    try:
        response = requests.get(url, timeout=30)
        if response.status_code != 200: return []
        data = response.json()
    except:
        return []

    # Собираем всё в одну кучу: избранное, обычные события и рождения ученых
    all_raw = data.get('selected', []) + data.get('events', []) + data.get('births', [])
    
    found_events = []
    for e in all_raw:
        text = e.get('text', '').lower()
        
        # Ищем космос и отсекаем политику
        is_space = any(word in text for word in SPACE_KEYWORDS)
        no_politics = not any(word in text for word in STOP_WORDS)
        
        if is_space and no_politics:
            found_events.append(e)
            
    return found_events

def send_to_telegram():
    events = get_space_history()
    
    if not events:
        print("📭 Космических событий на сегодня не найдено.")
        return

    # Выбираем главное (желательно с фото)
    main_event = events[0]
    for e in events:
        if 'pages' in e and e['pages'][0].get('originalimage'):
            main_event = e
            break

    year = main_event.get('year')
    raw_text = main_event.get('text', '')
    text_ru = translator.translate(raw_text)
    
    # Формируем пост
    caption = (
        f"🚀 <b>КОСМИЧЕСКИЙ КАЛЕНДАРЬ</b>\n"
        f"📅 <b>{datetime.now().strftime('%d %B')} {year} года</b>\n"
        f"─────────────────────\n\n"
        f"<b>ГЛАВНОЕ СОБЫТИЕ:</b>\n"
        f"{text_ru}\n\n"
    )

    # Добавляем другие факты (открытия, наблюдения и т.д.)
    other_facts = [e for e in events if e != main_event]
    if other_facts:
        caption += "<b>ЧТО ЕЩЕ УЗНАЛО ЧЕЛОВЕЧЕСТВО:</b>\n"
        for fact in other_facts[:3]: # Берем еще 3 факта
            f_year = fact.get('year')
            f_text = translator.translate(fact.get('text', ''))
            caption += f"• <b>{f_year}:</b> {f_text}\n"
        caption += "\n"

    caption += (
        f"⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
        f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
    )

    photo_url = None
    if 'pages' in main_event and main_event['pages'][0].get('originalimage'):
        photo_url = main_event['pages'][0]['originalimage']['source']

    base_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
    
    if photo_url:
        payload = {'chat_id': CHANNEL_NAME, 'photo': photo_url, 'caption': caption, 'parse_mode': 'HTML', 'show_caption_above_media': True}
        requests.post(f"{base_url}/sendPhoto", data=payload)
    else:
        payload = {'chat_id': CHANNEL_NAME, 'text': caption, 'parse_mode': 'HTML', 'link_preview_options': {'is_disabled': True}}
        requests.post(f"{base_url}/sendMessage", json=payload)
    
    print("✅ Космическая летопись отправлена!")

if __name__ == '__main__':
    send_to_telegram()
