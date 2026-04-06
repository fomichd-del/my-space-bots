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

# 🚀 ТОЛЬКО КОСМОС (Обязательные слова)
STRICT_SPACE_WORDS = [
    'nasa', 'наса', 'космос', 'астронавт', 'космонавт', 'планета', 'звезда',
    'спутник', 'ракета-носитель', 'байконур', 'мкс', 'iss', 'телескоп', 
    'хаббл', 'hubble', 'марсоход', 'луноход', 'аполлон', 'apollo', 'союз', 
    'шаттл', 'shuttle', 'pioneer', 'voyager', 'discovery', 'orbit', 'орбита'
]

# 🚫 ЗАПРЕТ (Никакой политики, ядерных испытаний и войн)
TOTAL_FORBIDDEN = [
    'война', 'военный', 'армия', 'ядерный', 'атомный', 'взрыв', 'испытание', 
    'полигон', 'бомба', 'удар', 'база', 'штаб', 'министр', 'президент', 
    'правительство', 'конфликт', 'битва', 'убит', 'смерть', 'politics', 'nuclear'
]

def get_pure_cosmic_lesson():
    now = datetime.now()
    # Английская база "Selected" — самая качественная и проверенная
    url = f"https://en.wikipedia.org/api/rest_v1/feed/onthisday/selected/{now.month:02d}/{now.day:02d}"
    
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    try:
        r = requests.get(url, headers=headers, timeout=30)
        if r.status_code != 200: return []
        data = r.json()
        
        events = data.get('selected', [])
        clean_events = []
        
        for e in events:
            text = e.get('text', '').lower()
            
            # Проверка 1: Это точно про космос?
            is_space = any(word in text for word in STRICT_SPACE_WORDS)
            # Проверка 2: Там точно нет политики и ядерных тем?
            is_clean = not any(word in text for word in TOTAL_FORBIDDEN)
            
            if is_space and is_clean:
                clean_events.append(e)
        
        return clean_events
    except:
        return []

def send_to_telegram():
    events = get_pure_cosmic_lesson()
    
    if not events:
        print("📭 Космических уроков на сегодня не найдено. Пост отменен.")
        return

    # Выбираем самое красивое событие с картинкой
    main_event = events[0]
    for e in events:
        if 'pages' in e and e['pages'][0].get('originalimage'):
            main_event = e
            break

    year = main_event.get('year')
    raw_text = main_event.get('text', '')
    
    # Делаем перевод понятным и добрым
    text_ru = translator.translate(raw_text)
    
    # ОФОРМЛЕНИЕ
    caption = (
        f"🧑‍🚀 <b>УРОК КОСМИЧЕСКОЙ ИСТОРИИ</b>\n"
        f"📅 <b>Тема: {datetime.now().strftime('%d %B')} {year} года</b>\n"
        f"─────────────────────\n\n"
        f"📖 <b>ИНТЕРЕСНЫЙ ФАКТ:</b>\n"
        f"{text_ru}\n\n"
        f"⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
        f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
    )

    photo_url = None
    if 'pages' in main_event and main_event['pages'][0].get('originalimage'):
        photo_url = main_event['pages'][0]['originalimage']['source']

    base_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
    
    if photo_url:
        # В Telegram при отправке Photo подпись (caption) всегда под картинкой
        payload = {
            'chat_id': CHANNEL_NAME,
            'photo': photo_url,
            'caption': caption,
            'parse_mode': 'HTML'
        }
        requests.post(f"{base_url}/sendPhoto", data=payload)
    else:
        # Если фото нет, шлем текстом с эмодзи
        requests.post(f"{base_url}/sendMessage", data={'chat_id': CHANNEL_NAME, 'text': "🌌 " + caption, 'parse_mode': 'HTML'})
    
    print("✅ Космический урок успешно отправлен в канал!")

if __name__ == '__main__':
    send_to_telegram()
