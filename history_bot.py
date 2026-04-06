import requests
import os
import json
from datetime import datetime
from deep_translator import GoogleTranslator

# ============================================================
# ⚙️ НАСТРОЙКИ
# ============================================================
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHANNEL_NAME   = '@vladislav_space' # Твой канал

translator = GoogleTranslator(source='auto', target='ru')

# СПИСОК ЗАПРЕЩЕННЫХ ТЕМ (Стоп-слова)
STOP_WORDS = [
    'война', 'битва', 'убит', 'казнен', 'президент', 'партия', 
    'революция', 'вторжение', 'армия', 'фронт', 'политика', 
    'договор', 'ссср', 'нато', 'сражение', 'захват', 'санкции'
]

def get_peaceful_history_event():
    """Получает исторические события и фильтрует их"""
    month = datetime.now().month
    day = datetime.now().day
    
    # Используем API Википедии для событий дня
    url = f"https://ru.wikipedia.org/api/rest_v1/feed/onthisday/events/{month}/{day}"
    
    try:
        res = requests.get(url, timeout=20).json()
        events = res.get('events', [])
        
        # Фильтруем события: только наука, техника, открытия
        good_events = []
        for e in events:
            text = e.get('text', '').lower()
            
            # Проверяем на стоп-слова
            has_politics = any(word in text for word in STOP_WORDS)
            
            # Ищем ключевые слова "интереса"
            is_interesting = any(word in text for word in [
                'открыт', 'изобретен', 'космос', 'первый', 'ученый', 
                'экспедиция', 'полет', 'основан', 'построен', 'животное'
            ])
            
            if not has_politics and is_interesting:
                good_events.append(e)

        if not good_events:
            # Если ничего научного не нашли, берем просто самое спокойное
            return events[0] if events else None
            
        # Берем самое свежее или интересное из отфильтрованных
        return good_events[0]
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return None

def send_to_telegram():
    event = get_peaceful_history_event()
    if not event:
        return

    year = event.get('year')
    text_en = event.get('text')
    
    # Формируем заголовок и текст без лишней "воды"
    caption = (
        f"📜 <b>ЭТОТ ДЕНЬ В ИСТОРИИ</b>\n"
        f"📅 <b>{datetime.now().strftime('%d %B')} {year} года</b>\n"
        f"─────────────────────\n\n"
        f"{text_en}\n\n"
        f"⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
        f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
    )

    # Пытаемся взять картинку, если она есть в событии
    photo_url = None
    if 'pages' in event and event['pages'][0].get('originalimage'):
        photo_url = event['pages'][0]['originalimage']['source']

    base_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
    
    if photo_url:
        payload = {
            'chat_id': CHANNEL_NAME,
            'photo': photo_url,
            'caption': caption,
            'parse_mode': 'HTML',
            'show_caption_above_media': True # Наш любимый стиль!
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
