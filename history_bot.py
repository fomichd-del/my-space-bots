import requests
import os
import json
from datetime import datetime
from deep_translator import GoogleTranslator

# ============================================================
# ⚙️ НАСТРОЙКИ
# ============================================================
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHANNEL_NAME   = '@vladislav_space'

translator = GoogleTranslator(source='auto', target='ru')

# 🚀 КОСМИЧЕСКИЕ МАРКЕРЫ (для поиска)
SPACE_KEYWORDS = [
    'космос', 'ракета', 'спутник', 'астроном', 'планета', 'звезда', 
    'наса', 'nasa', 'байконур', 'гагарин', 'космонавт', 'астронавт', 
    'телескоп', 'хаббл', 'марсоход', 'луноход', 'орбита', 'мкс', 
    'аполлон', 'союз', 'шаттл', 'запуск', 'открытие', 'вселенная', 'space'
]

# 🚫 ЖЕСТКИЙ ЗАПРЕТ (война, политика, базы)
STOP_WORDS = [
    'война', 'военный', 'армия', 'флот', 'битва', 'база', 'штаб', 
    'оружие', 'атака', 'конфликт', 'президент', 'политика', 'вторжение',
    'министр', 'правительство', 'санкции', 'плен', 'убит', 'смерть', 'strike'
]

def get_space_history():
    """Ищет космические события. Сначала в RU, если нет - в EN Википедии"""
    now = datetime.now()
    month, day = now.month, now.day
    
    # 1. Пробуем русскую Википедию
    urls = [
        f"https://ru.wikipedia.org/api/rest_v1/feed/onthisday/events/{month}/{day}",
        f"https://en.wikipedia.org/api/rest_v1/feed/onthisday/events/{month}/{day}" # Резерв
    ]
    
    space_events = []
    
    for url in urls:
        try:
            print(f"📡 Запрос к API: {url}")
            response = requests.get(url, timeout=25)
            if response.status_code != 200:
                continue
                
            res = response.json()
            events = res.get('events', [])
            
            for e in events:
                text_to_check = e.get('text', '').lower()
                
                # Проверяем на космос и отсутствие политики
                is_space = any(word in text_to_check for word in SPACE_KEYWORDS)
                no_politics = not any(word in text_to_check for word in STOP_WORDS)
                
                if is_space and no_politics:
                    space_events.append(e)
            
            # Если нашли события в первой же базе, дальше не идем
            if space_events:
                print(f"✅ Найдено {len(space_events)} событий!")
                break
        except Exception as e:
            print(f"⚠️ Ошибка при чтении API: {e}")
            continue

    return space_events

def send_to_telegram():
    events = get_space_history()
    
    if not events:
        print("📭 Космических событий на сегодня не найдено.")
        return

    # Выбираем главное
    main_event = events[0]
    for e in events:
        if 'pages' in e and e['pages'][0].get('originalimage'):
            main_event = e
            break

    # Переводим, если пришло из английской базы
    raw_text = main_event.get('text', '')
    print("📝 Перевожу основной факт...")
    text_ru = translator.translate(raw_text)
    
    year = main_event.get('year')
    
    # Формируем пост
    caption = (
        f"🚀 <b>КОСМИЧЕСКИЙ КАЛЕНДАРЬ</b>\n"
        f"📅 <b>{datetime.now().strftime('%d %B')} {year} года</b>\n"
        f"─────────────────────\n\n"
        f"<b>ГЛАВНОЕ СОБЫТИЕ:</b>\n"
        f"{text_ru}\n\n"
    )

    # Добавляем доп. факты (с переводом)
    if len(events) > 1:
        caption += "<b>ТАКЖЕ В ЭТОТ ДЕНЬ:</b>\n"
        for fact in events[1:3]:
            f_text = translator.translate(fact.get('text', ''))
            caption += f"• В {fact.get('year')} году: {f_text}\n"
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
