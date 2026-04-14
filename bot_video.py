import requests
import os
import random
import time
import xml.etree.ElementTree as ET
from datetime import datetime
from deep_translator import GoogleTranslator

# ============================================================
# ⚙️ НАСТРОЙКИ
# ============================================================
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
NASA_API_KEY   = os.getenv('NASA_API_KEY') or "DEMO_KEY"
CHANNEL_NAME   = '@vladislav_space'
DB_FILE        = "last_video_date.txt"

translator = GoogleTranslator(source='auto', target='ru')

# Источники RSS (не только YouTube)
FEEDS = {
    'ESA (Европа/Vimeo/Native)': 'https://www.esa.int/rssfeed/Videos',
    'NASA (Общий)': 'https://www.nasa.gov/rss/dyn/breaking_news.rss',
    'JAXA (Япония)': 'https://www.jaxa.jp/rss/index_e.rdf'
}

# Каналы YouTube (как дополнительный, но не единственный источник)
YT_CHANNELS = {
    'SpaceX': 'UC_h_S6G_9A440VUM_KOn6Zg',
    'Роскосмос': 'UCp7fGZ8Z9zX_lZpY_l475_g',
    'Blue Origin': 'UCOpNcN46zbB0AgvW4t6OMvA'
}

SEARCH_KEYWORDS = ['Mars Rover', 'ISS Tour', 'Saturn Rings', 'SpaceX Launch', 'Black Hole']

# ============================================================
# 🛰️ МОДУЛИ ПОИСКА
# ============================================================

def get_esa_video():
    """Источник: ESA (Европейское агентство) - часто Vimeo или прямые MP4"""
    print("📡 Проверяю архивы Европы (ESA)...")
    try:
        res = requests.get(FEEDS['ESA (Европа/Vimeo/Native)'], timeout=20)
        root = ET.fromstring(res.content)
        item = root.find('.//item')
        title = item.find('title').text
        link = item.find('link').text
        desc = item.find('description').text if item.find('description') is not None else ""
        return {'url': link, 'title': title, 'desc': desc, 'source': 'ESA'}
    except: return None

def get_nasa_library():
    """Источник: NASA Archive - Прямые ссылки на .mp4 файлы"""
    keyword = random.choice(SEARCH_KEYWORDS)
    print(f"📡 Глубокий поиск в архивах NASA по теме: {keyword}...")
    try:
        url = f"https://images-api.nasa.gov/search?q={keyword}&media_type=video"
        res = requests.get(url, timeout=20).json()
        item = random.choice(res['collection']['items'][:5])
        nasa_id = item['data'][0]['nasa_id']
        title = item['data'][0]['title']
        desc = item['data'][0].get('description', '')
        
        # Получаем прямую ссылку на видеофайл высокого качества
        assets = requests.get(f"https://images-api.nasa.gov/asset/{nasa_id}", timeout=20).json()
        video_url = next(a['href'] for a in assets['collection']['items'] if '~orig.mp4' in a['href'] or 'mp4' in a['href'])
        return {'url': video_url, 'title': title, 'desc': desc, 'source': 'NASA Library'}
    except: return None

def get_youtube_fallback():
    """Источник: YouTube RSS (SpaceX, Роскосмос и др.)"""
    name, c_id = random.choice(list(YT_CHANNELS.items()))
    print(f"📡 Проверяю канал: {name}...")
    try:
        url = f"https://www.youtube.com/feeds/videos.xml?channel_id={c_id}"
        res = requests.get(url, timeout=20)
        root = ET.fromstring(res.content)
        entry = root.find('{http://www.w3.org/2005/Atom}entry')
        v_id = entry.find('{http://www.youtube.com/xml/schemas/2009}videoId').text
        title = entry.find('{http://www.w3.org/2005/Atom}title').text
        return {'url': f"https://www.youtube.com/watch?v={v_id}", 'title': title, 'desc': f"Свежее видео от {name}.", 'source': name}
    except: return None

# ============================================================
# 🎬 ГЛАВНАЯ ЛОГИКА
# ============================================================

def send():
    print("🎬 Запуск Межгалактического Кинотеатра...")
    
    # Ротация источников для разнообразия
    methods = [get_esa_video, get_nasa_library, get_youtube_fallback]
    random.shuffle(methods)
    
    video = None
    for method in methods:
        video = method()
        if video: break

    if not video: return

    # Проверка памяти
    v_id = video['url']
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            if v_id in f.read():
                print("⏭ Это видео уже было.")
                return

    # Перевод
    title_ru = translator.translate(video['title'])
    desc_ru = translator.translate('. '.join(video['desc'].split('.')[:3]) + '.')

    caption = (
        f"🎬 <b>КОСМИЧЕСКИЙ КИНОТЕАТР: {video['source']}</b>\n"
        f"🌟 <b>{title_ru.upper()}</b>\n\n"
        f"🍿 <a href='{video['url']}'><b>СМОТРЕТЬ РОЛИК</b></a>\n"
        f"─────────────────────\n"
        f"<b>ИНФО:</b> {desc_ru}\n\n"
        f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
    )

    payload = {
        "chat_id": CHANNEL_NAME,
        "text": caption,
        "parse_mode": "HTML",
        "link_preview_options": {"url": video['url'], "prefer_large_media": True}
    }
    
    r = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", json=payload)
    
    if r.status_code == 200:
        with open(DB_FILE, 'a', encoding='utf-8') as f: f.write(f"{v_id}\n")
        print(f"✅ Опубликовано из источника: {video['source']}")

if __name__ == '__main__':
    send()
