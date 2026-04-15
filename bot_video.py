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
# ⚙️ КОНФИГУРАЦИЯ v116.0
# ============================================================
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
NASA_API_KEY   = os.getenv('NASA_API_KEY')
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
CHANNEL_NAME   = '@vladislav_space'
DB_FILE        = "last_video_date.txt"

translator = GoogleTranslator(source='auto', target='ru')
try:
    # Используем base модель для чуть лучшего распознавания при тех же ресурсах
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

def compress_video_safe(input_path, output_path, target_size_mb=45):
    try:
        prob = subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', input_path])
        duration = float(prob)
        target_total_bitrate = int((target_size_mb * 8 * 1024 * 1024) / duration)
        video_bitrate = target_total_bitrate - 128000
        
        # Используем libx264 с ultrafast для скорости в GitHub Actions
        subprocess.run([
            'ffmpeg', '-y', '-i', input_path,
            '-c:v', 'libx264', '-b:v', str(video_bitrate),
            '-preset', 'ultrafast', '-c:a', 'aac', '-b:a', '128k', output_path
        ], capture_output=True)
        return True
    except: return False

# ============================================================
# 🎬 ПРОЦЕССОР v116.0
# ============================================================

async def process_mission_v116(v_url, title, desc, source_name):
    f_raw, f_final = "raw_video.mp4", "final_video.mp4"
    for f in [f_raw, f_final, "subs.srt"]:
        if os.path.exists(f): os.remove(f)

    try:
        print(f"📥 Захват объекта: {v_url}")
        if any(v_url.lower().endswith(ext) for ext in ['.mp4', '.m4v', '.mov']):
            r = requests.get(v_url, stream=True, timeout=120)
            with open(f_raw, 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024*1024): f.write(chunk)
        else:
            ydl_opts = {'format': 'best[height<=720]', 'outtmpl': f_raw, 'quiet': True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl: ydl.download([v_url])
        
        if not os.path.exists(f_raw) or os.path.getsize(f_raw) < 50000: return False

        # --- РАБОТА С СУБТИТРАМИ ---
        mode_text = "🔊 Оригинальный звук"
        has_subs = False
        if model:
            print("🎙 Whisper: Анализ аудиодорожки...")
            res = model.transcribe(f_raw, language='en') # Явно указываем английский для ESO/NASA
            segments = res.get('segments', [])
            
            if segments:
                srt_content = ""
                counter = 1
                for seg in segments:
                    txt = seg.get('text', '').strip()
                    if len(txt) > 1:
                        start = time.strftime('%H:%M:%S,000', time.gmtime(seg['start']))
                        end = time.strftime('%H:%M:%S,000', time.gmtime(seg['end']))
                        txt_ru = safe_translate(txt)
                        if txt_ru:
                            srt_content += f"{counter}\n{start} --> {end}\n{txt_ru}\n\n"
                            counter += 1
                
                if srt_content:
                    with open("subs.srt", "w", encoding="utf-8") as fs:
                        fs.write(srt_content)
                    print(f"📝 Субтитры созданы (фрагментов: {counter-1})")
                    mode_text = "🎥 Русские субтитры"
                    has_subs = True
                else:
                    print("🔇 Речь не обнаружена (только музыка/шум)")
                    mode_text = "🎵 Атмосферное видео (без слов)"

        # --- МОНТАЖ ---
        raw_size = os.path.getsize(f_raw) / (1024*1024)
        if has_subs or raw_size > 48:
            print(f"🛠 Запуск FFmpeg (Сжатие: {raw_size > 48}, Субтитры: {has_subs})")
            # Если есть субтитры - вшиваем. Если файл большой - сжимаем.
            if has_subs:
                # Вшиваем субтитры + сжимаем если надо
                bitrate_cmd = []
                if raw_size > 48:
                    prob = subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', f_raw])
                    target_br = int((45 * 8 * 1024 * 1024) / float(prob)) - 128000
                    bitrate_cmd = ['-b:v', str(target_br)]
                
                subprocess.run([
                    'ffmpeg', '-y', '-i', f_raw, 
                    '-vf', "subtitles=subs.srt:force_style='FontSize=16,Outline=1'", 
                    '-c:v', 'libx264'] + bitrate_cmd + ['-preset', 'ultrafast', '-c:a', 'aac', '-b:a', '128k', f_final], 
                    capture_output=True)
            else:
                compress_video_safe(f_raw, f_final)
            
            path_to_send = f_final if os.path.exists(f_final) else f_raw
        else:
            path_to_send = f_raw

        # --- ОФОРМЛЕНИЕ ---
        clean_title = super_clean(safe_translate(title).upper())
        clean_desc = super_clean(safe_translate(desc))
        
        if len(clean_desc) < 30:
            fact_block = f"🔹 На видео запечатлено важное событие: {clean_title.lower()}."
        else:
            facts = clean_desc.split('. ')
            fact_block = "🔹 " + facts[0] + ('. ' + facts[1] if len(facts) > 1 else '') + "."

        caption = (
            f"🚀 <b>{clean_title}</b>\n\n"
            f"🛰 <b>ИСТОЧНИК:</b> {source_name}\n"
            f"📡 <b>СТАТУС:</b> {mode_text}\n"
            f"─────────────────────\n"
            f"🪐 <b>ГЛАВНЫЕ ФАКТЫ:</b>\n\n"
            f"{fact_block}\n\n"
            f"🔭 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
        )

        with open(path_to_send, 'rb') as v:
            requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo", 
                          files={"video": v}, data={"chat_id": CHANNEL_NAME, "caption": caption, "parse_mode": "HTML"}, timeout=300)
        return True
    except Exception as e:
        print(f"⚠️ Ошибка: {e}")
        return False

# ============================================================
# 🛰 СКАНЕР (ОТ 2020 ГОДА)
# ============================================================

async def main():
    print("🎬 [ЦУП] v116.0 'Subtitles Force' активирована...")
    if not os.path.exists(DB_FILE): open(DB_FILE, 'w').close()
    db = open(DB_FILE, 'r').read()

    SOURCES = [
        {'n': 'Роскосмос (РФ)', 'id': 'UCOm4M6L_L7xOovvS_I-k__A', 't': 'yt'},
        {'n': 'SpaceX (Elon Musk)', 'id': 'UC_MhefFv_XW3c66m7ZAnxHA', 't': 'yt'},
        {'n': 'Phys.org (Наука)', 'u': 'https://phys.org/rss-feed/space-news/', 't': 'rss'},
        {'n': 'Universe Today', 'u': 'https://www.universetoday.com/feed/', 't': 'rss'},
        {'n': 'NASA JPL', 'id': 'UC99RW7X_XzM_C6P6z_pXlAw', 't': 'yt'},
        {'n': 'ESO (Чили)', 'u': 'https://www.eso.org/public/videos/feed/', 't': 'rss'}
    ]

    random.shuffle(SOURCES)
    date_limit = "2020-01-01T00:00:00Z"

    for s in SOURCES:
        try:
            print(f"📡 Сектор: {s['n']}...")
            if s['t'] == 'yt' and YOUTUBE_API_KEY:
                url = f"https://www.googleapis.com/youtube/v3/search?key={YOUTUBE_API_KEY}&channelId={s['id']}&part=snippet,id&order=date&publishedAfter={date_limit}&maxResults=10&type=video"
                items = requests.get(url).json().get('items', [])
                for item in items:
                    v_id = item['id']['videoId']
                    if v_id not in db:
                        if await process_mission_v116(f"https://www.youtube.com/watch?v={v_id}", item['snippet']['title'], item['snippet']['description'], s['n']):
                            with open(DB_FILE, 'a') as f: f.write(f"\n{v_id}")
                            return
            
            elif s['t'] == 'rss':
                res = requests.get(s['u'], timeout=20)
                root = ET.fromstring(res.content)
                for item in root.findall('.//item')[:15]:
                    link = item.find('link').text
                    encl = item.find('enclosure')
                    v_url = encl.get('url') if encl is not None else link
                    if link not in db:
                        if await process_mission_v116(v_url, item.find('title').text, item.find('description').text, s['n']):
                            with open(DB_FILE, 'a') as f: f.write(f"\n{link}")
                            return
        except: continue

if __name__ == '__main__':
    asyncio.run(main())
