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

# 🚀 КОСМИЧЕСКИЕ КЛЮЧИ (Для поиска во всех базах)
SPACE_TERMS = [
    'космос', 'ракета', 'спутник', 'планета', 'звезда', 'наса', 'байконур', 
    'гагарин', 'космонавт', 'астроном', 'орбита', 'мкс', 'space', 'nasa', 
    'rocket', 'satellite', 'planet', 'pioneer', 'voyager', 'apollo', 'soyuz', 
    'iss', 'shuttle', 'telescope', 'hubble', 'galaxy', 'discovery', 'moon'
]

# 🚫 СТОП-СЛОВА (Никакой политики, войн и баз)
STOP_WORDS = [
    'война', 'армия', 'битва', 'база', 'штаб', 'оружие', 'атака', 'конфликт', 
    'президент', 'политика', 'вторжение', 'министр', 'правительство', 'плен', 
    'убит', 'war', 'military', 'army', 'base', 'politics', 'killed', 'strike', 'syria'
]

def get_combined_history():
    """Собирает космические факты со всего мира (RU + EN базы)"""
    now = datetime.now()
    month, day = now.month, now.day
    
    # Ссылки на русскую и английскую базы
    urls = [
        f"https://ru.wikipedia.org/api/rest_v1/feed/onthisday/events/{month}/{day}",
        f"https://en.wikipedia.org/api/rest_v1/feed/onthisday/selected/{month}/{day}"
    ]
    
    found_events = {} # Используем словарь, чтобы избежать дублей по годам
    
    for url in urls:
        try:
            print(f"📡 Опрашиваю базу: {url}")
            r = requests.get(url, timeout=25)
            if r.status_code != 200: continue
            
            data = r.json()
            events = data.get('selected', []) + data.get('events', [])
            
            for e in events:
                year = e.get('year')
                text = e.get('text', '').lower()
                
                # Проверка: это про космос и без политики?
                is_space = any(word in text for word in SPACE_TERMS)
                no_politics = not any(word in text for word in STOP_WORDS)
                
                if is_space and no_politics:
                    # Если этого года еще нет в списке — добавляем
                    if year not in found_events:
                        found_events[year] = e
        except:
            continue
            
    # Сортируем по годам (от старых к новым)
    sorted_years = sorted(found_events.keys())
    return [found_events[y] for y in sorted_years]

def send_to_telegram():
    events = get_combined_history()
    
    if not events:
        print("📭 Космических событий на сегодня не найдено.")
        return

    # 1. Главное событие (берем самое раннее или с фото)
    main_event = events[0]
    for e in events:
        if 'pages' in e and e['pages'][0].get('originalimage'):
            main_event = e
            break

    year = main_event.get('year')
    # Переводим, если текст не на русском
    raw_text = main_event.get('text', '')
    text_ru = translator.translate(raw_text)
    
    # 2. Дополнительные факты (еще 3 интересных события)
    extra_facts = []
    for e in events:
        if e != main_event and len(extra_facts) < 3:
            f_year = e.get('year')
            f_text = translator.translate(e.get('text', ''))
            extra_facts.append(f"• <b>{f_year} год:</b> {f_text}")

    # ФОРМИРУЕМ ПОСТ
    caption = (
        f"🚀 <b>КОСМИЧЕСКАЯ ЛЕТОПИСЬ МИРА</b>\n"
        f"📅 <b>{datetime.now().strftime('%d %B')}</b>\n"
        f"─────────────────────\n\n"
        f"🌟 <b>ГЛАВНОЕ СОБЫТИЕ {year} ГОДА:</b>\n"
        f"{text_ru}\n\n"
    )

    if extra_facts:
        caption += "🔍 <b>ТАКЖЕ В ЭТОТ ДЕНЬ:</b>\n"
        caption += "\n".join(extra_facts) + "\n\n"

    caption += (
        f"⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
        f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
    )

    photo_url = None
    if 'pages' in main_event and main_event['pages'][0].get('originalimage'):
        photo_url = main_event['pages'][0]['originalimage']['source']

    base_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
    
    # Текст СВЕРХУ, фото/бар СНИЗУ
    if photo_url:
        payload = {
            'chat_id': CHANNEL_NAME,
            'photo': photo_url,
            'caption': caption,
            'parse_mode': 'HTML',
            'show_caption_above_media': True
        }
        requests.post(f"{base_url}/sendPhoto", data=payload)
    else:
        payload = {
            'chat_id': CHANNEL_NAME,
            'text': caption,
            'parse_mode': 'HTML',
            'link_preview_options': {'is_disabled': True}
        }
        requests.post(f"{base_url}/sendMessage", json=payload)

if __name__ == '__main__':
    send_to_telegram()
