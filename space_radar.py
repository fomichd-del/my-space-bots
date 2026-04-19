import requests
import os
import random
import json  # Добавлено для работы с клавиатурой и настройками превью
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
    if not YOUTUBE_API_KEY: return None
    try:
        url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&eventType=live&type=video&q={query}&key={YOUTUBE_API_KEY}"
        res = requests.get(url, timeout=10).json()
        if res.get('items'):
            # Возвращаем кортеж (bypass-ссылка, оригинальный ID)
            return res['items'][0]['id']['videoId']
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
        res = requests.get("https://ll.thespacedevs.com/2.2.0/launch/upcoming/?limit=10", timeout=30).json()
        launches = res.get('results', [])
    except: return

    sent_ids = open(DB_FILE, 'r').read().splitlines() if os.path.exists(DB_FILE) else []

    for l in launches:
        l_id = str(l['id'])
        if l_id in sent_ids: continue

        desc = l.get('mission', {}).get('description', '')
        if any(w in (desc + l['name']).lower() for w in FORBIDDEN):
            print(f"🛑 Пропуск (Военная миссия): {l['name']}")
            continue

        net = datetime.fromisoformat(l['net'].replace('Z', '+00:00'))
        diff = (net - datetime.now(timezone.utc)).total_seconds() / 60

        if -20 < diff < 180:
            prov = l['launch_service_provider']['name']
            
            # Поиск видео
            video_id = get_yt_live(f"{prov} {l['name']} live launch")
            
            # Если через поиск не нашли, пробуем взять из базы
            if not video_id and l.get('vidURLs'):
                db_v = l['vidURLs'][0]['url']
                if "youtube.com/watch?v=" in db_v:
                    video_id = db_v.split('v=')[-1]
                elif "youtu.be/" in db_v:
                    video_id = db_v.split('/')[-1]

            if not video_id:
                print(f"🔇 Для {l['name']} эфир пока не обнаружен.")
                continue

            # Ссылки для разных целей
            bypass_url = f"https://www.youtube.com/watch?v={video_id}"
            standard_url = f"https://www.youtube.com/watch?v={video_id}"
            img = l.get('image') or get_nasa_image()

            # ОФОРМЛЕНИЕ ТЕКСТА
            # Скрытая ссылка на фото (нулевой ширины пробел) позволяет оставить картинку сверху
            text = (
                f"<a href='{img}'>&#8203;</a>"
                f"📡 <b>РАДАР ПОЙМАЛ ЭФИР: {l['rocket']['configuration']['name'].upper()}</b>\n"
                f"─────────────────────\n\n"
                f"🏢 <b>Организатор:</b> {translator.translate(prov)}\n"
                f"📅 <b>Старт:</b> {net.strftime('%H:%M')} UTC\n\n"
                f"📖 <b>О МИССИИ:</b>\n{translator.translate(desc) if desc else 'Научное исследование.'}\n\n"
                f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
            )

            # Кнопка-"бар" снизу
            keyboard = {"inline_keyboard": [[{"text": "🍿 СМОТРЕТЬ ПРЯМОЙ ЭФИР", "url": bypass_url}]]}

            # Настройки превью для создания "видео-экрана"
            payload = {
                "chat_id": CHANNEL_NAME,
                "text": text,
                "parse_mode": "HTML",
                "reply_markup": json.dumps(keyboard),
                "link_preview_options": {
                    "url": standard_url,       # Ссылка, по которой строится плеер
                    "show_above_text": False,  # Разместить экран СНИЗУ под текстом
                    "prefer_large_media": True # Сделать видео-экран большим
                }
            }

            # Отправка через sendMessage
            r = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", json=payload)
            
            if r.status_code == 200:
                with open(DB_FILE, 'a') as f: f.write(f"{l_id}\n")
                print(f"✅ Радар зафиксировал эфир с плеером: {l['name']}")
                break

if __name__ == '__main__':
    run_radar()
