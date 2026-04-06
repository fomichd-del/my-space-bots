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

# 🚀 СУПЕР-КОСМИЧЕСКИЕ СЛОВА (Обязательно наличие хотя бы одного)
STRICT_SPACE = [
    'nasa', 'наса', 'байконур', 'космонавт', 'астронавт', 'космодром', 
    'мкс', 'iss', 'pioneer', 'voyager', 'apollo', 'аполлон', 'гагарин', 
    'спутник', 'луноход', 'марсоход', 'hubble', 'хаббл', 'telescope', 
    'shuttle', 'шаттл', 'запуск ракеты', 'космический аппарат'
]

# 🚫 ТОТАЛЬНОЕ ТАБУ (Если есть хоть одно слово — удаляем факт)
TOTAL_STOP = [
    'война', 'армия', 'битва', 'база', 'штаб', 'оружие', 'атака', 'конфликт', 
    'президент', 'политика', 'министр', 'правительство', 'сирия', 'удар', 
    'обстрел', 'терроризм', 'военный', 'war', 'military', 'politics'
]

def get_pure_space_lesson():
    now = datetime.now()
    # Берем английскую базу "ALL" - там больше всего науки
    url = f"https://en.wikipedia.org/api/rest_v1/feed/onthisday/all/{now.month:02d}/{now.day:02d}"
    
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    try:
        r = requests.get(url, headers=headers, timeout=30)
        if r.status_code != 200: return []
        data = r.json()
        
        all_events = data.get('selected', []) + data.get('events', [])
        pure_space = []
        
        for e in all_events:
            text = e.get('text', '').lower()
            
            # Проверка 1: Есть ли супер-космическое слово?
            is_real_space = any(word in text for word in STRICT_SPACE)
            # Проверка 2: Нет ли политики/войны?
            has_trash = any(word in text for word in TOTAL_STOP)
            
            if is_real_space and not has_trash:
                pure_space.append(e)
        
        return pure_space
    except:
        return []

def send_to_telegram():
    events = get_pure_space_lesson()
    
    if not events:
        print("📭 Реальных космических уроков на сегодня не найдено. Пост не создаем.")
        return

    # Выбираем главное событие
    main_event = events[0]
    for e in events:
        if 'pages' in e and e['pages'][0].get('originalimage'):
            main_event = e
            break

    year = main_event.get('year')
    text_ru = translator.translate(main_event.get('text', ''))
    
    # 👨‍🚀 ОФОРМЛЕНИЕ УРОКА
    caption = (
        f"👨‍🚀 <b>УРОК КОСМИЧЕСКОЙ ИСТОРИИ</b>\n"
        f"📅 <b>Тема: {datetime.now().strftime('%d %B')} {year} года</b>\n"
        f"─────────────────────\n\n"
        f"📖 <b>ЧЕМУ МЫ УЧИМСЯ:</b>\n"
        f"{text_ru}\n\n"
    )

    # Добавляем 2 доп. факта, если они ЕСТЬ и они КОСМИЧЕСКИЕ
    other = [e for e in events if e != main_event]
    if other:
        caption += "🔍 <b>ЕЩЕ ОДНО ОТКРЫТИЕ:</b>\n"
        for f in other[:1]: # Берем только один самый четкий
            f_text = translator.translate(f.get('text', ''))
            caption += f"• В {f.get('year')}г. — {f_text}\n"

    caption += (
        f"\n⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
        f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
    )

    photo_url = None
    if 'pages' in main_event and main_event['pages'][0].get('originalimage'):
        photo_url = main_event['pages'][0]['originalimage']['source']

    base_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
    
    if photo_url:
        # В телеграм ФОТО всегда идет ВЫШЕ текста подписи
        payload = {'chat_id': CHANNEL_NAME, 'photo': photo_url, 'caption': caption, 'parse_mode': 'HTML'}
        requests.post(f"{base_url}/sendPhoto", data=payload)
    else:
        requests.post(f"{base_url}/sendMessage", data={'chat_id': CHANNEL_NAME, 'text': caption, 'parse_mode': 'HTML'})
    
    print("✅ Космический урок успешно отправлен!")

if __name__ == '__main__':
    send_to_telegram()
