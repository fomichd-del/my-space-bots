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

# 🛰 КОСМИЧЕСКИЕ КЛЮЧИ (Расширил для точности)
SPACE_KEYWORDS = [
    'space', 'nasa', 'rocket', 'satellite', 'planet', 'star', 'astronomy',
    'pioneer', 'voyager', 'apollo', 'soyuz', 'shuttle', 'iss', 'orbit',
    'launch', 'telescope', 'hubble', 'galaxy', 'cosmos', 'comet', 'nebula',
    'asteroid', 'discovery', 'observed', 'moon', 'mars', 'intelsat'
]

# 🚫 ФИЛЬТР (Политика и война)
STOP_WORDS = [
    'war', 'military', 'army', 'battle', 'killed', 'politics', 'weapon',
    'война', 'военный', 'армия', 'битва', 'убит', 'оружие', 'база', 'штаб',
    'агрессия', 'удар', 'вторжение', 'конфликт', 'сирия', 'missile'
]

def get_cosmic_lesson():
    now = datetime.now()
    # Стучимся в английскую базу (она самая полная)
    url = f"https://en.wikipedia.org/api/rest_v1/feed/onthisday/all/{now.month}/{now.day}"
    
    # 🛡 ВАЖНО: Добавляем "паспорт" для Википедии, чтобы не было ошибки 403
    headers = {
        'User-Agent': 'VladislavSpaceBot/1.0 (https://t.me/vladislav_space; contact: your-email@example.com)'
    }
    
    try:
        print(f"📡 Подключаюсь к архивам за {now.day}/{now.month}...")
        r = requests.get(url, headers=headers, timeout=30)
        
        if r.status_code != 200:
            print(f"❌ Ошибка доступа к Википедии: {r.status_code}")
            return []
        
        data = r.json()
        # Собираем все события
        all_events = data.get('selected', []) + data.get('events', [])
        
        print(f"🔎 Проверяю {len(all_events)} событий на 'космичность'...")
        
        found = []
        for e in all_events:
            text = e.get('text', '').lower()
            
            is_space = any(word in text for word in SPACE_KEYWORDS)
            has_politics = any(word in text for word in STOP_WORDS)
            
            if is_space and not has_politics:
                found.append(e)
            elif is_space and has_politics:
                print(f"🚫 Отфильтровано (политика): {text[:60]}...")
        
        return found
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        return []

def send_to_telegram():
    events = get_cosmic_lesson()
    
    if not events:
        print("📭 Космических уроков на сегодня не найдено.")
        return

    # Выбираем главное событие (лучше с картинкой)
    main_event = events[0]
    for e in events:
        if 'pages' in e and e['pages'][0].get('originalimage'):
            main_event = e
            break

    year = main_event.get('year')
    raw_text = main_event.get('text', '')
    
    print(f"📝 Перевожу событие {year} года...")
    text_ru = translator.translate(raw_text)
    
    # Оформление (Картинка всегда сверху)
    caption = (
        f"👨‍🚀 <b>УРОК КОСМИЧЕСКОЙ ИСТОРИИ</b>\n"
        f"📅 <b>Тема: {datetime.now().strftime('%d %B')} {year} года</b>\n"
        f"─────────────────────\n\n"
        f"📖 <b>ЧТО ПРОИЗОШЛО:</b>\n"
        f"{text_ru}\n\n"
    )

    # Добавляем 2 доп. факта
    other = [e for e in events if e != main_event]
    if other:
        caption += "🔍 <b>ДОПОЛНИТЕЛЬНО:</b>\n"
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
        print(f"📸 Отправляю фото урока...")
        payload = {'chat_id': CHANNEL_NAME, 'photo': photo_url, 'caption': caption, 'parse_mode': 'HTML'}
        requests.post(f"{base_url}/sendPhoto", data=payload)
    else:
        print("📝 Отправляю текстовый урок...")
        requests.post(f"{base_url}/sendMessage", data={'chat_id': CHANNEL_NAME, 'text': caption, 'parse_mode': 'HTML'})
    
    print("✅ Готово!")

if __name__ == '__main__':
    send_to_telegram()
