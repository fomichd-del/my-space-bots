import requests
import os
from datetime import datetime
from deep_translator import GoogleTranslator

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHANNEL_NAME   = '@vladislav_space'
translator = GoogleTranslator(source='auto', target='ru')

# Список слов, которые мы ХОТИМ видеть
GOOD_WORDS = ['space', 'nasa', 'rocket', 'planet', 'pioneer', 'satellite', 'star', 'astronomy', 'apollo']
# Список слов-табу
STOP_WORDS = ['war', 'military', 'army', 'base', 'politics', 'killed', 'война', 'база', 'сирия']

def get_history():
    now = datetime.now()
    # Берем английскую базу (она надежнее и больше)
    url = f"https://en.wikipedia.org/api/rest_v1/feed/onthisday/selected/{now.month}/{now.day}"
    
    try:
        r = requests.get(url, timeout=20)
        if r.status_code != 200: return None
        data = r.json()
        
        events = data.get('selected', [])
        for e in events:
            text = e.get('text', '').lower()
            # Проверка: есть космос и нет политики
            if any(w in text for w in GOOD_WORDS) and not any(w in text for w in STOP_WORDS):
                return e
    except:
        return None

def send_to_telegram():
    event = get_history()
    if not event: return

    year = event.get('year')
    text_ru = translator.translate(event.get('text', ''))
    
    caption = (
        f"🚀 <b>КОСМИЧЕСКИЙ КАЛЕНДАРЬ</b>\n"
        f"📅 <b>{datetime.now().strftime('%d %B')} {year} года</b>\n"
        f"─────────────────────\n\n"
        f"<b>ГЛАВНОЕ СОБЫТИЕ:</b>\n"
        f"{text_ru}\n\n"
        f"⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
        f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
    )

    photo_url = event['pages'][0].get('originalimage', {}).get('source') if 'pages' in event else None

    base_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
    if photo_url:
        requests.post(f"{base_url}/sendPhoto", data={'chat_id': CHANNEL_NAME, 'photo': photo_url, 'caption': caption, 'parse_mode': 'HTML', 'show_caption_above_media': True})
    else:
        requests.post(f"{base_url}/sendMessage", data={'chat_id': CHANNEL_NAME, 'text': caption, 'parse_mode': 'HTML'})

if __name__ == '__main__':
    send_to_telegram()
