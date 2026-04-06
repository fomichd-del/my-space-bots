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

# 🛰 КОСМИЧЕСКИЕ ТЕМЫ (То, что мы любим)
GOOD_WORDS = [
    'space', 'nasa', 'rocket', 'satellite', 'planet', 'star', 'astronomy',
    'pioneer', 'voyager', 'apollo', 'soyuz', 'shuttle', 'iss', 'orbit',
    'launch', 'telescope', 'hubble', 'galaxy', 'cosmos', 'comet', 'nebula',
    'moon', 'mars', 'intelsat', 'exploration', 'discovery'
]

# 🚫 ТАБУ (То, что мы ненавидим: война, базы, Сирия)
STOP_WORDS = [
    'war', 'military', 'army', 'battle', 'killed', 'politics', 'weapon',
    'война', 'военный', 'армия', 'битва', 'убит', 'оружие', 'база', 'штаб',
    'агрессия', 'удар', 'вторжение', 'конфликт', 'сирия', 'missile', 'tomahawk'
]

def get_cosmic_data():
    now = datetime.now()
    month, day = now.month, now.day
    
    # Пытаемся по очереди: RU база, потом EN база (Selected), потом EN база (All)
    urls = [
        f"https://ru.wikipedia.org/api/rest_v1/feed/onthisday/events/{month}/{day}",
        f"https://en.wikipedia.org/api/rest_v1/feed/onthisday/selected/{month}/{day}",
        f"https://en.wikipedia.org/api/rest_v1/feed/onthisday/all/{month}/{day}"
    ]
    
    for url in urls:
        try:
            print(f"📡 Проверяю источник: {url}")
            r = requests.get(url, timeout=30)
            if r.status_code != 200: continue
            
            data = r.json()
            # Собираем все типы событий
            events = data.get('selected', []) + data.get('events', [])
            
            filtered = []
            for e in events:
                text = e.get('text', '').lower()
                # Проверка: есть космос и НЕТ войны
                if any(w in text for w in GOOD_WORDS) and not any(w in text for w in STOP_WORDS):
                    filtered.append(e)
            
            if filtered:
                return filtered
        except Exception as e:
            print(f"⚠️ Ошибка при чтении {url}: {e}")
            continue
    return []

def send_to_telegram():
    events = get_cosmic_data()
    
    if not events:
        print("📭 Космических уроков на сегодня не найдено.")
        return

    # Выбираем главное событие (лучше с фото)
    main_event = events[0]
    for e in events:
        if 'pages' in e and e['pages'][0].get('originalimage'):
            main_event = e
            break

    year = main_event.get('year')
    text_ru = translator.translate(main_event.get('text', ''))
    
    # 🖼 ФОРМИРУЕМ ПОСТ (Картинка будет СВЕРХУ)
    caption = (
        f"👨‍🚀 <b>УРОК КОСМИЧЕСКОЙ ИСТОРИИ</b>\n"
        f"📅 <b>Тема: {datetime.now().strftime('%d %B')} {year} года</b>\n"
        f"─────────────────────\n\n"
        f"📖 <b>ЧТО ПРОИЗОШЛО:</b>\n"
        f"{text_ru}\n\n"
    )

    # Добавляем еще пару фактов для интереса
    other = [e for e in events if e != main_event]
    if other:
        caption += "🔍 <b>ДОПОЛНИТЕЛЬНО:</b>\n"
        for f in other[:2]:
            f_year = f.get('year')
            f_text = translator.translate(f.get('text', ''))
            caption += f"• В {f_year}г. — {f_text}\n"
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
        # Отправляем фото — в Телеграм оно всегда сверху текста
        payload = {
            'chat_id': CHANNEL_NAME,
            'photo': photo_url,
            'caption': caption,
            'parse_mode': 'HTML'
        }
        requests.post(f"{base_url}/sendPhoto", data=payload)
    else:
        # Если фото нет — шлем просто текст
        requests.post(f"{base_url}/sendMessage", data={'chat_id': CHANNEL_NAME, 'text': caption, 'parse_mode': 'HTML'})

if __name__ == '__main__':
    send_to_telegram()
