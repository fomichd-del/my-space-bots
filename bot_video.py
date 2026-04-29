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

print("🚀 [ЦУП] Системы v180.0 'Deep Memory' активны. Устранение повторов...")

# ============================================================
# ⚙️ КОНФИГУРАЦИЯ
# ============================================================
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY') 
YOUTUBE_COOKIES = os.getenv('YOUTUBE_COOKIES') 
CHANNEL_NAME   = '@vladislav_space'
DB_FILE        = "last_video_date.txt"
SOURCE_LOG     = "last_source.txt"
SAFE_LIMIT_MB  = 46 

INTRO_FILE = "intro.png"
OUTRO_FILE = "intro0.png"

whisper_model = None

SPACE_KEYWORDS = ['космос', 'планета', 'звезда', 'галактика', 'марс', 'вселенная', 'астрономия', 'черная дыра', 'астероид', 'луна', 'солнце', 'ракета', 'spacex', 'nasa', 'роскосмос', 'мкс', 'starship']
USER_AGENTS = ['Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36']

MARTY_QUOTES = [
    "Гав! Проверил бортовой журнал — этого видео там точно нет! 📚🐾",
    "Ррр-гав! Нашел уникальный фрагмент Вселенной! 🌌",
    "Тяв! Командор, я зачистил дубликаты, только свежий контент! 🛰️",
    "Гав! Мой нос не обманешь — это видео пахнет новизной! 🐕",
    "Ррр-гав! Летим к звездам по новому маршруту! 🚀",
    "Гав! Вижу Марс, и мы там еще не были в таком ракурсе! 🟠",
    "Тяв! Космическая память теперь надежна, как сейф! 🔐"
]

def get_smart_summary(text):
    if not text: return "Тайны космоса ждут вас внутри этого выпуска! ✨"
    text = re.sub(r'http\S+', '', text); text = re.sub(r'#\S+', '', text); text = html.unescape(text)
    junk = ['vk.com', 'ok.ru', 't.me', 'подписывайтесь', 'подпишись', 'наш канал', 'vpn', 'amnezia', 'сайт:', 'скидк']
    lines = [l.strip() for l in text.split('\n') if len(l.strip()) > 25 and not any(j in l.lower() for j in junk)]
    full = " ".join(lines); sentences = re.split(r'(?<=[.!?]) +', full)
    res = " ".join([s.strip() for s in sentences if len(s) > 35][:2])
    return res if (res and len(res) > 15) else "Погружаемся в тайны Вселенной в новом выпуске!"

def get_fast_proxy():
    url = "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=5000&country=all&ssl=all&anonymity=all"
    try:
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            proxies = resp.text.strip().split('\n'); random.shuffle(proxies)
            for p in proxies[:15]:
                p_str = f"http://{p.strip()}"
                try: requests.get("https://www.google.com", proxies={"https": p_str}, timeout=2); return p_str
                except: continue
    except: pass
    return None

async def process_mission(v_url, title, desc_raw, is_russian=False, source_name=""):
    global whisper_model
    v_id = v_url.split('=')[-1] if '=' in v_url else v_url.split('/')[-1]
    f_raw, f_final, f_thumb, f_cookies = "raw_video.mp4", "final_video.mp4", "thumb.jpg", "cookies.txt"
    
    for f in [f_raw, f_final, "subs.srt", f_thumb, f_cookies]:
        if os.path.exists(f): os.remove(f)

    if YOUTUBE_COOKIES:
        with open(f_cookies, "w", encoding="utf-8") as f: f.write(YOUTUBE_COOKIES)

    try:
        proxy = get_fast_proxy()
        print(f"📡 [ЦУП] Захват объекта {v_id}...")
        
        ydl_opts = {
            'quiet': True, 'proxy': proxy, 'user_agent': random.choice(USER_AGENTS),
            'nocheckcertificate': True, 'cookiefile': f_cookies if os.path.exists(f_cookies) else None,
            'extractor_args': {'youtube': {'player_client': ['tv', 'web']}}
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(v_url, download=False)
            duration = info.get('duration', 0)
            filesize = (info.get('filesize_approx') or 0) / (1024 * 1024)

        if duration > 2400 or duration == 0: return False

        # УМНАЯ НАВИГАЦИЯ 2.0 (разрешение от веса и времени)
        h_limit = 720
        if duration > 1200 or filesize > 400: h_limit = 360
        elif duration > 600 or filesize > 200: h_limit = 480
        
        print(f"⚖️ ТТХ: {duration}с | ~{filesize:.1f}Мб -> Лимит: {h_limit}p")

        with yt_dlp.YoutubeDL({**ydl_opts, 'format': f'bestvideo[height<={h_limit}][ext=mp4]+bestaudio[ext=m4a]/best[height<={h_limit}]', 'outtmpl': f_raw}) as ydl:
            ydl.download([v_url])
            
        if not os.path.exists(f_raw): return False
        
        # WHISPER (Перевод)
        has_subs = False
        if not is_russian:
            if whisper_model is None: whisper_model = whisper.load_model("base")
            res = whisper_model.transcribe(f_raw)
            segments = res.get('segments', [])
            if segments:
                srt_data = [f"{i+1}\n{time.strftime('%H:%M:%S,000', time.gmtime(s['start']))} --> {time.strftime('%H:%M:%S,000', time.gmtime(s['end']))}\n{GoogleTranslator(source='auto', target='ru').translate(s['text'].strip())}\n\n" for i, s in enumerate(segments)]
                with open("subs.srt", "w", encoding="utf-8") as fs: fs.write("".join(srt_data))
                has_subs = True

        # МОНТАЖ (FFMPEG)
        target_bps = int((44 * 1024 * 1024 * 8) / (duration + 2))
        v_br = max(100000, min(target_bps - 40000, 2000000))
        vf = f"{'subtitles=subs.srt:' if has_subs else ''}scale=-2:{h_limit}"
        
        subprocess.run(['ffmpeg', '-y', '-i', f_raw, '-vf', vf, '-c:v', 'libx264', '-b:v', str(v_br), '-preset', 'ultrafast', '-max_muxing_queue_size', '1024', '-c:a', 'aac', '-b:a', '32k', f_final])
        
        # ОТПРАВКА
        ru_title = (title if is_russian else GoogleTranslator(source='auto', target='ru').translate(title)).upper()
        summary = get_smart_summary(desc_raw if is_russian else GoogleTranslator(source='auto', target='ru').translate(desc_raw))
        caption = f"<b>{'🎙 ОРИГИНАЛ' if is_russian else '📝 ПЕРЕВОД'}</b>\n\n🎬 <b>{ru_title}</b>\n──────────────────────\n\n🚀 <b>В ВЫПУСКЕ:</b>\n<i>{summary}</i>\n\n<b>Марти:</b> <i>{random.choice(MARTY_QUOTES)}</i>\n\n📡 <a href='https://t.me/vladislav_space'>ДНЕВНИК ЮНОГО КОСМОНАВТА</a>"

        with open(f_final, 'rb') as v:
            requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo", files={"video": v}, data={"chat_id": CHANNEL_NAME, "caption": caption, "parse_mode": "HTML", "supports_streaming": "true"}, timeout=600)
            return True
    except Exception as e: print(f"⚠️ Ошибка: {e}"); return False

async def main():
    # Загружаем базу как SET для мгновенного и точного поиска
    db = set()
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r') as f:
            db = {line.strip() for line in f if line.strip()}

    last_s = open(SOURCE_LOG, 'r').read().strip() if os.path.exists(SOURCE_LOG) else ""
    
    YT_SOURCES = [
        {'n': 'ADME_RU', 'cid': '@ADME_RU', 'ru': True},
        {'n': 'Космос понятно', 'cid': '@Космоспонятно', 'ru': True},
        {'n': 'SpaceX Fan', 'cid': '@spacexfan420', 'ru': True},
        {'n': 'Rocket Hub', 'cid': '@rockethubspace', 'ru': True},
        {'n': 'KOSMO', 'cid': '@off_kosmo', 'ru': True},
        {'n': 'EVLSPACE', 'cid': '@EVLSPACE', 'ru': True}
    ]
    random.shuffle(YT_SOURCES)

    for s in YT_SOURCES:
        if s['n'] == last_s: continue
        print(f"🛰 [ЦУП] Сектор: {s['n']}...")
        try:
            url = f"https://www.googleapis.com/youtube/v3/channels?part=contentDetails&forHandle={s['cid'].replace('@','')}&key={YOUTUBE_API_KEY}"
            res = requests.get(url).json()
            up_id = res['items'][0]['contentDetails']['relatedPlaylists']['uploads']
            vids_resp = requests.get(f"https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&playlistId={up_id}&maxResults=10&key={YOUTUBE_API_KEY}").json()
            
            # Собираем кандидатов (те, которых нет в базе)
            candidates = [v for v in vids_resp.get('items', []) if v['snippet']['resourceId']['videoId'] not in db]
            if not candidates: continue

            # Берем случайное из новых (для разнообразия)
            target = random.choice(candidates)
            v_id = target['snippet']['resourceId']['videoId']
            
            if await process_mission(f"https://www.youtube.com/watch?v={v_id}", target['snippet']['title'], target['snippet']['description'], s['ru'], s['n']):
                with open(DB_FILE, 'a') as f: f.write(f"{v_id}\n")
                with open(SOURCE_LOG, 'w') as f: f.write(s['n'])
                print(f"✅ Миссия завершена. ID {v_id} сохранен."); return
        except: continue

if __name__ == '__main__':
    asyncio.run(main())
