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
DB_FILE        = "last_history_event.txt"

translator = GoogleTranslator(source='auto', target='ru')

# Заголовки для обхода блокировок
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) SpaceEducationBot/1.0'}

def get_space_devs_event():
    """Источник №1: Профессиональный архив запусков и событий (The Space Devs)"""
    today = datetime.now()
    # Запрашиваем события на конкретный месяц и день
    url = f"https://ll.thespacedevs.com/2.2.0/event/?date__month={today.month}&date__day={today.day}&limit=5"
    
    try:
        print(f"📡 Сканирую глобальный космический архив на {today.day}/{today.month}...")
        response = requests.get(url, headers=HEADERS, timeout=30)
        if response.status_code != 200:
            return None
        
        results = response.json().get('results', [])
        if not results:
            return None

        # Выбираем случайное историческое событие
        event = random.choice(results)
        dt = datetime.fromisoformat(event['date'].replace('Z', '+00:00'))
        
        return {
            'year': dt.year,
            'text': event['description'],
            'img': event.get('feature_image'),
            'title': event.get('name'),
            'source': 'The Space Devs Archive'
        }
    except Exception as e:
        print(f"⚠️ Ошибка Space Devs: {e}")
        return None

def get_nasa_archive_event():
    """Источник №2: Поиск по официальным архивам NASA за этот день"""
    today = datetime.now()
    month_name = today.strftime("%B")
    query = f"{month_name} {today.day}"
    url = f"https://images-api.nasa.gov/search?q={query}&media_type=image"
    
    try:
        print(f"📡 Ищу в фото-архивах NASA за {query}...")
        response = requests.get(url, headers=HEADERS, timeout=30)
        if response.status_code != 200:
            return None
            
        items = response.json()['collection']['items']
        if not items:
            return None

        # Берем случайный исторический кадр
        item = random.choice(items[:15])
        data = item['data'][0]
        
        # Пытаемся вытащить год из даты создания
        year = today.year - 10 # Запасной вариант
        if 'date_created' in data:
            year = data['date_created'].split('-')[0]

        return {
            'year': year,
            'text': data.get('description', data.get('title')),
            'img': item['links'][0]['href'],
            'title': data.get('title'),
            'source': 'NASA Historical Library'
        }
    except Exception as e:
        print(f"⚠️ Ошибка NASA Archive: {e}")
        return None

def send_history():
    # Пробуем основной источник (самый точный)
    event = get_space_devs_event()
    
    # Если там ничего нет, идем в архив NASA
    if not event:
        event = get_nasa_archive_event()
        
    if not event:
        print("📭 Сегодня тихий день в истории космоса.")
        return

    # Проверка на дубликаты (по году и части текста)
    event_key = f"{event['year']}_{event['title'][:20]}"
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            if event_key in f.read():
                print(f"✋ Событие {event_key} уже было опубликовано.")
                return

    # Перевод
    print(f"📝 Найдено событие: {event['title']}. Перевожу...")
    title_ru = translator.translate(event['title'])
    # Описание часто длинное, берем 3-4 предложения
    short_desc = '. '.join(event['text'].split('.')[:4]) + '.'
    desc_ru = translator.translate(short_desc)
    
    caption = (
        f"📜 <b>УРОК КОСМИЧЕСКОЙ ИСТОРИИ</b>\n"
        f"📅 <b>Дата: {datetime.now().day}.{datetime.now().month}.{event['year']} года</b>\n"
        f"─────────────────────\n\n"
        f"🚀 <b>СОБЫТИЕ: {title_ru.upper()}</b>\n\n"
        f"📖 <b>ЧТО ПРОИЗОШЛО:</b>\n{desc_ru}\n\n"
        f"🔭 <i>Источник: {event['source']}</i>\n\n"
        f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
    )

    # Отправка
    payload = {
        'chat_id': CHANNEL_NAME,
        'photo': event['img'] or "https://images.unsplash.com/photo-1451187580459-43490279c0fa",
        'caption': caption,
        'parse_mode': 'HTML'
    }
    
    r = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto", data=payload)
    
    if r.status_code == 200:
        with open(DB_FILE, 'a', encoding='utf-8') as f:
            f.write(f"{event_key}\n")
        print(f"✅ Пост успешно отправлен!")
    else:
        print(f"❌ Ошибка Telegram: {r.text}")

if __name__ == '__main__':
    send_history()
