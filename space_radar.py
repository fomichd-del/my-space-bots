import requests
import os
from datetime import datetime, timezone
from deep_translator import GoogleTranslator

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
NASA_API_KEY = os.getenv('NASA_API_KEY')
CHANNEL_NAME = '@vladislav_space'
DB_FILE = "sent_radar_lives.txt"

translator = GoogleTranslator(source='auto', target='ru')
FORBIDDEN = ['military', 'spy', 'defense', 'weapon', 'война', 'оборона']

def get_radar():
    print("📡 [РАДАР] Сканирование частот...")
    res = requests.get("https://ll.thespacedevs.com/2.2.0/launch/upcoming/?limit=10").json()
    launches = res.get('results', [])
    
    sent_ids = open(DB_FILE, 'r').read().splitlines() if os.path.exists(DB_FILE) else []

    for l in launches:
        l_id = str(l['id'])
        if l_id in sent_ids: continue
        
        # Мирный фильтр
        desc = l.get('mission', {}).get('description', '')
        if any(w in (desc + l['name']).lower() for w in FORBIDDEN): continue

        # Ищем трансляцию (за 3 часа до пуска)
        net = datetime.fromisoformat(l['net'].replace('Z', '+00:00'))
        diff = (net - datetime.now(timezone.utc)).total_seconds() / 60
        
        if -20 < diff < 180:
            video = None
            if l.get('vidURLs'): video = l['vidURLs'][0]['url']
            
            if not video and YOUTUBE_API_KEY:
                # Поиск через YouTube если нет в базе
                q = f"{l['launch_service_provider']['name']} {l['name']} live"
                r = requests.get(f"https://www.googleapis.com/youtube/v3/search?part=snippet&eventType=live&type=video&q={q}&key={YOUTUBE_API_KEY}").json()
                if r.get('items'): video = f"https://www.youtube.com/watch?v={r['items'][0]['id']['videoId']}"

            if video:
                prov_ru = translator.translate(l['launch_service_provider']['name'])
                text = (
                    f"📡 <b>РАДАР: ПРЯМОЙ ЭФИР {l['rocket']['configuration']['name'].upper()}</b>\n"
                    f"─────────────────────\n\n"
                    f"🏢 <b>Организатор:</b> {prov_ru}\n"
                    f"📅 <b>Старт:</b> {net.strftime('%H:%M')} UTC\n\n"
                    f"🍿 <a href='{video}'><b>ПОДКЛЮЧИТЬСЯ К ТРАНСЛЯЦИИ</b></a>\n\n"
                    f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
                )
                
                payload = {"chat_id": CHANNEL_NAME, "text": text, "parse_mode": "HTML"}
                if requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", json=payload).status_code == 200:
                    with open(DB_FILE, 'a') as f: f.write(f"{l_id}\n")
                    print(f"✅ Радар засёк эфир: {l['name']}")
                    return

if __name__ == '__main__':
    get_radar()
