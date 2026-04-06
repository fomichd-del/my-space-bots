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

# 🚀 ТОЛЬКО КОСМОС (Ключевые слова-маркеры)
SPACE_KEYWORDS = [
    'космос', 'ракета', 'спутник', 'астроном', 'планета', 'звезда', 
    'наса', 'nasa', 'байконур', 'гагарин', 'космонавт', 'астронавт', 
    'телескоп', 'хаббл', 'марсоход', 'луноход', 'орбита', 'мкс', 
    'аполлон', 'союз', 'запуск', 'открытие', 'вселенная', 'галактика'
]

# 🚫 ПОЛНЫЙ ЗАПРЕТ (Политика, война, базы)
STOP_WORDS = [
    'война', 'военный', 'армия', 'флот', 'битва', 'база', 'штаб', 
    'оружие', 'атака', 'конфликт', 'президент', 'политика', 'вторжение',
    'министр', 'правительство', 'санкции', 'плен', 'убит', 'смерть'
]

def get_space_history():
    """Ищет только космические события в мировой истории"""
    now = datetime.now()
    url = f"https://ru.wikipedia.org/api/rest_v1/feed/onthisday/events/{now.month}/{now.day}"
    
    try:
        print("📡 Ищу космические события в истории...")
        res = requests.get(url, timeout=20).json()
        all_events = res.get('events', [])
        
        space_events = []
        for e in all_events:
            text = e.get('text', '').lower()
            
            # Проверяем: это про космос и без политики?
            is_space = any(word in text for word in SPACE_KEYWORDS)
            no_politics = not any(word in text for word in STOP_WORDS)
            
            if is_space and no_politics:
                space_events.append(e)
        
        return space_events
    except Exception as e:
        print(f"❌ Ошибка API: {e}")
        return []

def send_to_telegram():
    events = get_space_history()
    
    if not events:
        print("📭 Сегодня чисто космических дат не найдено. Пропускаю пост.")
        return

    # Выбираем главное событие (лучше с картинкой)
    main_event = events[0]
    for e in events:
        if 'pages' in e and e['pages'][0].get('originalimage'):
            main_event = e
            break

    year = main_event.get('year')
    text = main_event.get('text', 'Нет описания')
    
    # Формируем структуру поста
    caption = (
        f"🚀 <b>КОСМИЧЕСКИЙ КАЛЕНДАРЬ</b>\n"
        f"📅 <b>{datetime.now().strftime('%d %B')} {year} года</b>\n"
        f"─────────────────────\n\n"
        f"<b>ГЛАВНОЕ СОБЫТИЕ:</b>\n"
        f"{text}\n\n"
    )

    # Добавляем дополнительные факты, если они есть
    if len(events) > 1:
        caption += "<b>ТАКЖЕ В ЭТОТ ДЕНЬ:</b>\n"
        for fact in events[1:3]: # Берем еще максимум 2 факта
            caption += f"• В {fact.get('year')} году: {fact.get('text')}\n"
        caption += "\n"

    caption += (
        f"⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
        f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
    )

    # Ищем фото
    photo_url = None
    try:
        if 'pages' in main_event and main_event['pages'][0].get('originalimage'):
            photo_url = main_event['pages'][0]['originalimage']['source']
    except:
        photo_url = None

    base_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
    
    # Отправляем
    if photo_url:
        payload = {
            'chat_id': CHANNEL_NAME,
            'photo': photo_url,
            'caption': caption,
            'parse_mode': 'HTML',
            'show_caption_above_media': True # Текст СВЕРХУ
        }
        r = requests.post(f"{base_url}/sendPhoto", data=payload)
    else:
        payload = {
            'chat_id': CHANNEL_NAME,
            'text': caption,
            'parse_mode': 'HTML',
            'link_preview_options': {'is_disabled': True} # Отключаем бар канала
        }
        r = requests.post(f"{base_url}/sendMessage", json=payload)

    if r.status_code == 200:
        print("✅ Космический календарь опубликован!")
    else:
        print(f"❌ Ошибка отправки: {r.text}")

if __name__ == '__main__':
    send_to_telegram()
