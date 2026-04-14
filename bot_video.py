import requests
import os
import random
import time
import xml.etree.ElementTree as ET
import urllib.parse
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

FEEDS = {
    'ESA (Европа)': 'https://www.esa.int/rssfeed/Videos',
    'NASA Breaking': 'https://www.nasa.gov/rss/dyn/breaking_news.rss'
}

YT_CHANNELS = {
    'SpaceX': 'UC_h_S6G_9A440VUM_KOn6Zg',
    'Роскосмос': 'UCp7fGZ8Z9zX_lZpY_l475_g',
    'NASA Video': 'UCOpNcN46zbB0AgvW4t6OMvA'
}

SEARCH_KEYWORDS = ['Mars Rover', 'ISS Tour', 'Saturn Rings', 'SpaceX Starship', 'Black Hole']

def clean_url(url):
    """Исправляет ссылки для Telegram (http -> https + кодировка)"""
    if not url: return url
    url = url.replace("http://", "https://")
    parsed = list(urllib.parse.urlparse(url))
    parsed[2] = urllib.parse.quote(parsed[2])
    return urllib.parse.urlunparse(parsed)

# ============================================================
# 🛰️ МОДУЛИ ПОИСКА
# ============================================================

def get_esa_video():
    print("📡 [SCANNER] Проверяю ESA...")
    try:
        res = requests.get(FEEDS['ESA (Европа)'], timeout=30)
        root = ET.fromstring(res.content)
        item = root.find('.//item')
        if item is not None:
            return {'url': clean_url(item.find('link').text), 'title': item.find('title').text, 
                    'desc': "Космические открытия Европы.", 'source': 'ESA'}
    except: return None

def get_nasa_library():
    keyword = random.choice(SEARCH_KEYWORDS)
    print(f"📡 [SCANNER] NASA Library: {keyword}...")
    try:
        url = f"https://images-api.nasa.gov/search?q={keyword}&media_type=video"
        res = requests.get(url, timeout=30).json()
        items = res.get('collection', {}).get('items', [])
        for item in items[:10]:
            nasa_id = item['data'][0]['nasa_id']
            assets = requests.get(f"https://images-api.nasa.gov/asset/{nasa_id}", timeout=20).json()
            for a in assets.get('collection', {}).get('items', []):
                # Ищем именно mp4 файл
                if '~orig.mp4' in a['href'] or 'mp4' in a['href']:
                    return {'url': clean_url(a['href']), 'title': item['data'][0]['title'], 
                            'desc': item['data'][0].get('description', ''), 'source': 'NASA Library'}
    except: return None

def get_youtube_fallback():
    name, c_id = random.choice(list(YT_CHANNELS.items()))
    print(f"📡 [SCANNER] YouTube: {name}...")
    try:
        url = f"https://www.youtube.com/feeds/videos.xml?channel_id={c_id}"
        res = requests.get(url, timeout=30)
        root = ET.fromstring(res.content)
        entry = root.find('{http://www.w3.org/2005/Atom}entry')
        v_id = entry.find('{http://www.youtube.com/xml/schemas/2009}videoId').text
        return {'url': f"https://www.youtube.com/watch?v={v_id}", 'title': entry.find('{http://www.w3.org/2005/Atom}title').text, 
                'desc': f"Свежее видео от {name}.", 'source': f"YouTube ({name})"}
    except: return None

# ============================================================
# 🎬 ГЛАВНАЯ ЛОГИКА ОТПРАВКИ
# ============================================================

def send():
    print("🎬 [ЦУП] Кинотеатр v4.2 стартовал...")
    methods = [get_esa_video, get_nasa_library, get_youtube_fallback]
    random.shuffle(methods)
    
    sent_data = ""
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r', encoding='utf-8') as f: sent_data = f.read()

    for method in methods:
        video = method()
        if video and video['url'] not in sent_data:
            print(f"✅ [PROCESS] Найдено: {video['title']}. Перевожу...")
            t_ru = translator.translate(video['title'])
            d_ru = translator.translate('. '.join(video['desc'].split('.')[:3]) + '.')
            
            # Общий заголовок
            caption = (f"🎬 <b>{video['source'].upper()}: {t_ru.upper()}</b>\n\n"
                       f"📖 <b>О ЧЕМ:</b> {d_ru}\n\n"
                       f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>")

            # ПРОВЕРКА: Если это прямой файл MP4 (например, из NASA Library)
            if '.mp4' in video['url'].lower():
                print("🎥 Отправляю как нативное видео для 'окошка'...")
                payload = {
                    "chat_id": CHANNEL_NAME,
                    "video": video['url'],
                    "caption": caption,
                    "parse_mode": "HTML"
                }
                r = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo", data=payload)
            
            # ПРОВЕРКА: Если это YouTube
            else:
                print("📺 Отправляю как ссылку с плеером...")
                payload = {
                    "chat_id": CHANNEL_NAME,
                    "text": f"🍿 <b>ВИДЕО:</b> <a href='{video['url']}'>{t_ru.upper()}</a>\n\n{caption}",
                    "parse_mode": "HTML",
                    "link_preview_options": {
                        "url": video['url'],
                        "prefer_large_media": True,
                        "show_above_text": True
                    }
                }
                r = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", json=payload)

            if r.status_code == 200:
                with open(DB_FILE, 'a', encoding='utf-8') as f: f.write(f"\n{video['url']}")
                print("🎉 Видео успешно встроено в канал!")
                return
            else:
                print(f"❌ Ошибка отправки: {r.text}")

    print("🛑 Ничего нового не найдено.")

if __name__ == '__main__':
    send()
