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
from deep_translator import GoogleTranslator

# ============================================================
# ⚙️ КОНФИГУРАЦИЯ v100.0
# ============================================================
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
NASA_API_KEY   = os.getenv('NASA_API_KEY')
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
CHANNEL_NAME   = '@vladislav_space'
DB_FILE        = "last_video_date.txt"

translator = GoogleTranslator(source='auto', target='ru')
try:
    model = whisper.load_model("tiny")
except:
    model = None

# ============================================================
# 🛠 ИНСТРУМЕНТЫ ЗАХВАТА
# ============================================================

def safe_translate(text):
    if not text or len(str(text)) < 5: return str(text) if text else ""
    try: return translator.translate(str(text))
    except: return str(text)

def super_clean(text):
    if not text: return ""
    text = re.sub(r'http\S+', '', str(text)) 
    text = re.sub(r'<[^>]+>', '', text)      
    try: text = html.unescape(text)
    except: pass
    return html.escape(text).strip()

async def download_file(url, path):
    """Качает файл напрямую через requests (самый надежный способ для прямых ссылок)"""
    try:
        r = requests.get(url, stream=True, timeout=120)
        if r.status_code == 200:
            with open(path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
            return True
    except: return False
    return False

async def process_video(video_url):
    video_url = video_url.strip().replace(" ", "%20")
    print(f"🎬 [ЦУП] Попытка захвата: {video_url}")
    
    f_in, f_out = "input.mp4", "output.mp4"
    for f in [f_in, f_out, "subs.srt"]:
        if os.path.exists(f): os.remove(f)

    try:
        success = False
        # Если ссылка прямая — качаем напрямую
        if any(video_url.lower().endswith(ext) for ext in ['.mp4', '.m4v', '.mov']):
            success = await download_file(video_url, f_in)
        
        # Если не прямая или не скачалось — используем yt-dlp
        if not success:
            ydl_opts = {'format': 'best[height<=720]', 'outtmpl': f_in, 'quiet': True, 'noplaylist': True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])
            success = os.path.exists(f_in)
        
        if not success or os.path.getsize(f_in) < 20000: return None, "error"

        if model:
            print("🎙 Анализ аудио...")
            res = model.transcribe(f_in)
            segments = res.get('segments', [])
            if segments:
                srt_data = ""
                for i, seg in enumerate(segments):
                    s = time.strftime('%H:%M:%S,000', time.gmtime(seg.get('start', 0)))
                    e = time.strftime('%H:%M:%S,000', time.gmtime(seg.get('end', 0)))
                    txt = safe_translate(seg.get('text', ''))
                    if txt: srt_data += f"{i+1}\n{s} --> {e}\n{txt}\n\n"
                
                if srt_data:
                    with open("subs.srt", "w", encoding="utf-8") as fs: fs.write(srt_data)
                    subprocess.run(["ffmpeg", "-y", "-i", f_in, "-vf", "subtitles=subs.srt", "-c:v", "libx264", "-crf", "28", "-preset", "veryfast", "-c:a", "copy", f_out], capture_output=True)
                    if os.path.exists(f_out): return f_out, "subs"
        
        return f_in, "original"
    except Exception as e:
        print(f"⚠️ Ошибка обработки: {e}")
        return None, "error"

# ============================================================
# 🛰 ГЛАВНАЯ ПРОГРАММА
# ============================================================

async def main():
    print("🚀 [ЦУП] v100.0 'Centurion' активирована...")
    if not os.path.exists(DB_FILE): open(DB_FILE, 'w').close()
    db = open(DB_FILE, 'r').read()

    SOURCES = [
        {'n': 'Роскосмос (РФ)', 'id': 'UCOm4M6L_L7xOovvS_I-k__A', 't': 'yt'},
        {'n': 'SpaceX (США)', 'id': 'UC_MhefFv_XW3c66m7ZAnxHA', 't': 'yt'},
        {'n': 'ESA (Европа)', 'u': 'https://www.esa.int/rssfeed/Videos', 't': 'rss'},
        {'n': 'ESO (Наука)', 'u': 'https://www.eso.org/public/videos/feed/', 't': 'rss'},
        {'n': 'NASA TV', 'id': 'UCOpNcN46zbL++h_Z270F9iQ', 't': 'yt'},
        {'n': 'NASA Image API', 't': 'nasa'}
    ]

    random.shuffle(SOURCES)

    for s in SOURCES:
        try:
            print(f"📡 Сектор: {s['n']}...")
            v_list = []

            if s['t'] == 'yt' and YOUTUBE_API_KEY:
                r = requests.get(f"https://www.googleapis.com/youtube/v3/search?key={YOUTUBE_API_KEY}&channelId={s['id']}&part=snippet,id&order=date&maxResults=3&type=video").json()
                for item in r.get('items', []):
                    v_id = item['id']['videoId']
                    if v_id not in db:
                        v_list.append({'url': f"https://www.youtube.com/watch?v={v_id}", 'title': item['snippet']['title'], 'desc': item['snippet']['description'], 'id': v_id})

            elif s['t'] == 'rss':
                res = requests.get(s['u'], timeout=30)
                root = ET.fromstring(res.content)
                for item in root.findall('.//item')[:5]:
                    link = item.find('link').text
                    if link not in db:
                        # Ищем прямое видео в enclosure
                        v_url = link
                        encl = item.find('enclosure')
                        if encl is not None: v_url = encl.get('url')
                        v_list.append({'url': v_url, 'title': item.find('title').text, 'desc': item.find('description').text if item.find('description') is not None else "", 'id': link})

            elif s['t'] == 'nasa' and NASA_API_KEY:
                res = requests.get(f"https://images-api.nasa.gov/search?media_type=video&q=earth&api_key={NASA_API_KEY}").json()
                item = random.choice(res['collection']['items'][:5])
                v_id = item['data'][0]['nasa_id']
                if v_id not in db:
                    assets = requests.get(f"https://images-api.nasa.gov/asset/{v_id}").json()
                    v_url = next(a['href'] for a in assets['collection']['items'] if '~medium.mp4' in a['href'])
                    v_list.append({'url': v_url, 'title': item['data'][0]['title'], 'desc': item['data'][0].get('description', ''), 'id': v_id})

            for v in v_list:
                path, mode = await process_video(v['url'])
                if not path: continue

                t_ru = super_clean(safe_translate(v['title']).upper())
                d_ru = super_clean(safe_translate(v['desc'][:1000]))
                
                caption = (f"⭐ <b>{t_ru}</b>\n\n🛰 <b>ОТПРАВИТЕЛЬ:</b> {s['n']}\n"
                           f"─────────────────────\n🪐 <b>ИНФО:</b>\n{d_ru[:500]}...\n\n"
                           f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>")

                with open(path, 'rb') as f_v:
                    requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo", files={"video": f_v}, data={"chat_id": CHANNEL_NAME, "caption": caption, "parse_mode": "HTML"}, timeout=300)
                
                with open(DB_FILE, 'a') as f: f.write(f"\n{v['id']}")
                print(f"🎉 МИССИЯ ВЫПОЛНЕНА!"); return

        except Exception as e:
            print(f"⚠️ Сбой: {e}")
            continue

if __name__ == '__main__':
    asyncio.run(main())
