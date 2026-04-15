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
# ⚙️ НАСТРОЙКИ ЦУП
# ============================================================
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHANNEL_NAME   = '@vladislav_space'
DB_FILE        = "last_video_date.txt"

translator = GoogleTranslator(source='auto', target='ru')
model = whisper.load_model("tiny")
VOICE = "ru-RU-SvetlanaNeural"
VOICE_RATE = "-15%" # Замедляем речь для идеального тайминга
VOICE_LIMIT = 540 # Лимит 9 минут

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
# 🛠 ТЕХНИЧЕСКИЙ ОТСЕК
# ============================================================

def safe_translate(text):
    if not text or len(str(text)) < 3: return text
    try:
        res = translator.translate(str(text))
        return res if res else text
    except: return text

def super_clean(text):
    if not text: return ""
    text = re.sub(r'<[^>]+>', '', str(text))
    text = re.sub(r'http\S+', '', text)
    text = text.replace('—', '-').replace('–', '-').replace('&', 'и')
    return html.escape(html.unescape(text)).strip()

def clear_workspace():
    for f in ["input.mp4", "output.mp4", "voice_final.mp3", "silent_base.mp3", "subs.srt"]:
        if os.path.exists(f):
            try: os.remove(f)
            except: pass
    if os.path.exists("voice"):
        try: shutil.rmtree("voice")
        except: pass
    os.makedirs("voice", exist_ok=True)

# ============================================================
# 📝 МОДУЛЬ СУБТИТРОВ
# ============================================================

def create_srt(segments):
    if not segments: return None
    srt_content = ""
    for i, seg in enumerate(segments[:60]):
        start = time.strftime('%H:%M:%S,000', time.gmtime(seg['start']))
        end = time.strftime('%H:%M:%S,000', time.gmtime(seg['end']))
        text_ru = safe_translate(seg['text'].strip())
        srt_content += f"{i+1}\n{start} --> {end}\n{text_ru}\n\n"
    
    with open("subs.srt", "w", encoding="utf-8") as f:
        f.write(srt_content)
    return "subs.srt"

# ============================================================
# 🎙 МОДУЛЬ ОЗВУЧКИ (v16.0 - ГРОМКИЙ)
# ============================================================

async def build_voice_track(segments, total_duration):
    inputs = []; filter_parts = []; valid_count = 0
    # Создаем базу тишины
    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-t", str(total_duration + 5), "silent_base.mp3"], capture_output=True)
    inputs.extend(["-i", "silent_base.mp3"])
    
    for i, seg in enumerate(segments[:40]):
        try:
            phrase = seg['text'].strip()
            if len(phrase) < 4: continue
            path = f"voice/v_{valid_count}.mp3"
            communicate = edge_tts.Communicate(safe_translate(phrase), VOICE, rate=VOICE_RATE)
            await communicate.save(path)
            if os.path.exists(path) and os.path.getsize(path) > 100:
                start_ms = int(seg['start'] * 1000) + 150 # Смещение для синхронизации
                inputs.extend(["-i", path])
                filter_parts.append(f"[{valid_count+1}:a]adelay={start_ms}|{start_ms}[a{valid_count}]")
                valid_count += 1
        except: continue
    
    if valid_count < 1: return None
    labels = "".join([f"[a{i}]" for i in range(valid_count)])
    amix_filter = f"[0:a]{labels}amix=inputs={valid_count+1}:duration=longest[out]"
    cmd = ["ffmpeg", "-y"] + inputs + ["-filter_complex", f"{';'.join(filter_parts)};{amix_filter}", "-map", "[out]", "voice_final.mp3"]
    subprocess.run(cmd, check=True, capture_output=True)
    return "voice_final.mp3"

async def process_video_async(video_url, is_yt):
    f_in, f_out = "input.mp4", "output.mp4"
    clear_workspace()
    try:
        # Загрузка
        ydl_opts = {'format': 'best[height<=720][ext=mp4]', 'outtmpl': f_in, 'quiet': True, 'noplaylist': True}
        if is_yt:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=True)
                dur = info.get('duration', 0) if info else 0
        else:
            r = requests.get(video_url, timeout=120)
            with open(f_in, "wb") as f: f.write(r.content)
            try:
                dur_out = subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", f_in])
                dur = float(dur_out.decode().strip())
            except: dur = 60 # Фоллбек если ffprobe барахлит

        # Проверка аудио (мягкая)
        has_audio = True
        try:
            audio_check = subprocess.run(["ffprobe", "-i", f_in, "-show_streams", "-select_streams", "a", "-loglevel", "error"], capture_output=True)
            if not audio_check.stdout: has_audio = False
        except: pass

        # Транскрибация
        res = model.transcribe(f_in)
        segments = res.get('segments', [])
        
        if segments and dur <= VOICE_LIMIT:
            # Приоритет субтитрам для длинных видео (>5 мин)
            if dur > 300:
                srt_file = create_srt(segments)
                if srt_file:
                    subprocess.run(["ffmpeg", "-y", "-i", f_in, "-vf", "subtitles=subs.srt", "-c:a", "copy", f_out], check=True)
                    return f_out, "subs"

            # Озвучка
            voice_file = await build_voice_track(segments, dur)
            if voice_file:
                print(f"🎬 Финальное сведение... (Звук: {has_audio})")
                if has_audio:
                    # УСИЛЕНИЕ ГОЛОСА В 3 РАЗА, ПРИГЛУШЕНИЕ ФОНА ДО 10%
                    cmd = ["ffmpeg", "-y", "-i", f_in, "-i", voice_file, 
                           "-filter_complex", "[0:a]volume=0.1[bg];[1:a]volume=3.0[v];[bg][v]amix=inputs=2:duration=first[outa]", 
                           "-map", "0:v", "-map", "[outa]", "-c:v", "copy", "-c:a", "aac", "-ignore_unknown", f_out]
                else:
                    cmd = ["ffmpeg", "-y", "-i", f_in, "-i", voice_file, 
                           "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-ignore_unknown", f_out]
                subprocess.run(cmd, check=True)
                return f_out, "voice"
        
        return f_in, "original"
    except Exception as e:
        print(f"⚠️ Ошибка: {e}")
        return (f_in if os.path.exists(f_in) else None), "original"

# ============================================================
# 🎬 ГЛАВНЫЙ ЦИКЛ ( v16.0 )
# ============================================================

async def main():
    print("🎬 [ЦУП] v16.0 'Absolute Zero' запущен...")
    db_content = open(DB_FILE, 'r').read() if os.path.exists(DB_FILE) else ""
    
    pool = SOURCES.copy()
    random.shuffle(pool)
    pool.sort(key=lambda x: x['t'] == 'nasa_api')

    for s in pool:
        try:
            print(f"📡 Сектор: {s['n']}...")
            video_list = []
            
            if s['t'] == 'nasa_api':
                if db_content.split('\n')[-1].startswith("nasa_"): continue
                nasa_res = requests.get(f"https://images-api.nasa.gov/search?q=universe&media_type=video").json()
                for item in nasa_res['collection']['items'][:5]:
                    v_id = item['data'][0]['nasa_id']
                    if f"nasa_{v_id}" not in db_content:
                        assets = requests.get(f"https://images-api.nasa.gov/asset/{v_id}").json()
                        v_url = next(a['href'] for a in assets['collection']['items'] if '~medium.mp4' in a['href'])
                        video_list.append({'url': v_url, 'title': item['data'][0]['title'], 'is_yt': False, 'desc': item['data'][0].get('description', ''), 'id': f"nasa_{v_id}"})
                        break
            else:
                url_f = s['u'] if 'u' in s else f"https://www.youtube.com/feeds/videos.xml?channel_id={s['id']}"
                res = requests.get(url_f, headers={'User-Agent': 'Mozilla/5.0'}, timeout=20)
                if res and "<?xml" in res.text[:100]:
                    root = ET.fromstring(res.content)
                    items = root.findall('.//item') or root.findall('{http://www.w3.org/2005/Atom}entry')
                    for item in items[:3]:
                        link = item.find('link').text if item.find('link') is not None else ""
                        if s['t'] == 'rss' and item.find('.//enclosure') is not None: link = item.find('.//enclosure').get('url')
                        if link and link not in db_content:
                            video_list.append({'url': link, 'title': item.find('title').text, 'is_yt': 'youtube' in link, 'desc': item.find('description').text if item.find('description') is not None else "", 'id': link})
                            break

            for v in video_list:
                path, mode = await process_video_async(v['url'], v['is_yt'])
                if not path or not os.path.exists(path): continue
                
                t_ru = super_clean(safe_translate(v['title']).upper())
                raw_desc = v['desc'] if v['desc'] else "Эксклюзивные кадры из глубин космоса, передающие масштаб и величие нашей Вселенной."
                d_ru = super_clean(safe_translate(raw_desc[:600]))
                
                # Статус по уставу
                status_audio = "Видео с переводом" if mode == "voice" else ("Видео с субтитрами" if mode == "subs" else "Оригинал")

                caption = (
                    f"⭐ <b>{t_ru}</b>\n\n"
                    f"🛰 <b>ОБЪЕКТ:</b> {s['n']}\n"
                    f"🔊 <b>ЗВУК:</b> {status_audio}\n"
                    f"─────────────────────\n"
                    f"📖 <b>СЮЖЕТ:</b> {d_ru[:400]}...\n\n"
                    f"🌌 <i>Тайны Вселенной раскрываются здесь!</i>\n"
                    f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
                )

                with open(path, 'rb') as video_file:
                    r = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo", files={"video": video_file}, data={"chat_id": CHANNEL_NAME, "caption": caption, "parse_mode": "HTML", "supports_streaming": True}, timeout=180)
                
                if r.status_code == 200:
                    with open(DB_FILE, 'a') as f: f.write(f"\n{v['id']}")
                    print(f"🎉 Готово: {v['title']}"); return
        except: continue

if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(main())
