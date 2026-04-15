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
VOICE_LIMIT = 420 

SOURCES = [
    {'n': 'ESO (Наука Европы)', 't': 'rss', 'u': 'https://www.eso.org/public/videos/feed/'},
    {'n': 'ESA (Европейская наука)', 't': 'rss', 'u': 'https://www.esa.int/rssfeed/Videos'},
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
    return html.unescape(text).strip()

def clear_workspace():
    for f in ["input.mp4", "output.mp4", "voice_final.mp3", "subs.srt"]:
        if os.path.exists(f): 
            try: os.remove(f)
            except: pass
    if os.path.exists("voice"): 
        try: shutil.rmtree("voice")
        except: pass
    os.makedirs("voice", exist_ok=True)

# ============================================================
# 🎙 МОДУЛЬ ОЗВУЧКИ (ИСПРАВЛЕННЫЙ LOOP)
# ============================================================

async def build_voice_track(segments):
    inputs = []; filter_parts = []; valid_count = 0
    for i, seg in enumerate(segments[:80]):
        try:
            phrase = super_clean(seg['text'])
            if len(phrase) < 2: continue
            
            path = f"voice/v_{valid_count}.mp3"
            t_text = translator.translate(phrase)
            
            # Генерация голоса
            communicate = edge_tts.Communicate(t_text, VOICE)
            await communicate.save(path)
            
            start_ms = int(seg['start'] * 1000)
            inputs.extend(["-i", path])
            filter_parts.append(f"[{valid_count+1}:a]adelay={start_ms}|{start_ms}[v{valid_count}]")
            valid_count += 1
        except Exception as e:
            print(f"⚠️ Пропуск сегмента {i}: {e}")
            continue
    
    if valid_count == 0: return None
    
    labels = "".join([f"[v{i}]" for i in range(valid_count)])
    amix = f"amix=inputs={valid_count}:duration=first:dropout_transition=0"
    # Смешиваем только голоса в один файл
    cmd = ["ffmpeg", "-y"] + inputs + ["-filter_complex", f"{';'.join(filter_parts)};{labels}{amix}[out]", "-map", "[out]", "voice_final.mp3"]
    subprocess.run(cmd, check=True)
    return "voice_final.mp3"

async def process_video_async(video_url, is_yt):
    f_in, f_out = "input.mp4", "output.mp4"
    clear_workspace()
    try:
        ydl_opts = {'format': 'best[height<=720][ext=mp4]', 'outtmpl': f_in, 'quiet': True, 'noplaylist': True}
        if is_yt:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=True)
                dur = info.get('duration', 0)
        else:
            r = requests.get(video_url, timeout=120)
            with open(f_in, "wb") as f: f.write(r.content)
            dur = float(subprocess.check_output(f"ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 {f_in}", shell=True))

        print(f"🧠 Нейросеть слушает видео...")
        res = model.transcribe(f_in)
        segments = res.get('segments', [])
        
        if segments and dur <= VOICE_LIMIT:
            print(f"🎙 Светлана приступает к озвучке...")
            voice_track = await build_voice_track(segments)
            if voice_track:
                # Накладываем голос на видео (0 - видео, 1 - собранный голос)
                cmd = ["ffmpeg", "-y", "-i", f_in, "-i", voice_track, 
                       "-filter_complex", "[0:a]volume=0.2[bg];[bg][1:a]amix=inputs=2:duration=first[outa]", 
                       "-map", "0:v", "-map", "[outa]", "-c:v", "copy", "-c:a", "aac", f_out]
                subprocess.run(cmd, check=True)
                return f_out, "voice"
        
        return f_in, "original"
    except Exception as e:
        print(f"❌ Ошибка в асинхронном процессе: {e}")
        return None, None

# ============================================================
# 🎬 ГЛАВНЫЙ ЦИКЛ
# ============================================================

def main():
    print("🎬 [ЦУП] v8.3 'Nova' запущен...")
    db = open(DB_FILE, 'r').read() if os.path.exists(DB_FILE) else ""
    
    pool = SOURCES.copy()
    random.shuffle(pool)

    for s in pool:
        try:
            print(f"📡 Сектор: {s['n']}...")
            url_f = s['u'] if 'u' in s else f"https://www.youtube.com/feeds/videos.xml?channel_id={s['id']}"
            res = requests.get(url_f, headers={'User-Agent': 'Mozilla/5.0'}, timeout=20)
            if "<?xml" not in res.text[:100]: continue
            
            root = ET.fromstring(res.content)
            video = None
            if s['t'] == 'rss':
                item = root.find('.//item') or root.find('{http://www.w3.org/2005/Atom}entry')
                if item is not None:
                    lt = item.find('.//enclosure')
                    link = lt.get('url') if lt is not None else item.find('link').text
                    if link and link not in db:
                        video = {'url': link, 'title': item.find('title').text, 'is_yt': 'youtube' in link, 'source': s['n'], 'desc': item.find('description').text or ''}
            else:
                entry = root.find('{http://www.w3.org/2005/Atom}entry')
                if entry is not None:
                    v_id = entry.find('{http://www.youtube.com/xml/schemas/2009}videoId').text
                    link = f"https://www.youtube.com/watch?v={v_id}"
                    if link not in db:
                        video = {'url': link, 'title': entry.find('title').text, 'is_yt': True, 'source': s['n'], 'desc': ''}

            if video:
                # ЗАПУСКАЕМ АСИНХРОННУЮ ОБРАБОТКУ ПРАВИЛЬНО
                path, mode = asyncio.run(process_video_async(video['url'], video['is_yt']))
                
                if not path: continue

                t_ru = super_clean(translator.translate(video['title']).upper())
                raw_d = super_clean(video['desc'][:300])
                d_ru = super_clean(translator.translate(raw_d)) if raw_d else "Новые тайны Вселенной."
                if len(d_ru) > 170: d_ru = d_ru[:170] + "..."

                caption = (
                    f"🎬 <b>{t_ru}</b>\n"
                    f"─────────────────────\n"
                    f"🪐 <b>ОБЪЕКТ:</b> {s['n']}\n"
                    f"🔊 <b>ЗВУК:</b> {('Голос Светланы' if mode=='voice' else 'Оригинал')}\n"
                    f"─────────────────────\n"
                    f"📖 {d_ru}\n\n"
                    f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
                )

                print(f"📤 Отправка в Telegram...")
                with open(path, 'rb') as v:
                    r = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo", 
                                      files={"video": v}, 
                                      data={"chat_id": CHANNEL_NAME, "caption": caption, "parse_mode": "HTML", "supports_streaming": True}, 
                                      timeout=120)
                
                if r.status_code == 200:
                    open(DB_FILE, 'a').write(f"\n{video['url']}")
                    print("🎉 УСПЕХ!")
                    return
                else:
                    print(f"❌ Ошибка Telegram: {r.text}")
        except Exception as e:
            print(f"⚠️ Сбой в {s['n']}: {e}")
            continue

if __name__ == '__main__': main()
