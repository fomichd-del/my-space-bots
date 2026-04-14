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

# Список официальных каналов для поиска (YouTube RSS)
YOUTUBE_CHANNELS = {
    'SpaceX': 'UC_h_S6G_9A440VUM_KOn6Zg',
    'Роскосмос': 'UCp7fGZ8Z9zX_lZpY_l475_g',
    'ESA (Европа)': 'UC8u9uH_V83_Fns70cyJK_Iw',
    'NASA': 'UCOpNcN46zbB0AgvW4t6OMvA',
    'JAXA (Япония)': 'UC1S_S6G_9A440VUM_KOn6Zg', # Пример ID
    'Deep Space (Наука)': 'UC6PnFayKstU9O_2uU_9rS7w'
}

# Темы для поиска в библиотеке NASA
SEARCH_KEYWORDS = ['Mars Landing', 'Saturn Voyager', 'Black Hole Energy', 'ISS Tour', 'Artemis Moon']

# ============================================================
# 🛰️ ФУНКЦИИ ПОИСКА
# ============================================================

def get_nasa_apod():
    """Источник 1: NASA APOD (Видео дня)"""
    url = f"https://api.nasa.gov/planetary/apod?api_key={NASA_API_KEY}"
    try:
        res = requests.get(url, timeout=20).json()
        if res.get('media_type') == 'video':
            return {
                'url': res.get('url'),
                'title': res.get('title'),
                'desc': res.get('explanation'),
                'source': 'NASA APOD'
            }
    except: pass
    return None

def get_global_youtube():
    """Источник 2: Глобальные агентства (SpaceX, Роскосмос, ESA)"""
    # Выбираем случайный канал из списка
    name, c_id = random.choice(list(YOUTUBE_CHANNELS.items()))
    print(f"📡 Проверяю канал: {name}...")
    rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={c_id}"
    
    try:
        response = requests.get(rss_url, timeout=20)
        root = ET.fromstring(response.content)
        # Берем самое свежее видео
        entry = root.find('{http://www.w3.org/2005/Atom}entry')
        v_id = entry.find('{http://www.youtube.com/xml/schemas/2009}videoId').text
        title = entry.find('{http://www.w3.org/2005/Atom}title').text
        
        return {
            'url': f"https://www.youtube.com/watch?v={v_id}",
            'title': title,
            'desc': f"Новое видео из официального архива {name}.",
            'source': name
        }
    except: pass
    return None

def get_nasa_library():
    """Источник 3: Глубокий архив NASA"""
    keyword = random.choice(SEARCH_KEYWORDS)
    url = f"https://images-api.nasa.gov/search?q={keyword}&media_type=video"
    try:
        res = requests.get(url, timeout=20).json()
        items = res['collection']['items']
        if items:
            item = random.choice(items[:5])
            nasa_id = item['data'][0]['nasa_id']
            # Получаем ссылку на файл
            assets = requests.get(f"https://images-api.nasa.gov/asset/{nasa_id}").json()
            video_url = next(a['href'] for a in assets['collection']['items'] if '~orig.mp4' in a['href'])
            return {
                'url': video_url,
                'title': item['data'][0]['title'],
                'desc': item['data'][0].get('description', ''),
                'source': 'NASA Archive'
            }
    except: pass
    return None

# ============================================================
# 🎬 ГЛАВНАЯ ЛОГИКА
# ============================================================

def send_to_telegram():
    print("🎬 Запуск Космического Кинотеатра...")
    
    # 1. Сначала пробуем APOD (Традиция)
    video = get_nasa_apod()
    
    # 2. Если нет, идем по миру (YouTube RSS)
    if not video:
        video = get_global_youtube()
        
    # 3. Если и там сбой, лезем в архивы
    if not video:
        video = get_nasa_library()

    if not video:
        print("❌ Видео не найдено ни в одном источнике.")
        return

    # ПРОВЕРКА ПАМЯТИ
    v_id = video['url']
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            if v_id in f.read():
                print(f"✋ Видео {v_id} уже было.")
                return

    # ПЕРЕВОД
    title_ru = translator.translate(video['title'])
    desc_ru = translator.translate('. '.join(video['desc'].split('.')[:4]) + '.')

    # Оформление ссылки YouTube
    final_url = video['url']
    if 'embed/' in final_url:
        v_id_clean = final_url.split('/embed/')[1].split('?')[0]
        final_url = f"https://www.youtube.com/watch?v={v_id_clean}"

    caption = (
        f"🎬 <b>КОСМИЧЕСКИЙ КИНОТЕАТР: {video['source']}</b>\n"
        f"🌟 <b>{title_ru.upper()}</b>\n\n"
        f"🍿 <a href='{final_url}'><b>СМОТРЕТЬ РОЛИК</b></a>\n"
        f"─────────────────────\n"
        f"<b>ИНФО:</b>\n{desc_ru}\n\n"
        f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
    )

    payload = {
        "chat_id": CHANNEL_NAME,
        "text": caption,
        "parse_mode": "HTML",
        "link_preview_options": {"url": final_url, "prefer_large_media": True}
    }
    
    r = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", json=payload)
    
    if r.status_code == 200:
        with open(DB_FILE, 'a', encoding='utf-8') as f:
            f.write(f"{v_id}\n")
        print(f"✅ Успех! Источник: {video['source']}")

if __name__ == '__main__':
    send_to_telegram()
