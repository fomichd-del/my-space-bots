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

# Список слов для СТРОГОЙ фильтрации (никакой политики и религии)
SPACE_KEYWORDS = [
    'space', 'nasa', 'rocket', 'satellite', 'orbit', 'launch', 'moon', 'mars', 
    'astronaut', 'cosmonaut', 'sputnik', 'apollo', 'soyuz', 'telescope', 'galaxy',
    'astronomy', 'iss', 'mks', 'baikonur', 'shuttle', 'gagarin', 'armstrong', 
    'planet', 'nebula', 'supernova', 'vostok', 'pioneer', 'voyager'
]

def get_space_history_event():
    """Ищет только те события из Википедии, которые реально про космос"""
    today = datetime.now()
    month, day = today.month, today.day
    
    url = f"https://en.wikipedia.org/api/rest_v1/feed/onthisday/events/{month}/{day}"
    
    try:
        print(f"📡 Запрос к архивам Википедии на {day}/{month}...")
        response = requests.get(url, timeout=30)
        
        # Защита от пустых ответов или ошибок сервера
        if response.status_code != 200:
            print(f"⚠️ Википедия временно недоступна (Код: {response.status_code}).")
            return None, None, None

        if not response.text.strip():
            print("❌ Ошибка: Получен пустой ответ от API.")
            return None, None, None

        data = response.json()
        events = data.get('events', [])
        
        # 1. СТРОГИЙ ФИЛЬТР: Ищем только космос
        space_events = []
        for e in events:
            text_en = e['text'].lower()
            if any(key in text_en for key in SPACE_KEYWORDS):
                space_events.append(e)
        
        if not space_events:
            print("📭 Космических дат на сегодня не обнаружено. Ждем завтра!")
            return None, None, None

        # 2. ПРОВЕРКА ПАМЯТИ
        sent_years = []
        if os.path.exists(DB_FILE):
            with open(DB_FILE, 'r', encoding='utf-8') as f:
                sent_years = f.read().splitlines()

        # 3. ВЫБОР НОВОГО СОБЫТИЯ
        random.shuffle(space_events)
        target = None
        for e in space_events:
            if str(e['year']) not in sent_years:
                target = e
                break
        
        if not target:
            print("✋ Все космические события этого дня уже были в канале.")
            return None, None, None

        year = target['year']
        text_en = target['text']
        
        # Получаем фото темы (или космос по умолчанию)
        img_url = "https://images.unsplash.com/photo-1446776811953-b23d57bd21aa?q=80&w=1200&auto=format&fit=crop"
        if target.get('pages') and target['pages'][0].get('originalimage'):
            img_url = target['pages'][0]['originalimage']['source']

        # ПЕРЕВОД
        print(f"📝 Перевожу событие {year} года...")
        text_ru = translator.translate(text_en)
        
        caption = (
            f"📜 <b>УРОК КОСМИЧЕСКОЙ ИСТОРИИ</b>\n"
            f"📅 <b>Дата: {day}.{month}.{year} года</b>\n"
            f"─────────────────────\n\n"
            f"🚀 <b>ЧТО ПРОИЗОШЛО:</b>\n"
            f"{text_ru}\n\n"
            f"🔭 <i>Это событие — важный шаг в освоении бескрайних просторов Вселенной.</i>\n\n"
            f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
        )
        
        return img_url, caption, year

    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        return None, None, None

def send():
    img_url, caption, year = get_space_history_event()
    if img_url:
        payload = {'chat_id': CHANNEL_NAME, 'photo': img_url, 'caption': caption, 'parse_mode': 'HTML'}
        r = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto", data=payload)
        if r.status_code == 200:
            with open(DB_FILE, 'a', encoding='utf-8') as f:
                f.write(f"{year}\n")
            print(f"✅ Урок истории за {year} год опубликован!")

if __name__ == '__main__':
    send()
