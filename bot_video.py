import requests
import os
import random
import time
import xml.etree.ElementTree as ET
import subprocess
import whisper
import yt_dlp
import asyncio
import edge_tts
import html
import re
import shutil
from deep_translator import GoogleTranslator

# ============================================================
# ⚙️ НАСТРОЙКИ
# ============================================================
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHANNEL_NAME   = '@vladislav_space'
DB_FILE        = "last_video_date.txt"

translator = GoogleTranslator(source='auto', target='ru')
model = whisper.load_model("tiny")
VOICE = "ru-RU-SvetlanaNeural"
VOICE_LIMIT = 450 

SOURCES = [
    {'n': 'ESO (Наука Европы)', 't': 'rss', 'u': 'https://www.eso.org/public/videos/feed/'},
    {'n': 'ESA (Открытия Европы)', 't': 'rss', 'u': 'https://www.esa.int/rssfeed/Videos'},
    {'n': 'JAXA (Космос Японии)', 't': 'yt', 'id': 'UC1S_S6G_9A440VUM_KOn6Zg'},
    {'n': 'ISRO (Миссии Индии)', 't': 'yt', 'id': 'UC16vrn4PmwzOm_8atGYU8YQ'},
    {'n': 'Роскосмос (Россия)', 't': 'yt', 'id': 'UCp7fGZ8Z9zX_lZpY_l475_g'},
    {'n': 'SciNews (Мировые факты)', 't': 'yt', 'id': 'UCu3WicZMcXpUksat9yU859g'},
    {'n': 'Hubble (Открытия)', 't': 'rss', 'u': 'https://hubblesite.org/rss/news'},
    {'n': 'NASA (Архив)', 't': 'nasa_api'}
]

# ============================================================
# 🛠 УТИЛИТЫ
# ============================================================

def super_clean(text):
    if not text: return ""
    text = re.sub(r'<[^>]+>', '', str(text))
    text = re.sub(r'http\S+', '', text)
    # Замена зарезервированных символов, которые бесят Telegram
    text = text.replace('—', '-').replace('–', '-').replace('«', '"').replace('»', '"')
    return html.escape(html.unescape(text)).strip()

def clear_workspace():
    for f in ["input.mp4", "output.mp4", "voice_final.mp3", "silent_base.mp3"]:
        if os.path.exists(f):
            try: os.remove(f)
            except: pass
    if os.path.exists("voice"):
        try: shutil.rmtree("voice")
        except: pass
    os.makedirs("voice", exist_ok=True)

# ============================================================
# 🎙 МОДУЛЬ ОЗВУЧКИ (v9.4 - СВЕРХНАДЕЖНЫЙ)
# ============================================================

async def build_voice_track(segments, total_duration):
    inputs = []; filter_parts = []; valid_count = 0
    # 1. Создаем базу тишины
    subprocess.run(f"ffmpeg -y -f lavfi -i anullsrc=r=44100:cl=stereo -t {total_duration + 5} -ar 44100 silent_base.mp3", shell=True, capture_output=True)
    inputs.extend(["-i", "silent_base.mp3"])
    
    for i, seg in enumerate(segments[:45]): # Оптимально 45 фраз
        try:
            phrase = seg['text'].strip()
            if len(phrase) < 3: continue
            path = f"voice/v_{valid_count}.mp3"
            await edge_tts.Communicate(translator.translate(phrase), VOICE).save(path)
            
            if os.path.exists(path) and os.path.getsize(path) > 100:
                start_ms = int(seg['start'] * 1000)
                inputs.extend(["-i", path])
                filter_parts.append(f"[{valid_count+1}:a]aresample=44100,adelay={start_ms}|{start_ms}[a{valid_count}]")
                valid_count += 1
        except: continue
    
    if valid_count == 0: return None
    labels = "".join([f"[a{i}]" for i in range(valid_count)])
    amix_filter = f"[0:a]{labels}amix=inputs={valid_count+1}:duration=longest:dropout_transition=0[out]"
    cmd = ["ffmpeg", "-y"] + inputs + ["-filter_complex", f"{';'.join(filter_parts)};{amix_filter}", "-map", "[out]", "-c:a", "libmp3lame", "voice_final.mp3"]
    subprocess.run(cmd, check=True, capture_output=True)
    return "voice_final.mp3"

async def process_video_async(video_url, is_yt):
    f_in, f_out = "input.mp4", "output.mp4"
    clear_workspace()
    try:
        # ЗАГРУЗКА С ПРОВЕРКОЙ
        ydl_opts = {'format': 'best[height<=720][ext=mp4]', 'outtmpl': f_in, 'quiet': True, 'noplaylist': True}
        dur = 0
        if is_yt:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=True)
                if not info: return None, None # ПРОВЕРКА NoneType
                dur = info.get('duration', 0)
        else:
            r = requests.get(video_url, timeout=120)
            with open(f_in, "wb") as f: f.write(r.content)
            dur = float(subprocess.check_output(f"ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 {f_in}", shell=True))

        has_audio = False
        try:
            if subprocess.check_output(f"ffprobe -i {f_in} -show_streams -select_streams a -loglevel error", shell=True): has_audio = True
        except: has_audio = False

        res = model.transcribe(f_in)
        segments = res.get('segments', [])
        
        if segments and dur <= VOICE_LIMIT:
            voice_file = await build_voice_track(segments, dur)
            if voice_file and os.path.exists(voice_file):
                print(f"🎬 Монтаж (Звук в оригинале: {has_audio})")
                if has_audio:
                    cmd = ["ffmpeg", "-y", "-i", f_in, "-i", voice_file, "-filter_complex", "[0:a]volume=0.2[bg];[bg][1:a]amix=inputs=2:duration=first:async=1[outa]", "-map", "0:v", "-map", "[outa]", "-c:v", "copy", "-c:a", "aac", f_out]
                else:
                    cmd = ["ffmpeg", "-y", "-i", f_in, "-i", voice_file, "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", f_out]
                subprocess.run(cmd, check=True)
                return f_out, "voice"
        return f_in, "original"
    except Exception as e:
        print(f"❌ Сбой: {e}"); return None, None

# ============================================================
# 🎬 ГЛАВНЫЙ АСИНХРОННЫЙ ЦИКЛ (v9.4)
# ============================================================

async def main():
    print("🎬 [ЦУП] v9.4 'Void Runner' запущен...")
    db = open(DB_FILE, 'r').read() if os.path.exists(DB_FILE) else ""
    pool = SOURCES.copy()
    random.shuffle(pool)
    pool.sort(key=lambda x: x['t'] == 'nasa_api')

    for s in pool:
        try:
            print(f"📡 Сектор: {s['n']}...")
            url_f = s['u'] if 'u' in s else f"https://www.youtube.com/feeds/videos.xml?channel_id={s['id']}"
            res = requests.get(url_f, headers={'User-Agent': 'Mozilla/5.0'}, timeout=20)
            if "<?xml" not in res.text[:100]: continue
            
            root = ET.fromstring(res.content)
            items = root.findall('.//item') or root.findall('{http://www.w3.org/2005/Atom}entry')
            for item in items[:3]:
                link = ""
                if s['t'] == 'rss':
                    lt = item.find('.//enclosure'); link = lt.get('url') if lt is not None else item.find('link').text
                else:
                    v_node = item.find('{http://www.youtube.com/xml/schemas/2009}videoId')
                    if v_node is not None: link = f"https://www.youtube.com/watch?v={v_node.text}"
                
                if link and link not in db:
                    t_n = item.find('title')
                    d_n = item.find('description') or item.find('{http://www.w3.org/2005/Atom}summary')
                    title = t_n.text if t_n is not None else "Событие"
                    desc = d_n.text if d_n is not None else ""
                    
                    path, mode = await process_video_async(link, 'youtube' in link)
                    if not path: continue
                    
                    t_ru = super_clean(translator.translate(title).upper())
                    d_ru = super_clean(translator.translate(desc[:250])) if desc else "Свежий репортаж из Вселенной."
                    
                    caption = (f"🎬 <b>{t_ru}</b>\n─────────────────────\n🪐 <b>ОБЪЕКТ:</b> {s['n']}\n🔊 <b>ЗВУК:</b> {('Голос Светланы' if mode=='voice' else 'Оригинал')}\n─────────────────────\n📖 {d_ru[:160]}...\n\n🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>")

                    with open(path, 'rb') as v:
                        r = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo", files={"video": v}, data={"chat_id": CHANNEL_NAME, "caption": caption, "parse_mode": "HTML", "supports_streaming": True}, timeout=150)
                    if r.status_code == 200:
                        open(DB_FILE, 'a').write(f"\n{link}"); return
                    else:
                        # План Б: отправка без HTML если ТГ ругается
                        with open(path, 'rb') as v:
                            requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo", files={"video": v}, data={"chat_id": CHANNEL_NAME, "caption": f"🎥 {t_ru}\n\n{link}"})
                        open(DB_FILE, 'a').write(f"\n{link}"); return
        except: continue

if __name__ == '__main__':
    # Бронированный запуск цикла
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(main())
        else:
            loop.run_until_complete(main())
    except:
        asyncio.run(main())
