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
# ⚙️ КОНФИГУРАЦИЯ v122.0
# ============================================================
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
NASA_API_KEY   = os.getenv('NASA_API_KEY')
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
CHANNEL_NAME   = '@vladislav_space'
DB_FILE        = "last_video_date.txt"
SOURCE_LOG     = "last_source.txt"

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
        if match: return float(match.group(1)) > -60.0
        return False
    except: return False

# ============================================================
# 🎬 ПРОЦЕССОР v122.0
# ============================================================

async def process_mission_v122(v_url, title, desc, source_name):
    f_raw, f_final = "raw_video.mp4", "final_video.mp4"
    for f in [f_raw, f_final, "subs.srt"]:
        if os.path.exists(f): os.remove(f)

    try:
        print(f"📥 Захват объекта: {v_url}")
        
        # 1. Загрузка (Ограничиваем 10 минутами для очень длинных видео)
        ydl_opts = {
            'format': 'best[height<=480]', # Сразу берем 480p для экономии
            'outtmpl': f_raw, 
            'quiet': True,
            'download_ranges': lambda info, dict: [{'start_time': 0, 'end_time': 600}], # Берем первые 10 мин
            'force_keyframes_at_cuts': True
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl: ydl.download([v_url])
        
        if not os.path.exists(f_raw) or os.path.getsize(f_raw) < 100000: return False

        # --- АНАЛИЗ АУДИО И ЯЗЫКА ---
        mode_label = "● 🛰 КОСМИЧЕСКАЯ ТИШИНА ●" 
        has_subs = False
        if model:
            print("🎙 Whisper: Анализ речи...")
            # Определяем язык
            audio_res = model.transcribe(f_raw)
            detected_lang = audio_res.get('language', 'en')
            segments = audio_res.get('segments', [])
            
            # Если язык НЕ русский, делаем субтитры
            if detected_lang != 'ru' and segments:
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
            elif detected_lang == 'ru':
                mode_label = "● 🎙 РУССКАЯ ОЗВУЧКА ●"
            elif check_real_audio(f_raw):
                mode_label = "● 🎵 АТМОСФЕРНЫЙ ЗВУК ●"

        # --- МОНТАЖ (СЖАТИЕ) ---
        prob = subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', f_raw])
        duration = float(prob)
        # Рассчитываем битрейт, чтобы влезть в 48 МБ
        target_br = int((47 * 8 * 1024 * 1024) / duration) - 128000
        if target_br < 100000: target_br = 100000 # Минимум 100kbps

        vf = "subtitles=subs.srt:force_style='FontSize=16,Outline=1'" if has_subs else "scale=trunc(iw/2)*2:trunc(ih/2)*2"
        
        print(f"🛠 Сжатие до {target_br//1000}kbps...")
        subprocess.run(['ffmpeg', '-y', '-i', f_raw, '-vf', vf, '-c:v', 'libx264', '-b:v', str(target_br), '-preset', 'ultrafast', '-c:a', 'aac', '-b:a', '128k', f_final], capture_output=True)
        
        # --- ПОСТ ---
        clean_title = super_clean(safe_translate(title).upper())
        clean_desc = super_clean(safe_translate(desc))
        facts = clean_desc.split('. ')
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
                          files={"video": v}, data={"chat_id": CHANNEL_NAME, "caption": caption, "parse_mode": "HTML"}, timeout=450)
        return True
    except: return False

# ============================================================
# 🛰 СКАНЕР (ОБЪЕДИНЕННЫЙ ФЛОТ)
# ============================================================

async def main():
    print("🎬 [ЦУП] v122.0 'Deep Universe' активирована...")
    if not os.path.exists(DB_FILE): open(DB_FILE, 'w').close()
    if not os.path.exists(SOURCE_LOG): open(SOURCE_LOG, 'w').write("None")
    
    db = open(DB_FILE, 'r').read()
    last_source = open(SOURCE_LOG, 'r').read().strip()

    SOURCES = [
        {'n': 'Роскосмос', 'id': 'UCOm4M6L_L7xOovvS_I-k__A', 't': 'yt'},
        {'n': 'SpaceX News', 'id': 'UC_MhefFv_XW3c66m7ZAnxHA', 't': 'yt'},
        {'n': 'NASA JPL', 'id': 'UC99RW7X_XzM_C6P6z_pXlAw', 't': 'yt'},
        {'n': 'KOSMO', 'id': 'UC8M_itU9f_v7Yp7mQo-879A', 't': 'yt'},
        {'n': 'AdMe Космос', 'id': 'UCB_S_1BIn3Y_t9Uf9Msn6Bw', 't': 'yt'},
        {'n': '2081 / 208I', 'id': 'UCMZp-X_lYfN0-n_9n9_vXpw', 't': 'yt'},
        {'n': 'Universe Today', 'u': 'https://www.universetoday.com/feed/', 't': 'rss'},
        {'n': 'ESO Observatory', 'u': 'https://www.eso.org/public/videos/feed/', 't': 'rss'}
    ]

    AVAILABLE = [s for s in SOURCES if s['n'] != last_source]
    random.shuffle(AVAILABLE)

    for s in AVAILABLE:
        try:
            print(f"📡 Сектор: {s['n']}...")
            if s['t'] == 'yt' and YOUTUBE_API_KEY:
                url = f"https://www.googleapis.com/youtube/v3/search?key={YOUTUBE_API_KEY}&channelId={s['id']}&part=snippet,id&order=date&maxResults=10&type=video"
                items = requests.get(url).json().get('items', [])
                random.shuffle(items)
                for item in items:
                    v_id = item['id']['videoId']
                    if v_id not in db:
                        if await process_mission_v122(f"https://www.youtube.com/watch?v={v_id}", item['snippet']['title'], item['snippet']['description'], s['n']):
                            with open(DB_FILE, 'a') as f: f.write(f"\n{v_id}")
                            with open(SOURCE_LOG, 'w') as f: f.write(s['n'])
                            return
            
            elif s['t'] == 'rss':
                res = requests.get(s['u'], timeout=30)
                root = ET.fromstring(res.content)
                items = root.findall('.//item')
                random.shuffle(items)
                for item in items[:15]:
                    link = item.find('link').text
                    encl = item.find('enclosure')
                    v_url = encl.get('url') if encl is not None else link
                    if link not in db:
                        if await process_mission_v122(v_url, item.find('title').text, item.find('description').text, s['n']):
                            with open(DB_FILE, 'a') as f: f.write(f"\n{link}")
                            with open(SOURCE_LOG, 'w') as f: f.write(s['n'])
                            return
        except: continue

if __name__ == '__main__':
    asyncio.run(main())
