import requests
import os
import random
import json
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
FORBIDDEN = ['military', 'spy', 'defense', 'weapon', 'война', 'оборона', 'classified', 'reconnaissance']

def get_yt_live(query):
    """Ищет видео, отдавая приоритет трансляциям (live/upcoming)"""
    if not YOUTUBE_API_KEY: return None
    try:
        # Убираем жесткий фильтр eventType=live, чтобы видеть запланированные пуски
        url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&type=video&q={query}&key={YOUTUBE_API_KEY}&maxResults=3"
        res = requests.get(url, timeout=10).json()
        
        if res.get('items'):
            for item in res['items']:
                status = item['snippet'].get('liveBroadcastContent')
                # Берем только если это прямой эфир или запланированный
                if status in ['live', 'upcoming']:
                    return item['id']['videoId']
    except: pass
    return None

def get_nasa_image():
    if not NASA_API_KEY: return "https://www.nasa.gov/wp-content/uploads/2023/03/fgs_stsci-01h072ykf6p2p68zvgq4ay79e0.png"
    try:
        res = requests.get(f"https://api.nasa.gov/planetary/apod?api_key={NASA_API_KEY}", timeout=10).json()
        return res.get('url') if res.get('media_type') == 'image' else "https://www.nasa.gov/wp-content/uploads/2023/03/fgs_stsci-01h072ykf6p2p68zvgq4ay79e0.png"
    except: return "https://www.nasa.gov/wp-content/uploads/2023/03/fgs_stsci-01h072ykf6p2p68zvgq4ay79e0.png"

def run_radar():
    print("📡 [РАДАР] Сканирование мировых эфиров...")
    try:
        # Увеличили лимит до 15, чтобы видеть больше событий
        res = requests.get("https://ll.thespacedevs.com/2.2.0/launch/upcoming/?limit=15", timeout=30).json()
        launches = res.get('results', [])
    except: return

    sent_ids = open(DB_FILE, 'r').read().splitlines() if os.path.exists(DB_FILE) else []

    for l in launches:
        l_id = str(l['id'])
        if l_id in sent_ids: continue

        # Мирный фильтр
        desc = l.get('mission', {}).get('description', '')
        if any(w in (desc + l['name']).lower() for w in FORBIDDEN):
            print(f"🛑 Пропуск (Военная миссия): {l['name']}")
            continue

        net = datetime.fromisoformat(l['net'].replace('Z', '+00:00'))
        diff = (net - datetime.now(timezone.utc)).total_seconds() / 60

        # Окно работы: за 4 часа (240 мин) до пуска и до 30 мин после старта
        if -30 < diff < 240:
            prov = l['launch_service_provider']['name']
            
            # 1. Пробуем найти через YouTube API (самый надежный способ для плеера)
            video_id = get_yt_live(f"{prov} {l['name']} live launch")
            
            # 2. Если поиск не дал плодов, проверяем базу Space Devs
            if not video_id and l.get('vidURLs'):
                db_v = l['vidURLs'][0]['url']
                if "youtube.com/watch?v=" in db_v:
                    video_id = db_v.split('v=')[-1].split('&')[0]
                elif "youtu.be/" in db_v:
                    video_url_part = db_v.split('/')[-1].split('?')[0]
                    video_id = video_url_part

            if not video_id:
                print(f"🔇 Для {l['name']} (через {int(diff)} мин) эфир пока не создан.")
                continue

            video_url = f"https://www.youtube.com/watch?v={video_id}"

            # Оформление
            text = (
                f"📡 <b>РАДАР ПОЙМАЛ ЭФИР: {l['rocket']['configuration']['name'].upper()}</b>\n"
                f"─────────────────────\n\n"
                f"🏢 <b>Организатор:</b> {translator.translate(prov)}\n"
                f"📅 <b>Старт:</b> {net.strftime('%H:%M')} UTC\n\n"
                f"📖 <b>О МИССИИ:</b>\n{translator.translate(desc) if desc else 'Научное исследование.'}\n\n"
                f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
            )

            # Кнопка под постом
            keyboard = {"inline_keyboard": [[{"text": "🍿 СМОТРЕТЬ ТРАНСЛЯЦИЮ", "url": video_url}]]}

            # Настройки превью: плеер СВЕРХУ, большой экран
            payload = {
                "chat_id": CHANNEL_NAME,
                "text": text,
                "parse_mode": "HTML",
                "reply_markup": json.dumps(keyboard),
                "link_preview_options": {
                    "url": video_url,
                    "show_above_text": True,
                    "prefer_large_media": True
                }
            }

            r = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", json=payload)
            
            if r.status_code == 200:
                with open(DB_FILE, 'a') as f: f.write(f"{l_id}\n")
                print(f"✅ Радар опубликовал эфир: {l['name']}")
                # Убрали break, чтобы обрабатывать все подходящие пуски за раз
            else:
                print(f"❌ Ошибка отправки: {r.text}")

if __name__ == '__main__':
    run_radar()
