import requests
import os
import random
import re
from datetime import datetime
from deep_translator import GoogleTranslator

# ============================================================
# ⚙️ НАСТРОЙКИ
# ============================================================
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHANNEL_NAME   = '@vladislav_space'
DB_FILE        = "last_history_event.txt"

translator = GoogleTranslator(source='auto', target='ru')

# Список слов, которые НЕЛЬЗЯ переводить (сохраняем профессионализм)
PROTECTED_TERMS = [
    'NASA', 'SpaceX', 'ISS', 'SLS', 'Starship', 'Apollo', 'Soyuz', 'Vostok',
    'Hubble', 'James Webb', 'Artemis', 'Blue Origin', 'ESA', 'JAXA', 'Roscosmos'
]

# Заголовки для обхода блокировок
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) SpaceEducationBot/1.0'}

def get_marti_comment(text_ru):
    """Генератор забавных комментариев Марти на основе ключевых слов"""
    text_low = text_ru.lower()
    
    # Реакции на ключевые слова
    reactions = {
        'лун': 'Луна... там, говорят, идеальный песок для того, чтобы зарыть косточку. Только вот прыгать придется высоко! 🐾',
        'ракета': 'Если эта ракета летит вверх, значит ли это, что мой мячик можно забросить на орбиту? Я готов бежать за ним! 🚀',
        'марс': 'Марс красный, потому что там много пыли. Моя шерстка стала бы такой же через пять минут прогулки! 🐩',
        'еда': 'Космическая еда в тюбиках? Надеюсь, там есть вкус говядины, иначе я в космонавты не пойду! 🥩',
        'станция': 'МКС — это как большая будка, которая летает очень быстро. Интересно, а там разрешают спать на диване? 🛰',
        'звезд': 'Я часто гавкаю на звезды ночью, но они никогда не гавкают в ответ. Вежливые они, эти звезды... ✨'
    }

    for key, comment in reactions.items():
        if key in text_low:
            return comment
            
    # Универсальные фразы, если совпадений нет
    return random.choice([
        "Мой хвост виляет со скоростью первой космической, когда я читаю такие новости! 🐕",
        "Интересно, а в скафандре есть место, чтобы почесать за ушком? 🛸",
        "Космос такой большой... Надеюсь, там достаточно места для всех хороших мальчиков! 🐾"
    ])

def professional_translate(text):
    """Перевод с защитой технических терминов"""
    temp_text = text
    replacements = {}
    
    # Прячем термины в заглушки
    for i, term in enumerate(PROTECTED_TERMS):
        placeholder = f"__TERM{i}__"
        if term in temp_text:
            temp_text = temp_text.replace(term, placeholder)
            replacements[placeholder] = term
            
    # Переводим
    translated = translator.translate(temp_text)
    
    # Возвращаем термины на место
    for placeholder, original in replacements.items():
        translated = translated.replace(placeholder, original)
        
    return translated

def get_space_devs_event():
    """Источник №1: Профессиональный архив запусков и событий (The Space Devs)"""
    today = datetime.now()
    url = f"https://ll.thespacedevs.com/2.2.0/event/?date__month={today.month}&date__day={today.day}&limit=5"
    
    try:
        print(f"📡 Сканирую глобальный космический архив на {today.day}/{today.month}...")
        response = requests.get(url, headers=HEADERS, timeout=30)
        if response.status_code != 200: return None
        
        results = response.json().get('results', [])
        if not results: return None

        event = random.choice(results)
        dt = datetime.fromisoformat(event['date'].replace('Z', '+00:00'))
        
        return {
            'year': dt.year,
            'text': event['description'],
            'img': event.get('feature_image'),
            'title': event.get('name'),
            'source': 'The Space Devs Archive'
        }
    except Exception as e:
        print(f"⚠️ Ошибка Space Devs: {e}")
        return None

def get_nasa_archive_event():
    """Источник №2: Поиск по официальным архивам NASA за этот день"""
    today = datetime.now()
    month_name = today.strftime("%B")
    query = f"{month_name} {today.day}"
    url = f"https://images-api.nasa.gov/search?q={query}&media_type=image"
    
    try:
        print(f"📡 Ищу в фото-архивах NASA за {query}...")
        response = requests.get(url, headers=HEADERS, timeout=30)
        if response.status_code != 200: return None
            
        items = response.json()['collection']['items']
        if not items: return None

        item = random.choice(items[:15])
        data = item['data'][0]
        
        year = today.year - 10
        if 'date_created' in data:
            year = data['date_created'].split('-')[0]

        return {
            'year': year,
            'text': data.get('description', data.get('title')),
            'img': item['links'][0]['href'],
            'title': data.get('title'),
            'source': 'NASA Historical Library'
        }
    except Exception as e:
        print(f"⚠️ Ошибка NASA Archive: {e}")
        return None

def send_history():
    event = get_space_devs_event()
    if not event:
        event = get_nasa_archive_event()
        
    if not event:
        print("📭 Сегодня тихий день в истории космоса.")
        return

    event_key = f"{event['year']}_{event['title'][:20]}"
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            if event_key in f.read():
                print(f"✋ Событие {event_key} уже было опубликовано.")
                return

    print(f"📝 Найдено событие: {event['title']}. Обработка...")
    
    # 1. Профессиональный перевод
    title_ru = professional_translate(event['title'])
    
    # 2. Умное разбиение на предложения (не ломается на "U.S." или "St.")
    raw_desc = event['text']
    sentences = re.split(r'(?<![A-Z])\.\s+', raw_desc)
    short_desc_en = '. '.join(sentences[:4]) + ('.' if not sentences[0].endswith('.') else '')
    desc_ru = professional_translate(short_desc_en)
    
    # 3. Получаем комментарий от Марти
    marti_msg = get_marti_comment(desc_ru)
    
    # 4. Формирование красочного поста
    caption = (
        f"📜 <b>УРОК КОСМИЧЕСКОЙ ИСТОРИИ</b>\n"
        f"📅 <code>ДАТА: {datetime.now().day:02d}.{datetime.now().month:02d}.{event['year']}</code>\n"
        f"─────────────────────\n\n"
        f"🚀 <b>СОБЫТИЕ:</b>\n<u>{title_ru.upper()}</u>\n\n"
        f"📖 <b>ЧТО ПРОИЗОШЛО:</b>\n{desc_ru}\n\n"
        f"🐩 <b>МЫСЛИ МАРТИ:</b>\n<i>«{marti_msg}»</i>\n\n"
        f"📡 <b>ИСТОЧНИК:</b> <code>{event['source']}</code>\n"
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
        with open(DB_FILE, 'a', encoding='utf-8') as f:
            f.write(f"{event_key}\n")
        print(f"✅ Пост успешно отправлен!")
    else:
        print(f"❌ Ошибка Telegram: {r.text}")

if __name__ == '__main__':
    send_history()
