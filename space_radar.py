import requests
import os
import time
from datetime import datetime, timezone
from deep_translator import GoogleTranslator

# ============================================================
# ⚙️ НАСТРОЙКИ
# ============================================================
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHANNEL_NAME = '@vladislav_space'
DB_FILE = "sent_radar_lives.txt"

translator = GoogleTranslator(source='auto', target='ru')

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) SpaceRadar/2.0'}
FORBIDDEN_WORDS = ['military', 'defense', 'spy', 'reconnaissance', 'missile', 'combat', 'war', 'weapon', 'nuke', 'army', 'война', 'оборона']

def is_military(text):
    if not text: return False
    return any(word in text.lower() for word in FORBIDDEN_WORDS)

def get_live_launch():
    # Мы берем 10 пусков, чтобы точно зацепить все страны
    url = "https://ll.thespacedevs.com/2.2.0/launch/upcoming/?limit=10"
    
    for attempt in range(3): # СИСТЕМА ПЕРЕСДАЧИ
        try:
            print(f"📡 Сканирую мировые частоты (Попытка {attempt + 1})...")
            res = requests.get(url, headers=HEADERS, timeout=30).json()
            launches = res.get('results', [])
            
            sent_ids = []
            if os.path.exists(DB_FILE):
                with open(DB_FILE, 'r', encoding='utf-8') as f:
                    sent_ids = f.read().splitlines()

            for launch in launches:
                l_id = str(launch['id'])
                if l_id in sent_ids: continue

                # Фильтр на мирный космос
                mission_desc = launch.get('mission', {}).get('description', '')
                if is_military(mission_desc) or is_military(launch.get('name', '')):
                    continue

                # ИЩЕМ ССЫЛКИ ПО ВСЕМУ МИРУ
                video_url = None
                vid_urls = launch.get('vidURLs', [])
                
                # 1. Приоритет видео-хостингам
                if vid_urls:
                    for v in vid_urls:
                        if any(x in v['url'] for x in ['youtube.com', 'youtu.be', 'twitch.tv', 'vimeo.com', 'space.com']):
                            video_url = v['url']
                            break
                    if not video_url: video_url = vid_urls[0]['url']
                
                # 2. Если видео нет, ищем страницу миссии (актуально для Китая/Индии)
                if not video_url:
                    info_urls = launch.get('infoURLs', [])
                    if info_urls: video_url = info_urls[0]['url']

                if not video_url: continue

                # Данные пуска
                rocket = launch['rocket']['configuration']['name']
                agency_name = launch['launch_service_provider']['name']
                agency_ru = translator.translate(agency_name)
                mission_ru = translator.translate(mission_desc) if mission_desc else "Научное исследование космоса."
                launch_time = datetime.fromisoformat(launch['net'].replace('Z', '+00:00'))

                caption = (
                    f"🚀 <b>ПРЯМОЙ ЭФИР: {rocket.upper()}</b>\n"
                    f"─────────────────────\n\n"
                    f"🏢 <b>Организатор:</b> {agency_ru}\n"
                    f"📍 <b>Космодром:</b> {launch['pad']['location']['name']}\n"
                    f"📅 <b>Старт:</b> {launch_time.strftime('%d.%m.%Y %H:%M')} UTC\n\n"
                    f"📖 <b>О МИССИИ:</b>\n{mission_ru}\n\n"
                    f"🍿 <a href='{video_url}'><b>СМОТРЕТЬ ТРАНСЛЯЦИЮ</b></a>\n\n"
                    f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
                )
                
                return caption, l_id, video_url, launch.get('image')
            
            return None, None, None, None # Если ничего нового не нашли

        except Exception as e:
            print(f"⚠️ Ошибка: {e}. Ждем...")
            time.sleep(5)
            
    return None, None, None, None

def send():
    text, l_id, video_url, fallback_img = get_live_launch()
    if text:
        payload = {
            "chat_id": CHANNEL_NAME,
            "text": text,
            "parse_mode": "HTML",
            "link_preview_options": {
                "url": video_url,
                "prefer_large_media": True
            }
        }
        r = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", json=payload)
        if r.status_code == 200:
            with open(DB_FILE, 'a', encoding='utf-8') as f: f.write(f"{l_id}\n")
            print(f"✅ Мировая трансляция {l_id} отправлена!")

if __name__ == '__main__':
    send()
