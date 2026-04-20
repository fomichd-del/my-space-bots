import requests
import os
import random
import re
import xml.etree.ElementTree as ET
from datetime import datetime
from deep_translator import GoogleTranslator

# ============================================================
# ⚙️ НАСТРОЙКИ
# ============================================================
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHANNEL_NAME   = '@vladislav_space'
DB_FILE        = "last_history_event.txt"

translator = GoogleTranslator(source='auto', target='ru')

# Профессиональные термины (не переводим)
PROTECTED_TERMS = [
    'NASA', 'SpaceX', 'ISS', 'SLS', 'Starship', 'Apollo', 'Soyuz', 'Vostok',
    'Hubble', 'James Webb', 'Artemis', 'Blue Origin', 'ESA', 'JAXA', 'Roscosmos',
    'Baikonur', 'Plesetsk', 'Vostochny', 'N1', 'Falcon 9', 'Falcon Heavy'
]

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) SpaceEducationBot/1.0'}

def get_marti_comment(text_ru):
    """Генератор комментариев Марти"""
    text_low = text_ru.lower()
    reactions = {
        'лун': 'Луна... там, говорят, идеальный песок для того, чтобы зарыть косточку. Только вот прыгать придется высоко! 🐾',
        'ракета': 'Если эта ракета летит вверх, значит ли это, что мой мячик можно забросить на орбиту? Я готов бежать за ним! 🚀',
        'марс': 'Марс красный, потому что там много пыли. Моя шерстка стала бы такой же через пять минут прогулки! 🐩',
        'еда': 'Космическая еда в тюбиках? Надеюсь, там есть вкус говядины, иначе я в космонавты не пойду! 🥩',
        'станция': 'МКС — это как большая будка, которая летает очень быстро. Интересно, а там разрешают спать на диване? 🛰',
        'звезд': 'Я часто гавкаю на звезды ночью, но они никогда не гавкают в ответ. Вежливые они... ✨',
        'союз': '«Союз» — звучит надежно! Как мой поводок. Только летит быстрее. 🚀',
        'гагарин': 'Первый человек в космосе! Интересно, он брал с собой угощения для собак? 🐕'
    }
    for key, comment in reactions.items():
        if key in text_low: return comment
    return random.choice([
        "Мой хвост виляет со скоростью первой космической, когда я читаю такие новости! 🐕",
        "Интересно, а в скафандре есть место, чтобы почесать за ушком? 🛸",
        "Космос такой большой... Надеюсь, там достаточно места для всех хороших мальчиков! 🐾"
    ])

def professional_translate(text):
    """Перевод с сохранением терминологии"""
    if not text: return ""
    temp_text = text
    replacements = {}
    for i, term in enumerate(PROTECTED_TERMS):
        placeholder = f"__TERM{i}__"
        if term in temp_text:
            temp_text = temp_text.replace(term, placeholder)
            replacements[placeholder] = term
    try:
        translated = translator.translate(temp_text)
        for placeholder, original in replacements.items():
            translated = translated.replace(placeholder, original)
        return translated
    except: return text

# --- ИСТОЧНИКИ ДАННЫХ ---

def get_space_devs_event():
    """Источник №1: The Space Devs (Профессиональный архив)"""
    today = datetime.now()
    url = f"https://ll.thespacedevs.com/2.2.0/event/?date__month={today.month}&date__day={today.day}&limit=5"
    try:
        res = requests.get(url, headers=HEADERS, timeout=15).json()
        results = res.get('results', [])
        if not results: return None
        event = random.choice(results)
        dt = datetime.fromisoformat(event['date'].replace('Z', '+00:00'))
        return {'year': dt.year, 'text': event['description'], 'img': event.get('feature_image'), 'title': event.get('name'), 'source': 'The Space Devs Archive'}
    except: return None

def get_wikipedia_event():
    """Источник №2: Wikipedia API (Глобальный охват)"""
    today = datetime.now()
    url = f"https://en.wikipedia.org/api/rest_v1/feed/onthisday/events/{today.month}/{today.day}"
    try:
        res = requests.get(url, headers=HEADERS, timeout=15).json()
        events = [e for e in res.get('events', []) if any(k in e['text'].lower() for k in ['space', 'orbit', 'launch', 'nasa', 'soviet', 'satellite'])]
        if not events: return None
        event = random.choice(events)
        img = event.get('pages', [{}])[0].get('originalimage', {}).get('source')
        return {'year': event['year'], 'text': event['text'], 'img': img, 'title': 'Космическая веха', 'source': 'Wikipedia Global Archive'}
    except: return None

def get_roscosmos_event():
    """Источник №3: Roscosmos RSS (Отечественная история)"""
    url = "https://www.roscosmos.ru/export/news.xml" # Пример RSS Роскосмоса
    try:
        response = requests.get(url, timeout=15)
        root = ET.fromstring(response.content)
        items = root.findall('.//item')
        # Ищем новости со словами "годовщина", "юбилей", "история"
        historical = []
        for item in items:
            title = item.find('title').text
            desc = item.find('description').text
            if any(k in (title + desc).lower() for k in ['годовщин', 'юбилей', 'памят', 'истори']):
                historical.append({
                    'year': datetime.now().year, # RSS обычно дает текущие новости о прошлом
                    'text': desc,
                    'img': None,
                    'title': title,
                    'source': 'Пресс-служба Роскосмоса'
                })
        return random.choice(historical) if historical else None
    except: return None

def send_history():
    # Очередность проверки источников
    sources = [get_space_devs_event, get_wikipedia_event, get_roscosmos_event]
    random.shuffle(sources) # Рандомизируем, чтобы контент был разным
    
    event = None
    for get_data in sources:
        event = get_data()
        if event: break

    if not event:
        print("📭 Событий не найдено.")
        return

    event_key = f"{event['year']}_{event['title'][:20]}"
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            if event_key in f.read(): return

    # Обработка текста
    title_ru = professional_translate(event['title'])
    sentences = re.split(r'(?<![A-Z])\.\s+', event['text'])
    short_desc_en = '. '.join(sentences[:4]) + ('.' if not sentences[0].endswith('.') else '')
    desc_ru = professional_translate(short_desc_en)
    marti_msg = get_marti_comment(desc_ru)
    
    # Оформление "Архив ЦУП"
    caption = (
        f"📜 <b>УРОК КОСМИЧЕСКОЙ ИСТОРИИ</b>\n"
        f"📅 <code>ДАТА: {datetime.now().day:02d}.{datetime.now().month:02d}.{event['year']}</code>\n"
        f"─────────────────────\n\n"
        f"🚀 <b>ОБЪЕКТ:</b>\n<u>{title_ru.upper()}</u>\n\n"
        f"📖 <b>СВОДКА ЦУП:</b>\n{desc_ru}\n\n"
        f"🐩 <b>АНАЛИЗ МАРТИ:</b>\n<i>«{marti_msg}»</i>\n\n"
        f"📡 <b>КАНАЛ СВЯЗИ:</b> <code>{event['source']}</code>\n"
        f"─────────────────────\n"
        f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
    )

    payload = {
        'chat_id': CHANNEL_NAME,
        'photo': event['img'] or "https://images.unsplash.com/photo-1451187580459-43490279c0fa",
        'caption': caption,
        'parse_mode': 'HTML'
    }
    
    r = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto", data=payload)
    if r.status_code == 200:
        with open(DB_FILE, 'a', encoding='utf-8') as f: f.write(f"{event_key}\n")
