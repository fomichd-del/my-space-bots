import requests
import os
from datetime import datetime, timezone
from deep_translator import GoogleTranslator

# --- ⚙️ НАСТРОЙКИ ---
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHANNEL_NAME = '@vladislav_space'
DB_FILE = "sent_radar_lives.txt" # Память, чтобы не частить

translator = GoogleTranslator(source='auto', target='ru')

# Стоп-слова (строго без войны и политики)
FORBIDDEN_WORDS = ['military', 'defense', 'spy', 'reconnaissance', 'missile', 'combat', 'war', 'weapon', 'nuke', 'army', 'война', 'оборона', 'ядерный']

def is_military(text):
    if not text: return False
    return any(word in text.lower() for word in FORBIDDEN_WORDS)

def get_global_launches():
    """Ищет ближайшие мирные запуски"""
    url = "https://ll.thespacedevs.com/2.2.0/launch/upcoming/?limit=5"
    try:
        response = requests.get(url, timeout=25)
        if response.status_code != 200: return None, None, None, None
        
        data = response.json()
        launches = data.get('results', [])
        
        if os.path.exists(DB_FILE):
            with open(DB_FILE, 'r', encoding='utf-8') as f:
                sent_ids = f.read().splitlines()
        else:
            sent_ids = []

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
            
            # --- ЛОГИКА ПОИСКА ССЫЛКИ ---
            watch_link = None
            # 1. Проверяем видео-ссылки (YouTube, X, Twitch)
            vid_urls = launch.get('vidURLs', [])
            if vid_urls:
                watch_link = vid_urls[0].get('url')
            
            # 2. Если видео нет, берем ссылку на инфо-страницу
            if not watch_link:
                info_urls = launch.get('infoURLs', [])
                if info_urls:
                    watch_link = info_urls[0].get('url')

            mission_ru = translator.translate(mission_desc) if mission_desc else "Научная миссия по изучению космоса."
            agency_ru = translator.translate(launch['launch_service_provider']['name'])

            # Формируем строку кнопки только если ссылка есть
            if watch_link:
                action_line = f"🍿 <a href='{watch_link}'><b>СМОТРЕТЬ ТРАНСЛЯЦИЮ</b></a>\n\n"
            else:
                action_line = f"🍿 <i>Ссылка на трансляцию появится ближе к старту</i>\n\n"
            
            caption = (
                f"🚀 <b>МИРОВОЙ ЗАПУСК: {rocket_name.upper()}</b>\n"
                f"─────────────────────\n\n"
                f"🏢 <b>Организатор:</b> {agency_ru}\n"
                f"📍 <b>Космодром:</b> {location}\n"
                f"📅 <b>Старт:</b> {launch_time.strftime('%d.%m.%Y %H:%M')} UTC\n\n"
                f"📖 <b>О МИССИИ:</b>\n{mission_ru}\n\n"
                f"{action_line}"
                f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
            )
            
            return caption, launch_id, img_url, watch_link

    except: return None, None, None, None
    return None, None, None, None

def send():
    text, launch_id, img_url, watch_link = get_global_launches()
    if text:
        # Если ссылки на видео нет, используем картинку запуска для превью
        preview_url = watch_link if watch_link else img_url
        
        payload = {
            "chat_id": CHANNEL_NAME,
            "text": text,
            "parse_mode": "HTML",
            "link_preview_options": {
                "url": preview_url,
                "prefer_large_media": True, 
                "show_above_text": False
            }
        }
        
        r = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", json=payload)
        if r.status_code == 200:
            with open(DB_FILE, 'a', encoding='utf-8') as f:
                f.write(f"{launch_id}\n")

if __name__ == '__main__':
    send()
