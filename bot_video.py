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
# ⚙️ КОНФИГУРАЦИЯ
# ============================================================
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
NASA_API_KEY   = os.getenv('NASA_API_KEY')
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
CHANNEL_NAME   = '@vladislav_space'
DB_FILE        = "last_video_date.txt"

translator = GoogleTranslator(source='auto', target='ru')
try:
    model = whisper.load_model("tiny")
except:
    model = None

# ============================================================
# 🛠 ВИДЕО-ИНЖЕНЕРИЯ (v111.0 - ПРОДВИНУТОЕ СЖАТИЕ)
# ============================================================

def compress_video_safe(input_path, output_path, target_size_mb=45):
    """Сжимает видео, чтобы оно гарантированно влезло в лимиты Telegram"""
    print(f"📉 Начинаю компрессию файла: {input_path}")
    try:
        prob = subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', input_path])
        duration = float(prob)
        # Рассчитываем битрейт с запасом
        target_total_bitrate = int((target_size_mb * 8 * 1024 * 1024) / duration)
        video_bitrate = target_total_bitrate - 128000 # Оставляем 128k на звук
        
        print(f"⚙️ Расчетный битрейт: {video_bitrate // 1000} kbps для длительности {int(duration)} сек.")
        
        # Однопроходное быстрое сжатие для стабильности на GitHub Actions
        subprocess.run([
            'ffmpeg', '-y', '-i', input_path,
            '-c:v', 'libx264', '-b:v', str(video_bitrate),
            '-preset', 'ultrafast', '-c:a', 'aac', '-b:a', '128k', output_path
        ], capture_output=True)
        return True
    except Exception as e:
        print(f"⚠️ Ошибка сжатия: {e}")
        return False

# ============================================================
# 🛰 ГЛАВНЫЙ ЦИКЛ ОБРАБОТКИ
# ============================================================

async def process_mission_v111(v_url, title, desc, source_name):
    f_raw, f_final = "raw_video.mp4", "final_video.mp4"
    for f in [f_raw, f_final, "subs.srt"]:
        if os.path.exists(f): os.remove(f)

    try:
        print(f"📥 Загрузка: {v_url}")
        ydl_opts = {'format': 'best[height<=720]', 'outtmpl': f_raw, 'quiet': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([v_url])
        
        raw_size = os.path.getsize(f_raw) / (1024*1024)
        print(f"📦 Файл скачан. Размер: {raw_size:.1f} MB")

        # Субтитры
        mode_text = "🔊 Оригинал"
        if model:
            print("🎙 Whisper: Поиск речи...")
            res = model.transcribe(f_raw)
            if res.get('segments'):
                srt = ""
                for i, seg in enumerate(res['segments']):
                    s = time.strftime('%H:%M:%S,000', time.gmtime(seg['start']))
                    e = time.strftime('%H:%M:%S,000', time.gmtime(seg['end']))
                    txt = translator.translate(seg['text'])
                    srt += f"{i+1}\n{s} --> {e}\n{txt}\n\n"
                with open("subs.srt", "w", encoding="utf-8") as fs: fs.write(srt)
                mode_text = "🎥 С переводом"
                print("📝 Субтитры готовы.")

        # Решаем: сжимать или нет
        needs_subs = os.path.exists("subs.srt")
        if raw_size > 48 or needs_subs:
            vf = "subtitles=subs.srt" if needs_subs else "scale=trunc(iw/2)*2:trunc(ih/2)*2"
            print(f"🛠 Запуск FFmpeg (Сжатие/Субтитры)...")
            # Если файл маленький, просто вшиваем субтитры без жесткого сжатия
            if raw_size <= 48:
                subprocess.run(['ffmpeg', '-y', '-i', f_raw, '-vf', vf, '-c:a', 'copy', f_final], capture_output=True)
            else:
                compress_video_safe(f_raw, f_final)
            path_to_send = f_final if os.path.exists(f_final) else f_raw
        else:
            path_to_send = f_raw

        # Оформление
        t_ru = translator.translate(title).upper()
        # Извлекаем главные факты (первые предложения)
        d_ru = translator.translate(desc[:600])
        
        caption = (
            f"🚀 <b>{t_ru}</b>\n\n"
            f"🛰 <b>МИССИЯ:</b> {source_name}\n"
            f"📡 <b>СТАТУС:</b> {mode_text}\n"
            f"─────────────────────\n"
            f"🪐 <b>ИНФОРМАЦИОННАЯ СВОДКА:</b>\n\n"
            f"{d_ru[:500]}...\n\n"
            f"🔭 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
        )

        print("📤 Отправка в Telegram...")
        with open(path_to_send, 'rb') as v:
            requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo", 
                          files={"video": v}, data={"chat_id": CHANNEL_NAME, "caption": caption, "parse_mode": "HTML"}, timeout=300)
        return True
    except Exception as e:
        print(f"⚠️ Ошибка миссии: {e}")
        return False

async def main():
    print("🎬 [ЦУП] v111.0 'Galactic Insight' активирована...")
    if not os.path.exists(DB_FILE): open(DB_FILE, 'w').close()
    db = open(DB_FILE, 'r').read()

    SOURCES = [
        {'n': 'Роскосмос (РФ)', 'id': 'UCOm4M6L_L7xOovvS_I-k__A', 't': 'yt'},
        {'n': 'SpaceX', 'id': 'UC_MhefFv_XW3c66m7ZAnxHA', 't': 'yt'},
        {'n': 'ESA (Европа)', 'u': 'https://www.esa.int/rssfeed/Videos', 't': 'rss'},
        {'n': 'ESO (Чили)', 'u': 'https://www.eso.org/public/videos/feed/', 't': 'rss'},
        {'n': 'NASA JPL', 'id': 'UC99RW7X_XzM_C6P6z_pXlAw', 't': 'yt'}
    ]

    random.shuffle(SOURCES)
    # Поиск с начала 2025 года
    date_limit = "2025-01-01T00:00:00Z"

    for s in SOURCES:
        try:
            print(f"📡 Сканирую сектор: {s['n']}...")
            if s['t'] == 'yt' and YOUTUBE_API_KEY:
                url = f"https://www.googleapis.com/youtube/v3/search?key={YOUTUBE_API_KEY}&channelId={s['id']}&part=snippet,id&order=date&publishedAfter={date_limit}&maxResults=5&type=video"
                res = requests.get(url).json()
                items = res.get('items', [])
                print(f"🔍 Найдено видео: {len(items)}")
                for item in items:
                    v_id = item['id']['videoId']
                    if v_id not in db:
                        if await process_mission_v111(f"https://www.youtube.com/watch?v={v_id}", item['snippet']['title'], item['snippet']['description'], s['n']):
                            with open(DB_FILE, 'a') as f: f.write(f"\n{v_id}")
                            print("🎉 Миссия успешно завершена."); return
            
            elif s['t'] == 'rss':
                res = requests.get(s['u'], timeout=20)
                root = ET.fromstring(res.content)
                items = root.findall('.//item')
                print(f"🔍 Найдено в ленте: {len(items)}")
                for item in items[:5]:
                    link = item.find('link').text
                    if link not in db:
                        title = item.find('title').text
                        desc = item.find('description').text if item.find('description') is not None else ""
                        if await process_mission_v111(link, title, desc, s['n']):
                            with open(DB_FILE, 'a') as f: f.write(f"\n{link}")
                            print("🎉 Миссия успешно завершена."); return
        except Exception as e:
            print(f"⚠️ Сбой в секторе {s['n']}: {e}")
            continue

if __name__ == '__main__':
    asyncio.run(main())
