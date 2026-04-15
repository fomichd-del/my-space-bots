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

async def process_mission_v122(v_url, title, desc, source_name, is_russian=False):
    f_raw, f_final = "raw_video.mp4", "final_video.mp4"
    for f in [f_raw, f_final, "subs.srt"]:
        if os.path.exists(f): os.remove(f)

    try:
        print(f"📥 Захват объекта: {v_url}")
        
        # Загрузка (лимит 10 минут для очень длинных видео, чтобы не грузить сервер)
        ydl_opts = {
            'format': 'best[height<=480]', 
            'outtmpl': f_raw, 
            'quiet': True, 
            'no_warnings': True,
            'download_ranges': lambda info, dict: [{'start_time': 0, 'end_time': 600}] # Первые 10 мин
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl: ydl.download([v_url])
        if not os.path.exists(f_raw) or os.path.getsize(f_raw) < 100000: return False

        # --- АНАЛИЗ АУДИО И СУБТИТРОВ ---
        mode_label = "● 🛰 КОСМИЧЕСКАЯ ТИШИНА ●"
        has_subs = False
        
        if is_russian:
            mode_label = "● 🔊 ОРИГИНАЛЬНАЯ ОЗВУЧКА ●"
        elif model:
            print("🎙 Whisper: Анализ речи...")
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
        duration = float(prob)
        # Динамический битрейт: втискиваем в 48 МБ
        target_br = int((48 * 8 * 1024 * 1024) / duration) - 128000
        if target_br < 200000: target_br = 200000 # Минимум для 240p
        
        # Настройка субтитров: жирный шрифт с обводкой поверх видео
        vf = "subtitles=subs.srt:force_style='FontSize=18,Outline=2,PrimaryColour=&HFFFFFF,OutlineColour=&H000000'" if has_subs else "scale=trunc(iw/2)*2:trunc(ih/2)*2"
        
        subprocess.run(['ffmpeg', '-y', '-i', f_raw, '-vf', vf, '-c:v', 'libx264', '-b:v', str(target_br), '-preset', 'ultrafast', '-c:a', 'aac', '-b:a', '128k', f_final], capture_output=True)
        
        # --- ПОСТ ---
        clean_title = super_clean(safe_translate(title).upper() if not is_russian else title.upper())
        raw_desc = super_clean(safe_translate(desc) if not is_russian else desc)
        facts = raw_desc.split('. ')
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
# 🛰 СКАНЕР
# ============================================================

async def main():
    print("🎬 [ЦУП] v122.0 'Deep Universe' активирована...")
    if not os.path.exists(DB_FILE): open(DB_FILE, 'w').close()
    if not os.path.exists(SOURCE_LOG): open(SOURCE_LOG, 'w').write("None")
    
    db = open(DB_FILE, 'r').read()
    last_source = open(SOURCE_LOG, 'r').read().strip()

    # НОВЫЕ КАНАЛЫ ВСЕГДА ПЕРВЫМИ
    PRIORITY_SOURCES = [
        {'n': 'KOSMO', 'id': 'UC8M_itU9f_v7Yp7mQo-879A', 't': 'yt', 'ru': True},
        {'n': 'AdMe Космос', 'id': 'UCB_S_1BIn3Y_t9Uf9Msn6Bw', 't': 'yt', 'ru': True},
        {'n': '2081 / 208I', 'id': 'UCMZp-X_lYfN0-n_9n9_vXpw', 't': 'yt', 'ru': True}
    ]
    
    OTHER_SOURCES = [
        {'n': 'Роскосмос', 'id': 'UCOm4M6L_L7xOovvS_I-k__A', 't': 'yt', 'ru': True},
        {'n': 'SpaceX News', 'id': 'UC_MhefFv_XW3c66m7ZAnxHA', 't': 'yt', 'ru': False},
        {'n': 'NASA JPL', 'id': 'UC99RW7X_XzM_C6P6z_pXlAw', 't': 'yt', 'ru': False},
        {'n': 'ESO Observatory', 'u': 'https://www.eso.org/public/videos/feed/', 't': 'rss', 'ru': False}
    ]

    # Сначала проверяем приоритетные, если они не были последними
    AVAILABLE_PRIO = [s for s in PRIORITY_SOURCES if s['n'] != last_source]
    random.shuffle(AVAILABLE_PRIO)
    
    AVAILABLE_OTHER = [s for s in OTHER_SOURCES if s['n'] != last_source]
    random.shuffle(AVAILABLE_OTHER)

    ALL_TO_CHECK = AVAILABLE_PRIO + AVAILABLE_OTHER

    for s in ALL_TO_CHECK:
        try:
            print(f"📡 Поиск в секторе: {s['n']}...")
            if s['t'] == 'yt' and YOUTUBE_API_KEY:
                url = f"https://www.googleapis.com/youtube/v3/search?key={YOUTUBE_API_KEY}&channelId={s['id']}&part=snippet,id&order=date&maxResults=5&type=video"
                items = requests.get(url).json().get('items', [])
                for item in items:
                    v_id = item['id']['videoId']
                    if v_id not in db:
                        if await process_mission_v122(f"https://www.youtube.com/watch?v={v_id}", item['snippet']['title'], item['snippet']['description'], s['n'], s.get('ru', False)):
                            with open(DB_FILE, 'a') as f: f.write(f"\n{v_id}")
                            with open(SOURCE_LOG, 'w') as f: f.write(s['n'])
                            return
            
            elif s['t'] == 'rss':
                res = requests.get(s['u'], timeout=30)
                root = ET.fromstring(res.content)
                for item in root.findall('.//item')[:10]:
                    link = item.find('link').text
                    encl = item.find('enclosure')
                    v_url = encl.get('url') if encl is not None else link
                    if link not in db:
                        if await process_mission_v122(v_url, item.find('title').text, item.find('description').text, s['n'], s.get('ru', False)):
                            with open(DB_FILE, 'a') as f: f.write(f"\n{link}")
                            with open(SOURCE_LOG, 'w') as f: f.write(s['n'])
                            return
        except: continue

if __name__ == '__main__':
    asyncio.run(main())
