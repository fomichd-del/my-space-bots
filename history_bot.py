import requests
import os
import random
from datetime import datetime
from deep_translator import GoogleTranslator

# ============================================================
# ⚙️ НАСТРОЙКИ
# ============================================================
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHANNEL_NAME   = '@vladislav_space'
DB_FILE        = "last_history_event.txt"

translator = GoogleTranslator(source='auto', target='ru')

# Строгий фильтр для Википедии
SPACE_KEYWORDS = [
    'space', 'nasa', 'rocket', 'satellite', 'orbit', 'launch', 'moon', 'mars', 
    'astronaut', 'cosmonaut', 'sputnik', 'apollo', 'soyuz', 'telescope', 'galaxy',
    'astronomy', 'iss', 'mks', 'baikonur', 'shuttle', 'gagarin', 'armstrong'
]

# Заголовки, чтобы сайты не думали, что мы злой бот (Фикс ошибки 403)
HEADERS = {'User-Agent': 'SpaceBotHistoryProject/1.0 (contact: your-email@example.com)'}

def get_pro_space_events():
    """Источник 1: Профессиональный календарь космических событий (The Space Devs)"""
    today = datetime.now()
    month, day = today.month, today.day
    # Ищем события, связанные с текущим днем
    url = f"https://ll.thespacedevs.com/2.2.0/event/?limit=10"
    
    try:
        print("📡 Сканирую профессиональную базу космических событий...")
        response = requests.get(url, headers=HEADERS, timeout=30)
        if response.status_code != 200: return None
        
        events = response.json().get('results', [])
        valid_events = []
        
        for e in events:
            # Проверяем, совпадает ли дата (день и месяц)
            event_date = datetime.fromisoformat(e['date'].replace('Z', '+00:00'))
            if event_date.month == month and event_date.day == day:
                valid_events.append(e)
        
        if not valid_events: return None
        
        # Выбираем случайное из подходящих
        event = random.choice(valid_events)
        year = datetime.fromisoformat(event['date'].replace('Z', '+00:00')).year
        
        return {
            'year': year,
            'text': event['description'],
            'img': event.get('feature_image'),
            'source': 'Space Devs Archive'
        }
    except: return None

def get_wikipedia_event():
    """Источник 2: Википедия (Запасной вариант с фильтром)"""
    today = datetime.now()
    month, day = today.month, today.day
    url = f"https://en.wikipedia.org/api/rest_v1/feed/onthisday/events/{month}/{day}"
    
    try:
        print("📡 Профессиональная база пуста. Ищу в Википедии...")
        response = requests.get(url, headers=HEADERS, timeout=30)
        if response.status_code != 200: return None
        
        data = response.json()
        events = data.get('events', [])
        
        # Строгая фильтрация по ключевым словам
        space_events = [e for e in events if any(k in e['text'].lower() for k in SPACE_KEYWORDS)]
        
        if not space_events: return None
        
        # Проверка памяти
        sent_years = []
        if os.path.exists(DB_FILE):
            with open(DB_FILE, 'r') as f: sent_years = f.read().splitlines()
            
        random.shuffle(space_events)
        for e in space_events:
            if str(e['year']) not in sent_years:
                img = e['pages'][0]['originalimage']['source'] if e.get('pages') and e['pages'][0].get('originalimage') else None
                return {'year': e['year'], 'text': e['text'], 'img': img, 'source': 'Wikipedia History'}
        
        return None
    except: return None

def send_history():
    # Пробуем сначала профильный источник
    event = get_pro_space_events()
    
    # Если там пусто — идем в Википедию
    if not event:
        event = get_wikipedia_event()
        
    if not event:
        print("📭 Сегодня ничего космического не произошло.")
        return

    # Перевод и оформление
    text_ru = translator.translate(event['text'])
    img_url = event['img'] or "https://images.unsplash.com/photo-1446776811953-b23d57bd21aa?q=80&w=1200"
    
    caption = (
        f"📜 <b>УРОК КОСМИЧЕСКОЙ ИСТОРИИ</b>\n"
        f"📅 <b>Дата: {datetime.now().day}.{datetime.now().month}.{event['year']} года</b>\n"
        f"─────────────────────\n\n"
        f"🚀 <b>ЧТО ПРОИЗОШЛО:</b>\n"
        f"{text_ru}\n\n"
        f"🔭 <i>Источник: {event['source']}</i>\n\n"
        f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
    )

    payload = {'chat_id': CHANNEL_NAME, 'photo': img_url, 'caption': caption, 'parse_mode': 'HTML'}
    r = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto", data=payload)
    
    if r.status_code == 200:
        with open(DB_FILE, 'a') as f: f.write(f"{event['year']}\n")
        print(f"✅ Урок за {event['year']} год опубликован!")

if __name__ == '__main__':
    send_history()
