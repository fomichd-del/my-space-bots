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
from datetime import datetime
from deep_translator import GoogleTranslator

# ============================================================
# ⚙️ КОНФИГУРАЦИЯ v146.2 (Turbo Bypass Protocol)
# ============================================================
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY') 
CHANNEL_NAME   = '@vladislav_space'
DB_FILE        = "last_video_date.txt"
SOURCE_LOG     = "last_source.txt"
MAX_FILE_SIZE_BYTES = 45 * 1024 * 1024 

SPACE_KEYWORDS = ['космос', 'вселенная', 'планета', 'звезд', 'галактик', 'астероид', 'черная дыра', 'марса', 'луна', 'солнц', 'космическ', 'spacex', 'nasa', 'телескоп', 'мкс', 'astronomy', 'universe', 'telescope']

try:
    model = whisper.load_model("base")
except:
    model = None

MARTY_QUOTES = [
    "Гав! Пробил турбо-коридор сквозь защиту! 🚀🐩",
    "Ррр-гав! Отбросил медленные прокси, летим на форсаже! ✨",
    "Тяв! Нашел свежак, пока YouTube моргал! 🐾",
    "Гав! Командор, я теперь быстрее кометы! 🛰️"
]

# ============================================================
# 🛠 ТУРБО-ИНСТРУМЕНТЫ
# ============================================================

def get_short_facts(text):
    if not text: return "Подробности миссии смотрите в ролике! ✨"
    text = re.sub(r'http\S+', '', text)
    text = re.sub(r'#\S+', '', text)
    text = html.unescape(text).strip()
    sentences = [s.strip() for s in text.split('.') if len(s.strip()) > 10]
    summary = ". ".join(sentences[:2]) 
    if len(summary) > 300: summary = summary[:297] + "..."
    return summary + "." if summary else "Свежие кадры прямо с орбиты! 🪐"

def get_fast_proxy():
    print("🛰 [ЦУП] Поиск гипер-коридора (5s limit)...")
    url = "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=5000&country=all&ssl=all&anonymity=all"
    try:
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            proxies = resp.text.strip().split('\n')
            random.shuffle(proxies)
            for p in proxies[:40]: # Ищем среди 40 кандидатов
                p = p.strip()
                try:
                    # Очень быстрая проверка
                    requests.get("https://www.google.com", proxies={"https": f"http://{p}"}, timeout=2)
                    return f"http://{p}"
                except: continue
    except: pass
    return None

# ============================================================
# 🎬 ОСНОВНОЙ ПРОЦЕССОР
# ============================================================

async def process_mission_v146(v_id, title, desc_raw, is_russian=False, source_name=""):
    f_raw, f_final = "raw_video.mp4", "final_video.mp4"
    for f in [f_raw, f_final, "subs.srt"]:
        if os.path.exists(f): os.remove(f)

    try:
        v_url = f"https://www.youtube.com/watch?v={v_id}"
        proxy = get_fast_proxy()
        
        modern_args = ['player_client=mweb', 'player_skip=webpage']
        ydl_opts = {
            'format': 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720]',
            'outtmpl': f_raw,
            'quiet': True,
            'extractor_args': {'youtube': modern_args},
            'retries': 3, # Снизили количество ретраев, чтобы не виснуть
            'js_runtimes': {'deno': {}},
            'socket_timeout': 15 # Не ждем видео вечно
        }
        if proxy: ydl_opts['proxy'] = proxy

        print(f"📡 [ЦУП] Захват объекта: {v_id} ({source_name})...")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([v_url])

        if not os.path.exists(f_raw) or os.path.getsize(f_raw) < 500000: return False

        raw_size = os.path.getsize(f_raw)
        has_subs, mode_tag = False, "🎙 ОРИГИНАЛЬНАЯ ОЗВУЧКА"
        
        if not is_russian and model:
            print(f"🎙 Whisper: Анализ аудио...")
            res = model.transcribe(f_raw)
            clean_text = res.get('text', '').strip()
            if len(clean_text) > 15:
                mode_tag = "📝 ПЕРЕВОД (СУБТИТРЫ)"
                srt = ""
                for i, seg in enumerate(res.get('segments', [])):
                    t_ru = GoogleTranslator(source='auto', target='ru').translate(seg['text'].strip())
                    srt += f"{i+1}\n{time.strftime('%H:%M:%S,000', time.gmtime(seg['start']))} --> {time.strftime('%H:%M:%S,000', time.gmtime(seg['end']))}\n{t_ru}\n\n"
                with open("subs.srt", "w", encoding="utf-8") as fs: fs.write(srt)
                has_subs = True
            else:
                mode_tag = "🎵 МУЗЫКА КОСМОСА"
        elif not is_russian: mode_tag = "🎵 МУЗЫКА КОСМОСА"

        # УМНОЕ КАЧЕСТВО
        if raw_size < MAX_FILE_SIZE_BYTES and not has_subs:
            f_to_send = f_raw
        else:
            print("⚙️ Режим обработки...")
            duration = 600
            try:
                with yt_dlp.YoutubeDL({'quiet': True, 'proxy': proxy}) as ydl:
                    duration = ydl.extract_info(v_url, download=False).get('duration', 600)
            except: pass
            target_br = int((MAX_FILE_SIZE_BYTES * 8) / duration) - 128000
            v_br = max(200000, min(target_br, 2500000)) if raw_size < MAX_FILE_SIZE_BYTES else max(100000, min(target_br, 1200000))
            vf = "subtitles=subs.srt:force_style='FontSize=22,BorderStyle=3,BackColour=&H80000000'" if has_subs else "scale=trunc(iw/2)*2:trunc(ih/2)*2"
            subprocess.run(['ffmpeg', '-y', '-i', f_raw, '-vf', vf, '-c:v', 'libx264', '-b:v', str(v_br), '-preset', 'ultrafast', '-c:a', 'aac', '-b:a', '128k', f_final], capture_output=True)
            f_to_send = f_final

        caption = (
            f"<b>{mode_tag}</b>\n\n🎬 <b>{(title if is_russian else GoogleTranslator(source='auto', target='ru').translate(title)).upper()}</b>\n"
            f"─────────────────────\n\n🪐 <b>О ЧЕМ РОЛИК:</b>\n<i>{get_short_facts(desc_raw if is_russian else GoogleTranslator(source='auto', target='ru').translate(desc_raw))}</i>\n\n"
            f"<b>Марти:</b> <i>{random.choice(MARTY_QUOTES)}</i>\n\n🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
        )

        with open(f_to_send, 'rb') as v:
            requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo", files={"video": v}, data={"chat_id": CHANNEL_NAME, "caption": caption, "parse_mode": "HTML"}, timeout=600)
            return True
    except: return False

async def main():
    print("🎬 [ЦУП] v146.2 'Turbo Bypass' запуск...")
    db = (open(DB_FILE, 'r').read() if os.path.exists(DB_FILE) else "")
    last_s = (open(SOURCE_LOG, 'r').read().strip() if os.path.exists(SOURCE_LOG) else "")

    SOURCES = [
        {'n': 'SpaceX Fan', 'cid': '@spacexfan420', 'ru': False},
        {'n': 'NASA', 'cid': '@NASAJPL', 'ru': False},
        {'n': 'KOSMO', 'cid': '@off_kosmo', 'ru': True},
        {'n': 'ESO Observatory', 'cid': '@ESOobservatory', 'ru': False},
        {'n': 'Ночная наука', 'cid': '@ночнаянаука-ц4ш', 'ru': True},
        {'n': 'Роскосмос ТВ', 'cid': '@tvroscosmos', 'ru': True},
        {'n': 'AdMe', 'cid': '@AdMe', 'ru': True, 'filter': True}
    ]
    random.shuffle(SOURCES)
    
    for s in SOURCES:
        if s['n'] == last_s: continue
        print(f"📡 Сектор: {s['n']}")
        try:
            url = f"https://www.googleapis.com/youtube/v3/channels?part=contentDetails&forHandle={s['cid'].replace('@','')}&key={YOUTUBE_API_KEY}"
            up_id = requests.get(url).json()['items'][0]['contentDetails']['relatedPlaylists']['uploads']
            url_v = f"https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&playlistId={up_id}&maxResults=3&key={YOUTUBE_API_KEY}"
            vids = [{'id': i['snippet']['resourceId']['videoId'], 'title': i['snippet']['title'], 'desc': i['snippet']['description']} for i in requests.get(url_v).json()['items']]
            
            for v in vids:
                if v['id'] not in db:
                    if s.get('filter') and not any(kw in (v['title'] + v['desc']).lower() for kw in SPACE_KEYWORDS): continue
                    if await process_mission_v146(v['id'], v['title'], v['desc'], s['ru'], s['n']):
                        with open(DB_FILE, 'a') as f: f.write(f"\n{v['id']}")
                        with open(SOURCE_LOG, 'w') as f: f.write(s['n'])
                        print("🎉 Миссия успешно завершена!"); return
        except: continue
    print("🛰 Горизонт чист.")

if __name__ == '__main__':
    asyncio.run(main())
