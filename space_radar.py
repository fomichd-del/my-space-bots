import requests
import os
from datetime import datetime, timezone
from deep_translator import GoogleTranslator

# --- ⚙️ НАСТРОЙКИ ---
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHANNEL_NAME = '@vladislav_space'
DB_FILE = "sent_radar_lives.txt"

translator = GoogleTranslator(source='auto', target='ru')

# Список стоп-слов (без политики и войны)
FORBIDDEN_WORDS = ['military', 'defense', 'spy', 'reconnaissance', 'missile', 'combat', 'war', 'weapon', 'nuke', 'army', 'война', 'оборона']

def is_military(text):
    if not text: return False
    return any(word in text.lower() for word in FORBIDDEN_WORDS)

def get_global_launches():
    url = "https://ll.thespacedevs.com/2.2.0/launch/upcoming/?limit=5"
    try:
        response = requests.get(url, timeout=25)
        if response.status_code != 200: return None, None, None, None
        
        data = response.json()
        launches = data.get('results', [])
        
        sent_ids = []
        if os.path.exists(DB_FILE):
            with open(DB_FILE, 'r', encoding='utf-8') as f:
                sent_ids = f.read().splitlines()

        for launch in launches:
            launch_id = str(launch['id'])
            if launch_id in sent_ids: continue

            mission = launch.get('mission')
            mission_desc = mission.get('description', '') if mission else ""
            if is_military(mission_desc) or is_military(launch.get('name', '')): continue

            rocket_name = launch['rocket']['configuration']['name']
            location = launch['pad']['location']['name']
            launch_time = datetime.fromisoformat(launch['net'].replace('Z', '+00:00'))
            img_url = launch.get('image')
            
            # Собираем все возможные ссылки на видео
            video_url = None
            vid_urls = launch.get('vidURLs', [])
            if vid_urls:
                video_url = vid_urls[0].get('url')
            
            # Если видео-ссылки нет совсем, используем ссылку на инфо-страницу
            if not video_url:
                info_urls = launch.get('infoURLs', [])
                if info_urls: video_url = info_urls[0].get('url')

            mission_ru = translator.translate(mission_desc) if mission_desc else "Научная миссия."
            agency_ru = translator.translate(launch['launch_service_provider']['name'])

            # ОФОРМЛЕНИЕ
            # Если видео нет, ссылка в тексте ведет на пост, а превью покажет картинку запуска
            watch_link = video_url if video_url else f"https://t.me/{CHANNEL_NAME[1:]}"
            
            caption = (
                f"🚀 <b>МИРОВОЙ ЗАПУСК: {rocket_name.upper()}</b>\n"
                f"─────────────────────\n\n"
                f"🏢 <b>Организатор:</b> {agency_ru}\n"
                f"📍 <b>Космодром:</b> {location}\n"
                f"📅 <b>Старт:</b> {launch_time.strftime('%d.%m.%Y %H:%M')} UTC\n\n"
                f"📖 <b>О МИССИИ:</b>\n{mission_ru}\n\n"
                f"🍿 <a href='{watch_link}'><b>СМОТРЕТЬ ТРАНСЛЯЦИЮ</b></a>\n\n"
                f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
            )
            
            return caption, launch_id, img_url, watch_link

    except: return None, None, None, None
    return None, None, None, None

def send():
    text, launch_id, img_url, watch_link = get_global_launches()
    if text:
        # Умный превью-бар: 
        # Если есть видео — покажет плеер. Если нет — покажет большую картинку запуска.
        payload = {
            "chat_id": CHANNEL_NAME,
            "text": text,
            "parse_mode": "HTML",
            "link_preview_options": {
                "url": watch_link,
                "prefer_large_media": True, # Делает картинку/видео на всю ширину
                "show_above_text": False
            }
        }
        
        # Если ссылка на трансляцию слабая, используем img_url как обложку
        if not any(x in watch_link for x in ['youtube', 'youtu.be', 'vimeo', 'twitch']):
            payload["link_preview_options"]["url"] = img_url if img_url else watch_link

        r = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", json=payload)
        if r.status_code == 200:
            with open(DB_FILE, 'a', encoding='utf-8') as f:
                f.write(f"{launch_id}\n")

if __name__ == '__main__':
    send()
