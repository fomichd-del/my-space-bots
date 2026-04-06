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

# 🚀 КОСМИЧЕСКИЙ ФИЛЬТР
SPACE_ONLY = ['space', 'nasa', 'rocket', 'planet', 'pioneer', 'voyager', 'apollo', 'soyuz', 'shuttle', 'iss', 'orbit', 'launch', 'telescope']
FORBIDDEN = ['war', 'military', 'nuclear', 'test', 'explosion', 'army', 'politics', 'weapon', 'война', 'ядерный', 'испытание', 'взрыв']

# 🎖 ЗОЛОТОЙ ФОНД (Развернутый урок на 6 апреля)
FALLBACK_LESSON = {
    "year": "1973",
    "title": "ЗАПУСК СТАНЦИИ «ПИОНЕР-11»",
    "description": "В этот день с Земли улетела автоматическая станция «Пионер-11». Это был настоящий смельчак среди роботов! Он отправился в невероятно долгое путешествие к самым большим планетам нашей Солнечной системы — Юпитеру и Сатурну.",
    "why_cool": "«Пионер-11» стал первым в истории человечества аппаратом, который смог вблизи сфотографировать Сатурн и его таинственные кольца. До него люди видели Сатурн только в телескопы как маленькое пятнышко.",
    "fact": "На борту аппарата закреплена золотая пластинка с посланием для инопланетян! На ней нарисовано, как выглядят люди и где находится наша Земля в огромном космосе.",
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
            if any(w in text for w in SPACE_ONLY) and not any(w in text for w in FORBIDDEN):
                return e
        return None
    except:
        return None

def send_to_telegram():
    event = get_event()
    
    # Если событие из интернета, формируем его подробно
    if event and event.get('year') != "1973": 
        year = event.get('year')
        raw_text = event.get('text', '')
        translated_text = translator.translate(raw_text)
        
        lesson = {
            "year": year,
            "title": "НОВОЕ ОТКРЫТИЕ",
            "description": translated_text,
            "why_cool": "Это событие помогло нам лучше понять, как устроена Вселенная и как работают законы физики в космосе.",
            "fact": "Каждый такой запуск или открытие приближает нас к моменту, когда люди смогут свободно путешествовать между звездами!",
            "image": event['pages'][0].get('originalimage', {}).get('source') if 'pages' in event else None
        }
    else:
        # Берем наш детальный резерв
        lesson = FALLBACK_LESSON

    # ФОРМИРУЕМ КРАСИВЫЙ ПОСТ
    caption = (
        f"👨‍🚀 <b>УРОК КОСМИЧЕСКОЙ ИСТОРИИ</b>\n"
        f"📅 <b>Тема: {datetime.now().strftime('%d %B')} {lesson['year']} года</b>\n"
        f"─────────────────────\n\n"
        f"🚀 <b>{lesson['title']}</b>\n\n"
        f"📖 <b>ЧТО ПРОИЗОШЛО:</b>\n{lesson['description']}\n\n"
        f"🌟 <b>ПОЧЕМУ ЭТО ВАЖНО:</b>\n{lesson['why_cool']}\n\n"
        f"💡 <b>А ТЫ ЗНАЛ, ЧТО...</b>\n{lesson['fact']}\n\n"
        f"⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
        f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
    )

    base_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
    
    if lesson.get('image'):
        payload = {'chat_id': CHANNEL_NAME, 'photo': lesson['image'], 'caption': caption, 'parse_mode': 'HTML'}
        requests.post(f"{base_url}/sendPhoto", data=payload)
    else:
        requests.post(f"{base_url}/sendMessage", data={'chat_id': CHANNEL_NAME, 'text': caption, 'parse_mode': 'HTML'})

if __name__ == '__main__':
    send_to_telegram()
