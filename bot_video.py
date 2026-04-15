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
# 🛠 СЕРВИСНЫЕ ФУНКЦИИ
# ============================================================

def super_clean(text):
    if not text: return ""
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'http\S+', '', text)
    return html.unescape(text).strip()

def clear_workspace():
    """Очистка временных файлов"""
    for f in ["input.mp4", "output.mp4", "voice_final.mp3", "subs.srt"]:
        if os.path.exists(f): os.remove(f)
    if os.path.exists("voice"): shutil.rmtree("voice")
    os.makedirs("voice")

# ============================================================
# 🎙 МОДУЛЬ ОЗВУЧКИ (БЕЗОПАСНЫЙ МОНТАЖ)
# ============================================================

async def build_voice_track(segments):
    """Создает единую дорожку озвучки"""
    inputs = []
    filter_parts = []
    valid_count = 0
    
    for i, seg in enumerate(segments[:80]):
        try:
            phrase = seg['text'].strip()
            if len(phrase) < 3: continue
            
            path = f"voice/v_{valid_count}.mp3"
            await edge_tts.Communicate(translator.translate(phrase), VOICE).save(path)
            
            start_ms = int(seg['start'] * 1000)
            inputs.extend(["-i", path])
            # Формируем задержку для каждого кусочка
            filter_parts.append(f"[{valid_count}:a]adelay={start_ms}|{start_ms}[a{valid_count}]")
            valid_count += 1
        except: continue
    
    if valid_count == 0: return None
    
    # Смешиваем все голоса в один файл voice_final.mp3
    labels = "".join([f"[a{i}]" for i in range(valid_count)])
    amix = f"amix=inputs={valid_count}:duration=first:dropout_transition=0"
    filter_complex = f"{';'.join(filter_parts)};{labels}{amix}[out]"
    
    cmd = ["ffmpeg", "-y"] + inputs + ["-filter_complex", filter_complex, "-map", "[out]", "voice_final.mp3"]
    subprocess.run(cmd, check=True)
    return "voice_final.mp3"

def process_video_master(video_url, is_yt):
    f_in, f_out = "input.mp4", "output.mp4"
    try:
        # ЗАГРУЗКА
        ydl_opts = {'format': 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]', 'outtmpl': f_in, 'quiet': True, 'noplaylist': True}
        if is_yt:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=True)
                dur = info.get('duration', 0)
        else:
            r = requests.get(video_url, timeout=120); open(f_in, "wb").write(r.content)
            dur = float(subprocess.check_output(f"ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 {f_in}", shell=True))

        # ТРАНСКРИБАЦИЯ
        res = model.transcribe(f_in)
        segments = res.get('segments', [])
        
        # ОЗВУЧКА
        if segments and dur <= VOICE_LIMIT:
            print(f"🎙 Синтез русской озвучки ({int(dur)} сек)...")
            voice_track = asyncio.run(build_voice_track(segments))
            if voice_track:
                # Накладываем готовую дорожку на видео (видео - index 0, звук - index 1)
                cmd = [
                    "ffmpeg", "-y", "-i", f_in, "-i", voice_track,
                    "-filter_complex", "[0:a]volume=0.2[bg];[bg][1:a]amix=inputs=2:duration=first[outa]",
                    "-map", "0:v", "-map", "[outa]", "-c:v", "copy", "-c:a", "aac", f_out
                ]
                subprocess.run(cmd, check=True)
                return f_out, "voice"
        
        return f_in, "original"
    except Exception as e:
        print(f"⚠️ Ошибка студии: {e}"); return None, None

# ============================================================
# 🎬 ГЛАВНЫЙ ЦИКЛ
# ============================================================

def main():
    print("🎬 [ЦУП] v8.0 'Supernova' запущен...")
    clear_workspace()
    db = open(DB_FILE, 'r').read() if os.path.exists(DB_FILE) else ""
    
    pool = SOURCES.copy()
    random.shuffle(pool)

    headers = {'User-Agent': 'Mozilla/5.0'}

    for s in pool:
        try:
            print(f"📡 Сектор: {s['n']}...")
            video = None
            res = requests.get(s['u'] if 'u' in s else f"https://www.youtube.com/feeds/videos.xml?channel_id={s['id']}", headers=headers, timeout=20)
            
            # Проверка на валидность XML
            try:
                root = ET.fromstring(res.content)
            except:
                print(f"❌ Ошибка данных в секторе {s['n']}, иду дальше..."); continue
                
            if s['t'] == 'rss':
                items = root.findall('.//item') or root.findall('{http://www.w3.org/2005/Atom}entry')
                for item in items[:5]:
                    link = item.find('.//enclosure').get('url') if item.find('.//enclosure') is not None else item.find('link').text
                    if link and link not in db:
                        video = {'url': link, 'title': item.find('title').text, 'is_yt': 'youtube' in link, 'source': s['n'], 'desc': item.find('description').text or ''}
                        break
            else:
                entries = root.findall('{http://www.w3.org/2005/Atom}entry')
                for entry in entries[:3]:
                    link = f"https://www.youtube.com/watch?v={entry.find('{http://www.youtube.com/xml/schemas/2009}videoId').text}"
                    if link and link not in db:
                        video = {'url': link, 'title': entry.find('title').text, 'is_yt': True, 'source': s['n'], 'desc': ''}
                        break

            if video:
                path, mode = process_video_master(video['url'], video['is_yt'])
                if not path: continue

                t_ru = super_clean(translator.translate(video['title']).upper())
                d_ru = super_clean(translator.translate(video['desc'][:300])) if video['desc'] else "Увлекательные факты о нашей Вселенной."
                if len(d_ru) > 180: d_ru = d_ru[:180] + "..."

                caption = (
                    f"🎬 <b>{t_ru}</b>\n"
                    f"─────────────────────\n"
                    f"🪐 <b>ОБЪЕКТ:</b> {s['n']}\n"
                    f"🔊 <b>ЗВУК:</b> {('Русский голос' if mode=='voice' else 'Оригинал')}\n"
                    f"─────────────────────\n"
                    f"📖 {d_ru}\n\n"
                    f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
                )

                with open(path, 'rb') as v:
                    r = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo", 
                                      files={"video": v}, data={"chat_id": CHANNEL_NAME, "caption": caption, "parse_mode": "HTML", "supports_streaming": True})
                    if r.status_code == 200:
                        open(DB_FILE, 'a').write(f"\n{video['url']}")
                        print("🎉 Выпуск в эфире!")
                        return
        except Exception as e:
            print(f"⚠️ Сбой сектора {s['n']}: {e}"); continue

if __name__ == '__main__': main()
