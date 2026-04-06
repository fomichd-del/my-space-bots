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

# СПИСОК ЗАПРЕЩЕННЫХ ТЕМ (Политика и негатив)
STOP_WORDS = [
    'война', 'битва', 'убит', 'казнен', 'президент', 'партия', 
    'революция', 'вторжение', 'армия', 'фронт', 'политика', 
    'договор', 'ссср', 'нато', 'сражение', 'захват', 'санкции'
]

def get_history_content():
    """Получает главное событие и дополнительные факты дня"""
    month = datetime.now().month
    day = datetime.now().day
    url = f"https://ru.wikipedia.org/api/rest_v1/feed/onthisday/events/{month}/{day}"
    
    try:
        res = requests.get(url, timeout=20).json()
        events = res.get('events', [])
        
        # Фильтруем все мирные и интересные события
        peaceful_events = []
        for e in events:
            text = e.get('text', '').lower()
            if not any(word in text for word in STOP_WORDS):
                peaceful_events.append(e)

        if not peaceful_events:
            return None, None

        # 1. Главное событие (с картинкой, если есть)
        main_event = peaceful_events[0]
        for e in peaceful_events:
            if 'pages' in e and e['pages'][0].get('originalimage'):
                main_event = e
                break

        # 2. Дополнительные факты (еще 2-3 интересных события)
        other_facts = []
        for e in peaceful_events:
            if e != main_event and len(other_facts) < 3:
                # Берем только короткие и емкие факты
                fact_text = e.get('text', '')
                if len(fact_text) < 150:
                    other_facts.append(f"• В {e.get('year')} году: {fact_text}")

        return main_event, other_facts
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return None, None

def send_to_telegram():
    main_event, other_facts = get_history_content()
    if not main_event:
        return

    year = main_event.get('year')
    text = main_event.get('text')
    
    # ФОРМИРУЕМ ТЕКСТ ПОСТА
    caption = (
        f"📜 <b>ЭТОТ ДЕНЬ В ИСТОРИИ</b>\n"
        f"📅 <b>{datetime.now().strftime('%d %B')} {year} года</b>\n"
        f"─────────────────────\n\n"
        f"<b>ГЛАВНОЕ СОБЫТИЕ:</b>\n"
        f"{text}\n\n"
    )
    
    if other_facts:
        caption += "<b>ИНТЕРЕСНЫЕ ФАКТЫ ЭТОГО ДНЯ:</b>\n"
        caption += "\n".join(other_facts) + "\n\n"
        
    caption += (
        f"⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
        f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
    )

    # Картинка
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
            'parse_mode': 'HTML'
        }
        requests.post(f"{base_url}/sendMessage", data=payload)

if __name__ == '__main__':
    send_to_telegram()
