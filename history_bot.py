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

# 🚀 ФИЛЬТРЫ
SPACE_WORDS = ['space', 'nasa', 'rocket', 'planet', 'pioneer', 'voyager', 'apollo', 'soyuz', 'shuttle', 'iss', 'orbit', 'launch', 'telescope']
FORBIDDEN = ['war', 'military', 'nuclear', 'test', 'explosion', 'army', 'politics', 'weapon', 'война', 'ядерный', 'испытание', 'взрыв']

# 🎖 ПОДРОБНЫЙ УРОК НА 6 АПРЕЛЯ (Если сайт не выдаст детали)
FALLBACK_LESSON = {
    "year": "1973",
    "title": "МИССИЯ «ПИОНЕР-11»: ПУТЕШЕСТВИЕ К ГИГАНТАМ",
    "description": "В этот день с Земли стартовал космический аппарат «Пионер-11». Это был небольшой, но очень отважный робот-исследователь весом всего 258 килограммов.",
    "purpose": "Ученые хотели впервые в истории увидеть Сатурн вблизи. До этого мы знали об этой планете очень мало, и нам нужны были четкие фотографии её колец.",
    "result": "Аппарат летел долгих 6 лет! В 1979 году он наконец добрался до Сатурна, пролетел всего в 20 тысячах километров от него и открыл новое кольцо, которое раньше никто не видел. Он доказал, что на Сатурне очень холодно и ветрено.",
    "fact": "На борту «Пионера-11» есть золотая пластинка с посланием. Если когда-нибудь инопланетяне найдут его, они увидят карту, как найти нашу Землю!",
    "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/60/Pioneer_11.jpg/800px-Pioneer_11.jpg"
}

def get_event():
    now = datetime.now()
    url = f"https://en.wikipedia.org/api/rest_v1/feed/onthisday/all/{now.month:02d}/{now.day:02d}"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    try:
        r = requests.get(url, headers=headers, timeout=30)
        if r.status_code != 200: return None
        data = r.json()
        events = data.get('selected', []) + data.get('events', [])
        for e in events:
            text = e.get('text', '').lower()
            if any(w in text for w in SPACE_WORDS) and not any(w in text for w in FORBIDDEN):
                return e
        return None
    except:
        return None

def send_to_telegram():
    event = get_event()
    
    # Если событие сегодня — наш «Пионер-11», берем готовое глубокое описание
    if event and event.get('year') == "1973":
        lesson = FALLBACK_LESSON
    elif event:
        # Для других событий делаем перевод и базовую структуру
        year = event.get('year')
        raw_text = event.get('text', '')
        translated_text = translator.translate(raw_text)
        lesson = {
            "year": year,
            "title": "ВАЖНЫЙ ШАГ В КОСМОС",
            "description": translated_text,
            "purpose": "Это событие было частью большого плана человечества по изучению звезд и планет.",
            "result": "Благодаря этому успеху ученые получили новые знания, которые помогли нам строить более совершенные ракеты и телескопы.",
            "fact": "Каждое такое событие делает нас на шаг ближе к жизни на других планетах!",
            "image": event['pages'][0].get('originalimage', {}).get('source') if 'pages' in event else None
        }
    else:
        lesson = FALLBACK_LESSON # Резерв

    # ФОРМИРУЕМ ПОДРОБНЫЙ ПОСТ
    caption = (
        f"👨‍🚀 <b>УРОК КОСМИЧЕСКОЙ ИСТОРИИ</b>\n"
        f"📅 <b>Дата: {datetime.now().strftime('%d %B')} {lesson['year']} года</b>\n"
        f"─────────────────────\n\n"
        f"🚀 <b>{lesson['title']}</b>\n\n"
        f"📖 <b>ЧТО ЭТО БЫЛО?</b>\n{lesson['description']}\n\n"
        f"🎯 <b>ДЛЯ ЧЕГО ЭТО СДЕЛАЛИ?</b>\n{lesson['purpose']}\n\n"
        f"✅ <b>ЧТО В ИТОГЕ СЛУЧИЛОСЬ?</b>\n{lesson['result']}\n\n"
        f"💡 <b>А ТЫ ЗНАЛ, ЧТО...</b>\n{lesson['fact']}\n\n"
        f"⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
        f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
    )

    base_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
    
    if lesson.get('image'):
        # Фото СВЕРХУ, текст ПОД НИМ
        payload = {'chat_id': CHANNEL_NAME, 'photo': lesson['image'], 'caption': caption, 'parse_mode': 'HTML'}
        requests.post(f"{base_url}/sendPhoto", data=payload)
    else:
        requests.post(f"{base_url}/sendMessage", data={'chat_id': CHANNEL_NAME, 'text': caption, 'parse_mode': 'HTML'})

if __name__ == '__main__':
    send_to_telegram()
