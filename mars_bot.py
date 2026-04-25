import requests
import os
import random
import json
from deep_translator import GoogleTranslator

# ============================================================
# ⚙️ НАСТРОЙКИ
# ============================================================
NASA_API_KEY   = os.getenv('NASA_API_KEY', 'DEMO_KEY') 
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHANNEL_NAME   = '@vladislav_space'
DB_FILE        = "last_mars_photo.txt" 

translator = GoogleTranslator(source='auto', target='ru')

# Темы для поиска
SPACE_TOPICS = [
    "Mercury planet", "Venus surface", "Mars landscape", 
    "Jupiter Juno", "Saturn Cassini", "Uranus planet", 
    "Neptune planet", "Pluto New Horizons", "Nebula Hubble",
    "Galaxy", "Star cluster", "Supernova", "Black hole space"
]

def is_earth_content(text):
    """Проверка, не является ли контент земным."""
    stop_words = ['earth', 'terra', 'iss', 'international space station', 'blue marble', 'satellite of earth']
    text_lower = text.lower()
    return any(word in text_lower for word in stop_words)

def get_file_size_mb(url):
    """Проверка размера файла."""
    try:
        response = requests.head(url, timeout=10)
        size = int(response.headers.get('Content-Length', 0))
        return size / (1024 * 1024)
    except:
        return 0

def get_best_image_url(asset_manifest_url):
    """Выбирает самое качественное фото из доступных."""
    try:
        res = requests.get(asset_manifest_url).json()
        items = [i['href'] for i in res['collection']['items'] if i['href'].lower().endswith('.jpg')]
        items.sort(key=lambda x: ('~orig' in x.lower(), '~large' in x.lower()), reverse=True)
        for url in items:
            size = get_file_size_mb(url)
            if 0 < size <= 48:
                return url
        return items[-1] if items else None
    except:
        return None

def get_planet_data():
    source = random.choice(['apod', 'search'])
    sent_ids = []
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            sent_ids = f.read().splitlines()

    try:
        if source == 'apod':
            y, m, d = random.randint(2010, 2024), random.randint(1, 12), random.randint(1, 28)
            url = f"https://api.nasa.gov/planetary/apod?api_key={NASA_API_KEY}&date={y}-{m}-{d}"
            data = requests.get(url).json()
            if data.get('media_type') != 'image' or is_earth_content(data.get('title', '')):
                return get_planet_data()
            img_url = data.get('hdurl') or data.get('url')
            if get_file_size_mb(img_url) > 48: img_url = data.get('url')
            title_en = data.get('title')
            desc_en = data.get('explanation', '')
            nasa_id = f"APOD_{y}{m}{d}"
        else:
            query = random.choice(SPACE_TOPICS)
            search_url = f"https://images-api.nasa.gov/search?q={query}&media_type=image"
            res = requests.get(search_url).json()
            items = res['collection']['items']
            random.shuffle(items)
            target = None
            for item in items[:25]:
                data = item['data'][0]
                if data['nasa_id'] not in sent_ids and not is_earth_content(data['title']):
                    target = item
                    break
            if not target: return get_planet_data()
            nasa_id = target['data'][0]['nasa_id']
            title_en = target['data'][0]['title']
            desc_en = target['data'][0].get('description', '')
            img_url = get_best_image_url(target['href'])

        if not img_url or nasa_id in sent_ids:
            return get_planet_data()

        title_ru = translator.translate(title_en)
        short_desc_en = '. '.join(desc_en.split('.')[:3]) + '.'
        desc_ru = translator.translate(short_desc_en)

        # --- СБОРКА ПОСТА (БЕЗ КНОПКИ ЧАТА) ---
        header = f"🪐 <b>ОБЪЕКТ ДНЯ: {title_ru.upper()}</b>\n─────────────────────\n\n"
        body = f"📖 <b>Интересный факт:</b>\n{desc_ru}\n\n"
        
        pseudo_buttons = (
            "<b>ВЗГЛЯНИ СЮДА:</b>\n"
            f"🌌 <b><a href='https://eyes.nasa.gov/apps/exo/'>[ ОХОТНИК ЗА ЭКЗОПЛАНЕТАМИ ]</a></b>\n"
            f"🚜 <b><a href='https://eyes.nasa.gov/apps/mars2020/'>[ ГДЕ СЕЙЧАС РОВЕР? ]</a></b>\n"
            "─────────────────────\n"
        )
        
        footer = f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
        
        caption = header + body + pseudo_buttons + footer
        return img_url, caption, nasa_id
        
    except:
        return None, None, None

def send_to_telegram():
    img_url, caption, nasa_id = get_planet_data()
    if not img_url: return

    payload = {
        'chat_id': CHANNEL_NAME,
        'photo': img_url,
        'caption': caption,
        'parse_mode': 'HTML'
    }
    
    r = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto", json=payload)
    
    if r.status_code == 200:
        with open(DB_FILE, 'a', encoding='utf-8') as f:
            f.write(f"{nasa_id}\n")
        print(f"✅ Пост {nasa_id} отправлен. Лишние кнопки удалены.")
    else:
        print(f"❌ Ошибка Telegram: {r.text}")

if __name__ == '__main__':
    send_to_telegram()
