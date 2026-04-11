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

# Список слов, которые ОБЯЗАТЕЛЬНО должны быть в событии, чтобы мы его запостили
SPACE_KEYWORDS = [
    'space', 'nasa', 'rocket', 'satellite', 'orbit', 'launch', 'moon', 'mars', 
    'astronaut', 'cosmonaut', 'sputnik', 'apollo', 'soyuz', 'telescope', 'galaxy',
    'astronomy', 'iss', 'mks', 'baikonur', 'shuttle', 'gagarin', 'armstrong'
]

def get_space_history_event():
    """Ищет только те события из Википедии, которые связаны с космосом"""
    today = datetime.now()
    month = today.month
    day = today.day
    
    # Берем события дня из Википедии (английской, там база больше)
    url = f"https://en.wikipedia.org/api/rest_v1/feed/onthisday/events/{month}/{day}"
    
    try:
        print(f"📡 Сканирую исторические архивы на {day}/{month}...")
        response = requests.get(url, timeout=20)
        data = response.json()
        events = data.get('events', [])
        
        # Фильтруем: оставляем только те, где есть 'space' ключевые слова
        space_events = []
        for e in events:
            text_lower = e['text'].lower()
            if any(key in text_lower for key in SPACE_KEYWORDS):
                space_events.append(e)
        
        if not space_events:
            print("📭 Настоящих космических событий сегодня не найдено.")
            return None, None, None

        # Проверка памяти (чтобы не постить одно и то же каждый год)
        if os.path.exists(DB_FILE):
            with open(DB_FILE, 'r', encoding='utf-8') as f:
                sent_years = f.read().splitlines()
        else:
            sent_years = []

        # Ищем событие, которого еще не было
        random.shuffle(space_events)
        target_event = None
        for e in space_events:
            if str(e['year']) not in sent_years:
                target_event = e
                break
        
        if not target_event:
            return None, None, None

        year = target_event['year']
        text_en = target_event['text']
        
        # Получаем картинку, если она есть
        img_url = "https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=1200&auto=format&fit=crop"
        if target_event.get('pages') and target_event['pages'][0].get('originalimage'):
            img_url = target_event['pages'][0]['originalimage']['source']

        # Перевод
        print(f"📝 Нашел событие {year} года. Перевожу...")
        text_ru = translator.translate(text_en)
        
        caption = (
            f"📜 <b>УРОК КОСМИЧЕСКОЙ ИСТОРИИ</b>\n"
            f"📅 <b>Дата: {day} {today.strftime('%B')} {year} года</b>\n"
            f"─────────────────────\n\n"
            f"🚀 <b>ЧТО ПРОИЗОШЛО:</b>\n"
            f"{text_ru}\n\n"
            f"🔭 <i>Это событие навсегда вошло в летопись освоения Вселенной.</i>\n\n"
            f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
        )
        
        return img_url, caption, year

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return None, None, None

def send():
    img_url, caption, year = get_space_history_event()
    if img_url:
        payload = {
            'chat_id': CHANNEL_NAME,
            'photo': img_url,
            'caption': caption,
            'parse_mode': 'HTML'
        }
        r = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto", data=payload)
        if r.status_code == 200:
            with open(DB_FILE, 'a', encoding='utf-8') as f:
                f.write(f"{year}\n")
            print(f"✅ Урок истории за {year} год отправлен!")

if __name__ == '__main__':
    send()
