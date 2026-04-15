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
# ⚙️ КОНФИГУРАЦИЯ v121.0
# ============================================================
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
NASA_API_KEY   = os.getenv('NASA_API_KEY')
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
CHANNEL_NAME   = '@vladislav_space'
DB_FILE        = "last_video_date.txt"
SOURCE_LOG     = "last_source.txt" # Журнал последнего источника

translator = GoogleTranslator(source='auto', target='ru')
try:
    model = whisper.load_model("base")
except:
    model = None

# ============================================================
# 🛠 ТЕХНИЧЕСКИЙ ОТСЕК
# ============================================================

def safe_translate(text):
    if not text or len(str(text)) < 2: return ""
    try: return translator.translate(text)
    except: return text

def super_clean(text):
    if not text: return ""
    text = re.sub(r'http\S+', '', str(text)) 
    text = re.sub(r'<[^>]+>', '', text)      
    return html.escape(html.unescape(text)).strip()

def check_real_audio(file_path):
    try:
        cmd = ['ffmpeg', '-i', file_path, '-af', 'volumedetect', '-vn', '-sn', '-dn', '-f', 'null', '/dev/null']
        result = subprocess.run(cmd, capture_output=True, text=True)
        match = re.search(r"mean_volume: ([\-\d\.]+) dB", result.stderr)
        if match:
            return float(match.group(1)) > -60.0
        return False
    except: return False

# ============================================================
# 🎬 ПРОЦЕССОР v121.0
# ============================================================

async def process_mission_v121(v_url, title, desc, source_name):
    f_raw, f_final = "raw_video.mp4", "final_video.mp4"
    for f in [f_raw, f_final, "subs.srt"]:
        if os.path.exists(f): os.remove(f)

    try:
        print(f"📥 Захват объекта: {v_url}")
        
        # Загрузка
        is_direct = any(v_url.lower().endswith(ext) for ext in ['.mp4', '.m4v', '.mov'])
        success = False
        if is_direct:
            r = requests.get(v_url, stream=True, timeout=120)
            if r.status_code == 200:
                with open(f_raw, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=1024*1024): f.write(chunk)
                success = True
        
        if not success:
            ydl_opts = {'format': 'best[height<=720]', 'outtmpl': f_raw, 'quiet': True, 'no_warnings': True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl: ydl.download([v_url])
            success = os.path.exists(f_raw)

        if not success or os.path.getsize(f_raw) < 100000: return False

        # --- АНАЛИЗ АУДИО ---
        mode_label = "● 🛰 КОСМИЧЕСКАЯ ТИШИНА ●" 
        has_subs = False
        if model:
            res = model.transcribe(f_raw)
            segments = res.get('segments', [])
            srt_content = ""
            counter = 1
            for seg in segments:
                txt = seg.get('text', '').strip()
                if len(txt) > 2:
                    txt_ru = safe_translate(txt)
                    if txt_ru:
                        start = time.strftime('%H:%M:%S,000', time.gmtime(seg['start']))
                        end = time.strftime('%H:%M:%S,000', time.gmtime(seg['end']))
                        srt_content += f"{counter}\n{start} --> {end}\n{txt_ru}\n\n"
                        counter += 1
            
            if srt_content:
                with open("subs.srt", "w", encoding="utf-8") as fs: fs.write(srt_content)
                mode_label = "● 📝 СУБТИТРЫ ПОДГОТОВЛЕНЫ ●"
                has_subs = True
            elif check_real_audio(f_raw):
                mode_label = "● 🎵 АТМОСФЕРНЫЙ ЗВУК ●"

        # --- МОНТАЖ ---
        prob = subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', f_raw])
        target_br = int((45 * 8 * 1024 * 1024) / float(prob)) - 128000
        vf = "subtitles=subs.srt:force_style='FontSize=16,Outline=1'" if has_subs else "scale=trunc(iw/2)*2:trunc(ih/2)*2"
        subprocess.run(['ffmpeg', '-y', '-i', f_raw, '-vf', vf, '-c:v', 'libx264', '-b:v', str(target_br), '-preset', 'ultrafast', '-c:a', 'aac', '-b:a', '128k', f_final], capture_output=True)
        
        # --- ОТПРАВКА ---
        clean_title = super_clean(safe_translate(title).upper())
        facts = super_clean(safe_translate(desc)).split('. ')
        fact_block = "🔹 " + facts[0] + ('. ' + facts[1] if len(facts) > 1 else '...')

        caption = (
            f"<b>{mode_label}</b>\n\n🚀 <b>{clean_title}</b>\n\n"
            f"🛰 <b>ИСТОЧНИК:</b> {source_name}\n"
            f"─────────────────────\n"
            f"🪐 <b>НАУЧНЫЕ ФАКТЫ:</b>\n\n{fact_block}\n\n"
            f"✨ <i>Космос — это доказанная реальность.</i>\n"
            f"🔭 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
        )

        with open(f_final if os.path.exists(f_final) else f_raw, 'rb') as v:
            requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo", 
                          files={"video": v}, data={"chat_id": CHANNEL_NAME, "caption": caption, "parse_mode": "HTML"}, timeout=400)
        return True
    except: return False

# ============================================================
# 🛰 СКАНЕР С ПРИНУДИТЕЛЬНОЙ РОТАЦИЕЙ
# ============================================================

async def main():
    print("🎬 [ЦУП] v121.0 'Deep Rotation' активирована...")
    if not os.path.exists(DB_FILE): open(DB_FILE, 'w').close()
    if not os.path.exists(SOURCE_LOG): open(SOURCE_LOG, 'w').write("None")
    
    db = open(DB_FILE, 'r').read()
    last_source = open(SOURCE_LOG, 'r').read().strip()

    SOURCES = [
        {'n': 'Роскосмос', 'id': 'UCOm4M6L_L7xOovvS_I-k__A', 't': 'yt'},
        {'n': 'SpaceX News', 'id': 'UC_MhefFv_XW3c66m7ZAnxHA', 't': 'yt'},
        {'n': 'NASA JPL', 'id': 'UC99RW7X_XzM_C6P6z_pXlAw', 't': 'yt'},
        {'n': 'Universe Today', 'u': 'https://www.universetoday.com/feed/', 't': 'rss'},
        {'n': 'ESO Observatory', 'u': 'https://www.eso.org/public/videos/feed/', 't': 'rss'}
    ]

    # Исключаем последний использованный источник
    AVAILABLE = [s for s in SOURCES if s['n'] != last_source]
    random.shuffle(AVAILABLE)
    
    # Если все источники по кругу закончились (мало ли), берем любой
    if not AVAILABLE: AVAILABLE = SOURCES

    for s in AVAILABLE:
        try:
            print(f"📡 Поиск в секторе: {s['n']}...")
            if s['t'] == 'yt' and YOUTUBE_API_KEY:
                url = f"https://www.googleapis.com/youtube/v3/search?key={YOUTUBE_API_KEY}&channelId={s['id']}&part=snippet,id&order=date&maxResults=10&type=video"
                items = requests.get(url).json().get('items', [])
                for item in items:
                    v_id = item['id']['videoId']
                    if v_id not in db:
                        if await process_mission_v121(f"https://www.youtube.com/watch?v={v_id}", item['snippet']['title'], item['snippet']['description'], s['n']):
                            with open(DB_FILE, 'a') as f: f.write(f"\n{v_id}")
                            with open(SOURCE_LOG, 'w') as f: f.write(s['n']) # Записываем новый источник
                            return
            
            elif s['t'] == 'rss':
                res = requests.get(s['u'], timeout=30)
                root = ET.fromstring(res.content)
                for item in root.findall('.//item')[:15]:
                    link = item.find('link').text
                    encl = item.find('enclosure')
                    v_url = encl.get('url') if encl is not None else link
                    if not any(v_url.lower().endswith(ext) for ext in ['.mp4', '.m4v', '.mov']) and 'youtube' not in v_url: continue
                    if link not in db:
                        if await process_mission_v121(v_url, item.find('title').text, item.find('description').text, s['n']):
                            with open(DB_FILE, 'a') as f: f.write(f"\n{link}")
                            with open(SOURCE_LOG, 'w') as f: f.write(s['n']) # Записываем новый источник
                            return
        except: continue

if __name__ == '__main__':
    asyncio.run(main())
