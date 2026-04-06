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

# 🚫 ТОТАЛЬНЫЙ ЗАПРЕТ (Никакой политики, ядерных тестов и агрессии)
FORBIDDEN = [
    'war', 'military', 'nuclear', 'test', 'explosion', 'army', 'politics', 'weapon',
    'война', 'ядерный', 'испытание', 'взрыв', 'полигон', 'армия', 'битва', 'убит'
]

# 🚀 ТОЛЬКО КОСМОС
SPACE_ONLY = [
    'space', 'nasa', 'rocket', 'satellite', 'planet', 'pioneer', 'voyager', 
    'apollo', 'soyuz', 'shuttle', 'iss', 'orbit', 'launch', 'telescope'
]

# 🎖 РЕЗЕРВНЫЕ УРОКИ (Если сайт упал или не нашел космос)
# Если на 6 апреля ничего не найдется, бот возьмет этот факт
FALLBACK_LESSON = {
    "year": "1973",
    "text": "The Pioneer 11 spacecraft was launched. It became the first human-made object to encounter Saturn and send back close-up pictures of its rings!",
    "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/60/Pioneer_11.jpg/800px-Pioneer_11.jpg"
}

def get_pure_space_event():
    now = datetime.now()
    url = f"https://en.wikipedia.org/api/rest_v1/feed/onthisday/all/{now.month:02d}/{now.day:02d}"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) SpaceExplorer/1.0'}
    
    try:
        r = requests.get(url, headers=headers, timeout=30)
        if r.status_code != 200: return None
        data = r.json()
        
        # Собираем все события
        events = data.get('selected', []) + data.get('events', [])
        
        for e in events:
            text = e.get('text', '').lower()
            # Проверка: есть космос и НЕТ ядерных испытаний/войны
            if any(w in text for w in SPACE_ONLY) and not any(w in text for w in FORBIDDEN):
                return e
        return None
    except:
        return None

def send_to_telegram():
    event = get_pure_space_event()
    
    # Если интернет-база подвела, берем наш золотой запас
    if not event:
        print("🛰 Использую резервный космический урок...")
        event = FALLBACK_LESSON

    year = event.get('year')
    raw_text = event.get('text', '')
    
    # Перевод и адаптация для ребенка
    translated = translator.translate(raw_text)
    
    # ФОРМИРУЕМ ПОСТ (Картинка в Telegram всегда выше текста в подписи)
    caption = (
        f"🎬 <b>УРОК КОСМИЧЕСКОЙ ИСТОРИИ</b> 🧑‍🚀\n"
        f"📅 <b>Тема: {datetime.now().strftime('%d %B')} {year} года</b>\n"
        f"─────────────────────\n\n"
        f"🌟 <b>ЗНАЕШЬ ЛИ ТЫ, ЧТО:</b>\n"
        f"{translated}\n\n"
        f"⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
        f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
    )

    # Ищем фото (в событии или берем из резерва)
    photo_url = None
    if 'image' in event: # Для резервного факта
        photo_url = event['image']
    elif 'pages' in event and event['pages'][0].get('originalimage'):
        photo_url = event['pages'][0]['originalimage']['source']

    base_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
    
    if photo_url:
        payload = {'chat_id': CHANNEL_NAME, 'photo': photo_url, 'caption': caption, 'parse_mode': 'HTML'}
        requests.post(f"{base_url}/sendPhoto", data=payload)
    else:
        requests.post(f"{base_url}/sendMessage", data={'chat_id': CHANNEL_NAME, 'text': caption, 'parse_mode': 'HTML'})
    
    print("✅ Урок успешно отправлен!")

if __name__ == '__main__':
    send_to_telegram()
