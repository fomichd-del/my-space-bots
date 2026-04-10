import requests
import os
from datetime import datetime
from deep_translator import GoogleTranslator

# ============================================================
# ⚙️ НАСТРОЙКИ
# ============================================================
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHANNEL_NAME   = '@vladislav_space'
DB_FILE        = "last_history_event.txt" # Файл памяти

translator = GoogleTranslator(source='auto', target='ru')

# 🚀 КОСМИЧЕСКИЕ КЛЮЧИ
SPACE_WORDS = ['space', 'nasa', 'rocket', 'planet', 'pioneer', 'voyager', 'apollo', 'soyuz', 'shuttle', 'iss', 'orbit', 'launch', 'telescope']
FORBIDDEN = ['war', 'military', 'nuclear', 'test', 'explosion', 'army', 'politics', 'weapon', 'война', 'ядерный', 'испытание']

def get_detailed_summary(page_title):
    """Заходит вглубь Википедии и берет подробное описание статьи"""
    url = f"https://ru.wikipedia.org/api/rest_v1/page/summary/{page_title}"
    try:
        r = requests.get(url, timeout=20)
        if r.status_code == 200:
            data = r.json()
            return data.get('extract', '')
    except:
        return ""
    return ""

def get_event():
    """Ищет подходящее космическое событие на текущий день"""
    now = datetime.now()
    url = f"https://en.wikipedia.org/api/rest_v1/feed/onthisday/all/{now.month:02d}/{now.day:02d}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        r = requests.get(url, headers=headers, timeout=30)
        data = r.json()
        events = data.get('selected', []) + data.get('events', [])
        for e in events:
            text = e.get('text', '').lower()
            # Проверяем, чтобы было про космос и не было запрещенных тем
            if any(w in text for w in SPACE_WORDS) and not any(w in text for w in FORBIDDEN):
                return e
        return None
    except:
        return None

def send_to_telegram():
    event = get_event()
    if not event:
        print("📭 Космических событий на сегодня не найдено.")
        return

    year = event.get('year')
    page_title = event['pages'][0]['title'] if 'pages' in event else ""
    
    # --- ПРОВЕРКА НА ПОВТОРЫ ---
    # Создаем уникальный ключ события (год + заголовок страницы)
    current_event_id = f"{year}_{page_title}"
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            if f.read().strip() == current_event_id:
                print(f"✋ Событие '{current_event_id}' уже публиковалось ранее.")
                return

    # Пытаемся получить развернутый текст из русской Википедии
    detailed_info = get_detailed_summary(page_title)
    if not detailed_info:
        detailed_info = translator.translate(event.get('text', ''))

    # Спец-кейсы для оформления (твой авторский блок)
    if year == "1973" and "Pioneer" in page_title:
        title = "ЛЕГЕНДАРНЫЙ ПРЫЖОК К САТУРНУ: ПИОНЕР-11"
        purpose = "Главной целью было изучение пояса астероидов и гигантских планет. Ученые хотели впервые увидеть Сатурн и его кольца так близко, как никогда раньше."
        result = "Аппарат летел 6 лет! В итоге он открыл новое кольцо Сатурна и показал нам, что там бушуют мощные штормы. А еще он доказал, что через пояс астероидов можно летать безопасно."
        fact = "На его борту закреплена золотая пластинка с рисунками людей. Это письмо в бутылке, брошенное в космический океан!"
    else:
        title = "КОСМИЧЕСКАЯ МИССИЯ"
        purpose = "Изучение новых границ нашей Вселенной и проверка технологий, которые позволят людям в будущем жить на других планетах."
        result = "Это событие дало ученым бесценные данные, которые мы используем сегодня для запусков современных ракет SpaceX и постройки новых телескопов."
        fact = "Знаешь ли ты, что каждый такой запуск — это труд тысяч инженеров, которые работают, чтобы мы знали о звездах больше?"

    # ОФОРМЛЕНИЕ
    caption = (
        f"👨‍🚀 <b>УРОК КОСМИЧЕСКОЙ ИСТОРИИ</b>\n"
        f"📅 <b>Дата: {datetime.now().strftime('%d %B')} {year} года</b>\n"
        f"─────────────────────\n\n"
        f"🚀 <b>{title}</b>\n\n"
        f"📖 <b>ЧТО ПРОИЗОШЛО:</b>\n{detailed_info[:500]}...\n\n"
        f"🎯 <b>ОСНОВНАЯ ЦЕЛЬ:</b>\n{purpose}\n\n"
        f"✅ <b>ИТОГ И РЕЗУЛЬТАТ:</b>\n{result}\n\n"
        f"💡 <b>А ТЫ ЗНАЛ, ЧТО...</b>\n{fact}\n\n"
        f"⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
        f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
    )

    photo_url = event['pages'][0].get('originalimage', {}).get('source') if 'pages' in event else None
    base_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
    
    # Отправка
    if photo_url:
        r = requests.post(f"{base_url}/sendPhoto", data={'chat_id': CHANNEL_NAME, 'photo': photo_url, 'caption': caption, 'parse_mode': 'HTML'})
    else:
        r = requests.post(f"{base_url}/sendMessage", data={'chat_id': CHANNEL_NAME, 'text': caption, 'parse_mode': 'HTML'})

    # Если отправка успешна — записываем в память
    if r.status_code == 200:
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            f.write(current_event_id)
        print(f"✅ Пост за {year} год успешно опубликован!")

if __name__ == '__main__':
    send_to_telegram()
