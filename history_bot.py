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

# 🚫 ЧЕРНЫЙ СПИСОК (Агрессия, политика, военщина)
STOP_WORDS = [
    'война', 'военный', 'битва', 'убит', 'казнен', 'президент', 'партия', 
    'революция', 'вторжение', 'армия', 'фронт', 'политика', 'договор', 
    'ссср', 'нато', 'сражение', 'захват', 'санкции', 'оружие', 'теракт', 
    'взрыв', 'атака', 'конфликт', 'министр', 'правительство', 'смерть', 
    'погиб', 'убийство', 'флот', 'база', 'штаб', 'боевой', 'ядерный', 
    'атомный', 'вооружение', 'солдат', 'генерал', 'осада', 'плен'
]

# ✅ БЕЛЫЙ СПИСОК (То, что мы ХОТИМ видеть)
GOOD_WORDS = [
    'космос', 'астроном', 'звезда', 'планета', 'открыт', 'изобретен', 
    'первый', 'ученый', 'экспедиция', 'полет', 'основан', 'построен', 
    'животное', 'искусство', 'музыка', 'картина', 'писатель', 'книга', 
    'природа', 'заповедник', 'археолог', 'культура', 'фестиваль'
]

def get_history_content():
    """Получает только добрые и познавательные события"""
    month = datetime.now().month
    day = datetime.now().day
    url = f"https://ru.wikipedia.org/api/rest_v1/feed/onthisday/events/{month}/{day}"
    
    try:
        res = requests.get(url, timeout=20).json()
        events = res.get('events', [])
        
        filtered_events = []
        for e in events:
            text = e.get('text', '').lower()
            
            # 1. Проверяем, нет ли запрещенных слов
            has_forbidden = any(word in text for word in STOP_WORDS)
            
            # 2. Проверяем, есть ли хотя бы одно "доброе" слово
            is_positive = any(word in text for word in GOOD_WORDS)
            
            if not has_forbidden and is_positive:
                filtered_events.append(e)

        if not filtered_events:
            print("⚠️ Ничего идеально подходящего не нашли. Ищем самое нейтральное...")
            # Если нет идеально добрых, берем любое, где вообще нет политики
            for e in events:
                text = e.get('text', '').lower()
                if not any(word in text for word in STOP_WORDS):
                    filtered_events.append(e)
                    if len(filtered_events) > 5: break

        if not filtered_events:
            return None, None

        # Выбираем главное событие (с фото) и пару фактов
        main_event = filtered_events[0]
        for e in filtered_events:
            if 'pages' in e and e['pages'][0].get('originalimage'):
                main_event = e
                break

        other_facts = []
        for e in filtered_events:
            if e != main_event and len(other_facts) < 2:
                fact_text = e.get('text', '')
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
    
    caption = (
        f"📜 <b>ЭТОТ ДЕНЬ В ИСТОРИИ</b>\n"
        f"📅 <b>{datetime.now().strftime('%d %B')} {year} года</b>\n"
        f"─────────────────────\n\n"
        f"<b>ИНТЕРЕСНОЕ СОБЫТИЕ:</b>\n"
        f"{text}\n\n"
    )
    
    if other_facts:
        caption += "<b>ЧТО ЕЩЕ ПРОИЗОШЛО:</b>\n"
        caption += "\n".join(other_facts) + "\n\n"
        
    caption += (
        f"⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
        f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
    )

    photo_url = None
    if 'pages' in main_event and main_event['pages'][0].get('originalimage'):
        photo_url = main_event['pages'][0]['originalimage']['source']

    base_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
    
    payload = {
        'chat_id': CHANNEL_NAME,
        'caption': caption,
        'parse_mode': 'HTML',
        'show_caption_above_media': True
    }
    
    if photo_url:
        payload['photo'] = photo_url
        requests.post(f"{base_url}/sendPhoto", data=payload)
    else:
        payload['text'] = caption
        requests.post(f"{base_url}/sendMessage", data=payload)

if __name__ == '__main__':
    send_to_telegram()
