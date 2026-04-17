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
# ⚙️ КОНФИГУРАЦИЯ v142.0 (Golden Standard)
# ============================================================
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY') 
CHANNEL_NAME   = '@vladislav_space'
DB_FILE        = "last_video_date.txt"
SOURCE_LOG     = "last_source.txt"

# Строгий лимит 45 Мб, чтобы точно пролезть в Telegram (50 Мб предел)
MAX_FILE_SIZE_BYTES = 45 * 1024 * 1024 

translator = GoogleTranslator(source='auto', target='ru')
try:
    model = whisper.load_model("base")
except:
    model = None

MARTY_QUOTES = [
    "Гав! Подготовил ролик точно по расписанию! 🚀🐩",
    "Ррр-гав! Свежие новости из глубокого космоса! ✨",
    "Тяв! Корабль готов к вылету, приятного просмотра! 🛰️🐕"
]

# ============================================================
# 🛠 УМНЫЙ ОХОТНИК ЗА ПРОКСИ (Вариант 2: Скорость)
# ============================================================

def get_fast_proxy():
    print("🛰 [ЦУП] Поиск быстрого коридора (Proxy Speed Test)...")
    url = "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            proxies = resp.text.strip().split('\n')
            random.shuffle(proxies)
            for p in proxies[:20]:
                p = p.strip()
                try:
                    start = time.time()
                    # Проверка скорости: качаем маленький кусочек Google
                    requests.get("https://www.google.com", proxies={"https": f"http://{p}"}, timeout=3)
                    ping = (time.time() - start) * 1000
                    if ping < 1500: # Берем только быстрые (до 1.5 сек)
                        print(f"✅ Скоростной коридор: {p} ({int(ping)}ms)")
                        return f"http://{p}"
                except: continue
    except: pass
    return None

# ============================================================
# ⏰ ПЛАНИРОВЩИК ПУБЛИКАЦИЙ
# ============================================================

def wait_for_schedule():
    """Удерживает бота до 07:00 или 18:00 по Киеву/МСК"""
    now = datetime.now()
    h = now.hour
    
    # Целевые часы (по времени сервера, обычно это UTC)
    # Если запуск в 5:00 UTC (7:00 Киева), ждем 7:00.
    # Если запуск в 16:00 UTC (18:00 Киева), ждем 18:00.
    
    targets = [7, 18] # Часы публикации
    current_hour_local = (now.hour + 2) % 24 # Примерная коррекция на часовой пояс
    
    next_target = None
    for t in targets:
        if current_hour_local < t:
            next_target = t
            break
    
    if next_target:
        wait_seconds = (next_target - current_hour_local) * 3600 - now.minute * 60
        if wait_seconds > 0:
            print(f"⏳ [ЦУП] Видео готово! Ожидаю окна публикации ({next_target}:00)...")
            time.sleep(min(wait_seconds, 7200)) # Ждем не более 2 часов

# ============================================================
# 🎬 ПРОЦЕССОР (Вариант 1: Авто 360p)
# ============================================================

async def process_mission_v142(v_id, title, is_russian=False, source_name=""):
    f_raw, f_final = "raw_video.mp4", "final_video.mp4"
    for f in [f_raw, f_final, "subs.srt"]:
        if os.path.exists(f): os.remove(f)

    try:
        v_url = f"https://www.youtube.com/watch?v={v_id}"
        proxy = get_fast_proxy()
        
        # 1. Сначала узнаем длительность
        info_opts = {'quiet': True, 'proxy': proxy} if proxy else {'quiet': True}
        with yt_dlp.YoutubeDL(info_opts) as ydl:
            info = ydl.extract_info(v_url, download=False)
            duration = info.get('duration', 600)

        # 🛡 ВАРИАНТ 1: Если ролик длиннее 15 минут — принудительно 360p для скорости и веса
        res_limit = 360 if duration > 900 else 480
        print(f"📺 [ЦУП] Формат: {res_limit}p (Длительность: {duration}с)")

        # 2. Скачивание
        ydl_opts = {
            'format': f'bestvideo[height<={res_limit}][ext=mp4]+bestaudio[ext=m4a]/best[height<={res_limit}]',
            'outtmpl': f_raw, 'proxy': proxy, 'quiet': True
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([v_url])

        # 3. Whisper (только для EN)
        has_subs = False
        mode_tag = "🎙 ОРИГИНАЛЬНАЯ ОЗВУЧКА"
        if not is_russian and model:
            print("🎙 Whisper: Перевод...")
            mode_tag = "📝 РУССКИЕ СУБТИТРЫ"
            res = model.transcribe(f_raw)
            srt = ""
            for i, seg in enumerate(res.get('segments', [])):
                t_ru = GoogleTranslator(source='auto', target='ru').translate(seg['text'].strip())
                srt += f"{i+1}\n{time.strftime('%H:%M:%S,000', time.gmtime(seg['start']))} --> {time.strftime('%H:%M:%S,000', time.gmtime(seg['end']))}\n{t_ru}\n\n"
            with open("subs.srt", "w", encoding="utf-8") as fs: fs.write(srt)
            has_subs = True

        # 4. FFmpeg сжатие под СТРОГИЙ лимит
        target_br = int((MAX_FILE_SIZE_BYTES * 8) / duration) - 128000
        v_br = max(100000, min(target_br, 1500000))
        vf = "subtitles=subs.srt" if has_subs else "scale=trunc(iw/2)*2:trunc(ih/2)*2"
        
        print(f"⚙️ FFmpeg: Финальная плавка (Битрейт: {v_br//1000}kbps)...")
        subprocess.run(['ffmpeg', '-y', '-i', f_raw, '-vf', vf, '-c:v', 'libx264', '-b:v', str(v_br), '-preset', 'ultrafast', '-c:a', 'aac', '-b:a', '128k', f_final], capture_output=True)

        # 5. Ожидание времени публикации
        wait_for_schedule()

        # 6. Отправка
        clean_title = (title if is_russian else GoogleTranslator(source='auto', target='ru').translate(title)).upper()
        caption = f"<b>{mode_tag}</b>\n\n🎬 <b>{clean_title}</b>\n─────────────────────\n\n🪐 Из сектора: {source_name}\n🐩 <i>{random.choice(MARTY_QUOTES)}</i>\n\n🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"

        print("📡 Отправка в Telegram...")
        with open(f_final, 'rb') as v:
            r = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo", files={"video": v}, data={"chat_id": CHANNEL_NAME, "caption": caption, "parse_mode": "HTML"})
            if r.status_code == 200: return True
            else: print(f"❌ Сбой Telegram: {r.text}"); return False
            
    except Exception as e:
        print(f"⚠️ Ошибка: {e}")
        return False

# ============================================================
# 📡 ГЛАВНЫЙ ЦИКЛ
# ============================================================

def get_videos(cid):
    try:
        url = f"https://www.googleapis.com/youtube/v3/channels?part=contentDetails&forHandle={cid.replace('@','')}&key={YOUTUBE_API_KEY}"
        up_id = requests.get(url).json()['items'][0]['contentDetails']['relatedPlaylists']['uploads']
        url_v = f"https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&playlistId={up_id}&maxResults=5&key={YOUTUBE_API_KEY}"
        return [{'id': i['snippet']['resourceId']['videoId'], 'title': i['snippet']['title']} for i in requests.get(url_v).json()['items']]
    except: return []

async def main():
    print("🎬 [ЦУП] v142.0 'Golden Standard' запуск...")
    db = open(DB_FILE, 'r').read() if os.path.exists(DB_FILE) else ""
    last_s = open(SOURCE_LOG, 'r').read().strip() if os.path.exists(SOURCE_LOG) else ""

    SOURCES = [
        {'n': 'KOSMO', 'cid': '@off_kosmo', 'ru': True},
        {'n': 'NASA', 'cid': '@NASAJPL', 'ru': False},
        {'n': 'SpaceX', 'cid': '@SpaceX', 'ru': False},
        {'n': 'ESO', 'cid': '@ESOobservatory', 'ru': False},
        {'n': 'Роскосмос', 'cid': '@roscosmos', 'ru': True}
    ]
    random.shuffle(SOURCES)
    
    for s in SOURCES:
        if s['n'] == last_s: continue
        print(f"📡 Сектор: {s['n']}")
        vids = get_videos(s['cid'])
        for v in vids:
            if v['id'] not in db:
                if await process_mission_v142(v['id'], v['title'], s['ru'], s['n']):
                    with open(DB_FILE, 'a') as f: f.write(f"\n{v['id']}")
                    with open(SOURCE_LOG, 'w') as f: f.write(s['n'])
                    print("🎉 Миссия завершена успешно!"); return
    print("🛰 Новых объектов не обнаружено.")

if __name__ == '__main__':
    asyncio.run(main())
