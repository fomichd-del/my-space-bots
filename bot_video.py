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

# ВСЕ МИРОВЫЕ КАНАЛЫ (YouTube RSS)
GLOBAL_CHANNELS = {
    'Роскосмос': 'UCp7fGZ8Z9zX_lZpY_l475_g',
    'SpaceX': 'UC_h_S6G_9A440VUM_KOn6Zg',
    'ISRO (Индия)': 'UC16vrn4PmwzOm_8atGYU8YQ',
    'JAXA (Япония)': 'UC1S_S6G_9A440VUM_KOn6Zg',
    'ESA (Европа)': 'UC8u9uH_V83_Fns70cyJK_Iw',
    'NASA Video': 'UCOpNcN46zbB0AgvW4t6OMvA',
    'CNSA (Китай)': 'UCu3WicZMcXpUksat9yU859g',
    'James Webb': 'UCv88N6mY_D-FpXgK70l69iQ',
    'Space.com': 'UC6PnFayKstU9O_2uU_9rS7w'
}

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

def get_nasa_library():
    """Архивы NASA (прямые MP4)"""
    keywords = ['Mars', 'ISS', 'Artemis', 'Galaxy', 'Rocket', 'Jupiter']
    kw = random.choice(keywords)
    print(f"📡 [SCANNER] Поиск NASA: {kw}...")
    try:
        url = f"https://images-api.nasa.gov/search?q={kw}&media_type=video"
        res = requests.get(url, timeout=30).json()
        items = res['collection']['items']
        for item in items[:15]:
            nasa_id = item['data'][0]['nasa_id']
            assets = requests.get(f"https://images-api.nasa.gov/asset/{nasa_id}", timeout=20).json()
            # Ищем сначала medium, потом orig (medium легче качается Телеграмом)
            video_url = None
            asset_list = [a['href'] for a in assets['collection']['items']]
            for link in asset_list:
                if '~medium.mp4' in link: video_url = link; break
            if not video_url:
                for link in asset_list:
                    if '~orig.mp4' in link or '.mp4' in link: video_url = link; break
            
            if video_url:
                return {'url': clean_url(video_url), 'title': item['data'][0]['title'], 
                        'desc': item['data'][0].get('description', ''), 'source': 'NASA Library'}
    except: return None

def get_world_youtube():
    """Видео из любой точки планеты"""
    name, c_id = random.choice(list(GLOBAL_CHANNELS.items()))
    print(f"📡 [SCANNER] Канал: {name}...")
    try:
        url = f"https://www.youtube.com/feeds/videos.xml?channel_id={c_id}"
        res = requests.get(url, timeout=30)
        root = ET.fromstring(res.content)
        entry = root.find('{http://www.w3.org/2005/Atom}entry')
        if entry is not None:
            v_id = entry.find('{http://www.youtube.com/xml/schemas/2009}videoId').text
            return {'url': f"https://www.youtube.com/watch?v={v_id}", 
                    'title': entry.find('{http://www.w3.org/2005/Atom}title').text, 
                    'desc': f"Новое видео от {name}.", 'source': name}
    except: return None

# ============================================================
# 🎬 ГЛАВНАЯ ЛОГИКА С ЗАЩИТОЙ
# ============================================================

def send():
    print("🎬 [ЦУП] Кинотеатр v4.4 Запуск...")
    methods = [get_nasa_library, get_world_youtube]
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
            
            caption = (f"🎬 <b>{video['source'].upper()}: {t_ru.upper()}</b>\n\n"
                       f"📖 <b>О ЧЕМ:</b> {d_ru}\n\n"
                       f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>")

            # ПРОБУЕМ ОТПРАВИТЬ С ОКОШКОМ
            success = False
            if '.mp4' in video['url'].lower():
                r = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo", 
                                  data={"chat_id": CHANNEL_NAME, "video": video['url'], "caption": caption, "parse_mode": "HTML"})
                if r.status_code == 200: success = True
            
            if not success: # Если не mp4 или если sendVideo не сработал (как на скриншоте)
                payload = {
                    "chat_id": CHANNEL_NAME,
                    "text": f"🍿 <b>СМОТРЕТЬ:</b> <a href='{video['url']}'>{t_ru.upper()}</a>\n\n{caption}",
                    "parse_mode": "HTML",
                    "link_preview_options": {"url": video['url'], "prefer_large_media": True, "show_above_text": True}
                }
                r = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", json=payload)
                if r.status_code == 200: success = True

            if success:
                with open(DB_FILE, 'a', encoding='utf-8') as f: f.write(f"\n{video['url']}")
                print(f"🎉 Видео от {video['source']} в канале!")
                return
            else:
                print(f"⚠️ Ошибка ТГ: {r.text}. Иду к следующему источнику...")

    print("🛑 Поиск завершен. Ничего не отправлено.")

if __name__ == '__main__':
    send()
