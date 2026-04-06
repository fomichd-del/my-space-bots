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

# 🌌 ТЕМЫ ДЛЯ УРОКА
SPACE_TERMS = [
    'space', 'nasa', 'rocket', 'planet', 'star', 'astronomer', 'pioneer', 
    'voyager', 'apollo', 'soyuz', 'shuttle', 'iss', 'orbit', 'launch', 
    'telescope', 'hubble', 'galaxy', 'cosmos', 'comet', 'nebula', 'asteroid', 
    'discovery', 'observed', 'moon', 'mars', 'jupiter', 'saturn'
]

# 🚫 ЗАПРЕТНЫЕ ТЕМЫ (Анти-политика)
STOP_WORDS = [
    'war', 'military', 'army', 'battle', 'killed', 'politics', 'weapon',
    'война', 'военный', 'армия', 'битва', 'убит', 'оружие', 'база', 'штаб'
]

def get_lesson_content():
    now = datetime.now()
    month, day = now.month, now.day
    
    # Ищем в международной базе (EN) и русской (RU)
    urls = [
        f"https://en.wikipedia.org/api/rest_v1/feed/onthisday/selected/{month}/{day}",
        f"https://en.wikipedia.org/api/rest_v1/feed/onthisday/events/{month}/{day}",
        f"https://ru.wikipedia.org/api/rest_v1/feed/onthisday/events/{month}/{day}"
    ]
    
    found_events = []
    for url in urls:
        try:
            r = requests.get(url, timeout=25)
            if r.status_code != 200: continue
            data = r.json()
            batch = data.get('selected', []) + data.get('events', [])
            
            for e in batch:
                text = e.get('text', '').lower()
                if any(word in text for word in SPACE_TERMS) and not any(word in text for word in STOP_WORDS):
                    found_events.append(e)
            if len(found_events) > 5: break
        except:
            continue
    return found_events

def send_to_telegram():
    events = get_lesson_content()
    if not events:
        print("📭 На сегодня уроков истории не найдено.")
        return

    # Выбираем событие с картинкой (для "Урока" это обязательно)
    main_event = events[0]
    for e in events:
        if 'pages' in e and e['pages'][0].get('originalimage'):
            main_event = e
            break

    year = main_event.get('year')
    title_ru = translator.translate(main_event.get('text', ''))
    
    # Формируем пост в стиле урока
    caption = (
        f"🎬 <b>УРОК КОСМИЧЕСКОЙ ИСТОРИИ</b> 🧑‍🚀\n"
        f"📅 <b>Тема дня: {datetime.now().strftime('%d %B')} {year} года</b>\n"
        f"─────────────────────\n\n"
        f"📖 <b>ЧТО МЫ ИЗУЧАЕМ:</b>\n"
        f"{title_ru}\n\n"
    )

    # Добавляем дополнительные факты ("Домашнее чтение")
    extra = [e for e in events if e != main_event]
    if extra:
        caption += "🔍 <b>ДОПОЛНИТЕЛЬНЫЕ ФАКТЫ:</b>\n"
        for f in extra[:2]:
            f_text = translator.translate(f.get('text', ''))
            caption += f"• В {f.get('year')} году: {f_text}\n"
        caption += "\n"

    caption += (
        f"⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
        f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
    )

    photo_url = None
    if 'pages' in main_event and main_event['pages'][0].get('originalimage'):
        photo_url = main_event['pages'][0]['originalimage']['source']

    base_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
    
    # Отправляем фото СВЕРХУ
    if photo_url:
        payload = {
            'chat_id': CHANNEL_NAME,
            'photo': photo_url,
            'caption': caption,
            'parse_mode': 'HTML'
        }
        requests.post(f"{base_url}/sendPhoto", data=payload)
    else:
        # Если фото нет, шлем текст с иконкой урока
        payload = {
            'chat_id': CHANNEL_NAME,
            'text': "📚 " + caption,
            'parse_mode': 'HTML',
            'link_preview_options': {'is_disabled': True}
        }
        requests.post(f"{base_url}/sendMessage", json=payload)

if __name__ == '__main__':
    send_to_telegram()
