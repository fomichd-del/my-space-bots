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
VOICE_LIMIT = 480 

SOURCES = [
    {'n': 'ESO (Европа - Наука)', 't': 'rss', 'u': 'https://www.eso.org/public/videos/feed/'},
    {'n': 'ESA (Наука Европы)', 't': 'rss', 'u': 'https://www.esa.int/rssfeed/Videos'},
    {'n': 'JAXA (Япония)', 't': 'yt', 'id': 'UC1S_S6G_9A440VUM_KOn6Zg'},
    {'n': 'ISRO (Индия)', 't': 'yt', 'id': 'UC16vrn4PmwzOm_8atGYU8YQ'},
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
# 🎙 МОДУЛЬ ОЗВУЧКИ (v9.1 - ОПТИМИЗИРОВАННЫЙ)
# ============================================================

async def build_voice_track(segments, total_duration):
    print(f"🎙 Собираю аудио-стек Nebula...")
    inputs = []
    filter_parts = []
    valid_count = 0
    
    # 1. Тихий фон (база)
    subprocess.run(f"ffmpeg -y -f lavfi -i anullsrc=r=44100:cl=stereo -t {total_duration + 5} -ar 44100 silent_base.mp3", shell=True, check=True)
    inputs.extend(["-i", "silent_base.mp3"])
    
    # 2. Обработка фраз (лимит 40 для стабильности памяти)
    for i, seg in enumerate(segments[:40]):
        try:
            phrase = seg['text'].strip()
            if len(phrase) < 3: continue
            
            path = f"voice/v_{valid_count}.mp3"
            t_text = translator.translate(phrase)
            
            communicate = edge_tts.Communicate(t_text, VOICE)
            await communicate.save(path)
            
            # Проверка, что файл создался и он не пустой
            if os.path.exists(path) and os.path.getsize(path) > 100:
                start_ms = int(seg['start'] * 1000)
                # Нормализуем звук сегмента до 44100Гц, чтобы FFmpeg не ругался
                path_norm = f"voice/vn_{valid_count}.mp3"
                subprocess.run(f"ffmpeg -y -i {path} -ar 44100 {path_norm}", shell=True, capture_output=True)
                
                inputs.extend(["-i", path_norm])
                filter_parts.append(f"[{valid_count+1}:a]adelay={start_ms}|{start_ms}[a{valid_count}]")
                valid_count += 1
        except: continue
    
    if valid_count == 0: return None
    
    # 3. Микширование
    labels = "".join([f"[a{i}]" for i in range(valid_count)])
    amix_filter = f"[0:a]{labels}amix=inputs={valid_count+1}:duration=longest:dropout_transition=0[out]"
    
    cmd = ["ffmpeg", "-y"] + inputs + ["-filter_complex", amix_filter, "-map", "[out]", "-c:a", "libmp3lame", "-b:a", "128k", "voice_final.mp3"]
    subprocess.run(cmd, check=True)
    return "voice_final.mp3"

async def process_video_async(video_url, is_yt):
    f_in, f_out = "input.mp4", "output.mp4"
    clear_workspace()
    try:
        ydl_opts = {'format': 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]', 'outtmpl': f_in, 'quiet': True, 'noplaylist': True}
        dur = 0
        if is_yt:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=True)
                if not info: return None, None
                dur = info.get('duration', 0)
        else:
            r = requests.get(video_url, timeout=120)
            with open(f_in, "wb") as f: f.write(r.content)
            dur = float(subprocess.check_output(f"ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 {f_in}", shell=True))

        # Проверка аудио
        has_audio = False
        try:
            if subprocess.check_output(f"ffprobe -i {f_in} -show_streams -select_streams a -loglevel error", shell=True): has_audio = True
        except: has_audio = False

        res = model.transcribe(f_in)
        segments = res.get('segments', [])
        
        if segments and dur <= VOICE_LIMIT:
            voice_file = await build_voice_track(segments, dur)
            if voice_file and os.path.exists(voice_file):
                print(f"🎬 Финальный монтаж Nebula...")
                if has_audio:
                    cmd = ["ffmpeg", "-y", "-i", f_in, "-i", voice_file, 
                           "-filter_complex", "[0:a]volume=0.25[bg];[bg][1:a]amix=inputs=2:duration=first[outa]", 
                           "-map", "0:v", "-map", "[outa]", "-c:v", "copy", "-c:a", "aac", f_out]
                else:
                    cmd = ["ffmpeg", "-y", "-i", f_in, "-i", voice_file, "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", f_out]
                subprocess.run(cmd, check=True)
                return f_out, "voice"
        return f_in, "original"
    except Exception as e:
        print(f"❌ Сбой монтажа: {e}"); return None, None

# ============================================================
# 🎬 ГЛАВНЫЙ ЦИКЛ
# ============================================================

def main():
    print("🎬 [ЦУП] v9.1 'Nebula' запущен...")
    db = open(DB_FILE, 'r').read() if os.path.exists(DB_FILE) else ""
    pool = SOURCES.copy()
    random.shuffle(pool)
    # Гарантируем, что NASA не блокирует поиск
    pool.sort(key=lambda x: x['t'] == 'nasa_api')

    for s in pool:
        try:
            video = None
            if s['t'] == 'nasa_api':
                res = requests.get(f"https://images-api.nasa.gov/search?q=astronomy&media_type=video").json()
                items = res['collection']['items']
                random.shuffle(items)
                for item in items[:5]:
                    v_id = item['data'][0]['nasa_id']
                    if v_id not in db:
                        assets = requests.get(f"https://images-api.nasa.gov/asset/{v_id}").json()
                        v_url = next(a['href'] for a in assets['collection']['items'] if '~medium.mp4' in a['href'])
                        video = {'url': v_url, 'title': item['data'][0]['title'], 'is_yt': False, 'desc': item['data'][0].get('description', ''), 'db_id': v_id}
                        break
            else:
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
                        t_node = item.find('title')
                        d_node = item.find('description') or item.find('{http://www.w3.org/2005/Atom}summary')
                        video = {'url': link, 'title': t_node.text if t_node is not None else "Космос", 'is_yt': 'youtube' in link, 'desc': d_node.text if d_node is not None else "", 'db_id': link}
                        break

            if video:
                path, mode = asyncio.run(process_video_async(video['url'], video['is_yt']))
                if not path: continue
                
                t_ru = super_clean(translator.translate(video['title']).upper())
                d_ru = super_clean(translator.translate(video['desc'][:300])) if video['desc'] else "Новый репортаж из Вселенной."
                if len(d_ru) > 170: d_ru = d_ru[:170] + "..."
                
                caption = (f"🎬 <b>{t_ru}</b>\n\n🪐 <b>ОБЪЕКТ:</b> {super_clean(s['n'])}\n"
                           f"🔊 <b>ЗВУК:</b> {('Русский перевод' if mode=='voice' else 'Оригинал')}\n\n"
                           f"📖 {d_ru}\n\n"
                           f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>")

                with open(path, 'rb') as v:
                    r = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo", 
                                      files={"video": v}, data={"chat_id": CHANNEL_NAME, "caption": caption, "parse_mode": "HTML", "supports_streaming": True}, timeout=150)
                
                if r.status_code == 200:
                    open(DB_FILE, 'a').write(f"\n{video['db_id']}"); print("🎉 УСПЕХ!"); return
        except: continue

if __name__ == '__main__': main()
