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

# 🛡 ФИЛЬТР БЕЗОПАСНОСТИ: Исключаем военную тематику
FORBIDDEN_KEYWORDS = [
    'military', 'war', 'weapon', 'defense', 'army', 'pentagon', 'spy', 'classified', 
    'air force', 'война', 'военный', 'оборона', 'оружие', 'шпион', 'секретно', 
    'ядерный', 'nuclear', 'missile', 'ракетный удар', 'разведка'
]

# ✨ КОСМИЧЕСКИЙ ФИЛЬТР: Обязательные темы
SPACE_KEYWORDS = [
    'space', 'orbit', 'nasa', 'planet', 'star', 'galaxy', 'telescope', 'launch',
    'космос', 'орбита', 'планета', 'звезда', 'галактика', 'телескоп', 'запуск',
    'астроном', 'спутник', 'луна', 'марс', 'discovery', 'открытие'
]

PROTECTED_TERMS = ['NASA', 'SpaceX', 'ISS', 'Starship', 'Apollo', 'Roscosmos', 'ESA']

def log_status(message):
    """Вывод детального статуса в консоль ЦУП"""
    print(f"📡 [ЦУП-ДИАГНОСТИКА]: {message}")

def check_content_safety(text):
    """Проверка текста на соответствие мирному космосу"""
    text_low = text.lower()
    
    # 1. Ищем запрещенку
    for word in FORBIDDEN_KEYWORDS:
        if word in text_low:
            return False, f"Обнаружена военная тематика: '{word}'"
    
    # 2. Ищем подтверждение космоса
    if not any(word in text_low for word in SPACE_KEYWORDS):
        return False, "Событие не связано напрямую с космосом или наукой"
        
    return True, "Проверка безопасности пройдена"

def get_marti_comment(text_ru):
    # (Код Марти остается прежним, так как он уже настроен на забавный лад)
    reactions = {
        'лун': 'Луна... идеальное место, чтобы зарыть косточку. Никакой гравитации, прыгаешь как супер-пес! 🐾',
        'марс': 'На Марсе пыльно, моя шерстка станет рыжей! 🐩',
        'звезд': 'Я гавкаю на звезды, они красивые. ✨'
    }
    for key, comment in reactions.items():
        if key in text_ru.lower(): return comment
    return "Космос такой большой! Надеюсь, там достаточно места для всех хороших мальчиков! 🐾"

def professional_translate(text):
    try:
        # Упрощенная защита терминов
        temp_text = text
        for term in PROTECTED_TERMS:
            temp_text = temp_text.replace(term, f"[[{term}]]")
        
        translated = translator.translate(temp_text)
        
        for term in PROTECTED_TERMS:
            translated = translated.replace(f"[[{term}]]", term)
        return translated
    except Exception as e:
        log_status(f"Ошибка перевода: {e}")
        return text

# --- ИСТОЧНИКИ С ПРОВЕРКОЙ ---

def get_space_devs_event():
    today = datetime.now()
    url = f"https://ll.thespacedevs.com/2.2.0/event/?date__month={today.month}&date__day={today.day}&limit=5"
    try:
        res = requests.get(url, timeout=15).json()
        results = res.get('results', [])
        if not results: return None
        event = random.choice(results)
        return {'year': datetime.fromisoformat(event['date'].replace('Z', '+00:00')).year, 
                'text': event['description'], 'img': event.get('feature_image'), 
                'title': event.get('name'), 'source': 'The Space Devs Archive'}
    except: return None

def get_wikipedia_event():
    today = datetime.now()
    url = f"https://en.wikipedia.org/api/rest_v1/feed/onthisday/events/{today.month}/{today.day}"
    try:
        res = requests.get(url, timeout=15).json()
        events = res.get('events', [])
        random.shuffle(events)
        for e in events:
            is_safe, reason = check_content_safety(e['text'])
            if is_safe:
                img = e.get('pages', [{}])[0].get('originalimage', {}).get('source')
                return {'year': e['year'], 'text': e['text'], 'img': img, 'title': 'Космическая веха', 'source': 'Wikipedia Global Archive'}
        return None
    except: return None

def send_history():
    log_status("Запуск протокола History Bot v2.0")
    
    sources = [get_space_devs_event, get_wikipedia_event]
    random.shuffle(sources)
    
    event = None
    for fetch_method in sources:
        log_status(f"Опрос источника: {fetch_method.__name__}")
        event = fetch_method()
        if event:
            # Важнейшая проверка безопасности
            is_safe, reason = check_content_safety(event['text'] + " " + event['title'])
            if is_safe:
                log_status(f"Событие найдено: {event['title']} ({event['year']})")
                break
            else:
                log_status(f"Событие отклонено фильтром: {reason}")
                event = None

    if not event:
        log_status("ЗАВЕРШЕНИЕ: Подходящих мирных космических событий на сегодня не найдено.")
        return

    # Проверка базы данных
    event_key = f"{event['year']}_{event['title'][:20]}"
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            if event_key in f.read():
                log_status(f"ОТМЕНА: Событие {event_key} уже публиковалось ранее.")
                return

    # Подготовка контента
    title_ru = professional_translate(event['title'])
    sentences = re.split(r'(?<![A-Z])\.\s+', event['text'])
    short_desc = '. '.join(sentences[:4]) + '.'
    desc_ru = professional_translate(short_desc)
    marti_msg = get_marti_comment(desc_ru)

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

    # Попытка отправки
    log_status("Отправка пакета данных в Telegram...")
    payload = {
        'chat_id': CHANNEL_NAME,
        'photo': event['img'] or "https://images.unsplash.com/photo-1451187580459-43490279c0fa",
        'caption': caption,
        'parse_mode': 'HTML'
    }
    
    try:
        r = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto", json=payload, timeout=20)
        if r.status_code == 200:
            with open(DB_FILE, 'a', encoding='utf-8') as f:
                f.write(f"{event_key}\n")
            log_status("УСПЕХ: Сообщение доставлено в канал.")
        else:
            log_status(f"ОШИБКА TELEGRAM: {r.status_code} - {r.text}")
    except Exception as e:
        log_status(f"КРИТИЧЕСКАЯ ОШИБКА: {e}")

if __name__ == '__main__':
    send_history()
