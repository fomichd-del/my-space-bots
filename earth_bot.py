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

translator = GoogleTranslator(source='auto', target='ru')

def get_epic_data():
    """Режим 1: Полный диск Земли (DSCOVR)"""
    url = f"https://api.nasa.gov/EPIC/api/natural/available?api_key={NASA_API_KEY}"
    try:
        dates = requests.get(url).json()
        last_date = dates[-1]
        data_url = f"https://api.nasa.gov/EPIC/api/natural/date/{last_date}?api_key={NASA_API_KEY}"
        shots = requests.get(data_url).json()
        shot = random.choice(shots)
        
        p = last_date.split("-")
        img_url = f"https://epic.gsfc.nasa.gov/archive/natural/{p[0]}/{p[1]}/{p[2]}/jpg/{shot['image']}.jpg"
        
        caption = (
            f"🌍 <b>ВЗГЛЯД ИЗ ТОЧКИ L1</b>\n"
            f"─────────────────────\n"
            f"Этот снимок сделал спутник <b>DSCOVR</b> с расстояния 1.5 миллиона километров. Мы видим всю планету целиком!\n\n"
            f"📅 Дата: <b>{last_date}</b>\n"
            f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
        )
        return img_url, caption
    except: return None, None

def get_nasa_library_data():
    """Режим 2: Снимки с МКС и других спутников (NASA Library)"""
    # Ищем крутые фото Земли по ключевым словам
    queries = ["Earth from ISS", "Landsat Earth", "Terra satellite Earth", "Blue Marble"]
    q = random.choice(queries)
    url = f"https://images-api.nasa.gov/search?q={q}&media_type=image"
    
    try:
        res = requests.get(url).json()
        items = res['collection']['items']
        # Берем случайное фото из свежих результатов
        item = random.choice(items[:20])
        
        img_url = item['links'][0]['href']
        title = item['data'][0]['title']
        desc = item['data'][0].get('description', '')
        
        # Короткий перевод названия
        title_ru = translator.translate(title)
        
        caption = (
            f"🛰 <b>ОКОШКО В КОСМОС</b>\n"
            f"─────────────────────\n"
            f"<b>{title_ru}</b>\n\n"
            f"Этот кадр получен с околоземной орбиты (МКС или спутники Landsat/Terra). Здесь мы гораздо ближе к Земле!\n\n"
            f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
        )
        return img_url, caption
    except: return None, None

def post_to_telegram():
    # Шанс 50 на 50 какой режим выбрать
    mode = random.choice(["EPIC", "LIBRARY"])
    print(f"Выбран режим: {mode}")
    
    if mode == "EPIC":
        url, cap = get_epic_data()
    else:
        url, cap = get_nasa_library_data()
        
    # Если один режим сбоит, пробуем другой
    if not url:
        url, cap = get_epic_data()

    if url:
        payload = {'chat_id': CHANNEL_NAME, 'photo': url, 'caption': cap, 'parse_mode': 'HTML'}
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto", data=payload)
        print("✅ Пост отправлен!")
    else:
        print("❌ Ошибка получения данных")

if __name__ == '__main__':
    post_to_telegram()
