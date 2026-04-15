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
from deep_translator import GoogleTranslator

# ============================================================
# ⚙️ КОНФИГУРАЦИЯ ЦУП (v90.0)
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
# 🛠 СИСТЕМЫ СВЯЗИ
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

# ============================================================
# 🎬 ЛАБОРАТОРИЯ МОНТАЖА
# ============================================================

async def process_video(video_url):
    # Исправляем проблему NASA: заменяем пробелы в ссылке на %20
    video_url = video_url.replace(" ", "%20")
    print(f"🎬 [МОНТАЖ] Захват цели: {video_url}")
    
    f_in, f_out = "input.mp4", "output.mp4"
    for f in [f_in, f_out, "subs.srt"]:
        if os.path.exists(f): os.remove(f)

    try:
        ydl_opts = {
            'format': 'best[height<=720][ext=mp4]', 
            'outtmpl': f_in, 
            'quiet': True, 
            'noplaylist': True,
            'nocheckcertificate': True
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
        
        if not os.path.exists(f_in) or os.path.getsize(f_in) < 20000: return None, "error"

        if model:
            print("🎙 Генерирую субтитры...")
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
                    subprocess.run(["ffmpeg", "-y", "-i", f_in, "-vf", "subtitles=subs.srt:force_style='FontSize=18,OutlineColour=&H000000,BorderStyle=1'", "-c:a", "copy", f_out], capture_output=True)
                    if os.path.exists(f_out): return f_out, "subs"
        
        return f_in, "original"
    except Exception as e:
        print(f"⚠️ Сбой монтажа: {e}")
        return None, "error"

# ============================================================
# 🛰 ГЛАВНЫЙ ЦИКЛ (v90.0 - OFFICIAL API MODE)
# ============================================================

async def main():
    print("🚀 [ЦУП] v90.0 'Supernova Prime' активирована...")
    if not os.path.exists(DB_FILE): open(DB_FILE, 'w').close()
    db = open(DB_FILE, 'r').read()

    # Список целей (Официальные каналы)
    YT_CHANNELS = [
        {'n': 'SpaceX', 'id': 'UC_MhefFv_XW3c66m7ZAnxHA'},
        {'n': 'NASA JPL', 'id': 'UC99RW7X_XzM_C6P6z_pXlAw'},
        {'n': 'NASA TV', 'id': 'UCOpNcN46zbL++h_Z270F9iQ'},
        {'n': 'VideoFromSpace', 'id': 'UC6_OitvS-L0m_uVndA-K8lA'}
    ]

    random.shuffle(YT_CHANNELS)

    # 1. ПОИСК ЧЕРЕЗ YOUTUBE API
    if YOUTUBE_API_KEY:
        for ch in YT_CHANNELS:
            try:
                print(f"📡 YouTube API: Сканирую {ch['n']}...")
                url = f"https://www.googleapis.com/youtube/v3/search?key={YOUTUBE_API_KEY}&channelId={ch['id']}&part=snippet,id&order=date&maxResults=3&type=video"
                r = requests.get(url).json()
                
                for item in r.get('items', []):
                    v_id = item['id']['videoId']
                    if v_id in db: continue
                    
                    v_url = f"https://www.youtube.com/watch?v={v_id}"
                    path, mode = await process_video(v_url)
                    if not path: continue

                    caption = (f"⭐ <b>{super_clean(safe_translate(item['snippet']['title'])).upper()}</b>\n\n"
                               f"🛰 <b>МИССИЯ:</b> {ch['n']}\n"
                               f"🎬 <b>ФОРМАТ:</b> {'Субтитры' if mode=='subs' else 'Оригинал'}\n"
                               f"─────────────────────\n"
                               f"🪐 <b>ИНФОРМАЦИЯ:</b>\n{super_clean(safe_translate(item['snippet']['description'][:400]))}...\n\n"
                               f"🔭 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>")

                    with open(path, 'rb') as f_v:
                        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo", files={"video": f_v}, data={"chat_id": CHANNEL_NAME, "caption": caption, "parse_mode": "HTML"})
                    
                    with open(DB_FILE, 'a') as f: f.write(f"\n{v_id}")
                    print(f"🎉 YouTube успех!"); return
            except: continue

    # 2. ПОИСК ЧЕРЕЗ NASA API (Если YouTube молчит)
    try:
        print("📡 NASA API: Поиск свежих архивов...")
        n_url = f"https://images-api.nasa.gov/search?media_type=video&q=space&api_key={NASA_API_KEY}"
        res = requests.get(n_url).json()
        item = random.choice(res['collection']['items'][:10])
        v_id = item['data'][0]['nasa_id']
        
        if v_id not in db:
            assets = requests.get(f"https://images-api.nasa.gov/asset/{v_id}").json()
            # Берем самую надежную ссылку (medium)
            video_url = next(a['href'] for a in assets['collection']['items'] if '~medium.mp4' in a['href'])
            
            path, mode = await process_video(video_url)
            if path:
                caption = (f"⭐ <b>{super_clean(safe_translate(item['data'][0]['title'])).upper()}</b>\n\n"
                           f"🛰 <b>ИСТОЧНИК:</b> NASA Archive\n"
                           f"─────────────────────\n"
                           f"🪐 <b>ИНФОРМАЦИЯ:</b>\n{super_clean(safe_translate(item['data'][0].get('description', '')[:500]))}...\n\n"
                           f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>")

                with open(path, 'rb') as f_v:
                    requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo", files={"video": f_v}, data={"chat_id": CHANNEL_NAME, "caption": caption, "parse_mode": "HTML"})
                
                with open(DB_FILE, 'a') as f: f.write(f"\n{v_id}")
                print("🎉 NASA успех!"); return
    except: pass

if __name__ == '__main__':
    asyncio.run(main())
