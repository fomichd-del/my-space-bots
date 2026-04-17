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
# ⚙️ КОНФИГУРАЦИЯ v143.0 (Chameleon Protocol)
# ============================================================
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY') 
CHANNEL_NAME   = '@vladislav_space'
DB_FILE        = "last_video_date.txt"
SOURCE_LOG     = "last_source.txt"
MAX_FILE_SIZE_BYTES = 46 * 1024 * 1024 

translator = GoogleTranslator(source='auto', target='ru')
try:
    model = whisper.load_model("base")
except:
    model = None

MARTY_QUOTES = [
    "Гав! Маскировка активирована, пролетаем мимо радаров! 🛰️🐩",
    "Ррр-гав! Нашел лазейку в коде инопланетян! ✨",
    "Тяв! Космическая почта доставлена вовремя! 🐾"
]

# ============================================================
# 🛠 ОХОТНИК ЗА ПРОКСИ (v143: Усиленный)
# ============================================================

def get_fast_proxy():
    print("🛰 [ЦУП] Поиск свободного коридора...")
    url = "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            proxies = resp.text.strip().split('\n')
            random.shuffle(proxies)
            for p in proxies[:25]:
                p = p.strip()
                try:
                    # Проверяем не только Google, но и доступность API
                    requests.get("https://www.google.com", proxies={"https": f"http://{p}"}, timeout=3)
                    return f"http://{p}"
                except: continue
    except: pass
    return None

# ============================================================
# 🎬 ПРОЦЕССОР (v143: Chameleon Mode)
# ============================================================

async def process_mission_v143(v_id, title, is_russian=False, source_name=""):
    f_raw, f_final = "raw_video.mp4", "final_video.mp4"
    for f in [f_raw, f_final, "subs.srt"]:
        if os.path.exists(f): os.remove(f)

    try:
        v_url = f"https://www.youtube.com/watch?v={v_id}"
        proxy = get_fast_proxy()
        
        # Маскировка под Мобильный Браузер (самая высокая проходимость)
        modern_args = ['player_client=mweb', 'player_skip=webpage']

        # 1. Анализ
        info_opts = {
            'quiet': True, 
            'no_warnings': True,
            'extractor_args': {'youtube': modern_args}
        }
        if proxy: info_opts['proxy'] = proxy

        with yt_dlp.YoutubeDL(info_opts) as ydl:
            # Маленькая пауза перед запросом (имитация человека)
            time.sleep(random.randint(3, 7))
            info = ydl.extract_info(v_url, download=False)
            duration = info.get('duration', 600)

        res_limit = 360 if duration > 900 else 480
        print(f"📺 [ЦУП] Формат: {res_limit}p | Источник: {source_name}")

        # 2. Загрузка
        ydl_opts = {
            'format': f'bestvideo[height<={res_limit}][ext=mp4]+bestaudio[ext=m4a]/best[height<={res_limit}]',
            'outtmpl': f_raw, 
            'quiet': True,
            'no_warnings': True,
            'extractor_args': {'youtube': modern_args}
        }
        if proxy: ydl_opts['proxy'] = proxy

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([v_url])

        if not os.path.exists(f_raw) or os.path.getsize(f_raw) < 100000:
            return False

        # 3. Whisper (только для EN)
        has_subs = False
        mode_tag = "🎙 ОРИГИНАЛЬНАЯ ОЗВУЧКА"
        if not is_russian and model:
            print(f"🎙 Whisper: Обработка сектора {source_name}...")
            mode_tag = "📝 РУССКИЕ СУБТИТРЫ"
            res = model.transcribe(f_raw)
            srt = ""
            for i, seg in enumerate(res.get('segments', [])):
                t_ru = GoogleTranslator(source='auto', target='ru').translate(seg['text'].strip())
                srt += f"{i+1}\n{time.strftime('%H:%M:%S,000', time.gmtime(seg['start']))} --> {time.strftime('%H:%M:%S,000', time.gmtime(seg['end']))}\n{t_ru}\n\n"
            with open("subs.srt", "w", encoding="utf-8") as fs: fs.write(srt)
            has_subs = True
        elif not is_russian: mode_tag = "🎵 МУЗЫКА КОСМОСА"

        # 4. Сжатие
        target_br = int((MAX_FILE_SIZE_BYTES * 8) / duration) - 128000
        v_br = max(100000, min(target_br, 1500000))
        vf = "subtitles=subs.srt" if has_subs else "scale=trunc(iw/2)*2:trunc(ih/2)*2"
        
        print(f"⚙️ FFmpeg: Сжатие (Цель: {v_br//1000}kbps)...")
        subprocess.run(['ffmpeg', '-y', '-i', f_raw, '-vf', vf, '-c:v', 'libx264', '-b:v', str(v_br), '-preset', 'ultrafast', '-c:a', 'aac', '-b:a', '128k', f_final], capture_output=True)

        # 5. Оформление и отправка
        clean_title = (title if is_russian else GoogleTranslator(source='auto', target='ru').translate(title)).upper()
        caption = f"<b>{mode_tag}</b>\n\n🎬 <b>{clean_title}</b>\n─────────────────────\n\n🪐 Сектор: {source_name}\n🐩 <i>{random.choice(MARTY_QUOTES)}</i>\n\n🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"

        print("📡 Отправка в Telegram...")
        with open(f_final if os.path.exists(f_final) else f_raw, 'rb') as v:
            r = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo", files={"video": v}, data={"chat_id": CHANNEL_NAME, "caption": caption, "parse_mode": "HTML"})
            return r.status_code == 200
            
    except Exception as e:
        print(f"⚠️ Ошибка: {e}")
        return False

# ============================================================
# 📡 НАВИГАТОР
# ============================================================

def get_videos(cid):
    try:
        url = f"https://www.googleapis.com/youtube/v3/channels?part=contentDetails&forHandle={cid.replace('@','')}&key={YOUTUBE_API_KEY}"
        up_id = requests.get(url).json()['items'][0]['contentDetails']['relatedPlaylists']['uploads']
        url_v = f"https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&playlistId={up_id}&maxResults=5&key={YOUTUBE_API_KEY}"
        return [{'id': i['snippet']['resourceId']['videoId'], 'title': i['snippet']['title']} for i in requests.get(url_v).json()['items']]
    except: return []

async def main():
    print("🎬 [ЦУП] v143.0 'Chameleon' запуск...")
    db = open(DB_FILE, 'r').read() if os.path.exists(DB_FILE) else ""
    last_s = open(SOURCE_LOG, 'r').read().strip() if os.path.exists(SOURCE_LOG) else ""

    SOURCES = [
        {'n': 'KOSMO', 'cid': '@off_kosmo', 'ru': True},
        {'n': 'NASA', 'cid': '@NASAJPL', 'ru': False},
        {'n': 'SpaceX', 'cid': '@SpaceX', 'ru': False},
        {'n': 'Роскосмос', 'cid': '@roscosmos', 'ru': True}
    ]
    random.shuffle(SOURCES)
    
    for s in SOURCES:
        if s['n'] == last_s: continue
        print(f"📡 Сектор: {s['n']}")
        vids = get_videos(s['cid'])
        for v in vids:
            if v['id'] not in db:
                if await process_mission_v143(v['id'], v['title'], s['ru'], s['n']):
                    with open(DB_FILE, 'a') as f: f.write(f"\n{v['id']}")
                    with open(SOURCE_LOG, 'w') as f: f.write(s['n'])
                    print("🎉 Миссия выполнена!"); return
    print("🛰 Системы защиты YouTube пока не преодолимы. Ждем следующего окна...")

if __name__ == '__main__':
    asyncio.run(main())
