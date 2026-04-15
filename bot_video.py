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
import xml.etree.ElementTree as ET
from datetime import datetime
from deep_translator import GoogleTranslator

# ============================================================
# ⚙️ КОНФИГУРАЦИЯ v105.0
# ============================================================
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
NASA_API_KEY   = os.getenv('NASA_API_KEY')
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
CHANNEL_NAME   = '@vladislav_space'
DB_FILE        = "last_video_date.txt"
START_DATE     = "2026-01-01T00:00:00Z" # Наш временной барьер

translator = GoogleTranslator(source='auto', target='ru')
try:
    model = whisper.load_model("tiny")
except:
    model = None

# ============================================================
# 🛠 ИНСТРУМЕНТЫ ОБРАБОТКИ
# ============================================================

def safe_translate(text):
    if not text or len(str(text)) < 5: return ""
    try: return translator.translate(str(text))
    except: return str(text)

def super_clean(text):
    if not text: return ""
    text = re.sub(r'http\S+', '', str(text)) 
    text = re.sub(r'<[^>]+>', '', text)      
    return html.escape(html.unescape(text)).strip()

async def process_video(video_url):
    video_url = video_url.strip().replace(" ", "%20")
    f_in, f_out = "input.mp4", "output.mp4"
    for f in [f_in, f_out, "subs.srt"]:
        if os.path.exists(f): os.remove(f)

    try:
        ydl_opts = {'format': 'best[height<=720]', 'outtmpl': f_in, 'quiet': True, 'noplaylist': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            
            # ❗ ЛОГИКА 50 МБ
            filesize = info.get('filesize', 0) or info.get('filesize_approx', 0)
            if filesize > 48 * 1024 * 1024:
                print(f"📦 Файл слишком большой ({filesize // 1048576} MB). Переход в режим ссылки.")
                return "link_mode", info
            
            ydl.download([video_url])
        
        if os.path.exists(f_in) and model:
            res = model.transcribe(f_in)
            segments = res.get('segments', [])
            if segments:
                srt = ""
                for i, seg in enumerate(segments):
                    s = time.strftime('%H:%M:%S,000', time.gmtime(seg.get('start', 0)))
                    e = time.strftime('%H:%M:%S,000', time.gmtime(seg.get('end', 0)))
                    txt = safe_translate(seg.get('text', ''))
                    if txt: srt += f"{i+1}\n{s} --> {e}\n{txt}\n\n"
                
                if srt:
                    with open("subs.srt", "w", encoding="utf-8") as fs: fs.write(srt)
                    subprocess.run(["ffmpeg", "-y", "-i", f_in, "-vf", "subtitles=subs.srt", "-c:v", "libx264", "-preset", "ultrafast", "-c:a", "copy", f_out], capture_output=True)
                    return (f_out if os.path.exists(f_out) else f_in), "video"
        
        return (f_in if os.path.exists(f_in) else None), "video"
    except: return None, "error"

# ============================================================
# 🛰 ГЛАВНАЯ МИССИЯ
# ============================================================

async def main():
    print(f"🚀 [ЦУП] v105.0 активирована. Поиск с {START_DATE}")
    if not os.path.exists(DB_FILE): open(DB_FILE, 'w').close()
    db = open(DB_FILE, 'r').read()

    SOURCES = [
        {'n': 'SpaceX', 'id': 'UC_MhefFv_XW3c66m7ZAnxHA', 't': 'yt'},
        {'n': 'Роскосмос', 'id': 'UCOm4M6L_L7xOovvS_I-k__A', 't': 'yt'},
        {'n': 'CNSA (Китай)', 'id': 'UCB_yD62_O7V9_W_A4GZ5fLw', 't': 'yt'},
        {'n': 'ESA (Европа)', 'u': 'https://www.esa.int/rssfeed/Videos', 't': 'rss'},
        {'n': 'ESO Science', 'u': 'https://www.eso.org/public/videos/feed/', 't': 'rss'},
        {'n': 'NASA Archives', 't': 'nasa'}
    ]

    random.shuffle(SOURCES)

    for s in SOURCES:
        try:
            print(f"📡 Сканирование: {s['n']}...")
            v_list = []

            if s['t'] == 'yt' and YOUTUBE_API_KEY:
                # Фильтр по дате в YouTube API: publishedAfter
                r = requests.get(f"https://www.googleapis.com/youtube/v3/search?key={YOUTUBE_API_KEY}&channelId={s['id']}&part=snippet,id&order=date&publishedAfter={START_DATE}&maxResults=3&type=video").json()
                for item in r.get('items', []):
                    v_id = item['id']['videoId']
                    if v_id not in db:
                        v_list.append({'url': f"https://www.youtube.com/watch?v={v_id}", 'title': item['snippet']['title'], 'desc': item['snippet']['description'], 'id': v_id})

            elif s['t'] == 'nasa' and NASA_API_KEY:
                # Поиск в NASA с фильтром 2026
                r_nasa = requests.get(f"https://images-api.nasa.gov/search?media_type=video&year_start=2026&api_key={NASA_API_KEY}").json()
                items = r_nasa.get('collection', {}).get('items', [])
                if items:
                    target = items[0]
                    v_id = target['data'][0]['nasa_id']
                    if v_id not in db:
                        assets = requests.get(f"https://images-api.nasa.gov/asset/{v_id}").json()
                        v_url = next((a['href'] for a in assets['collection']['items'] if '~medium.mp4' in a['href']), None)
                        v_list.append({'url': v_url, 'title': target['data'][0]['title'], 'desc': target['data'][0].get('description', ''), 'id': v_id})

            for v in v_list:
                result, mode = await process_video(v['url'])
                if not result: continue

                t_ru = super_clean(safe_translate(v['title']).upper())
                d_ru = safe_translate(v['desc'])
                
                # 📝 КРАСОЧНОЕ ОФОРМЛЕНИЕ
                caption = (
                    f"🛰 <b>{t_ru}</b>\n\n"
                    f"🌍 <b>МИССИЯ:</b> {s['n']}\n"
                    f"📅 <b>ДАТА:</b> 2026\n"
                    f"─────────────────────\n"
                    f"🪐 <b>ГЛАВНЫЕ ФАКТЫ:</b>\n"
                    f"{super_clean(d_ru[:450])}...\n\n"
                    f"✨ <i>Посмотри на звезды — там наше будущее!</i>\n"
                    f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
                )

                if mode == "link_mode":
                    # Режим ссылки (для тяжелых видео)
                    caption = f"🎬 <b>БОЛЬШОЕ ВИДЕО:</b> {t_ru}\n\n" + caption + f"\n\n🔗 <b>СМОТРЕТЬ:</b> {v['url']}"
                    requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", data={"chat_id": CHANNEL_NAME, "text": caption, "parse_mode": "HTML"})
                else:
                    # Режим видео
                    with open(result, 'rb') as f_v:
                        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo", files={"video": f_v}, data={"chat_id": CHANNEL_NAME, "caption": caption, "parse_mode": "HTML"})
                
                with open(DB_FILE, 'a') as f: f.write(f"\n{v['id']}")
                return

        except: continue

if __name__ == '__main__':
    asyncio.run(main())
