import requests
import os
import random
import re
import json
from datetime import datetime
from deep_translator import GoogleTranslator

# ============================================================
# ⚙️ НАСТРОЙКИ
# ============================================================
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHANNEL_NAME   = '@vladislav_space'
DB_FILE        = "last_history_event.txt"

# Ссылка на нового бота эксперта (Deep Linking для автозапуска)
EXPERT_LINK = "https://t.me/Marty_Help_Bot?start=channel_post"

translator = GoogleTranslator(source='auto', target='ru')

# 🛡 ФИЛЬТР БЕЗОПАСНОСТИ: Исключаем военную тематику (строго целые слова)
FORBIDDEN_KEYWORDS = [
    'war', 'military', 'weapon', 'army', 'pentagon', 'spy', 'classified', 
    'air force', 'война', 'военный', 'оборона', 'оружие', 'шпион', 'секретно', 
    'ядерный', 'nuclear', 'missile', 'ракетный удар', 'разведка', 'combat'
]

# ✨ КОСМИЧЕСКИЙ ФИЛЬТР: Белый список тем
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
    for word in FORBIDDEN_KEYWORDS:
        if re.search(rf'\b{word}\b', text_low):
            return False, f"Обнаружена военная тематика: '{word}'"
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
        return res.get('results', [])
    except: return None

def get_wikipedia_event():
    today = datetime.now()
    url = f"https://en.wikipedia.org/api/rest_v1/feed/onthisday/events/{today.month}/{today.day}"
    try:
        res = requests.get(url, timeout=15).json()
        return res.get('events', [])
    except: return None

def send_history():
    log_status("Запуск протокола History Bot v2.2")
    source_funcs = [get_space_devs_event, get_wikipedia_event]
    random.shuffle(source_funcs)
    event_data = None
    
    for fetch in source_funcs:
        log_status(f"Опрос источника: {fetch.__name__}")
        raw_events = fetch()
        if not raw_events: continue
        random.shuffle(raw_events)

        for e in raw_events:
            if 'description' in e: # Space Devs
                title = e.get('name', 'Событие')
                text = e.get('description', '')
                year = datetime.fromisoformat(e['date'].replace('Z', '+00:00')).year
                img = e.get('feature_image')
                source = 'The Space Devs'
            else: # Wikipedia
                title = 'Космическая веха'
                text = e.get('text', '')
                year = e.get('year', 2000)
                img = e.get('pages', [{}])[0].get('originalimage', {}).get('source')
                source = 'Wikipedia'

            is_safe, reason = check_content_safety(text + " " + title)
            if not is_safe: continue

            event_key = f"{year}_{title[:20]}"
            if os.path.exists(DB_FILE):
                with open(DB_FILE, 'r', encoding='utf-8') as f:
                    if event_key in f.read(): continue

            event_data = {'year': year, 'text': text, 'img': img, 'title': title, 'source': source, 'key': event_key}
            break
        if event_data: break

    if not event_data:
        log_status("ЗАВЕРШЕНИЕ: Новых мирных событий на сегодня не найдено.")
        return

    title_ru = professional_translate(event_data['title'])
    sentences = re.split(r'(?<![A-Z])\.\s+', event_data['text'])
    short_desc = '. '.join(sentences[:4]) + ('.' if not sentences[0].endswith('.') else '')
    desc_ru = professional_translate(short_desc)
    marti_msg = get_marti_comment(desc_ru)

    # --- ФОРМИРОВАНИЕ CAPTION С СЫЛКОЙ НА ЭКСПЕРТА ---
    caption = (
        f"📜 <b>УРОК КОСМИЧЕСКОЙ ИСТОРИИ</b>\n"
        f"📅 <code>ДАТА: {datetime.now().day:02d}.{datetime.now().month:02d}.{event_data['year']}</code>\n"
        f"─────────────────────\n\n"
        f"🚀 <b>ОБЪЕКТ:</b>\n<u>{title_ru.upper()}</u>\n\n"
        f"📖 <b>СВОДКА ЦУП:</b>\n{desc_ru}\n\n"
        f"🐩 <b>АНАЛИЗ МАРТИ:</b>\n<i>«{marti_msg}»</i>\n\n"
        f"─────────────────────\n"
        f"🤖 <b>ЗАПРОС ДАННЫХ:</b>\n"
        f"👉 <a href='{EXPERT_LINK}'><b>Узнать больше у эксперта Марти</b></a>\n"
        f"─────────────────────\n\n"
        f"📡 <b>КАНАЛ СВЯЗИ:</b> <code>{event_data['source']}</code>\n"
        f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
    )

    payload = {
        'chat_id': CHANNEL_NAME,
        'photo': event_data['img'] or "https://images.unsplash.com/photo-1451187580459-43490279c0fa",
        'caption': caption,
        'parse_mode': 'HTML'
    }
    
    try:
        r = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto", data=payload, timeout=25)
        if r.status_code == 200:
            with open(DB_FILE, 'a', encoding='utf-8') as f:
                f.write(f"{event_data['key']}\n")
            log_status("УСПЕХ: Пост опубликован.")
        else:
            log_status(f"ОШИБКА TG: {r.text}")
    except Exception as e:
        log_status(f"КРИТИЧЕСКИЙ СБОЙ: {e}")

if __name__ == '__main__':
    send_history()
