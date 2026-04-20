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

# 🛡 ФИЛЬТР БЕЗОПАСНОСТИ: Исключаем только военную тематику (целые слова)
FORBIDDEN_KEYWORDS = [
    'war', 'military', 'weapon', 'army', 'pentagon', 'spy', 'classified', 
    'air force', 'война', 'военный', 'оборона', 'оружие', 'шпион', 'секретно', 
    'ядерный', 'nuclear', 'missile', 'ракетный удар', 'разведка', 'combat'
]

# ✨ КОСМИЧЕСКИЙ ФИЛЬТР: Подтверждение тематики
SPACE_KEYWORDS = [
    'space', 'orbit', 'nasa', 'planet', 'star', 'galaxy', 'telescope', 'launch',
    'rocket', 'shuttle', 'astronaut', 'cosmonaut', 'iss', 'station', 'apollo',
    'космос', 'орбита', 'планета', 'звезда', 'галактика', 'телескоп', 'запуск',
    'астроном', 'спутник', 'луна', 'марс', 'discovery', 'открытие', 'ракета'
]

PROTECTED_TERMS = ['NASA', 'SpaceX', 'ISS', 'Starship', 'Apollo', 'Roscosmos', 'ESA']

def log_status(message):
    """Вывод детального статуса в консоль ЦУП"""
    print(f"📡 [ЦУП-ДИАГНОСТИКА]: {message}")

def check_content_safety(text):
    """Проверка текста на соответствие мирному космосу"""
    text_low = text.lower()
    
    # 1. Ищем запрещенку как ЦЕЛЫЕ СЛОВА (чтобы не банить hardware/towards)
    for word in FORBIDDEN_KEYWORDS:
        if re.search(rf'\b{word}\b', text_low):
            return False, f"Обнаружена военная тематика: '{word}'"
    
    # 2. Ищем подтверждение космоса
    if not any(word in text_low for word in SPACE_KEYWORDS):
        return False, "Событие не связано напрямую с космосом или наукой"
        
    return True, "Проверка безопасности пройдена"

def get_marti_comment(text_ru):
    reactions = {
        'лун': 'Луна... идеальное место, чтобы зарыть косточку. Никакой гравитации, прыгаешь как супер-пес! 🐾',
        'марс': 'На Марсе пыльно, моя шерстка станет рыжей! 🐩',
        'звезд': 'Я гавкаю на звезды, они красивые. ✨',
        'ракета': 'Эта ракета летит так быстро, что я даже не успел бы сказать "Гав"! 🚀',
        'станция': 'Жить на станции круто, но там, наверное, нельзя гоняться за белками... 🛰'
    }
    for key, comment in reactions.items():
        if key in text_ru.lower(): return comment
    return "Космос такой большой! Надеюсь, там достаточно места для всех хороших мальчиков! 🐾"

def professional_translate(text):
    if not text: return ""
    try:
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

# --- ИСТОЧНИКИ ---

def get_space_devs_event():
    today = datetime.now()
    url = f"https://ll.thespacedevs.com/2.2.0/event/?date__month={today.month}&date__day={today.day}&limit=5"
    try:
        res = requests.get(url, timeout=15).json()
        results = res.get('results', [])
        if not results: return None
        event = random.choice(results)
        return {
            'year': datetime.fromisoformat(event['date'].replace('Z', '+00:00')).year, 
            'text': event['description'], 
            'img': event.get('feature_image'), 
            'title': event.get('name'), 
            'source': 'The Space Devs Archive'
        }
    except: return None

def get_wikipedia_event():
    today = datetime.now()
    url = f"https://en.wikipedia.org/api/rest_v1/feed/onthisday/events/{today.month}/{today.day}"
    try:
        res = requests.get(url, timeout=15).json()
        events = res.get('events', [])
        random.shuffle(events)
        for e in events:
            # Проверяем сразу здесь, чтобы найти подходящее
            is_safe, reason = check_content_safety(e['text'])
            if is_safe:
                img = e.get('pages', [{}])[0].get('originalimage', {}).get('source')
                return {'year': e['year'], 'text': e['text'], 'img': img, 'title': 'Космическая веха', 'source': 'Wikipedia Global Archive'}
        return None
    except: return None

def send_history():
    log_status("Запуск протокола History Bot v2.1")
    
    # Список функций-источников
    source_funcs = [get_space_devs_event, get_wikipedia_event]
    random.shuffle(source_funcs)
    
    event = None
    for fetch in source_funcs:
        log_status(f"Опрос источника: {fetch.__name__}")
        data = fetch()
        if data:
            is_safe, reason = check_content_safety(data['text'] + " " + data['title'])
            if is_safe:
                event = data
                log_status(f"Событие подтверждено: {event['title']}")
                break
            else:
                log_status(f"Событие отклонено: {reason}")

    if not event:
        log_status("ЗАВЕРШЕНИЕ: На сегодня подходящих мирных событий не найдено.")
        return

    # Проверка на повтор
    event_key = f"{event['year']}_{event['title'][:20]}"
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            if event_key in f.read():
                log_status(f"ОТМЕНА: {event_key} уже был в канале.")
                return

    # Формирование
    title_ru = professional_translate(event['title'])
    sentences = re.split(r'(?<![A-Z])\.\s+', event['text'])
    short_desc = '. '.join(sentences[:4]) + ('.' if not sentences[0].endswith('.') else '')
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

    log_status("Отправка в Telegram...")
    payload = {
        'chat_id': CHANNEL_NAME,
        'photo': event['img'] or "https://images.unsplash.com/photo-1451187580459-43490279c0fa",
        'caption': caption,
        'parse_mode': 'HTML'
    }
    
    try:
        # Используем data=payload для стабильности
        r = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto", data=payload, timeout=25)
        if r.status_code == 200:
            with open(DB_FILE, 'a', encoding='utf-8') as f:
                f.write(f"{event_key}\n")
            log_status("УСПЕХ: Пост опубликован.")
        else:
            log_status(f"ОШИБКА TG: {r.text}")
    except Exception as e:
        log_status(f"КРИТИЧЕСКИЙ СБОЙ: {e}")

if __name__ == '__main__':
    send_history()
