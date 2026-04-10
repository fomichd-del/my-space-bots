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
DB_FILE        = "last_mars_photo.txt" # Файл памяти для планетарной рулетки

translator = GoogleTranslator(source='auto', target='ru')

# Список планет для "Планетарной рулетки"
PLANETS = [
    "Mercury planet", "Venus planet", "Mars planet", 
    "Jupiter planet", "Saturn planet", "Uranus planet", 
    "Neptune planet", "Pluto dwarf planet"
]

def get_planet_data():
    """Выбирает случайную планету и ищет её лучшее фото в NASA Image Library"""
    planet_query = random.choice(PLANETS)
    planet_name_simple = planet_query.split()[0]
    
    url = f"https://images-api.nasa.gov/search?q={planet_query}&media_type=image"
    
    try:
        print(f"📡 Ищу фото для планеты: {planet_name_simple}...")
        res = requests.get(url, timeout=20).json()
        items = res['collection']['items']
        
        # Загружаем историю отправленных фото
        sent_ids = []
        if os.path.exists(DB_FILE):
            with open(DB_FILE, 'r', encoding='utf-8') as f:
                sent_ids = f.read().splitlines()

        # Ищем в результатах фото, которого еще не было в канале
        random.shuffle(items) # Перемешиваем результаты для разнообразия
        target_item = None
        
        for item in items[:20]: # Проверяем первые 20 качественных результатов
            nasa_id = item['data'][0]['nasa_id']
            if nasa_id not in sent_ids:
                target_item = item
                break
        
        if not target_item:
            print("📭 Все найденные сегодня фото уже были в канале.")
            return None, None, None

        img_url = target_item['links'][0]['href']
        nasa_id = target_item['data'][0]['nasa_id']
        title_en = target_item['data'][0]['title']
        desc_en = target_item['data'][0].get('description', '')

        # Перевод
        title_ru = translator.translate(title_en)
        short_desc_en = '. '.join(desc_en.split('.')[:3]) + '.'
        desc_ru = translator.translate(short_desc_en)

        # ОФОРМЛЕНИЕ (без бара)
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
        return

    base_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    payload = {
        'chat_id': CHANNEL_NAME,
        'photo': img_url,
        'caption': caption,
        'parse_mode': 'HTML'
    }
    
    r = requests.post(base_url, data=payload)
    if r.status_code == 200:
        # Сохраняем ID фото в память
        with open(DB_FILE, 'a', encoding='utf-8') as f:
            f.write(f"{nasa_id}\n")
        print(f"✅ Пост про {nasa_id} успешно отправлен!")
    else:
        print(f"❌ Ошибка Telegram: {r.text}")

if __name__ == '__main__':
    send_to_telegram()
