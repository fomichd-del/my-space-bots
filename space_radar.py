import requests
import os
import random
from datetime import datetime, timezone
from deep_translator import GoogleTranslator

# ============================================================
# ⚙️ НАСТРОЙКИ
# ============================================================
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
NASA_API_KEY    = os.getenv('NASA_API_KEY')
CHANNEL_NAME    = '@vladislav_space'
DB_FILE         = "sent_radar_lives.txt"

translator = GoogleTranslator(source='auto', target='ru')

# Мирный фильтр (Владик изучает только науку!)
FORBIDDEN = ['military', 'spy', 'defense', 'weapon', 'война', 'оборона', 'classified', 'reconnaissance']

def get_yt_live(query):
    if not YOUTUBE_API_KEY: return None
    try:
        url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&eventType=live&type=video&q={query}&key={YOUTUBE_API_KEY}"
        res = requests.get(url, timeout=10).json()
        if res.get('items'):
            return f"https://www.youtube.com/watch?v={res['items'][0]['id']['videoId']}"
    except: pass
    return None

def get_nasa_img():
    if not NASA_API_KEY: return "https://www.nasa.gov/wp-content/uploads/2023/03/fgs_stsci-01h072ykf6p2p68zvgq4ay79e0.png"
    try:
        res = requests.get(f"https://api.nasa.gov/planetary/apod?api_key={NASA_API_KEY}", timeout=10).json()
        return res.get('url') if res.get('media_type') == 'image' else "https://www.nasa.gov/wp-content/uploads/2023/03/fgs_stsci-01h072ykf6p2p68zvgq4ay79e0.png"
    except: return "https://www.nasa.gov/wp-content/uploads/2023/03/fgs_stsci-01h072ykf6p2p68zvgq4ay79e0.png"

def run_radar():
    print("📡 [РАДАР] Сканирование мировых трансляций...")
    try:
        res = requests.get("https://ll.thespacedevs.com/2.2.0/launch/upcoming/?limit=10", timeout=30).json()
        launches = res.get('results', [])
    except: return

    sent_ids = open(DB_FILE, 'r').read().splitlines() if os.path.exists(DB_FILE) else []

    for l in launches:
        l_id = str(l['id'])
        if l_id in sent_ids: continue

        # Проверка на военные цели
        mission_desc = l.get('mission', {}).get('description', '')
        if any(word in (mission_desc + l['name']).lower() for word in FORBIDDEN):
            print(f"🛑 Пропуск: {l['name']} (военная/секретная)")
            continue

        # Время до старта
        net = datetime.fromisoformat(l['net'].replace('Z', '+00:00'))
        diff = (net - datetime.now(timezone.utc)).total_seconds() / 60

        # Радар ловит только те, что СКОРО (за 3 часа до старта или уже в эфире)
        if -20 < diff < 180:
            provider = l['launch_service_provider']['name']
            
            # Ищем трансляцию через YouTube API
            video = get_yt_live(f"{provider} {l['name']} live launch")
            if not video and l.get('vidURLs'):
                db_v = l['vidURLs'][0]['url']
                if "channel" not in db_v: video = db_v

            # Если трансляции нет — радар не шлет пустой пост
            if not video:
                print(f"🔇 Эфир для {l['name']} еще не начался.")
                continue

            # Оформление
            prov_ru = translator.translate(provider)
            mission_ru = translator.translate(mission_desc) if mission_desc else "Научный запуск."
            img = l.get('image') or get_nasa_img()

            caption = (
                f"📡 <b>РАДАР ПОЙМАЛ СИГНАЛ: {l['rocket']['configuration']['name'].upper()}</b>\n"
                f"─────────────────────\n\n"
                f"🏢 <b>Организатор:</b> {prov_ru}\n"
                f"📍 <b>Локация:</b> {l['pad']['location']['name']}\n\n"
                f"📖 <b>О МИССИИ:</b>\n{mission_ru}\n\n"
                f"🍿 <a href='{video}'><b>ПОДКЛЮЧИТЬСЯ К ЭФИРУ</b></a>\n\n"
                f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
            )

            # Отправка
            payload = {"chat_id": CHANNEL_NAME, "photo": img, "caption": caption, "parse_mode": "HTML"}
            r = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto", json=payload)
            
            if r.status_code == 200:
                with open(DB_FILE, 'a') as f: f.write(f"{l_id}\n")
                print(f"✅ Радар зафиксировал эфир: {l['name']}")
                break

if __name__ == '__main__':
    run_radar()
