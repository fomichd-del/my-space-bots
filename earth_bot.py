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
NASA_API_KEY   = os.getenv('NASA_API_KEY') or "DEMO_KEY" 
HISTORY_FILE   = 'last_earth_id.txt'

translator = GoogleTranslator(source='auto', target='ru')

def is_already_sent(image_id):
    """Проверяет, отправляли ли мы это фото раньше"""
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r') as f:
            sent_ids = f.read().splitlines()
            return image_id in sent_ids
    return False

def save_sent_id(image_id):
    """Сохраняет ID отправленного фото"""
    with open(HISTORY_FILE, 'a') as f:
        f.write(f"{image_id}\n")

def get_epic_data():
    """Режим 1: Полный диск Земли (DSCOVR)"""
    url = f"https://api.nasa.gov/EPIC/api/natural/available?api_key={NASA_API_KEY}"
    try:
        dates = requests.get(url).json()
        last_date = dates[-1]
        data_url = f"https://api.nasa.gov/EPIC/api/natural/date/{last_date}?api_key={NASA_API_KEY}"
        shots = requests.get(data_url).json()
        
        # Фильтруем те, что еще не слали
        available_shots = [s for s in shots if not is_already_sent(s['image'])]
        if not available_shots: return None, None, None
        
        shot = random.choice(available_shots)
        img_id = shot['image']
        
        p = last_date.split("-")
        img_url = f"https://epic.gsfc.nasa.gov/archive/natural/{p[0]}/{p[1]}/{p[2]}/jpg/{img_id}.jpg"
        
        caption = (
            f"🌍 <b>ВЗГЛЯД ИЗ ТОЧКИ L1</b>\n"
            f"─────────────────────\n"
            f"Этот снимок сделал спутник <b>DSCOVR</b> с расстояния 1.5 миллиона километров. Мы видим всю планету целиком!\n\n"
            f"📅 Дата: <b>{last_date}</b>\n"
            f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
        )
        return img_url, caption, img_id
    except: return None, None, None

def get_nasa_library_data():
    """Режим 2: Снимки с МКС и других спутников (NASA Library)"""
    queries = ["Earth from ISS", "Landsat Earth", "Terra satellite Earth", "Blue Marble"]
    q = random.choice(queries)
    url = f"https://images-api.nasa.gov/search?q={q}&media_type=image"
    
    try:
        res = requests.get(url).json()
        items = res['collection']['items']
        
        # Ищем фото, которое еще не слали
        random.shuffle(items)
        for item in items[:30]:
            nasa_id = item['data'][0]['nasa_id']
            if not is_already_sent(nasa_id):
                img_url = item['links'][0]['href']
                title = item['data'][0]['title']
                title_ru = translator.translate(title)
                
                caption = (
                    f"🛰 <b>ОКОШКО В КОСМОС</b>\n"
                    f"─────────────────────\n"
                    f"<b>{title_ru}</b>\n\n"
                    f"Этот кадр получен с околоземной орбиты (МКС или спутники Landsat/Terra). Здесь мы гораздо ближе к Земле!\n\n"
                    f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
                )
                return img_url, caption, nasa_id
        return None, None, None
    except: return None, None, None

def post_to_telegram():
    mode = random.choice(["EPIC", "LIBRARY"])
    print(f"Выбран режим: {mode}")
    
    url, cap, img_id = get_epic_data() if mode == "EPIC" else get_nasa_library_data()
    
    if not url: # Пробуем запасной режим
        url, cap, img_id = get_nasa_library_data() if mode == "EPIC" else get_epic_data()

    if url and img_id:
        payload = {'chat_id': CHANNEL_NAME, 'photo': url, 'caption': cap, 'parse_mode': 'HTML'}
        r = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto", data=payload)
        
        if r.status_code == 200:
            save_sent_id(img_id)
            print(f"✅ Пост {img_id} отправлен!")
        else:
            print(f"❌ Ошибка ТГ: {r.text}")
    else:
        print("📭 Новых фото на сегодня нет.")

if __name__ == '__main__':
    post_to_telegram()
