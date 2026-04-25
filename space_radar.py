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
    """Ищет видео, захватывая и Live, и запланированные эфиры"""
    if not YOUTUBE_API_KEY: return None
    try:
        # Ищем трансляции (live) и запланированные (upcoming)
        url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&type=video&q={query}&key={YOUTUBE_API_KEY}&maxResults=3"
        res = requests.get(url, timeout=10).json()
        
        if res.get('items'):
            for item in res['items']:
                status = item['snippet'].get('liveBroadcastContent')
                # Берем только если эфир идет СЕЙЧАС или скоро начнется
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
    print("📡 [РАДАР] Инициализация сканирования...")
    try:
        res = requests.get("https://ll.thespacedevs.com/2.2.0/launch/upcoming/?limit=10", timeout=30).json()
        launches = res.get('results', [])
    except Exception as e:
        print(f"❌ Ошибка связи с космодромом: {e}")
        return

    sent_ids = open(DB_FILE, 'r').read().splitlines() if os.path.exists(DB_FILE) else []

    for l in launches:
        l_id = str(l['id'])
        
        # Пропускаем, если уже постили
        if l_id in sent_ids: continue

        net = datetime.fromisoformat(l['net'].replace('Z', '+00:00'))
        diff = (net - datetime.now(timezone.utc)).total_seconds() / 60
        
        # ДИАГНОСТИКА: Печатаем всё, что видим в радиусе 12 часов
        if diff < 720:
            print(f"🔎 В поле зрения: {l['name']} (T-{int(diff)} мин)")

        # Мирный фильтр
        desc = l.get('mission', {}).get('description', '')
        if any(w in (desc + l['name']).lower() for w in FORBIDDEN):
            print(f"🛑 Пропуск: {l['name']} (Военный объект)")
            continue

        # ОКНО ПУБЛИКАЦИИ: от 4 часов до старта до 30 минут после
        if -30 < diff < 240:
            prov = l['launch_service_provider']['name']
            print(f"🎯 ЦЕЛЬ ЗАХВАЧЕНА: {l['name']}. Поиск трансляции...")
            
            # Поиск через YouTube API
            video_id = get_yt_live(f"{prov} {l['name']} live launch")
            
            # Резервный поиск в базе (если YouTube API не нашел)
            if not video_id and l.get('vidURLs'):
                for vid in l['vidURLs']:
                    url_v = vid['url']
                    if "youtube.com/watch?v=" in url_v:
                        video_id = url_v.split('v=')[-1].split('&')[0]
                        break
                    elif "youtu.be/" in url_v:
                        video_id = url_v.split('/')[-1].split('?')[0]
                        break

            if not video_id:
                print(f"🔇 Эфир для {l['name']} пока не обнаружен.")
                continue

            video_url = f"https://www.youtube.com/watch?v={video_id}"
            img = l.get('image') or get_nasa_image()

            # ОФОРМЛЕНИЕ
            text = (
                f"📡 <b>РАДАР ПОЙМАЛ ЭФИР: {l['rocket']['configuration']['name'].upper()}</b>\n"
                f"─────────────────────\n\n"
                f"🏢 <b>Организатор:</b> {translator.translate(prov)}\n"
                f"📅 <b>Старт:</b> {net.strftime('%H:%M')} UTC\n\n"
                f"📖 <b>О МИССИИ:</b>\n{translator.translate(desc) if desc else 'Научное исследование.'}\n\n"
                f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
            )

            keyboard = {"inline_keyboard": [[{"text": "🍿 СМОТРЕТЬ ТРАНСЛЯЦИЮ", "url": video_url}]]}

            # Отправка с ВИДЕО-ЭКРАНОМ
            payload = {
                "chat_id": CHANNEL_NAME,
                "text": text,
                "parse_mode": "HTML",
                "reply_markup": json.dumps(keyboard),
                "link_preview_options": {
                    "url": video_url,
                    "show_above_text": True,   # Видео-плеер СВЕРХУ
                    "prefer_large_media": True # Большой размер
                }
            }

            r = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", json=payload)
            
            if r.status_code == 200:
                with open(DB_FILE, 'a') as f: f.write(f"{l_id}\n")
                print(f"✅ ПОСТ ОТПРАВЛЕН: {l['name']}")
            else:
                print(f"❌ Ошибка Telegram: {r.text}")

if __name__ == '__main__':
    run_radar()
