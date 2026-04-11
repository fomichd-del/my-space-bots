import requests
import os
import random
import json # НОВЫЙ ИМПОРТ (нужен для кнопок)
from datetime import datetime
from deep_translator import GoogleTranslator

# ============================================================
# ⚙️ НАСТРОЙКИ
# ============================================================
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHANNEL_NAME   = '@vladislav_space'
NASA_API_KEY   = os.getenv('NASA_API_KEY') or "DEMO_KEY" 
HISTORY_FILE   = 'last_earth_id.txt'

translator = GoogleTranslator(source='auto', target='ru')

def is_already_sent(image_id):
    """Проверяет память бота"""
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            return str(image_id) in f.read()
    return False

def save_sent_id(image_id):
    """Записывает ID в память"""
    with open(HISTORY_FILE, 'a', encoding='utf-8') as f:
        f.write(f"{image_id}\n")

def get_epic_data():
    """Режим 1: Полный диск Земли (точка L1, 1.5 млн км)"""
    url = f"https://api.nasa.gov/EPIC/api/natural/available?api_key={NASA_API_KEY}"
    try:
        dates = requests.get(url, timeout=20).json()
        last_date = dates[-1]
        data_url = f"https://api.nasa.gov/EPIC/api/natural/date/{last_date}?api_key={NASA_API_KEY}"
        shots = requests.get(data_url, timeout=20).json()
        
        available_shots = [s for s in shots if not is_already_sent(s['image'])]
        if not available_shots: return None, None, None
        
        shot = random.choice(available_shots)
        img_id = shot['image']
        p = last_date.split("-")
        img_url = f"https://epic.gsfc.nasa.gov/archive/natural/{p[0]}/{p[1]}/{p[2]}/jpg/{img_id}.jpg"
        
        caption = (
            f"🌍 <b>ВЗГЛЯД ИЗ ТОЧКИ L1</b>\n"
            f"─────────────────────\n"
            f"Этот снимок спутник DSCOVR сделал с расстояния 1.5 млн км. Мы видим нашу планету целиком, как хрупкий «Голубой мрамор» в пустоте.\n\n"
            f"📅 Дата: <b>{last_date}</b>\n\n"
            f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
        )
        return img_url, caption, img_id
    except: return None, None, None

def get_extensive_library_data():
    """Режим 2: Обширная библиотека (МКС, Горизонты, Виды с Луны)"""
    # Расширенные запросы для поиска самых крутых видов
    queries = [
        "Earth limb from space", "Earth and Moon", "Global Earth from ISS",
        "View of Earth from Apollo", "Earth at night from space", 
        "Beautiful Earth horizon", "Blue Marble Earth"
    ]
    q = random.choice(queries)
    url = f"https://images-api.nasa.gov/search?q={q}&media_type=image"
    
    try:
        print(f"📡 Ищу обширные фото по запросу: {q}...")
        res = requests.get(url, timeout=20).json()
        items = res['collection']['items']
        
        random.shuffle(items)
        # Ищем качественное фото, которого еще не было
        for item in items[:40]:
            nasa_id = item['data'][0]['nasa_id']
            if not is_already_sent(nasa_id):
                img_url = item['links'][0]['href']
                title_en = item['data'][0]['title']
                desc_en = item['data'][0].get('description', '')

                # Перевод
                title_ru = translator.translate(title_en)
                # Берем только суть из описания
                short_desc = '. '.join(desc_en.split('.')[:2]) + '.'
                desc_ru = translator.translate(short_desc)
                
                caption = (
                    f"🛰 <b>ОБШИРНЫЙ КОСМОС: {title_ru.upper()}</b>\n"
                    f"─────────────────────\n\n"
                    f"📖 <b>Инфо:</b> {desc_ru}\n\n"
                    f"🔭 <i>Этот кадр показывает нашу планету с орбиты или во время космических миссий.</i>\n\n"
                    f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
                )
                return img_url, caption, nasa_id
        return None, None, None
    except: return None, None, None

def post_to_telegram():
    # 50% шанс на полный диск, 50% на обширную библиотеку
    mode = random.choice(["EPIC", "LIBRARY"])
    print(f"Выбран режим: {mode}")
    
    url, cap, img_id = get_epic_data() if mode == "EPIC" else get_extensive_library_data()
    
    # Запасной вариант, если первый режим ничего не нашел
    if not url:
        url, cap, img_id = get_extensive_library_data() if mode == "EPIC" else get_epic_data()

    if url and img_id:
        
        # --- БЛОК КНОПОК (НОВОЕ!) ---
        # Формируем структуру кнопок одна под другой
        keyboard = {
            "inline_keyboard": [
                # Кнопка 1: 3D Глобус (NASA Eyes)
                [{"text": "🗺 ГЛАЗА ЗЕМЛИ (3D КАРТА)", "url": "https://eyes.nasa.gov/apps/earth/"}],
                # Кнопка 2: Ютуб-трансляция с МКС
                [{"text": "📹 МКС: ПРЯМОЙ ЭФИР", "url": "https://www.youtube.com/watch?v=jPTD2gnZFUw"}]
            ]
        }
        # --- КОНЕЦ БЛОКА КНОПОК ---

        # Добавляем reply_markup в payload
        payload = {
            'chat_id': CHANNEL_NAME, 
            'photo': url, 
            'caption': cap, 
            'parse_mode': 'HTML',
            'reply_markup': json.dumps(keyboard) # ПРЕВРАЩАЕМ КНОПКИ В СТРОКУ JSON
        }
        
        r = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto", data=payload)
        
        if r.status_code == 200:
            save_sent_id(img_id)
            print(f"✅ Успешно отправлено: {img_id}")
        else:
            print(f"❌ Ошибка ТГ: {r.text}")
    else:
        print("📭 Нового контента пока нет.")

if __name__ == '__main__':
    post_to_telegram()
