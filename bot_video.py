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
# ⚙️ НАСТРОЙКИ ЦУП
# ============================================================
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHANNEL_NAME   = '@vladislav_space'
DB_FILE        = "last_video_date.txt"

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'}

translator = GoogleTranslator(source='auto', target='ru')

# Загружаем нейронку (используем tiny для скорости на Actions)
try:
    model = whisper.load_model("tiny")
except Exception as e:
    print(f"⚠️ Ошибка загрузки Whisper: {e}")
    model = None

# ============================================================
# 🛠 МОДУЛИ ЗАЩИТЫ И ОБРАБОТКИ
# ============================================================

def safe_translate(text):
    if not text or len(str(text)) < 5: return str(text) if text else ""
    try: return translator.translate(str(text))
    except: return str(text)

def super_clean(text):
    if not text: return ""
    text = re.sub(r'<[^>]+>', '', str(text)) # Удаляем HTML теги
    try: text = html.unescape(text)
    except: pass
    return html.escape(text).strip()

async def process_video_final(video_url):
    """Скачивает видео и накладывает субтитры, если это возможно"""
    f_in, f_out = "input.mp4", "output.mp4"
    for f in [f_in, f_out, "subs.srt"]:
        if os.path.exists(f): os.remove(f)

    try:
        ydl_opts = {'format': 'best[height<=720][ext=mp4]', 'outtmpl': f_in, 'quiet': True, 'noplaylist': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Сначала проверяем, есть ли видео по ссылке
            check = ydl.extract_info(video_url, download=True)
            if not check: return None, "error"
        
        if not os.path.exists(f_in) or os.path.getsize(f_in) < 20000: return None, "error"

        # Пытаемся сделать субтитры
        if model:
            print("🎙 Транскрибация...")
            res = model.transcribe(f_in)
            segments = res.get('segments', [])
            if segments:
                srt_data = ""
                for i, seg in enumerate(segments):
                    start_t = time.strftime('%H:%M:%S,000', time.gmtime(seg.get('start', 0)))
                    end_t = time.strftime('%H:%M:%S,000', time.gmtime(seg.get('end', 0)))
                    txt = safe_translate(seg.get('text', ''))
                    if txt: srt_data += f"{i+1}\n{start_t} --> {end_t}\n{txt}\n\n"
                
                if srt_data:
                    with open("subs.srt", "w", encoding="utf-8") as f_s: f_s.write(srt_data)
                    # Вшиваем субтитры (самым надежным способом)
                    subprocess.run(["ffmpeg", "-y", "-i", f_in, "-vf", "subtitles=subs.srt", "-c:a", "copy", f_out], capture_output=True)
                    if os.path.exists(f_out): return f_out, "subs"
        
        return f_in, "original"
    except Exception as e:
        print(f"⚠️ Сбой монтажа: {e}")
        return (f_in if os.path.exists(f_in) else None), "original"

# ============================================================
# 🛰 ГЛАВНЫЙ ЦИКЛ
# ============================================================

async def main():
    print("🎬 [ЦУП] v60.0 'Event Horizon' запущена...")
    
    if not os.path.exists(DB_FILE): open(DB_FILE, 'w').close()
    db = open(DB_FILE, 'r').read()

    SOURCES = [
        {'n': 'SpaceX (Запуски)', 'u': 'https://www.youtube.com/feeds/videos.xml?channel_id=UC_MhefFv_XW3c66m7ZAnxHA'},
        {'n': 'NASA JPL (Марсоходы)', 'u': 'https://www.youtube.com/feeds/videos.xml?channel_id=UC99RW7X_XzM_C6P6z_pXlAw'},
        {'n': 'NASA (События)', 'u': 'https://www.youtube.com/feeds/videos.xml?channel_id=UCOpNcN46zbL++h_Z270F9iQ'},
        {'n': 'Space.com (Новости)', 'u': 'https://www.space.com/feeds/all'},
        {'n': 'ESA (Европа)', 'u': 'https://www.esa.int/rssfeed/Videos'}
    ]

    random.shuffle(SOURCES)

    for s in SOURCES:
        try:
            print(f"📡 Проверка: {s['n']}...")
            res = requests.get(s['u'], headers=HEADERS, timeout=30)
            if res.status_code != 200: continue
            
            root = ET.fromstring(res.content)
            # Ищем айтемы и в RSS, и в Atom (YouTube)
            items = root.findall('.//item') or root.findall('{http://www.w3.org/2005/Atom}entry')
            
            for item in items[:5]:
                # Ищем ссылку максимально безопасно
                link = ""
                l_node = item.find('{http://www.w3.org/2005/Atom}link')
                if l_node is not None: link = l_node.get('href', '')
                if not link:
                    l_node = item.find('link')
                    if l_node is not None: link = l_node.text if l_node.text else l_node.get('href', '')

                if not link or link in db: continue

                # ПРОВЕРКА ЗАГОЛОВКА И ОПИСАНИЯ
                t_node = item.find('title') or item.find('{http://www.w3.org/2005/Atom}title')
                title = t_node.text if t_node is not None else "Новое открытие"
                
                d_node = item.find('description') or item.find('{http://www.w3.org/2005/Atom}summary')
                desc = d_node.text if d_node is not None else ""

                # ЗАПУСК ОБРАБОТКИ
                path, mode = await process_video_final(link)
                if not path:
                    # Если ссылка не видео или битая — помечаем, чтобы не возвращаться
                    with open(DB_FILE, 'a') as db_f: db_f.write(f"\n{link}")
                    continue

                # ОФОРМЛЕНИЕ ТЕКСТА
                t_ru = super_clean(safe_translate(title).upper())
                d_ru = super_clean(safe_translate(desc[:1200]))
                status = "🎬 С переводом" if mode == "subs" else "🔈 Оригинал"

                caption = (
                    f"⭐ <b>{t_ru}</b>\n\n"
                    f"🛰 <b>ИСТОЧНИК:</b> {s['n']}\n"
                    f"📝 <b>СТАТУС:</b> {status}\n"
                    f"─────────────────────\n"
                    f"🪐 <b>ИНФОРМАЦИОННАЯ СВОДКА:</b>\n\n"
                    f"{d_ru[:550]}...\n\n"
                    f"🌌 <i>Тайны Вселенной в каждом кадре!</i>\n"
                    f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
                )

                # ОТПРАВКА В TELEGRAM
                with open(path, 'rb') as f_v:
                    r = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo", 
                                    files={"video": f_v}, 
                                    data={"chat_id": CHANNEL_NAME, "caption": caption, "parse_mode": "HTML"}, 
                                    timeout=300)
                
                if r.status_code == 200:
                    with open(DB_FILE, 'a') as db_f: db_f.write(f"\n{link}")
                    print(f"🎉 ПОБЕДА! Видео {title} отправлено."); return
                else:
                    print(f"❌ Ошибка Telegram: {r.text}")

        except Exception as e:
            print(f"⚠️ Ошибка в секторе {s['n']}: {e}")
            continue

if __name__ == '__main__':
    asyncio.run(main())
