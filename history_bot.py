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

translator = GoogleTranslator(source='auto', target='ru')

# 🚀 КОСМИЧЕСКИЕ КЛЮЧИ
SPACE_KEYWORDS = [
    'space', 'nasa', 'rocket', 'satellite', 'planet', 'star', 'astronomy',
    'pioneer', 'voyager', 'apollo', 'soyuz', 'shuttle', 'iss', 'orbit',
    'launch', 'telescope', 'hubble', 'galaxy', 'cosmos', 'comet', 'nebula',
    'asteroid', 'discovery', 'observed', 'moon', 'mars', 'intelsat'
]

# 🚫 СТОП-СЛОВА
STOP_WORDS = [
    'war', 'military', 'army', 'battle', 'killed', 'politics', 'weapon',
    'война', 'военный', 'армия', 'битва', 'убит', 'оружие', 'база', 'штаб',
    'агрессия', 'удар', 'вторжение', 'конфликт', 'сирия'
]

def get_cosmic_lesson():
    now = datetime.now()
    month = f"{now.month:02d}" # Делаем 04 вместо 4
    day = f"{now.day:02d}"     # Делаем 06 вместо 6
    
    # Списки адресов для проверки (если один даст 404, пробуем другой)
    urls = [
        f"https://en.wikipedia.org/api/rest_v1/feed/onthisday/all/{month}/{day}",
        f"https://en.wikipedia.org/api/rest_v1/feed/onthisday/selected/{month}/{day}",
        f"https://ru.wikipedia.org/api/rest_v1/feed/onthisday/events/{month}/{day}"
    ]
    
    # 🛡 МАСКИРОВКА ПОД БРАУЗЕР (чтобы не было 403 и 404)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9'
    }
    
    for url in urls:
        try:
            print(f"📡 Пробую достучаться до: {url}")
            r = requests.get(url, headers=headers, timeout=30)
            
            if r.status_code == 200:
                data = r.json()
                all_events = data.get('selected', []) + data.get('events', [])
                
                found = []
                for e in all_events:
                    text = e.get('text', '').lower()
                    if any(w in text for w in SPACE_KEYWORDS) and not any(w in text for w in STOP_WORDS):
                        found.append(e)
                
                if found:
                    print(f"✅ Найдено {len(found)} событий!")
                    return found
            else:
                print(f"⚠️ Сервер ответил кодом: {r.status_code}")
        except Exception as e:
            print(f"❌ Ошибка запроса: {e}")
            continue
    return []

def send_to_telegram():
    events = get_cosmic_lesson()
    
    if not events:
        print("📭 Космических уроков на сегодня не найдено.")
        return

    # Выбираем главное событие с картинкой
    main_event = events[0]
    for e in events:
        if 'pages' in e and e['pages'][0].get('originalimage'):
            main_event = e
            break

    year = main_event.get('year')
    text_ru = translator.translate(main_event.get('text', ''))
    
    # 🎨 ОФОРМЛЕНИЕ (Картинка всегда сверху)
    caption = (
        f"👨‍🚀 <b>УРОК КОСМИЧЕСКОЙ ИСТОРИИ</b>\n"
        f"📅 <b>Тема: {datetime.now().strftime('%d %B')} {year} года</b>\n"
        f"─────────────────────\n\n"
        f"📖 <b>ЧТО ПРОИЗОШЛО:</b>\n"
        f"{text_ru}\n\n"
    )

    other = [e for e in events if e != main_event]
    if other:
        caption += "🔍 <b>ДОПОЛНИТЕЛЬНЫЕ ФАКТЫ:</b>\n"
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
        print(f"📸 Отправляю урок с фото: {photo_url}")
        payload = {'chat_id': CHANNEL_NAME, 'photo': photo_url, 'caption': caption, 'parse_mode': 'HTML'}
        requests.post(f"{base_url}/sendPhoto", data=payload)
    else:
        print("📝 Отправляю текстовый урок...")
        requests.post(f"{base_url}/sendMessage", data={'chat_id': CHANNEL_NAME, 'text': caption, 'parse_mode': 'HTML'})

if __name__ == '__main__':
    send_to_telegram()
