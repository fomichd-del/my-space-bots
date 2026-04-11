import requests
import os
import random
import json
from deep_translator import GoogleTranslator

# ============================================================
# ⚙️ НАСТРОЙКИ
# ============================================================
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHANNEL_NAME   = '@vladislav_space'
DB_FILE        = "last_mars_photo.txt" 

translator = GoogleTranslator(source='auto', target='ru')

PLANETS = [
    "Mercury planet", "Venus planet", "Mars planet", 
    "Jupiter planet", "Saturn planet", "Uranus planet", 
    "Neptune planet", "Pluto dwarf planet"
]

def get_planet_data():
    planet_query = random.choice(PLANETS)
    planet_name_simple = planet_query.split()[0]
    
    url = f"https://images-api.nasa.gov/search?q={planet_query}&media_type=image"
    
    try:
        print(f"📡 Ищу фото для планеты: {planet_name_simple}...")
        res = requests.get(url, timeout=20).json()
        items = res['collection']['items']
        
        sent_ids = []
        if os.path.exists(DB_FILE):
            with open(DB_FILE, 'r', encoding='utf-8') as f:
                sent_ids = f.read().splitlines()

        random.shuffle(items)
        target_item = None
        
        for item in items[:20]:
            nasa_id = item['data'][0]['nasa_id']
            if nasa_id not in sent_ids:
                target_item = item
                break
        
        if not target_item:
            return None, None, None

        img_url = target_item['links'][0]['href']
        nasa_id = target_item['data'][0]['nasa_id']
        title_en = target_item['data'][0]['title']
        desc_en = target_item['data'][0].get('description', '')

        title_ru = translator.translate(title_en)
        short_desc_en = '. '.join(desc_en.split('.')[:3]) + '.'
        desc_ru = translator.translate(short_desc_en)

        caption = (
            f"🪐 <b>ПЛАНЕТА ДНЯ: {title_ru.upper()}</b>\n"
            f"─────────────────────\n\n"
            f"📖 <b>Интересный факт:</b>\n{desc_ru}\n\n"
            f"🔭 <i>Этот снимок был сделан одной из межпланетных станций NASA во время исследования нашей системы.</i>\n\n"
            f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
        )
        
        return img_url, caption, nasa_id
        
    except Exception as e:
        print(f"❌ Ошибка поиска: {e}")
        return None, None, None

def send_to_telegram():
    img_url, caption, nasa_id = get_planet_data()
    
    if not img_url:
        print("📭 Новых фото планет не найдено.")
        return

    # --- БЛОК КНОПОК (НОВОЕ!) ---
    keyboard = {
        "inline_keyboard": [
            # Кнопка 1: Охотник за экзопланетами (3D вид на чужие миры)
            [{"text": "🌌 ОХОТНИК ЗА ЭКЗОПЛАНЕТАМИ (3D)", "url": "https://eyes.nasa.gov/apps/exo/"}],
            # Кнопка 2: Где сейчас ровер (интерактивная карта Марса)
            [{"text": "🚜 ГДЕ СЕЙЧАС РОВЕР?", "url": "https://eyes.nasa.gov/apps/mars2020/"}]
        ]
    }

    base_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    payload = {
        'chat_id': CHANNEL_NAME,
        'photo': img_url,
        'caption': caption,
        'parse_mode': 'HTML',
        'reply_markup': json.dumps(keyboard) # Добавляем кнопки в сообщение
    }
    
    r = requests.post(base_url, data=payload)
    if r.status_code == 200:
        with open(DB_FILE, 'a', encoding='utf-8') as f:
            f.write(f"{nasa_id}\n")
        print(f"✅ Пост про {nasa_id} с интерактивными кнопками отправлен!")
    else:
        print(f"❌ Ошибка Telegram: {r.text}")

if __name__ == '__main__':
    send_to_telegram()
