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
# ⚙️ КОНФИГУРАЦИЯ v117.0
# ============================================================
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
NASA_API_KEY   = os.getenv('NASA_API_KEY')
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
CHANNEL_NAME   = '@vladislav_space'
DB_FILE        = "last_video_date.txt"

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

def compress_video_safe(input_path, output_path, target_size_mb=45):
    try:
        prob = subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', input_path])
        duration = float(prob)
        target_total_bitrate = int((target_size_mb * 8 * 1024 * 1024) / duration)
        video_bitrate = target_total_bitrate - 128000
        subprocess.run(['ffmpeg', '-y', '-i', input_path, '-c:v', 'libx264', '-b:v', str(video_bitrate), '-preset', 'ultrafast', '-c:a', 'aac', '-b:a', '128k', output_path], capture_output=True)
        return True
    except: return False

# ============================================================
# 🎬 ПРОЦЕССОР (v117.0 - ГИБКИЙ МОНТАЖ)
# ============================================================

async def process_mission(v_url, title, desc, source_name):
    f_raw, f_final = "raw_video.mp4", "final_video.mp4"
    for f in [f_raw, f_final, "subs.srt"]:
        if os.path.exists(f): os.remove(f)

    try:
        print(f"📥 Загрузка объекта: {v_url}")
        if any(v_url.lower().endswith(ext) for ext in ['.mp4', '.m4v', '.mov']):
            r = requests.get(v_url, stream=True, timeout=120)
            with open(f_raw, 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024*1024): f.write(chunk)
        else:
            ydl_opts = {'format': 'best[height<=720]', 'outtmpl': f_raw, 'quiet': True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl: ydl.download([v_url])
        
        if not os.path.exists(f_raw) or os.path.getsize(f_raw) < 50000: return False

        mode_text = "🔊 Оригинал"
        has_subs = False
        if model:
            print("🎙 Whisper: Глубокое сканирование...")
            res = model.transcribe(f_raw)
            segments = res.get('segments', [])
            if segments:
                srt_content = ""
                for i, seg in enumerate(segments):
                    txt = seg.get('text', '').strip()
                    if len(txt) > 1:
                        txt_ru = safe_translate(txt)
                        if txt_ru:
                            s = time.strftime('%H:%M:%S,000', time.gmtime(seg['start']))
                            e = time.strftime('%H:%M:%S,000', time.gmtime(seg['end']))
                            srt_content += f"{i+1}\n{s} --> {e}\n{txt_ru}\n\n"
                if srt_content:
                    with open("subs.srt", "w", encoding="utf-8") as fs: fs.write(srt_content)
                    mode_text = "🎥 Русские субтитры"; has_subs = True

        raw_size = os.path.getsize(f_raw) / (1024*1024)
        if has_subs or raw_size > 48:
            print(f"🛠 Монтаж (Сжатие: {raw_size > 48})")
            if has_subs:
                bit_cmd = []
                if raw_size > 48:
                    prob = subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', f_raw])
                    target_br = int((45 * 8 * 1024 * 1024) / float(prob)) - 128000
                    bit_cmd = ['-b:v', str(target_br)]
                subprocess.run(['ffmpeg', '-y', '-i', f_raw, '-vf', "subtitles=subs.srt", '-c:v', 'libx264'] + bit_cmd + ['-preset', 'ultrafast', '-c:a', 'aac', '-b:a', '128k', f_final], capture_output=True)
            else:
                compress_video_safe(f_raw, f_final)
            path_to_send = f_final if os.path.exists(f_final) else f_raw
        else:
            path_to_send = f_raw

        # --- КРАСИВОЕ ОФОРМЛЕНИЕ ---
        t_ru = super_clean(safe_translate(title).upper())
        d_ru = super_clean(safe_translate(desc))
        facts = d_ru.split('. ')
        fact_text = "🔹 " + facts[0] + ('. ' + facts[1] if len(facts) > 1 else '') + "."

        caption = (
            f"🚀 <b>{t_ru}</b>\n\n"
            f"🛰 <b>ИСТОЧНИК:</b> {source_name}\n"
            f"📡 <b>СТАТУС:</b> {mode_text}\n"
            f"─────────────────────\n"
            f"🪐 <b>ГЛАВНЫЕ ФАКТЫ:</b>\n\n"
            f"{fact_text}\n\n"
            f"✨ <i>Космос — это бесконечное приключение!</i>\n"
            f"🔭 <a href='https://t.me/vladislav_space'>Подписаться на Дневник</a>"
        )

        with open(path_to_send, 'rb') as v:
            requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo", files={"video": v}, data={"chat_id": CHANNEL_NAME, "caption": caption, "parse_mode": "HTML"}, timeout=300)
        return True
    except: return False

# ============================================================
# 🛰 ГЛОБАЛЬНАЯ ОЧЕРЕДЬ (v117.0)
# ============================================================

async def main():
    print("🎬 [ЦУП] v117.0 'Galaxy Mix' активирована...")
    if not os.path.exists(DB_FILE): open(DB_FILE, 'w').close()
    db = open(DB_FILE, 'r').read()

    SOURCES = [
        {'n': 'Роскосмос (РФ)', 'id': 'UCOm4M6L_L7xOovvS_I-k__A', 't': 'yt'},
        {'n': 'SpaceX (Elon Musk)', 'id': 'UC_MhefFv_XW3c66m7ZAnxHA', 't': 'yt'},
        {'n': 'Phys.org (Наука)', 'u': 'https://phys.org/rss-feed/space-news/', 't': 'rss'},
        {'n': 'NASA JPL', 'id': 'UC99RW7X_XzM_C6P6z_pXlAw', 't': 'yt'},
        {'n': 'ESO (Чили)', 'u': 'https://www.eso.org/public/videos/feed/', 't': 'rss'}
    ]

    all_found_videos = []

    # 1. Сканируем ВСЕ источники и собираем в одну кучу
    for s in SOURCES:
        try:
            print(f"📡 Сбор данных: {s['n']}...")
            if s['t'] == 'yt' and YOUTUBE_API_KEY:
                url = f"https://www.googleapis.com/youtube/v3/search?key={YOUTUBE_API_KEY}&channelId={s['id']}&part=snippet,id&order=date&publishedAfter=2020-01-01T00:00:00Z&maxResults=5&type=video"
                items = requests.get(url).json().get('items', [])
                for item in items:
                    v_id = item['id']['videoId']
                    if v_id not in db:
                        all_found_videos.append({'url': f"https://www.youtube.com/watch?v={v_id}", 'title': item['snippet']['title'], 'desc': item['snippet']['description'], 'src': s['n'], 'id': v_id})
            
            elif s['t'] == 'rss':
                root = ET.fromstring(requests.get(s['u']).content)
                for item in root.findall('.//item')[:10]:
                    link = item.find('link').text
                    if link not in db:
                        encl = item.find('enclosure')
                        v_url = encl.get('url') if encl is not None else link
                        all_found_videos.append({'url': v_url, 'title': item.find('title').text, 'desc': item.find('description').text or "", 'src': s['n'], 'id': link})
        except: continue

    # 2. Перемешиваем ВЕСЬ список
    random.shuffle(all_found_videos)
    print(f"🎲 Глобальная очередь сформирована. Объектов: {len(all_found_videos)}")

    # 3. Берем первое подходящее видео из перемешанного списка
    for v in all_found_videos:
        if await process_mission(v['url'], v['title'], v['desc'], v['src']):
            with open(DB_FILE, 'a') as f: f.write(f"\n{v['id']}")
            print(f"🎉 Миссия выполнена: {v['src']}")
            return

if __name__ == '__main__':
    asyncio.run(main())
