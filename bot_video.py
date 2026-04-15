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

# Имитация живого пользователя для обхода блокировок
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'}

translator = GoogleTranslator(source='auto', target='ru')

# Инициализация Whisper (используем tiny для скорости)
try:
    model = whisper.load_model("tiny")
except Exception as e:
    print(f"⚠️ Ошибка Whisper: {e}")
    model = None

# ============================================================
# 🛠 ЗАЩИТНЫЕ МОДУЛИ (The "Armor" Block)
# ============================================================

def safe_translate(text):
    if not text or len(str(text)) < 3: return str(text) if text else ""
    try: return translator.translate(str(text))
    except: return str(text)

def super_clean(text):
    if not text: return ""
    # Удаляем HTML, лишние пробелы и исправляем спецсимволы
    text = re.sub(r'<[^>]+>', '', str(text))
    try: text = html.unescape(text)
    except: pass
    return html.escape(text).strip()

def get_xml_data(node, tags, attr=None):
    """Универсальный и безопасный поиск данных в XML (RSS/Atom)"""
    for tag in tags:
        # Ищем с учетом пространств имен (для YouTube)
        found = node.find(tag) or node.find(f"{{http://www.w3.org/2005/Atom}}{tag}")
        if found is not None:
            if attr: return found.get(attr, "")
            return found.text if found.text else ""
    return ""

# ============================================================
# 🎬 ОБРАБОТКА (Subtitles & Video)
# ============================================================

async def process_video(video_url):
    f_in, f_out = "input.mp4", "output.mp4"
    for f in [f_in, f_out, "subs.srt"]:
        if os.path.exists(f): os.remove(f)

    try:
        ydl_opts = {'format': 'best[height<=720][ext=mp4]', 'outtmpl': f_in, 'quiet': True, 'noplaylist': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
        
        if not os.path.exists(f_in) or os.path.getsize(f_in) < 15000: return None, "error"

        if model:
            print("🎙 Анализ аудиодорожки...")
            res = model.transcribe(f_in)
            segments = res.get('segments', [])
            if segments:
                srt_content = ""
                for i, seg in enumerate(segments):
                    # Жесткая проверка сегментов на NoneType (защита v65.0)
                    start = seg.get('start', 0)
                    end = seg.get('end', 0)
                    txt = safe_translate(seg.get('text', ''))
                    if not txt: continue
                    
                    s_fmt = time.strftime('%H:%M:%S,000', time.gmtime(start))
                    e_fmt = time.strftime('%H:%M:%S,000', time.gmtime(end))
                    srt_content += f"{i+1}\n{s_fmt} --> {e_fmt}\n{txt}\n\n"
                
                if srt_content:
                    with open("subs.srt", "w", encoding="utf-8") as f_s: f_s.write(srt_content)
                    # Вшиваем субтитры (белый текст с черной обводкой)
                    subprocess.run(["ffmpeg", "-y", "-i", f_in, "-vf", "subtitles=subs.srt:force_style='FontSize=18,OutlineColour=&H000000,BorderStyle=1'", "-c:a", "copy", f_out], capture_output=True)
                    if os.path.exists(f_out): return f_out, "subs"
        
        return f_in, "original"
    except Exception as e:
        print(f"⚠️ Ошибка монтажа: {e}")
        return (f_in if os.path.exists(f_in) else None), "original"

# ============================================================
# 🛰 ГЛАВНАЯ МИССИЯ
# ============================================================

async def main():
    print("🚀 [ЦУП] v65.0 'Universal Discovery' запущена...")
    if not os.path.exists(DB_FILE): open(DB_FILE, 'w').close()
    db = open(DB_FILE, 'r').read()

    SOURCES = [
        {'n': 'SpaceX (Миссии)', 'u': 'https://www.youtube.com/feeds/videos.xml?channel_id=UC_MhefFv_XW3c66m7ZAnxHA'},
        {'n': 'NASA JPL (Роверы)', 'u': 'https://www.youtube.com/feeds/videos.xml?channel_id=UC99RW7X_XzM_C6P6z_pXlAw'},
        {'n': 'NASA (События)', 'u': 'https://www.youtube.com/feeds/videos.xml?channel_id=UCOpNcN46zbL++h_Z270F9iQ'},
        {'n': 'ESA (Европа)', 'u': 'https://www.esa.int/rssfeed/Videos'},
        {'n': 'VideoFromSpace', 'u': 'https://www.youtube.com/feeds/videos.xml?channel_id=UC6_OitvS-L0m_uVndA-K8lA'}
    ]

    random.shuffle(SOURCES)

    for s in SOURCES:
        try:
            print(f"📡 Сектор: {s['n']}...")
            res = requests.get(s['u'], headers=HEADERS, timeout=30)
            root = ET.fromstring(res.content)
            items = root.findall('.//item') or root.findall('{http://www.w3.org/2005/Atom}entry')
            
            for item in items[:5]:
                # Ищем ссылку (в YouTube это href, в RSS это текст)
                link = get_xml_data(item, ['link'], attr='href') or get_xml_data(item, ['link'])
                
                if not link or link in db: continue

                # ЗАПУСК ОБРАБОТКИ
                path, mode = await process_video(link)
                if not path:
                    with open(DB_FILE, 'a') as f: f.write(f"\n{link}")
                    continue

                # ОПИСАНИЕ (Качественное и яркое)
                raw_title = get_xml_data(item, ['title'])
                raw_desc = get_xml_data(item, ['description', 'summary'])

                title_ru = super_clean(safe_translate(raw_title).upper())
                desc_ru = super_clean(safe_translate(raw_desc[:1200]))
                status = "🎥 Перевод: Субтитры" if mode == "subs" else "🔊 Оригинальный звук"

                caption = (
                    f"⭐ <b>{title_ru}</b>\n\n"
                    f"🛰 <b>ИСТОЧНИК:</b> {s['n']}\n"
                    f"📝 <b>СТАТУС:</b> {status}\n"
                    f"─────────────────────\n"
                    f"🪐 <b>ИНФОРМАЦИЯ:</b>\n\n"
                    f"{desc_ru[:500]}...\n\n"
                    f"✨ <i>Космос — это бесконечное приключение!</i>\n"
                    f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
                )

                with open(path, 'rb') as f_v:
                    r = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo", 
                                    files={"video": f_v}, 
                                    data={"chat_id": CHANNEL_NAME, "caption": caption, "parse_mode": "HTML"}, 
                                    timeout=300)
                
                if r.status_code == 200:
                    with open(DB_FILE, 'a') as f: f.write(f"\n{link}")
                    print(f"🎉 ПОБЕДА! Видео отправлено в канал."); return
                else:
                    print(f"❌ Ошибка Telegram: {r.text}")
        except Exception as e:
            print(f"⚠️ Сбой в секторе {s['n']}: {e}")
            continue

if __name__ == '__main__':
    asyncio.run(main())
