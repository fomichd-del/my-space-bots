import os
import random
import time
import subprocess
import whisper
import yt_dlp
import asyncio
import html
import re
import requests
from datetime import datetime, timedelta, timezone
from deep_translator import GoogleTranslator

print("🚀 [ЦУП] Развертывание v181.5 'Stellar Drift'. Обход блокировок...")

# Настройки
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY') 
CHANNEL_NAME   = '@vladislav_space'
DB_FILE        = "last_video_date.txt"
SOURCE_LOG     = "last_source.txt"
SAFE_LIMIT_MB  = 46 

whisper_model = None

MARTY_QUOTES = [
    "Гав! Прокси-коридор обвалился, но я нашел лазейку! 🐾🧤",
    "Ррр-гав! YouTube ставит ловушки, а я их перепрыгиваю! 🚀",
    "Тяв! Командор, включаю режим невидимости, идем по приборам! 🛰️",
    "Гав! Мой нос чует чистый IP за миллион световых лет! 🐕",
    "Тяв! Защита пробита, начинаю захват данных! 🌌"
]

def get_fast_proxy():
    print("🛰 [ЦУП] Сканирование глубокого космоса на наличие чистых прокси...")
    url = "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=5000&country=all&ssl=all&anonymity=all"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            proxies = resp.text.strip().split('\n')
            random.shuffle(proxies)
            # Проверяем первые 20 штук на живучесть
            for p in proxies[:20]:
                p_str = f"http://{p.strip()}"
                try:
                    # Проверяем именно связь с YouTube!
                    requests.get("https://www.youtube.com", proxies={"https": p_str}, timeout=3)
                    print(f"✅ Найден рабочий коридор: {p.strip()}")
                    return p_str
                except: continue
    except: pass
    print("⚠️ Чистых коридоров не найдено. Пробуем прямой прыжок...")
    return None

async def process_mission(v_url, title, desc_raw, is_russian=False, source_name=""):
    global whisper_model
    v_id = v_url.split('=')[-1] if '=' in v_url else v_url.split('/')[-1]
    f_raw, f_final = "raw_video.mp4", "final_video.mp4"
    
    for f in [f_raw, f_final, "subs.srt"]:
        if os.path.exists(f): os.remove(f)

    try:
        proxy = get_fast_proxy()
        
        # Обновленные настройки: убираем 'tv', добавляем ротацию клиентов
        ydl_opts = {
            'quiet': True,
            'proxy': proxy,
            'nocheckcertificate': True,
            'js_runtimes': {'node': {}},
            'remote_components': ['ejs:github'],
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'ios', 'mweb'], # Самые стабильные сейчас
                    'player_skip': ['configs', 'webpage']
                }
            },
            'socket_timeout': 30,
            'retries': 10
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(v_url, download=False)
            duration = info.get('duration', 0)
            filesize = (info.get('filesize_approx') or 0) / (1024 * 1024)

        if duration > 2400 or duration == 0: return False

        # Умная навигация v2
        h_limit = 720
        if duration > 1200 or filesize > 400: h_limit = 360
        elif duration > 600 or filesize > 200: h_limit = 480
        
        print(f"🎯 Цель захвачена: {h_limit}p. Начинаю погружение...")

        with yt_dlp.YoutubeDL({**ydl_opts, 'format': f'bestvideo[height<={h_limit}][ext=mp4]+bestaudio[ext=m4a]/best[height<={h_limit}]', 'outtmpl': f_raw}) as ydl:
            ydl.download([v_url])
            
        if not os.path.exists(f_raw): return False
        
        # Whisper + FFmpeg (без изменений, они работают отлично)
        if not is_russian:
            if whisper_model is None: whisper_model = whisper.load_model("base")
            res = whisper_model.transcribe(f_raw)
            segments = res.get('segments', [])
            if segments:
                srt = "".join([f"{i+1}\n{time.strftime('%H:%M:%S,000', time.gmtime(s['start']))} --> {time.strftime('%H:%M:%S,000', time.gmtime(s['end']))}\n{GoogleTranslator(source='auto', target='ru').translate(s['text'].strip())}\n\n" for i, s in enumerate(segments)])
                with open("subs.srt", "w", encoding="utf-8") as fs: fs.write(srt)

        target_bps = int((44 * 1024 * 1024 * 8) / (duration + 2))
        v_br = max(100000, min(target_bps - 40000, 2000000))
        vf = f"{'subtitles=subs.srt:' if os.path.exists('subs.srt') else ''}scale=-2:{h_limit}"
        
        subprocess.run(['ffmpeg', '-y', '-i', f_raw, '-vf', vf, '-c:v', 'libx264', '-b:v', str(v_br), '-preset', 'ultrafast', '-max_muxing_queue_size', '1024', '-c:a', 'aac', '-b:a', '32k', f_final])
        
        # Отправка
        ru_title = (title if is_russian else GoogleTranslator(source='auto', target='ru').translate(title)).upper()
        caption = f"🎬 <b>{ru_title}</b>\n──────────────────────\n\n<b>Марти:</b> <i>{random.choice(MARTY_QUOTES)}</i>\n\n📡 <a href='https://t.me/vladislav_space'>ДНЕВНИК ЮНОГО КОСМОНАВТА</a>"

        with open(f_final, 'rb') as v:
            requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo", data={"chat_id": CHANNEL_NAME, "caption": caption, "parse_mode": "HTML", "supports_streaming": "true"}, files={"video": v}, timeout=600)
            return True
    except Exception as e:
        print(f"⚠️ Сбой систем: {e}")
        return False

# ... (остальной код main() из v181.0 остается без изменений) ...
async def main():
    db = set()
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r') as f:
            db = {line.strip() for line in f if line.strip()}
    last_s = open(SOURCE_LOG, 'r').read().strip() if os.path.exists(SOURCE_LOG) else ""
    YT_SOURCES = [{'n': 'ADME_RU', 'cid': '@ADME_RU', 'ru': True}, {'n': 'Космос понятно', 'cid': '@Космоспонятно', 'ru': True}, {'n': 'SpaceX Fan', 'cid': '@spacexfan420', 'ru': True}, {'n': 'Rocket Hub', 'cid': '@rockethubspace', 'ru': True}, {'n': 'NASA', 'cid': '@NASAJPL', 'ru': False}, {'n': 'KOSMO', 'cid': '@off_kosmo', 'ru': True}, {'n': 'EVLSPACE', 'cid': '@EVLSPACE', 'ru': True}]
    random.shuffle(YT_SOURCES)
    for s in YT_SOURCES:
        if s['n'] == last_s: continue
        try:
            url = f"https://www.googleapis.com/youtube/v3/channels?part=contentDetails&forHandle={s['cid'].replace('@','')}&key={YOUTUBE_API_KEY}"
            res = requests.get(url).json()
            up_id = res['items'][0]['contentDetails']['relatedPlaylists']['uploads']
            vids_resp = requests.get(f"https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&playlistId={up_id}&maxResults=15&key={YOUTUBE_API_KEY}").json()
            candidates = [v for v in vids_resp.get('items', []) if v['snippet']['resourceId']['videoId'] not in db]
            if not candidates: continue
            target = random.choice(candidates[:5])
            v_id = target['snippet']['resourceId']['videoId']
            if await process_mission(f"https://www.youtube.com/watch?v={v_id}", target['snippet']['title'], target['snippet']['description'], s['ru'], s['n']):
                with open(DB_FILE, 'a') as f: f.write(f"{v_id}\n")
                with open(SOURCE_LOG, 'w') as f: f.write(s['n']); return
        except: continue

if __name__ == '__main__':
    asyncio.run(main())
