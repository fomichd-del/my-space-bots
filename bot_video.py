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
# ⚙️ КОНФИГУРАЦИЯ v110.0
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
# 🛠 ВИДЕО-ИНЖЕНЕРИЯ (СЖАТИЕ ДО 50 МБ)
# ============================================================

def compress_video(input_path, output_path, target_size_mb=48):
    """Сжимает любое видео до заданного размера (48 МБ для запаса)"""
    try:
        # Узнаем длительность видео
        prob = subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', input_path])
        duration = float(prob)
        # Вычисляем нужный битрейт (размер в битах / длительность)
        target_bitrate = int((target_size_mb * 8 * 1024 * 1024) / duration) - 128000 # минус аудио
        
        print(f"📉 Сжатие: Целевой битрейт {target_bitrate // 1000} kbps")
        
        subprocess.run([
            'ffmpeg', '-y', '-i', input_path,
            '-c:v', 'libx264', '-b:v', str(target_bitrate),
            '-preset', 'veryfast', '-pass', '1', '-an', '-f', 'mp4', '/dev/null'
        ], capture_output=True)
        
        subprocess.run([
            'ffmpeg', '-y', '-i', input_path,
            '-c:v', 'libx264', '-b:v', str(target_bitrate),
            '-preset', 'veryfast', '-pass', '2', '-c:a', 'aac', '-b:a', '128k', output_path
        ], capture_output=True)
        return True
    except:
        return False

# ============================================================
# 🛰 УНИВЕРСАЛЬНЫЙ ПОИСК (С 2025 ГОДА)
# ============================================================

async def process_mission(video_url, title, desc, source_name):
    f_raw, f_final = "raw_video.mp4", "final_video.mp4"
    for f in [f_raw, f_final, "subs.srt", "ffmpeg2pass-0.log"]:
        if os.path.exists(f): os.remove(f)

    try:
        # 1. Загрузка
        ydl_opts = {'format': 'best', 'outtmpl': f_raw, 'quiet': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
        
        # 2. Субтитры
        mode_text = "🔊 Оригинал"
        if model:
            res = model.transcribe(f_raw)
            segments = res.get('segments', [])
            if segments:
                srt = ""
                for i, seg in enumerate(segments):
                    s = time.strftime('%H:%M:%S,000', time.gmtime(seg['start']))
                    e = time.strftime('%H:%M:%S,000', time.gmtime(seg['end']))
                    txt = translator.translate(seg['text'])
                    srt += f"{i+1}\n{s} --> {e}\n{txt}\n\n"
                with open("subs.srt", "w") as f: f.write(srt)
                mode_text = "🎥 С переводом"

        # 3. Сжатие и сборка
        # Если файл больше 49 МБ или нам нужны субтитры - прогоняем через FFmpeg
        current_size = os.path.getsize(f_raw) / (1024*1024)
        vf_params = "subtitles=subs.srt" if os.path.exists("subs.srt") else "scale=trunc(iw/2)*2:trunc(ih/2)*2"
        
        if current_size > 49 or os.path.exists("subs.srt"):
            compress_video(f_raw, f_final)
            path_to_send = f_final
        else:
            path_to_send = f_raw

        # 4. Оформление поста
        t_ru = translator.translate(title).upper()
        d_ru = translator.translate(desc[:800])
        
        caption = (
            f"🚀 <b>{t_ru}</b>\n\n"
            f"🛰 <b>МИССИЯ:</b> {source_name}\n"
            f"📡 <b>СТАТУС:</b> {mode_text}\n"
            f"─────────────────────\n"
            f"📖 <b>ГЛАВНЫЕ ФАКТЫ:</b>\n\n"
            f"{d_ru[:500]}...\n\n"
            f"✨ <i>Космические технологии будущего — сегодня.</i>\n"
            f"🔭 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
        )

        with open(path_to_send, 'rb') as v:
            requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo", 
                          files={"video": v}, data={"chat_id": CHANNEL_NAME, "caption": caption, "parse_mode": "HTML"})
        return True
    except:
        return False

async def main():
    print("🎬 [ЦУП] v110.0 активирована. Поиск с 2025 года...")
    if not os.path.exists(DB_FILE): open(DB_FILE, 'w').close()
    db = open(DB_FILE, 'r').read()

    SOURCES = [
        {'n': 'Роскосмос (РФ)', 'id': 'UCOm4M6L_L7xOovvS_I-k__A', 't': 'yt'},
        {'n': 'SpaceX (Elon Musk)', 'id': 'UC_MhefFv_XW3c66m7ZAnxHA', 't': 'yt'},
        {'n': 'NASA JPL', 'id': 'UC99RW7X_XzM_C6P6z_pXlAw', 't': 'yt'},
        {'n': 'ESA (Европа)', 'u': 'https://www.esa.int/rssfeed/Videos', 't': 'rss'},
        {'n': 'ESO (Чили)', 'u': 'https://www.eso.org/public/videos/feed/', 't': 'rss'}
    ]

    random.shuffle(SOURCES)
    # Дата отсечки: 2025-01-01
    date_after = "2025-01-01T00:00:00Z"

    for s in SOURCES:
        try:
            if s['t'] == 'yt' and YOUTUBE_API_KEY:
                url = f"https://www.googleapis.com/youtube/v3/search?key={YOUTUBE_API_KEY}&channelId={s['id']}&part=snippet,id&order=date&publishedAfter={date_after}&maxResults=3&type=video"
                items = requests.get(url).json().get('items', [])
                for item in items:
                    v_id = item['id']['videoId']
                    if v_id not in db:
                        if await process_mission(f"https://yt.be/v/{v_id}", item['snippet']['title'], item['snippet']['description'], s['n']):
                            with open(DB_FILE, 'a') as f: f.write(f"\n{v_id}")
                            return
            
            elif s['t'] == 'rss':
                res = requests.get(s['u'])
                items = ET.fromstring(res.content).findall('.//item')
                for item in items[:5]:
                    link = item.find('link').text
                    if link not in db:
                        if await process_mission(link, item.find('title').text, item.find('description').text, s['n']):
                            with open(DB_FILE, 'a') as f: f.write(f"\n{link}")
                            return
        except: continue

if __name__ == '__main__':
    asyncio.run(main())
