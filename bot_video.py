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

print("🚀 [ЦУП] Активация гибрида v182.5 'Supernova'. Режим: Невидимка.")

# ============================================================
# ⚙️ КОНФИГУРАЦИЯ (На базе v177 + улучшения)
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

SPACE_KEYWORDS = ['космос', 'планета', 'звезда', 'галактика', 'марс', 'юпитер', 'сатурн', 'вселенная', 'астрономия', 'телескоп', 'млечный путь', 'черная дыра', 'астероид', 'метеорит', 'луна', 'солнце', 'ракета', 'spacex', 'nasa', 'роскосмос', 'инопланет', 'орбита', 'мкс', 'космонавт', 'астронавт', 'марсоход', 'starship']
USER_AGENTS = ['Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36']

MARTY_QUOTES = [
    "Гав! Засек неопознанный объект, его точно нет в бортовом журнале! 🛸🐾",
    "Ррр-гав! Все системы синхронизированы, летим без повторов! ✨",
    "Тяв! Командор, я достал секретные ключи, YouTube нас пропустит! 🔐",
    "Гав! Мой хвост вибрирует от мощности этой ракеты! 🚀",
    "Ррр-гав! Взломал код Вселенной, несите косточку! 🦴",
    "Гав! Пролетаем через туманность, выглядит эпично! 🌌",
    "Тяв! Командор, связь с Землей стабильна, передаю данные! 📡",
    "Гав! Владислав, смотрите какой ракурс! Просто космос! 📸",
    "Гав! Миссия выполнена, возвращаюсь на базу за наградой! 🏆"
]

# ============================================================
# 🛠 ВСПОМОГАТЕЛЬНЫЕ СИСТЕМЫ
# ============================================================

def get_smart_summary(text):
    if not text: return "Тайны космоса ждут вас внутри этого выпуска! ✨"
    text = re.sub(r'http\S+', '', text); text = re.sub(r'#\S+', '', text); text = html.unescape(text)
    junk = ['vk.com', 'ok.ru', 't.me', 'подписывайтесь', 'подпишись', 'наш канал', 'vpn', 'amnezia', 'сайт:', 'facebook', 'instagram', 'twitter', 'скачать', 'boosty', 'patreon', 'кхл', 'билет', 'тинькофф']
    lines = [l.strip() for l in text.split('\n') if len(l.strip()) > 25 and not any(j in l.lower() for j in junk)]
    lines = [l for l in lines if not re.match(r'^\d{1,2}:\d{2}', l)]
    full = " ".join(lines); sentences = re.split(r'(?<=[.!?]) +', full)
    res = " ".join([s.strip() for s in sentences if len(s) > 35][:2])
    if not res or len(res) < 15: res = "Погружаемся в тайны Вселенной в новом выпуске!"
    return res.replace('<', '«').replace('>', '»').replace('&', 'и')

def get_fast_proxy():
    print("🛰 [ЦУП] Поиск гипер-коридора...")
    url = "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=5000&country=all&ssl=all&anonymity=all"
    try:
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            proxies = resp.text.strip().split('\n'); random.shuffle(proxies)
            for p in proxies[:20]:
                p_str = f"http://{p.strip()}"
                try: 
                    requests.get("https://www.youtube.com", proxies={"https": p_str}, timeout=2)
                    return p_str
                except: continue
    except: pass
    return None

# ============================================================
# 🎬 ПРОЦЕССОР (v182.5 Hybrid)
# ============================================================

async def process_mission(v_url, title, desc_raw, is_russian=False, source_name=""):
    global whisper_model
    v_id = v_url.split('=')[-1] if '=' in v_url else v_url.split('/')[-1]
    
    # Фильтр для определенных каналов
    if source_name in ["EVLSPACE", "ADME_RU"]:
        search_text = (title + " " + (desc_raw if desc_raw else "")).lower()
        if not any(word in search_text for word in SPACE_KEYWORDS): 
            print(f"⏭ [ЦУП] Объект {v_id} не прошел космо-фильтр."); return False
            
    f_raw, f_final, f_thumb, f_cookies = "raw_video.mp4", "final_video.mp4", "thumb.jpg", "cookies.txt"
    for f in [f_raw, f_final, "subs.srt", f_thumb, f_cookies]:
        if os.path.exists(f): os.remove(f)

    if YOUTUBE_COOKIES:
        with open(f_cookies, "w", encoding="utf-8") as f: f.write(YOUTUBE_COOKIES)

    try:
        proxy = get_fast_proxy()
        print(f"📡 [ЦУП] Анализ объекта {v_id} ({source_name})...")
        
        # Настройки захвата (Гибрид v177 + v181)
        base_ydl_opts = {
            'quiet': True, 'proxy': proxy,
            'user_agent': random.choice(USER_AGENTS),
            'nocheckcertificate': True,
            'js_runtimes': {'node': {}}, 
            'remote_components': ['ejs:github'], 
            'cookiefile': f_cookies if os.path.exists(f_cookies) else None,
            'extractor_args': {'youtube': {'player_client': ['android', 'ios'], 'player_skip': ['configs']}},
            'socket_timeout': 30
        }
        
        with yt_dlp.YoutubeDL(base_ydl_opts) as ydl:
            try:
                info = ydl.extract_info(v_url, download=False)
            except Exception as e:
                print(f"⚠️ Ошибка источника: {e}"); return False
            duration = info.get('duration', 0)
            filesize = (info.get('filesize_approx') or 0) / (1024 * 1024)
            print(f"⏱ Длительность: {duration}с. Вес: ~{filesize:.1f}Мб")

        if duration > 3600 or duration == 0: return False

        # УМНАЯ НАВИГАЦИЯ 2.0 (по весу и времени)
        h_limit = 720
        if duration > 1800 or filesize > 800: h_limit = 360
        elif duration > 900 or filesize > 400: h_limit = 480
        w_limit = {240: 426, 360: 640, 480: 854, 720: 1280}.get(h_limit, 854)

        print(f"📥 Загрузка в {h_limit}p...")
        with yt_dlp.YoutubeDL({**base_ydl_opts, 'format': f'bestvideo[height<={h_limit}][ext=mp4]+bestaudio[ext=m4a]/best[height<={h_limit}]', 'outtmpl': f_raw}) as ydl:
            ydl.download([v_url])
            
        if not os.path.exists(f_raw): return False
        
        # WHISPER
        has_subs = False
        if not is_russian:
            print("🧠 Whisper...")
            if whisper_model is None: whisper_model = whisper.load_model("base")
            res = whisper_model.transcribe(f_raw)
            segments = res.get('segments', [])
            if segments:
                srt_data = [f"{i+1}\n{time.strftime('%H:%M:%S,000', time.gmtime(s['start']))} --> {time.strftime('%H:%M:%S,000', time.gmtime(s['end']))}\n{GoogleTranslator(source='auto', target='ru').translate(s['text'].strip())}\n\n" for i, s in enumerate(segments)]
                with open("subs.srt", "w", encoding="utf-8") as fs: fs.write("".join(srt_data))
                has_subs = True

        # МОНТАЖ (FFMPEG С УСИЛЕНИЕМ)
        print("🎬 Финальный монтаж...")
        target_bps = int((SAFE_LIMIT_MB * 1024 * 1024 * 8) / (duration + 4))
        v_br = max(100000, min(target_bps - 40000, 2000000))
        
        filter_pad = f"scale={w_limit}:{h_limit}:force_original_aspect_ratio=decrease,pad={w_limit}:{h_limit}:(ow-iw)/2:(oh-ih)/2,setsar=1"
        
        if os.path.exists(INTRO_FILE) and os.path.exists(OUTRO_FILE):
            ff_cmd = ['ffmpeg', '-y', '-loop', '1', '-t', '2', '-i', INTRO_FILE, '-i', f_raw, '-loop', '1', '-t', '2', '-i', OUTRO_FILE, '-filter_complex', f"[0:v]{filter_pad}[v0];[1:v]{'subtitles=subs.srt:' if has_subs else ''}{filter_pad}[v1];[2:v]{filter_pad}[v2];[v0][v1][v2]concat=n=3:v=1:a=0[v];[1:a]adelay=2000|2000:all=1[a]", '-map', '[v]', '-map', '[a]', '-c:v', 'libx264', '-b:v', str(v_br), '-preset', 'ultrafast', '-max_muxing_queue_size', '1024', '-c:a', 'aac', '-b:a', '32k', f_final]
        else:
            ff_cmd = ['ffmpeg', '-y', '-i', f_raw, '-vf', f"{'subtitles=subs.srt:' if has_subs else ''}scale=-2:{h_limit}", '-c:v', 'libx264', '-b:v', str(v_br), '-preset', 'ultrafast', '-max_muxing_queue_size', '1024', '-c:a', 'aac', '-b:a', '32k', f_final]
        
        subprocess.run(ff_cmd)
        f_to_send = f_final if os.path.exists(f_final) else f_raw

        # Превью
        if os.path.exists(INTRO_FILE):
            subprocess.run(['ffmpeg', '-y', '-i', INTRO_FILE, '-vf', 'scale=320:-1', f_thumb], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            subprocess.run(['ffmpeg', '-y', '-i', f_to_send, '-ss', '00:00:01.000', '-vframes', '1', '-vf', 'scale=320:-1', f_thumb], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        ru_title = (title if is_russian else GoogleTranslator(source='auto', target='ru').translate(title)).upper()
        summary = get_smart_summary(desc_raw if is_russian else GoogleTranslator(source='auto', target='ru').translate(desc_raw))
        caption = f"<b>{'🎙 ОРИГИНАЛ' if is_russian else '📝 ПЕРЕВОД'}</b>\n\n🎬 <b>{ru_title}</b>\n──────────────────────\n\n🚀 <b>В ВЫПУСКЕ:</b>\n<i>{summary}</i>\n\n<b>Марти:</b> <i>{random.choice(MARTY_QUOTES)}</i>\n\n📡 <a href='https://t.me/vladislav_space'>ДНЕВНИК ЮНОГО КОСМОНАВТА</a>"

        with open(f_to_send, 'rb') as v:
            files = {"video": v}
            if os.path.exists(f_thumb): files["thumbnail"] = open(f_thumb, 'rb')
            requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo", files=files, data={"chat_id": CHANNEL_NAME, "caption": caption, "parse_mode": "HTML", "supports_streaming": "true"}, timeout=600)
            return True
    except Exception as e: print(f"⚠️ Сбой: {e}"); return False

# ============================================================
# 🛰 ГЛАВНЫЙ ЦИКЛ (С Железной Памятью)
# ============================================================

async def main():
    # Загружаем базу как SET (точное совпадение)
    db = set()
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r') as f:
            db = {line.strip() for line in f if line.strip()}

    last_s = open(SOURCE_LOG, 'r').read().strip() if os.path.exists(SOURCE_LOG) else ""
    time_limit = datetime.now(timezone.utc) - timedelta(days=30)
    
    YT_SOURCES = [{'n': 'ADME_RU', 'cid': '@ADME_RU', 'ru': True}, {'n': 'Космос понятно', 'cid': '@Космоспонятно', 'ru': True}, {'n': 'SpaceX Fan', 'cid': '@spacexfan420', 'ru': True}, {'n': 'Rocket Hub', 'cid': '@rockethubspace', 'ru': True}, {'n': 'NASA', 'cid': '@NASAJPL', 'ru': False}, {'n': 'KOSMO', 'cid': '@off_kosmo', 'ru': True}, {'n': 'EVLSPACE', 'cid': '@EVLSPACE', 'ru': True}, {'n': 'ночнаянаука-ц4ш', 'cid': '@ночнаянаука-ц4ш', 'ru': True}, {'n': 'Hubbler', 'cid': '@Hubbler', 'ru': True}, {'n': 'Cosmosprosto', 'cid': '@cosmosprosto', 'ru': True}]
    
    RESERVE_SOURCES = [{'n': 'NASA_Breaking', 'url': 'https://www.nasa.gov/rss/dyn/breaking_news.rss', 'ru': False}, {'n': 'ESA_Videos', 'url': 'https://www.esa.int/rssfeed/Videos', 'ru': False}]

    random.shuffle(YT_SOURCES)
    for s in YT_SOURCES:
        if s['n'] == last_s: continue
        print(f"🛰 [ЦУП] Сектор: {s['n']}...")
        try:
            url = f"https://www.googleapis.com/youtube/v3/channels?part=contentDetails&forHandle={s['cid'].replace('@','')}&key={YOUTUBE_API_KEY}"
            res = requests.get(url, timeout=10).json()
            up_id = res['items'][0]['contentDetails']['relatedPlaylists']['uploads']
            vids_resp = requests.get(f"https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&playlistId={up_id}&maxResults=15&key={YOUTUBE_API_KEY}").json()
            
            # Фильтруем то, что уже было
            candidates = [v for v in vids_resp.get('items', []) if v['snippet']['resourceId']['videoId'] not in db]
            if not candidates: continue

            target = random.choice(candidates[:5]) # Случайное из самых свежих
            v_id = target['snippet']['resourceId']['videoId']
            
            if await process_mission(f"https://www.youtube.com/watch?v={v_id}", target['snippet']['title'], target['snippet']['description'], s['ru'], s['n']):
                with open(DB_FILE, 'a') as f: f.write(f"{v_id}\n")
                with open(SOURCE_LOG, 'w') as f: f.write(s['n']); return
        except: continue

    # Резерв
    print("🛰 [ЦУП] Резервный режим...")
    for s in RESERVE_SOURCES:
        try:
            resp = requests.get(s['url'], timeout=10).text
            items = re.findall(r'<item>(.*?)</item>', resp, re.DOTALL)
            for item in items[:10]:
                title = re.search(r'<title>(.*?)</title>', item).group(1)
                link = re.search(r'<link>(.*?)</link>', item).group(1)
                v_id = link.split('/')[-1]
                if v_id in db: continue
                if await process_mission(link, title, "Новое видео из архивов", s['ru'], s['n']):
                    with open(DB_FILE, 'a') as f: f.write(f"\n{v_id}")
                    with open(SOURCE_LOG, 'w') as f: f.write(s['n']); return
        except: continue

if __name__ == '__main__':
    asyncio.run(main())
