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

# Глобальные RSS-каналы (Не только YouTube!)
FEEDS = {
    'ESA (Европа)': 'https://www.esa.int/rssfeed/Videos',
    'NASA Breaking': 'https://www.nasa.gov/rss/dyn/breaking_news.rss',
    'Hubble (Телескоп)': 'https://hubblesite.org/rss/news',
    'JAXA (Япония)': 'https://www.jaxa.jp/rss/index_e.rdf'
}

# YouTube каналы (через RSS)
YT_CHANNELS = {
    'SpaceX': 'UC_h_S6G_9A440VUM_KOn6Zg',
    'Роскосмос': 'UCp7fGZ8Z9zX_lZpY_l475_g',
    'NASA Video': 'UCOpNcN46zbB0AgvW4t6OMvA',
    'James Webb': 'UCv88N6mY_D-FpXgK70l69iQ'
}

SEARCH_KEYWORDS = ['Mars Rover', 'ISS Tour', 'Saturn Rings', 'SpaceX Starship', 'Black Hole', 'Earth from Space']

# ============================================================
# 🛰️ МОДУЛИ ПОИСКА (Теперь с подробным логированием)
# ============================================================

def get_esa_video():
    print("📡 [SCANNER] Проверяю архивы Европы (ESA)...")
    try:
        res = requests.get(FEEDS['ESA (Европа)'], timeout=30)
        root = ET.fromstring(res.content)
        item = root.find('.//item')
        if item is not None:
            return {
                'url': item.find('link').text,
                'title': item.find('title').text,
                'desc': item.find('description').text if item.find('description') is not None else "Космические открытия Европы.",
                'source': 'ESA (Европа)'
            }
    except Exception as e: print(f"⚠️ [ESA ERROR]: {e}")
    return None

def get_nasa_library():
    keyword = random.choice(SEARCH_KEYWORDS)
    print(f"📡 [SCANNER] Глубокий поиск в NASA Archive по теме: {keyword}...")
    try:
        url = f"https://images-api.nasa.gov/search?q={keyword}&media_type=video"
        res = requests.get(url, timeout=30).json()
        items = res.get('collection', {}).get('items', [])
        
        for item in items[:10]: # Проверяем первые 10 результатов
            nasa_id = item['data'][0]['nasa_id']
            assets_res = requests.get(f"https://images-api.nasa.gov/asset/{nasa_id}", timeout=25).json()
            asset_items = assets_res.get('collection', {}).get('items', [])
            
            video_url = None
            for a in asset_items:
                if '~orig.mp4' in a['href'] or 'mp4' in a['href']:
                    video_url = a['href']
                    break
            
            if video_url:
                return {
                    'url': video_url,
                    'title': item['data'][0]['title'],
                    'desc': item['data'][0].get('description', 'Захватывающие кадры из архивов.'),
                    'source': 'NASA Archive'
                }
        print(f"ℹ️ [NASA] По теме {keyword} видео не найдено, только статика.")
    except Exception as e: print(f"⚠️ [NASA LIB ERROR]: {e}")
    return None

def get_youtube_fallback():
    name, c_id = random.choice(list(YT_CHANNELS.items()))
    print(f"📡 [SCANNER] Заглядываю на канал: {name}...")
    try:
        url = f"https://www.youtube.com/feeds/videos.xml?channel_id={c_id}"
        res = requests.get(url, timeout=30)
        root = ET.fromstring(res.content)
        entry = root.find('{http://www.w3.org/2005/Atom}entry')
        if entry is not None:
            v_id = entry.find('{http://www.youtube.com/xml/schemas/2009}videoId').text
            return {
                'url': f"https://www.youtube.com/watch?v={v_id}",
                'title': entry.find('{http://www.w3.org/2005/Atom}title').text,
                'desc': f"Свежее видео от {name}.",
                'source': f"YouTube ({name})"
            }
    except Exception as e: print(f"⚠️ [YT ERROR]: {e}")
    return None

# ============================================================
# 🎬 ГЛАВНАЯ ЛОГИКА
# ============================================================

def send():
    print("🎬 [ЦУП] Запуск Межгалактического Кинотеатра v4.0...")
    
    # Пытаемся по очереди, пока не найдем что-то новое
    methods = [get_esa_video, get_nasa_library, get_youtube_fallback]
    random.shuffle(methods)
    
    final_video = None
    
    # Загружаем базу отправленных, чтобы не повторяться
    sent_data = ""
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            sent_data = f.read()

    for method in methods:
        video = method()
        if video:
            v_id = video['url']
            if v_id in sent_data or video['title'] in sent_data:
                print(f"⏭ [SKIP] Видео '{video['title']}' уже было в канале. Ищу дальше...")
                continue
            
            final_video = video
            break

    if not final_video:
        print("🛑 [STOP] Все системы сканирования молчат. Нового видео не найдено.")
        return

    # ПЕРЕВОД
    print(f"✅ [PROCESS] Найдено видео: {final_video['title']}. Перевожу...")
    title_ru = translator.translate(final_video['title'])
    desc_ru = translator.translate('. '.join(final_video['desc'].split('.')[:3]) + '.')

    caption = (
        f"🎬 <b>КОСМИЧЕСКИЙ КИНОТЕАТР: {final_video['source']}</b>\n"
        f"🌟 <b>{title_ru.upper()}</b>\n\n"
        f"🍿 <a href='{final_video['url']}'><b>СМОТРЕТЬ РОЛИК</b></a>\n"
        f"─────────────────────\n"
        f"<b>ИНФО:</b> {desc_ru}\n\n"
        f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
    )

    payload = {
        "chat_id": CHANNEL_NAME,
        "text": caption,
        "parse_mode": "HTML",
        "link_preview_options": {"url": final_video['url'], "prefer_large_media": True}
    }
    
    r = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", json=payload)
    
    if r.status_code == 200:
        with open(DB_FILE, 'a', encoding='utf-8') as f:
            f.write(f"\n{final_video['url']} | {final_video['title']}")
        print(f"🎉 [DONE] Пост опубликован!")
    else:
        print(f"❌ [TELEGRAM ERROR]: {r.text}")

if __name__ == '__main__':
    send()
