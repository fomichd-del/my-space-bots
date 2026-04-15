import requests
import os
import random
import time
import xml.etree.ElementTree as ET
import subprocess
import whisper
import yt_dlp
import asyncio
import html
import re
from deep_translator import GoogleTranslator

# ============================================================
# ⚙️ НАСТРОЙКИ
# ============================================================
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHANNEL_NAME   = '@vladislav_space'
DB_FILE        = "last_video_date.txt"

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'}

translator = GoogleTranslator(source='auto', target='ru')
try:
    model = whisper.load_model("tiny")
except:
    model = None

# ============================================================
# 🛠 УТИЛИТЫ
# ============================================================

def safe_translate(text):
    if not text or len(str(text)) < 2: return str(text) if text else ""
    try: return translator.translate(str(text))
    except: return str(text)

def super_clean(text):
    if not text: return ""
    text = re.sub(r'<[^>]+>', '', str(text))
    try: text = html.unescape(text)
    except: pass
    return html.escape(text).strip()

# ============================================================
# 🎬 ОБРАБОТКА С ПОДРОБНЫМ ОТЧЕТОМ
# ============================================================

async def process_video(video_url):
    print(f"🎬 [МОНТАЖ] Пытаюсь захватить видео: {video_url}")
    f_in, f_out = "input.mp4", "output.mp4"
    for f in [f_in, f_out, "subs.srt"]:
        if os.path.exists(f): os.remove(f)

    try:
        ydl_opts = {'format': 'best[height<=720][ext=mp4]', 'outtmpl': f_in, 'quiet': True, 'noplaylist': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
        
        if not os.path.exists(f_in):
            print("❌ [ОШИБКА] Файл не скачался.")
            return None, "error"
            
        print(f"📦 [УСПЕХ] Видео скачано. Размер: {os.path.getsize(f_in)} байт")

        if model:
            print("🎙 [WHISPER] Начинаю поиск речи для субтитров...")
            res = model.transcribe(f_in)
            segments = res.get('segments', [])
            if segments:
                print(f"📝 [WHISPER] Найдено сегментов: {len(segments)}")
                srt = ""
                for i, seg in enumerate(segments):
                    s = time.strftime('%H:%M:%S,000', time.gmtime(seg.get('start', 0)))
                    e = time.strftime('%H:%M:%S,000', time.gmtime(seg.get('end', 0)))
                    txt = safe_translate(seg.get('text', ''))
                    srt += f"{i+1}\n{s} --> {e}\n{txt}\n\n"
                
                with open("subs.srt", "w", encoding="utf-8") as f_s: f_s.write(srt)
                subprocess.run(["ffmpeg", "-y", "-i", f_in, "-vf", "subtitles=subs.srt", "-c:a", "copy", f_out], capture_output=True)
                if os.path.exists(f_out): return f_out, "subs"
        
        return f_in, "original"
    except Exception as e:
        print(f"⚠️ [СБОЙ МОНТАЖА] {e}")
        return (f_in if os.path.exists(f_in) else None), "original"

# ============================================================
# 🛰 ГЛАВНЫЙ ЦИКЛ (DEBUG MODE)
# ============================================================

async def main():
    print("🚀 [ЦУП] v53.0 'Void Walker' запущена...")
    if not os.path.exists(DB_FILE): open(DB_FILE, 'w').close()
    db = open(DB_FILE, 'r').read()

    SOURCES = [
        {'n': 'SpaceX', 'u': 'https://www.youtube.com/feeds/videos.xml?channel_id=UC_MhefFv_XW3c66m7ZAnxHA'},
        {'n': 'NASA JPL', 'u': 'https://www.youtube.com/feeds/videos.xml?channel_id=UC99RW7X_XzM_C6P6z_pXlAw'},
        {'n': 'Space.com', 'u': 'https://www.space.com/feeds/all'},
        {'n': 'ESA', 'u': 'https://www.esa.int/rssfeed/Videos'}
    ]

    random.shuffle(SOURCES)

    for s in SOURCES:
        try:
            print(f"📡 --- СЕКТОР: {s['n']} ---")
            res = requests.get(s['u'], headers=HEADERS, timeout=25)
            root = ET.fromstring(res.content)
            items = root.findall('.//item') or root.findall('{http://www.w3.org/2005/Atom}entry')
            
            print(f"🔍 Найдено объектов в ленте: {len(items)}")

            for item in items[:5]:
                link = ""
                l_node = item.find('{http://www.w3.org/2005/Atom}link')
                if l_node is not None: link = l_node.get('href', '')
                if not link:
                    l_node = item.find('link')
                    if l_node is not None: link = l_node.text if l_node.text else l_node.get('href', '')

                if not link:
                    print("⏭ Пропуск: Ссылка не найдена в узле.")
                    continue

                if link in db:
                    print(f"⏭ Пропуск: Ссылка уже есть в базе ({link[:40]}...)")
                    continue

                print(f"🎯 ЦЕЛЬ ОБНАРУЖЕНА: {link}")

                # ПОПЫТКА ОБРАБОТКИ
                path, mode = await process_video(link)
                
                if not path:
                    print("⏭ Пропуск: Видео не удалось обработать.")
                    with open(DB_FILE, 'a') as db_f: db_f.write(f"\n{link}")
                    continue

                title_node = item.find('title') or item.find('{http://www.w3.org/2005/Atom}title')
                title = title_node.text if title_node is not None else "Космический репортаж"

                caption = (
                    f"⭐ <b>{super_clean(safe_translate(title)).upper()}</b>\n\n"
                    f"🛰 <b>ИСТОЧНИК:</b> {s['n']}\n"
                    f"─────────────────────\n"
                    f"✨ <i>Новое открытие в нашем объективе!</i>\n"
                    f"🔭 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
                )

                print("📤 Отправка в Telegram...")
                with open(path, 'rb') as f_v:
                    r = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo", files={"video": f_v}, data={"chat_id": CHANNEL_NAME, "caption": caption, "parse_mode": "HTML"}, timeout=300)
                
                if r.status_code == 200:
                    with open(DB_FILE, 'a') as db_f: db_f.write(f"\n{link}")
                    print(f"🎉 МИССИЯ ВЫПОЛНЕНА! Пост в канале.")
                    return
                else:
                    print(f"❌ ОШИБКА TELEGRAM: {r.text}")

        except Exception as e:
            print(f"⚠️ ОШИБКА СЕКТОРА {s['n']}: {e}")
            continue

if __name__ == '__main__':
    asyncio.run(main())
