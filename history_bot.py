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

# 🌌 РАСШИРЕННЫЙ СПИСОК (Добавил конкретные миссии)
SPACE_KEYWORDS = [
    'space', 'nasa', 'rocket', 'satellite', 'planet', 'star', 'astronomy',
    'pioneer', 'voyager', 'apollo', 'soyuz', 'shuttle', 'iss', 'orbit',
    'launch', 'telescope', 'hubble', 'galaxy', 'cosmos', 'comet', 'nebula',
    'asteroid', 'discovery', 'observed', 'moon', 'mars', 'intelsat', 'exploration'
]

# 🚫 ЖЕСТКИЙ ФИЛЬТР (Никакой войны и политики)
STOP_WORDS = [
    'war', 'military', 'army', 'battle', 'killed', 'politics', 'weapon',
    'война', 'военный', 'армия', 'битва', 'убит', 'оружие', 'база', 'штаб',
    'агрессия', 'удар', 'вторжение', 'конфликт', 'сирия', 'missile'
]

def get_cosmic_lesson():
    now = datetime.now()
    # Английская база "ALL" - самая большая, ищем там
    url = f"https://en.wikipedia.org/api/rest_v1/feed/onthisday/all/{now.month}/{now.day}"
    
    try:
        print(f"📡 Проверяю архивы за {now.day}/{now.month}...")
        r = requests.get(url, timeout=30)
        if r.status_code != 200: 
            print(f"⚠️ Ошибка сервера Википедии: {r.status_code}")
            return []
        
        data = r.json()
        all_events = data.get('selected', []) + data.get('events', [])
        
        found = []
        for e in all_events:
            text = e.get('text', '').lower()
            
            # Проверяем: это космос?
            is_space = any(word in text for word in SPACE_KEYWORDS)
            # Проверяем: это не война?
            has_politics = any(word in text for word in STOP_WORDS)
            
            if is_space and not has_politics:
                found.append(e)
            elif is_space and has_politics:
                print(f"🚫 Пропущено (политика/война): {text[:50]}...")
        
        return found
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        return []

def send_to_telegram():
    events = get_cosmic_lesson()
    
    if not events:
        print("📭 Космических событий на сегодня не найдено в базе.")
        return

    # Выбираем главное событие
    main_event = events[0]
    # Приоритет событию с картинкой
    for e in events:
        if 'pages' in e and e['pages'][0].get('originalimage'):
            main_event = e
            break

    year = main_event.get('year')
    raw_text = main_event.get('text', '')
    
    print(f"📝 Перевожу событие {year} года...")
    text_ru = translator.translate(raw_text)
    
    # Собираем пост (Картинка в Телеграм всегда будет сверху, если она есть)
    caption = (
        f"👨‍🚀 <b>УРОК КОСМИЧЕСКОЙ ИСТОРИИ</b>\n"
        f"📅 <b>Тема: {datetime.now().strftime('%d %B')} {year} года</b>\n"
        f"─────────────────────\n\n"
        f"📖 <b>ЧТО ПРОИЗОШЛО:</b>\n"
        f"{text_ru}\n\n"
    )

    # Добавляем 2 доп. факта для интереса
    other = [e for e in events if e != main_event]
    if other:
        caption += "🔍 <b>ДОПОЛНИТЕЛЬНО В ЭТОТ ДЕНЬ:</b>\n"
        for f in other[:2]:
            f_text = translator.translate(f.get('text', ''))
            caption += f"• В {f.get('year')}г. — {f_text}\n"
        caption += "\n"

    caption += (
        f"⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
        f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
    )

    photo_url = None
    if 'pages' in main_event and main_event['pages'][0].get('originalimage'):
        photo_url = main_event['pages'][0]['originalimage']['source']

    base_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
    
    if photo_url:
        print(f"📸 Отправляю фото урока: {photo_url}")
        payload = {'chat_id': CHANNEL_NAME, 'photo': photo_url, 'caption': caption, 'parse_mode': 'HTML'}
        requests.post(f"{base_url}/sendPhoto", data=payload)
    else:
        print("📝 Отправляю текстовый урок (фото не найдено).")
        requests.post(f"{base_url}/sendMessage", data={'chat_id': CHANNEL_NAME, 'text': caption, 'parse_mode': 'HTML'})

if __name__ == '__main__':
    send_to_telegram()
