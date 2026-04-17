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
# ⚙️ КОНФИГУРАЦИЯ v141.0 (Proxy Pulse Protocol)
# ============================================================
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY') 
CHANNEL_NAME   = '@vladislav_space'
DB_FILE        = "last_video_date.txt"
SOURCE_LOG     = "last_source.txt"
MAX_FILE_SIZE = 48.5 * 1024 * 1024 

translator = GoogleTranslator(source='auto', target='ru')
try:
    model = whisper.load_model("base")
except:
    model = None

# ============================================================
# 🛠 СИСТЕМА ПРОКСИ (ПРОБИВ БЛОКИРОВКИ)
# ============================================================

def get_working_proxy():
    """Получает список бесплатных прокси и выбирает живой"""
    proxy_urls = [
        "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all",
        "https://www.proxy-list.download/api/v1/get?type=https"
    ]
    print("🛰 [ЦУП] Поиск свободного коридора (Proxy)...")
    try:
        for url in proxy_urls:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                proxies = resp.text.strip().split('\n')
                random.shuffle(proxies)
                for p in proxies[:10]: # Проверяем первые 10
                    p = p.strip()
                    try:
                        requests.get("https://www.google.com", proxies={"https": f"http://{p}"}, timeout=5)
                        print(f"✅ Коридор открыт: {p}")
                        return f"http://{p}"
                    except: continue
    except: pass
    return None

# ============================================================
# 🎬 УМНЫЙ ПРОЦЕССОР 
# ============================================================

async def process_mission_v141(v_id_or_url, title, desc, source_name, is_russian=False):
    f_raw, f_final = "raw_video.mp4", "final_video.mp4"
    for f in [f_raw, f_final, "subs.srt"]:
        if os.path.exists(f): os.remove(f)

    try:
        v_url = v_id_or_url if 'http' in v_id_or_url else f"https://www.youtube.com/watch?v={v_id_or_url}"
        print(f"📥 [ЦУП] Захват объекта: {v_url}")

        # Пытаемся получить прокси
        proxy = get_working_proxy()
        
        # Настройка маскировки под мобильный Android
        ydl_opts = {
            'format': 'bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480]/best',
            'outtmpl': f_raw, 
            'quiet': True,
            'no_warnings': True,
            'extractor_args': {'youtube': ['player_client=android', 'player_skip=webpage']}
        }
        if proxy: ydl_opts['proxy'] = proxy

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(v_url, download=True)
            duration = info.get('duration', 600)

        if not os.path.exists(f_raw): return False

        # --- СЖАТИЕ И ОФОРМЛЕНИЕ ---
        target_br = int((MAX_FILE_SIZE * 8) / duration) - 128000
        final_v_br = max(100000, min(target_br, 2500000))
        
        has_subs = False
        mode_tag = "🎙 ОРИГИНАЛЬНАЯ ОЗВУЧКА 🎙"
        
        if not is_russian and model:
            print("🎙 Whisper: Перевод вещания...")
            mode_tag = "📝 РУССКИЕ СУБТИТРЫ 📝"
            res = model.transcribe(f_raw)
            srt = ""
            for i, seg in enumerate(res.get('segments', [])):
                txt_ru = GoogleTranslator(source='auto', target='ru').translate(seg['text'].strip())
                if txt_ru:
                    s, e = time.strftime('%H:%M:%S,000', time.gmtime(seg['start'])), time.strftime('%H:%M:%S,000', time.gmtime(seg['end']))
                    srt += f"{i+1}\n{s} --> {e}\n{txt_ru}\n\n"
            if srt:
                with open("subs.srt", "w", encoding="utf-8") as fs: fs.write(srt)
                has_subs = True
        elif not is_russian:
            mode_tag = "🎵 МУЗЫКА КОСМОСА 🎵"

        vf = "subtitles=subs.srt:force_style='FontSize=22,BorderStyle=3,BackColour=&H80000000'" if has_subs else "scale=trunc(iw/2)*2:trunc(ih/2)*2"
        subprocess.run(['ffmpeg', '-y', '-i', f_raw, '-vf', vf, '-c:v', 'libx264', '-b:v', str(final_v_br), '-preset', 'ultrafast', '-c:a', 'aac', '-b:a', '128k', f_final], capture_output=True)

        caption = (
            f"<b>{mode_tag}</b>\n\n🎬 <b>{(title if is_russian else GoogleTranslator(source='auto', target='ru').translate(title)).upper()}</b>\n"
            f"─────────────────────\n\n🪐 <b>ГЛАВНОЕ:</b>\n🔹 Видео загружено специально для юных космонавтов! ✨\n\n"
            f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
        )

        with open(f_final if os.path.exists(f_final) else f_raw, 'rb') as v:
            requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo", 
                          files={"video": v}, data={"chat_id": CHANNEL_NAME, "caption": caption, "parse_mode": "HTML"}, timeout=600)
            return True
    except Exception as e:
        print(f"⚠️ Сбой: {e}")
        return False

# ============================================================
# 📡 НАВИГАТОР
# ============================================================

def get_youtube_videos(channel_handle):
    items = []
    try:
        handle = channel_handle.replace('@', '')
        url_h = f"https://www.googleapis.com/youtube/v3/channels?part=id,contentDetails&forHandle={handle}&key={YOUTUBE_API_KEY}"
        res_h = requests.get(url_h).json()
        up_id = res_h['items'][0]['contentDetails']['relatedPlaylists']['uploads']
        url_pl = f"https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&playlistId={up_id}&maxResults=5&key={YOUTUBE_API_KEY}"
        for it in requests.get(url_pl).json().get('items', []):
            snip = it['snippet']
            items.append({'id': snip['resourceId']['videoId'], 'title': snip['title'], 'desc': snip['description']})
    except: pass
    return items

async def main():
    print("🎬 [ЦУП] v141.0 'Proxy Pulse' запуск...")
    if not os.path.exists(DB_FILE): open(DB_FILE, 'w').close()
    if not os.path.exists(SOURCE_LOG): open(SOURCE_LOG, 'w').write("None")
    db = open(DB_FILE, 'r').read()
    last_source = open(SOURCE_LOG, 'r').read().strip()

    SOURCES = [
        {'n': 'KOSMO', 'cid': '@off_kosmo', 'ru': True},
        {'n': 'NASA JPL', 'cid': '@NASAJPL', 'ru': False},
        {'n': 'SpaceX', 'cid': '@SpaceX', 'ru': False},
        {'n': 'Роскосмос', 'cid': '@roscosmos', 'ru': True}
    ]

    random.shuffle(SOURCES)
    for s in SOURCES:
        if s['n'] == last_source: continue
        try:
            print(f"📡 Сектор: {s['n']}...")
            videos = get_youtube_videos(s['cid'])
            for v in videos:
                if v['id'] not in db:
                    if await process_mission_v141(v['id'], v['title'], v['desc'], s['n'], s['ru']):
                        with open(DB_FILE, 'a') as f: f.write(f"\n{v['id']}")
                        with open(SOURCE_LOG, 'w') as f: f.write(s['n'])
                        print("🎉 Миссия выполнена!"); return
        except: continue

if __name__ == '__main__':
    asyncio.run(main())
