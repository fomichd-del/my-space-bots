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
# ⚙️ КОНФИГУРАЦИЯ v147.0 (Long Range Observer Protocol)
# ============================================================
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY') 
CHANNEL_NAME   = '@vladislav_space'
DB_FILE        = "last_video_date.txt"
SOURCE_LOG     = "last_source.txt"
SAFE_LIMIT_MB  = 40  # Целевой вес 40 Мб для стабильного прохода в 50 Мб лимит

# Фильтр контента для сектора AdMe и других
SPACE_KEYWORDS = [
    'космос', 'вселенная', 'планета', 'звезд', 'галактик', 'астероид', 
    'черная дыра', 'марса', 'луна', 'солнц', 'космическ', 'spacex', 
    'nasa', 'телескоп', 'мкс', 'astronomy', 'universe', 'telescope'
]

try:
    model = whisper.load_model("base")
except:
    model = None

MARTY_QUOTES = [
    "Гав! Длинная миссия требует особой упаковки! 📦🐩",
    "Ррр-гав! Сжал видео так сильно, что оно пролезет сквозь черную дыру! ✨",
    "Тяв! Командор, доставил длинный ролик в целости и сохранности! 🐾",
    "Гав! Проверил системы — теперь даже длинные выпуски нам по зубам! 🛰️"
]

# ============================================================
# 🛠 ВСПОМОГАТЕЛЬНЫЕ ИНСТРУМЕНТЫ
# ============================================================

def get_short_facts(text):
    if not text: return "Подробности миссии смотрите в ролике! ✨"
    text = re.sub(r'http\S+', '', text).strip()
    text = html.unescape(text)
    summary = text[:250] + "..." if len(text) > 250 else text
    return summary

def get_fast_proxy():
    print("🛰 [ЦУП] Поиск гипер-коридора (5s limit)...")
    url = "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=5000&country=all&ssl=all&anonymity=all"
    try:
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            proxies = resp.text.strip().split('\n')
            random.shuffle(proxies)
            for p in proxies[:30]:
                p = p.strip()
                try:
                    requests.get("https://www.google.com", proxies={"https": f"http://{p}"}, timeout=2)
                    return f"http://{p}"
                except: continue
    except: pass
    return None

# ============================================================
# 🎬 ОСНОВНОЙ ПРОЦЕССОР (v147.0 Long Range)
# ============================================================

async def process_mission_v147(v_id, title, desc_raw, is_russian=False, source_name=""):
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
            'js_runtimes': {'deno': {}},
            'retries': 20,
            'fragment_retries': 50,
            'socket_timeout': 30,
            'continuedl': True
        }
        if proxy: ydl_opts['proxy'] = proxy

        print(f"📡 [ЦУП] Захват объекта: {v_id} ({source_name})...")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(v_url, download=True)
            duration = info.get('duration', 1)
            raw_size = os.path.getsize(f_raw)

        print(f"⚖️ Вес: {raw_size/(1024*1024):.1f}Мб, Длительность: {duration}сек")

        # АНАЛИЗ ЗВУКА
        has_subs, mode_tag = False, "🎙 ОРИГИНАЛЬНАЯ ОЗВУЧКА"
        if not is_russian and model:
            print(f"🎙 Whisper: Анализ аудиопотока...")
            res = model.transcribe(f_raw)
            if len(res.get('text', '').strip()) > 15:
                mode_tag = "📝 ПЕРЕВОД (СУБТИТРЫ)"
                srt = ""
                for i, seg in enumerate(res.get('segments', [])):
                    t_ru = GoogleTranslator(source='auto', target='ru').translate(seg['text'].strip())
                    srt += f"{i+1}\n{time.strftime('%H:%M:%S,000', time.gmtime(seg['start']))} --> {time.strftime('%H:%M:%S,000', time.gmtime(seg['end']))}\n{t_ru}\n\n"
                with open("subs.srt", "w", encoding="utf-8") as fs: fs.write(srt)
                has_subs = True
            else:
                mode_tag = "🎵 МУЗЫКА КОСМОСА"
        elif not is_russian: 
            mode_tag = "🎵 МУЗЫКА КОСМОСА"

        # УМНОЕ СЖАТИЕ ДЛЯ ДЛИННЫХ ВИДЕО (v147.0)
        if raw_size < SAFE_LIMIT_MB * 1024 * 1024 and not has_subs:
            print("🚀 Файл в норме. Отправка оригинала.")
            f_to_send = f_raw
        else:
            print("⚙️ Глубокая обработка для прохода в лимиты...")
            # 1. Динамическое разрешение
            if duration > 1200: # > 20 минут
                scale = "scale=-2:360"
                print("📉 Режим: 360p (Приоритет: длительность)")
            elif duration > 600: # > 10 минут
                scale = "scale=-2:480"
                print("📉 Режим: 480p (Приоритет: баланс)")
            else:
                scale = "scale=trunc(iw/2)*2:trunc(ih/2)*2"
                print("📉 Режим: 720p (Приоритет: качество)")

            # 2. Расчет битрейта (целимся в 40Мб для безопасности)
            target_br_bits = (SAFE_LIMIT_MB * 1024 * 1024 * 8) / duration
            v_br = int(target_br_bits * 0.85) # Оставляем 15% на аудио и метаданные
            v_br = max(150000, min(v_br, 2500000))
            
            vf = f"subtitles=subs.srt:force_style='FontSize=20,BorderStyle=3,BackColour=&H80000000'" if has_subs else scale
            
            print(f"🛠 FFmpeg: Сжатие в {v_br//1000}kbps...")
            # Используем пресет 'veryfast' для лучшего качества при том же весе
            subprocess.run(['ffmpeg', '-y', '-i', f_raw, '-vf', vf, '-c:v', 'libx264', '-b:v', str(v_br), '-preset', 'veryfast', '-c:a', 'aac', '-b:a', '96k', f_final], capture_output=True)
            f_to_send = f_final

        # ОТПРАВКА В TELEGRAM
        clean_title = (title if is_russian else GoogleTranslator(source='auto', target='ru').translate(title)).upper()
        desc_ru = get_short_facts(desc_raw if is_russian else GoogleTranslator(source='auto', target='ru').translate(desc_raw))
        
        caption = (
            f"<b>{mode_tag}</b>\n\n🎬 <b>{clean_title}</b>\n"
            f"─────────────────────\n\n🪐 <b>О ЧЕМ РОЛИК:</b>\n<i>{desc_ru}</i>\n\n"
            f"<b>Марти:</b> <i>{random.choice(MARTY_QUOTES)}</i>\n\n"
            f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
        )

        final_size = os.path.getsize(f_to_send) / (1024*1024)
        print(f"📡 Отправка в Telegram ({final_size:.1f} Мб)...")
        
        with open(f_to_send, 'rb') as v:
            r = requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo", 
                files={"video": v}, 
                data={"chat_id": CHANNEL_NAME, "caption": caption, "parse_mode": "HTML"}, 
                timeout=600
            )
            
            if r.status_code == 200:
                print("✅ Telegram подтвердил получение!")
                return True
            else:
                print(f"❌ ОШИБКА TELEGRAM: {r.status_code} - {r.text}")
                return False

    except Exception as e:
        print(f"⚠️ Ошибка миссии: {e}")
        return False

# ============================================================
# 🛰 ГЛАВНЫЙ ЦИКЛ (НАВИГАЦИЯ)
# ============================================================

def get_videos(cid):
    try:
        url = f"https://www.googleapis.com/youtube/v3/channels?part=contentDetails&forHandle={cid.replace('@','')}&key={YOUTUBE_API_KEY}"
        res = requests.get(url).json()
        up_id = res['items'][0]['contentDetails']['relatedPlaylists']['uploads']
        url_v = f"https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&playlistId={up_id}&maxResults=3&key={YOUTUBE_API_KEY}"
        return [{'id': i['snippet']['resourceId']['videoId'], 'title': i['snippet']['title'], 'desc': i['snippet']['description']} for i in requests.get(url_v).json()['items']]
    except: return []

async def main():
    print(f"🎬 [ЦУП] v147.0 'Long Range' запуск...")
    db = open(DB_FILE, 'r').read() if os.path.exists(DB_FILE) else ""
    last_s = open(SOURCE_LOG, 'r').read().strip() if os.path.exists(SOURCE_LOG) else ""

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
        vids = get_videos(s['cid'])
        for v in vids:
            if v['id'] not in db:
                if s.get('filter') and not any(kw in (v['title'] + v['desc']).lower() for kw in SPACE_KEYWORDS): continue
                if await process_mission_v147(v['id'], v['title'], v['desc'], s['ru'], s['n']):
                    with open(DB_FILE, 'a') as f: f.write(f"\n{v['id']}")
                    with open(SOURCE_LOG, 'w') as f: f.write(s['n'])
                    print("🎉 Миссия успешно завершена!"); return
    print("🛰 Горизонт чист.")

if __name__ == '__main__':
    asyncio.run(main())
