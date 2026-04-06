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

# 🌌 КОСМИЧЕСКИЙ ГЛОССАРИЙ (Для поиска во всех базах)
SPACE_TERMS = [
    'space', 'nasa', 'rocket', 'satellite', 'planet', 'star', 'astronomer',
    'pioneer', 'voyager', 'apollo', 'soyuz', 'shuttle', 'iss', 'orbit',
    'launch', 'telescope', 'hubble', 'galaxy', 'cosmos', 'comet', 'nebula',
    'asteroid', 'discovery', 'observed', 'moon', 'mars', 'jupiter', 'saturn',
    'intelsat', 'challenger', 'exploration', 'cosmonaut', 'astronaut'
]

# 🚫 ЗАПРЕТНАЯ ЗОНА (Никакой агрессии и политики)
STOP_WORDS = [
    'war', 'military', 'army', 'battle', 'killed', 'politics', 'weapon',
    'война', 'военный', 'армия', 'битва', 'убит', 'оружие', 'база', 'штаб',
    'агрессия', 'удар', 'ракета томагавк', 'вторжение', 'конфликт'
]

def get_cosmic_history():
    now = datetime.now()
    month, day = now.month, now.day
    
    # Сначала идем в самую полную английскую базу
    urls = [
        f"https://en.wikipedia.org/api/rest_v1/feed/onthisday/selected/{month}/{day}",
        f"https://en.wikipedia.org/api/rest_v1/feed/onthisday/events/{month}/{day}",
        f"https://ru.wikipedia.org/api/rest_v1/feed/onthisday/events/{month}/{day}"
    ]
    
    found_events = []
    
    for url in urls:
        try:
            print(f"📡 Сканирую: {url}")
            r = requests.get(url, timeout=25)
            if r.status_code != 200: continue
            
            data = r.json()
            # Собираем события и рождения великих ученых
            batch = data.get('selected', []) + data.get('events', []) + data.get('births', [])
            
            for e in batch:
                text = e.get('text', '').lower()
                is_space = any(word in text for word in SPACE_TERMS)
                no_politics = not any(word in text for word in STOP_WORDS)
                
                if is_space and no_politics:
                    found_events.append(e)
            
            if len(found_events) > 3: break # Нашли достаточно
        except:
            continue
            
    return found_events

def send_to_telegram():
    events = get_cosmic_history()
    
    if not events:
        print("📭 Космических тайн на сегодня больше не найдено.")
        return

    # Выбираем центральное событие (лучше с картинкой)
    main_event = events[0]
    for e in events:
        if 'pages' in e and e['pages'][0].get('originalimage'):
            main_event = e
            break

    year = main_event.get('year')
    title_ru = translator.translate(main_event.get('text', ''))
    
    # Собираем остальные факты
    extra_facts = []
    for e in events:
        if e != main_event and len(extra_facts) < 3:
            f_year = e.get('year')
            f_text = translator.translate(e.get('text', ''))
            extra_facts.append(f"• <b>{f_year}:</b> {f_text}")

    # Формируем пост
    caption = (
        f"🚀 <b>КОСМИЧЕСКАЯ ЛЕТОПИСЬ</b>\n"
        f"📅 <b>{datetime.now().strftime('%d %B')}</b>\n"
        f"─────────────────────\n\n"
        f"🌟 <b>ГЛАВНОЕ СОБЫТИЕ {year} ГОДА:</b>\n"
        f"{title_ru}\n\n"
    )

    if extra_facts:
        caption += "🔍 <b>ДРУГИЕ ФАКТЫ ЭТОГО ДНЯ:</b>\n"
        caption += "\n".join(extra_facts) + "\n\n"

    caption += (
        f"⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
        f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
    )

    photo_url = None
    if 'pages' in main_event and main_event['pages'][0].get('originalimage'):
        photo_url = main_event['pages'][0]['originalimage']['source']

    base_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
    
    # Отправляем фото или текст (всегда текст СВЕРХУ)
    if photo_url:
        payload = {'chat_id': CHANNEL_NAME, 'photo': photo_url, 'caption': caption, 'parse_mode': 'HTML', 'show_caption_above_media': True}
        requests.post(f"{base_url}/sendPhoto", data=payload)
    else:
        payload = {'chat_id': CHANNEL_NAME, 'text': caption, 'parse_mode': 'HTML', 'link_preview_options': {'is_disabled': True}}
        requests.post(f"{base_url}/sendMessage", json=payload)

if __name__ == '__main__':
    send_to_telegram()
