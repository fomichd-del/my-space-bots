import requests
import os
import random
import json
from datetime import datetime
from deep_translator import GoogleTranslator

# ============================================================
# ⚙️ НАСТРОЙКИ (Командор, проверь свои секреты в GitHub!)
# ============================================================
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHANNEL_NAME   = '@vladislav_space'
NASA_API_KEY   = os.getenv('NASA_API_KEY') or "DEMO_KEY" 
HISTORY_FILE   = 'last_earth_id.txt'

translator = GoogleTranslator(source='auto', target='ru')

# ============================================================
# 🧠 МОДУЛИ ПАМЯТИ И ТРАНСЛЯЦИИ
# ============================================================

def is_already_sent(image_id):
    """Проверяет, не отправляли ли мы это фото раньше"""
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            return str(image_id) in f.read()
    return False

def save_sent_id(image_id):
    """Записывает ID фото, чтобы не было повторов"""
    with open(HISTORY_FILE, 'a', encoding='utf-8') as f:
        f.write(f"{image_id}\n")

def get_epic_data():
    """Режим 1: Полный диск Земли (с расстояния 1.5 млн км)"""
    url = f"https://api.nasa.gov/EPIC/api/natural/available?api_key={NASA_API_KEY}"
    try:
        dates = requests.get(url, timeout=20).json()
        last_date = dates[-1]
        data_url = f"https://api.nasa.gov/EPIC/api/natural/date/{last_date}?api_key={NASA_API_KEY}"
        shots = requests.get(data_url, timeout=20).json()
        
        # Фильтруем те, что уже были
        available_shots = [s for s in shots if not is_already_sent(s['image'])]
        if not available_shots: return None, None, None
        
        shot = random.choice(available_shots)
        img_id = shot['image']
        p = last_date.split("-")
        img_url = f"https://epic.gsfc.nasa.gov/archive/natural/{p[0]}/{p[1]}/{p[2]}/jpg/{img_id}.jpg"
        
        caption = (
            f"🌍 <b>ВЗГЛЯД ИЗ ТОЧКИ L1</b>\n"
            f"─────────────────────\n"
            f"Этот снимок сделал спутник <b>DSCOVR</b> с расстояния 1.5 млн км. Мы видим нашу планету целиком, как хрупкий голубой шар в бескрайней пустоте.\n\n"
            f"📅 Дата: <b>{last_date}</b>\n\n"
            f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
        )
        return img_url, caption, img_id
    except: return None, None, None

def get_extensive_library_data():
    """Режим 2: Самые зрелищные виды (МКС, Аврора, Ночные города)"""
    queries = [
        "Earth aurora from space", "Earth at night city lights", 
        "Hurricane from space ISS", "Earth and Moon distance",
        "Astronaut photography Earth", "Earth horizon sunset space",
        "Himalayas from space", "Sahara desert from space"
    ]
    q = random.choice(queries)
    url = f"https://images-api.nasa.gov/search?q={q}&media_type=image"
    
    try:
        print(f"📡 Ищу космический эксклюзив по запросу: {q}...")
        res = requests.get(url, timeout=25).json()
        items = res['collection']['items']
        random.shuffle(items)

        for item in items[:50]:
            nasa_id = item['data'][0]['nasa_id']
            if not is_already_sent(nasa_id):
                img_url = item['links'][0]['href']
                title_en = item['data'][0]['title']
                desc_en = item['data'][0].get('description', '')

                # Перевод и форматирование описания
                title_ru = translator.translate(title_en)
                sentences = desc_en.split('.')
                short_desc_en = '. '.join(sentences[:3]) + '.'
                desc_ru = translator.translate(short_desc_en)
                
                caption = (
                    f"🛰 <b>КОСМИЧЕСКИЙ РЕПОРТАЖ: {title_ru.upper()}</b>\n"
                    f"─────────────────────\n\n"
                    f"📖 <b>ЧТО НА ФОТО:</b> {desc_ru}\n\n"
                    f"🔭 <i>Этот кадр получен с орбиты. Каждая такая фотография помогает нам лучше изучить наш общий дом!</i>\n\n"
                    f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
                )
                return img_url, caption, nasa_id
        return None, None, None
    except: return None, None, None

# ============================================================
# 📤 ГЛАВНАЯ ФУНКЦИЯ ОТПРАВКИ
# ============================================================

def post_to_telegram():
    # 50/50 выбираем режим (дальняя съемка или детальные фото)
    mode = random.choice(["EPIC", "LIBRARY"])
    print(f"🛰 Выбран режим: {mode}")
    
    if mode == "EPIC":
        url, cap, img_id = get_epic_data()
    else:
        url, cap, img_id = get_extensive_library_data()
    
    # План Б, если первый режим ничего не нашел
    if not url:
        url, cap, img_id = get_extensive_library_data() if mode == "EPIC" else get_epic_data()

    if url and img_id:
        # СОЗДАЕМ ИНТЕРАКТИВНЫЙ ПУЛЬТ УПРАВЛЕНИЯ
        keyboard = {
            "inline_keyboard": [
                # Та самая надежная ссылка на N2YO (Видео + Карта)
                [{"text": "🛰 МКС: ПРЯМОЙ ЭФИР + КАРТА", "url": "https://www.n2yo.com/space-station/"}],
                # Наглядная 3D карта от NASA
                [{"text": "🌍 ГЛАЗА ЗЕМЛИ (3D КАРТА)", "url": "https://eyes.nasa.gov/apps/earth/"}]
            ]
        }

        payload = {
            'chat_id': CHANNEL_NAME, 
            'photo': url, 
            'caption': cap, 
            'parse_mode': 'HTML',
            'reply_markup': json.dumps(keyboard),
            # Отключаем тяжелые превью ссылок, оставляем только фото
            'link_preview_options': {'is_disabled': True}
        }
        
        try:
            r = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto", json=payload)
            if r.status_code == 200:
                save_sent_id(img_id)
                print(f"✅ Успешно отправлено в канал: {img_id}")
            else:
                print(f"❌ Ошибка Telegram: {r.text}")
        except Exception as e:
            print(f"❌ Ошибка сети: {e}")
    else:
        print("📭 Космос молчит. Новых фото пока не найдено.")

if __name__ == '__main__':
    post_user_info = f"Для штурмана Влада: сигнал стабильный, системы в норме!"
    print(post_user_info)
    post_to_telegram()
