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

print("🚀 [ЦУП] Системы инициализированы. Запуск v147.6...")

# ============================================================
# ⚙️ КОНФИГУРАЦИЯ v147.6 (Stability & Beauty)
# ============================================================
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY') 
CHANNEL_NAME   = '@vladislav_space'
DB_FILE        = "last_video_date.txt"
SOURCE_LOG     = "last_source.txt"
SAFE_LIMIT_MB  = 42 

SPACE_KEYWORDS = ['космос', 'вселенная', 'планета', 'звезд', 'галактик', 'астероид', 'черная дыра', 'марса', 'луна', 'солнц', 'космическ', 'spacex', 'nasa', 'телескоп', 'мкс', 'astronomy', 'universe', 'telescope']

# Глобальная переменная для модели (грузим только по требованию)
whisper_model = None

MARTY_QUOTES = [
    "Гав! Навел лоск в описании, теперь всё сияет как сверхновая! ✨🐩",
    "Ррр-гав! Выбросил рекламный мусор, оставил только чистую науку! 🔭",
    "Тяв! Командор, оцените стиль: коротко, ярко и по делу! 🐾",
    "Гав! Красивому видео — красивое описание. Миссия v147.6 готова! 🛰️"
]

# ============================================================
# 🛠 УМНАЯ ОЧИСТКА ТЕКСТА (БЕЗ ХЕШТЕГОВ И РЕКЛАМЫ)
# ============================================================

def get_smart_summary(text):
    if not text: return "Интересные подробности — внутри ролика! ✨"
    
    # 1. Удаляем ссылки и ХЕШТЕГИ
    text = re.sub(r'http\S+', '', text)
    text = re.sub(r'#\S+', '', text)
    text = html.unescape(text)
    
    # 2. Фильтрация рекламного мусора
    junk_patterns = ['vk.com', 'ok.ru', 't.me', 'vk:', 'ok:', 'telegram:', 'rutube:', 'подписывайтесь', 'сайт:', 'facebook', 'instagram', 'max:']
    lines = text.split('\n')
    clean_lines = []
    
    for line in lines:
        line = line.strip()
        if len(line) < 15: continue 
        if any(junk in line.lower() for junk in junk_patterns): continue
        clean_lines.append(line)
    
    full_text = " ".join(clean_lines)
    sentences = re.split(r'(?<=[.!?]) +', full_text)
    meaningful = [s for s in sentences if len(s) > 25 and not s.lower().startswith(('мы в', 'подпишись', 'наш сайт'))]
    
    summary = " ".join(meaningful[:2])
    if len(summary) < 30:
        summary = full_text[:200]
        
    return summary.strip() + ".." if summary else "Свежий отчет из глубин космоса! 🪐"

def get_fast_proxy():
    print("🛰 [ЦУП] Поиск гипер-коридора...")
    url = "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=5000&country=all&ssl=all&anonymity=all"
    try:
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            proxies = resp.text.strip().split('\n')
            random.shuffle(proxies)
            for p in proxies[:30]:
                try:
                    requests.get("https://www.google.com", proxies={"https": f"http://{p.strip()}"}, timeout=2)
                    return f"http://{p.strip()}"
                except: continue
    except: pass
    return None

# ============================================================
# 🎬 ПРОЦЕССОР (v147.6 Stability)
# ============================================================

async def process_mission_v147(v_id, title, desc_raw, is_russian=False, source_name=""):
    global whisper_model
    f_raw, f_final = "raw_video.mp4", "final_video.mp4"
    for f in [f_raw, f_final, "subs.srt"]:
        if os.path.exists(f): os.remove(f)

    try:
        v_url = f"https://www.youtube.com/watch?v={v_id}"
        proxy = get_fast_proxy()
        
        # --- DIRECT STREAM (РАЗВЕДКА) ---
        print(f"📡 [ЦУП] Анализ объекта {v_id} ({source_name})...")
        temp_opts = {'quiet': True, 'js_runtimes': {'deno': {}}}
        if proxy: temp_opts['proxy'] = proxy
        with yt_dlp.YoutubeDL(temp_opts) as ydl:
            info = ydl.extract_info(v_url, download=False)
            duration = info.get('duration', 1)

        # Выбор разрешения ДО скачивания
        h_limit = 720
        if duration > 1800: h_limit = 240
        elif duration > 900: h_limit = 360
        elif duration > 480: h_limit = 480
        
        print(f"🎯 Выбран калибр: {h_limit}p (Время: {duration}с)")

        # --- ЗАХВАТ ---
        ydl_opts = {
            'format': f'bestvideo[height<={h_limit}][ext=mp4]+bestaudio[ext=m4a]/best[height<={h_limit}]',
            'outtmpl': f_raw, 'quiet': True, 'js_runtimes': {'deno': {}},
            'retries': 15, 'fragment_retries': 30, 'continuedl': True
        }
        if proxy: ydl_opts['proxy'] = proxy

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([v_url])
        
        if not os.path.exists(f_raw): return False
        raw_mb = os.path.getsize(f_raw) / (1024 * 1024)

        # --- МОЗГОВОЙ ЦЕНТР (WHISPER ПО ТРЕБОВАНИЮ) ---
        has_subs, mode_tag = False, "🎙 ОРИГИНАЛЬНАЯ ОЗВУЧКА"
        if not is_russian:
            if whisper_model is None:
                print("🧠 [ЦУП] Загрузка нейропрофиля Whisper (Base)...")
                whisper_model = whisper.load_model("base")
            
            print(f"🎙 Whisper: Перевод аудиопотока...")
            res = whisper_model.transcribe(f_raw)
            if len(res.get('text', '').strip()) > 15:
                mode_tag = "📝 ПЕРЕВОД (СУБТИТРЫ)"
                srt = ""
                for i, seg in enumerate(res.get('segments', [])):
                    t_ru = GoogleTranslator(source='auto', target='ru').translate(seg['text'].strip())
                    srt += f"{i+1}\n{time.strftime('%H:%M:%S,000', time.gmtime(seg['start']))} --> {time.strftime('%H:%M:%S,000', time.gmtime(seg['end']))}\n{t_ru}\n\n"
                with open("subs.srt", "w", encoding="utf-8") as fs: fs.write(srt)
                has_subs = True
            else: mode_tag = "🎵 МУЗЫКА КОСМОСА"
        elif not is_russian: mode_tag = "🎵 МУЗЫКА КОСМОСА"

        # --- УПАКОВКА ---
        if raw_mb < SAFE_LIMIT_MB and not has_subs:
            f_to_send = f_raw
        else:
            print(f"⚙️ Глубокая упаковка ({raw_mb:.1f} Мб -> {SAFE_LIMIT_MB} Мб)...")
            target_br = int((SAFE_LIMIT_MB * 1024 * 1024 * 8) / duration * 0.75)
            v_br = max(120000, min(target_br, 2000000))
            vf = "subtitles=subs.srt:force_style='FontSize=20,BorderStyle=3,BackColour=&H80000000'" if has_subs else f"scale=-2:{h_limit}"
            
            subprocess.run(['ffmpeg', '-y', '-i', f_raw, '-vf', vf, '-c:v', 'libx264', '-b:v', str(v_br), '-preset', 'ultrafast', '-c:a', 'aac', '-b:a', '48k', f_final], capture_output=True)
            f_to_send = f_final

        # --- ОФОРМЛЕНИЕ И ОТПРАВКА ---
        summary = get_smart_summary(desc_raw if is_russian else GoogleTranslator(source='auto', target='ru').translate(desc_raw))
        clean_title = (title if is_russian else GoogleTranslator(source='auto', target='ru').translate(title)).upper()
        
        caption = (
            f"<b>{mode_tag}</b>\n\n"
            f"🎬 <b>{clean_title}</b>\n"
            f"──────────────────────\n\n"
            f"🚀 <b>О ЧЕМ МИССИЯ:</b>\n"
            f"<i>{summary}</i>\n\n"
            f"<b>Марти:</b> <i>{random.choice(MARTY_QUOTES)}</i>\n\n"
            f"📡 <a href='https://t.me/vladislav_space'>ДНЕВНИК ЮНОГО КОСМОНАВТА</a>"
        )

        final_mb = os.path.getsize(f_to_send) / (1024 * 1024)
        print(f"📡 Отправка в Telegram ({final_mb:.1f} Мб)...")
        
        with open(f_to_send, 'rb') as v:
            r = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo", files={"video": v}, data={"chat_id": CHANNEL_NAME, "caption": caption, "parse_mode": "HTML"}, timeout=600)
            if r.status_code == 200:
                print("✅ Миссия выполнена успешно!")
                return True
            else:
                print(f"❌ Ошибка Telegram: {r.text}"); return False
    except Exception as e:
        print(f"⚠️ Сбой систем: {e}"); return False

# ============================================================
# 🛰 ГЛАВНЫЙ ЦИКЛ (НАВИГАЦИЯ)
# ============================================================

async def main():
    print(f"🎬 [ЦУП] v147.6 'Stability' запуск...")
    db = open(DB_FILE, 'r').read() if os.path.exists(DB_FILE) else ""
    last_s = open(SOURCE_LOG, 'r').read().strip() if os.path.exists(SOURCE_LOG) else ""

    SOURCES = [
        {'n': 'Rocket Hub', 'cid': '@rockethubspace', 'ru': True},
        {'n': 'SpaceX Fan', 'cid': '@spacexfan420', 'ru': True},
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
        print(f"📡 Сектор разведки: {s['n']}")
        try:
            url = f"https://www.googleapis.com/youtube/v3/channels?part=contentDetails&forHandle={s['cid'].replace('@','')}&key={YOUTUBE_API_KEY}"
            res = requests.get(url).json()
            up_id = res['items'][0]['contentDetails']['relatedPlaylists']['uploads']
            vids = [{'id': i['snippet']['resourceId']['videoId'], 'title': i['snippet']['title'], 'desc': i['snippet']['description']} for i in requests.get(f"https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&playlistId={up_id}&maxResults=3&key={YOUTUBE_API_KEY}").json()['items']]
            
            for v in vids:
                if v['id'] not in db:
                    if s.get('filter') and not any(kw in (v['title'] + v['desc']).lower() for kw in SPACE_KEYWORDS): continue
                    if await process_mission_v147(v['id'], v['title'], v['desc'], s['ru'], s['n']):
                        with open(DB_FILE, 'a') as f: f.write(f"\n{v['id']}")
                        with open(SOURCE_LOG, 'w') as f: f.write(s['n'])
                        return
        except: continue
    print("🛰 Горизонт чист.")

if __name__ == '__main__':
    asyncio.run(main())
