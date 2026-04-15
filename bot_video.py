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

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}

translator = GoogleTranslator(source='auto', target='ru')
# Загружаем модель один раз при старте
try:
    model = whisper.load_model("tiny")
except:
    model = None

# ============================================================
# 🛠 УТИЛИТЫ ВЫЖИВАНИЯ
# ============================================================

def safe_translate(text):
    if not text or len(str(text)) < 3: return str(text) if text else ""
    try: return translator.translate(str(text))
    except: return str(text)

def super_clean(text):
    if not text: return ""
    text = re.sub(r'<[^>]+>', '', str(text))
    return html.escape(html.unescape(text)).strip()

def get_xml_text(node, tag_name, default=""):
    """Безопасное извлечение текста из XML"""
    if node is None: return default
    try:
        res = node.find(tag_name)
        if res is not None and res.text: return res.text
        # Поиск с учетом пространств имен (для YouTube)
        res = node.find(f"{{http://www.w3.org/2005/Atom}}{tag_name}")
        if res is not None and res.text: return res.text
    except: pass
    return default

# ============================================================
# 🎬 ОБРАБОТКА ВИДЕО
# ============================================================

async def process_video(video_url):
    f_in, f_out = "input.mp4", "output.mp4"
    for f in [f_in, f_out, "subs.srt"]:
        if os.path.exists(f): os.remove(f)

    try:
        ydl_opts = {'format': 'best[height<=720][ext=mp4]', 'outtmpl': f_in, 'quiet': True, 'noplaylist': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
        
        if not os.path.exists(f_in) or os.path.getsize(f_in) < 10000: return None, "error"

        # Пытаемся сделать субтитры, если модель загружена
        if model:
            res = model.transcribe(f_in)
            segments = res.get('segments', [])
            if segments:
                srt = ""
                for i, seg in enumerate(segments):
                    s = time.strftime('%H:%M:%S,000', time.gmtime(seg['start']))
                    e = time.strftime('%H:%M:%S,000', time.gmtime(seg['end']))
                    txt = safe_translate(seg['text'])
                    srt += f"{i+1}\n{s} --> {end}\n{txt}\n\n"
                with open("subs.srt", "w", encoding="utf-8") as f: f.write(srt)
                
                # Накладываем титры (упрощенно для стабильности)
                subprocess.run(["ffmpeg", "-y", "-i", f_in, "-vf", "subtitles=subs.srt", "-c:a", "copy", f_out], capture_output=True)
                if os.path.exists(f_out): return f_out, "subs"
        
        return f_in, "original"
    except:
        return f_in if os.path.exists(f_in) else None, "original"

# ============================================================
# 🛰 ГЛАВНАЯ МИССИЯ
# ============================================================

async def main():
    print("🚀 [ЦУП] v50.0 'Supernova Final' запущена...")
    
    # Инициализация БД
    if not os.path.exists(DB_FILE): open(DB_FILE, 'w').close()
    db = open(DB_FILE, 'r').read()

    SOURCES = [
        {'n': 'SpaceX News', 'u': 'https://www.youtube.com/feeds/videos.xml?channel_id=UC_MhefFv_XW3c66m7ZAnxHA'},
        {'n': 'NASA JPL', 'u': 'https://www.youtube.com/feeds/videos.xml?channel_id=UC99RW7X_XzM_C6P6z_pXlAw'},
        {'n': 'Space.com', 'u': 'https://www.space.com/feeds/all'},
        {'n': 'ESA (Европа)', 'u': 'https://www.esa.int/rssfeed/Videos'},
        {'n': 'ESO (Наука)', 'u': 'https://www.eso.org/public/videos/feed/'}
    ]

    random.shuffle(SOURCES)

    for s in SOURCES:
        try:
            print(f"📡 Проверка сектора: {s['n']}...")
            res = requests.get(s['u'], headers=HEADERS, timeout=20)
            if res.status_code != 200: continue
            
            root = ET.fromstring(res.content)
            items = root.findall('.//item') or root.findall('{http://www.w3.org/2005/Atom}entry')
            
            for item in items[:3]:
                # Ищем ссылку максимально гибко
                link = ""
                link_node = item.find('link')
                if link_node is not None:
                    link = link_node.text if link_node.text else link_node.get('href', '')
                
                if not link or link in db: continue

                title = get_xml_text(item, 'title', 'Космическое событие')
                desc = get_xml_text(item, 'description', '') or get_xml_text(item, 'summary', '')

                # ОБРАБОТКА
                path, mode = await process_video(link)
                if not path: continue

                # ПЕРЕВОД И ОФОРМЛЕНИЕ
                t_ru = super_clean(safe_translate(title).upper())
                d_ru = super_clean(safe_translate(desc[:1000]))
                status = "🎬 Видео с субтитрами" if mode == "subs" else "🔈 Оригинальный звук"

                caption = (
                    f"⭐ <b>{t_ru}</b>\n\n"
                    f"🛰 <b>ИСТОЧНИК:</b> {s['n']}\n"
                    f"📝 <b>ФОРМАТ:</b> {status}\n"
                    f"─────────────────────\n"
                    f"🪐 <b>ИНФОРМАЦИЯ:</b>\n\n"
                    f"{d_ru[:500]}...\n\n"
                    f"🌌 <i>Изучай Вселенную вместе с нами!</i>\n"
                    f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
                )

                # ОТПРАВКА
                with open(path, 'rb') as f:
                    r = requests.post(
                        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo",
                        files={"video": f},
                        data={"chat_id": CHANNEL_NAME, "caption": caption, "parse_mode": "HTML"},
                        timeout=300
                    )
                
                if r.status_code == 200:
                    with open(DB_FILE, 'a') as db_f: db_f.write(f"\n{link}")
                    print("🎉 ПОБЕДА! Видео в канале."); return
                else:
                    print(f"❌ Ошибка Telegram: {r.text}")
        except Exception as e:
            print(f"⚠️ Сбой в секторе {s['n']}: {e}")
            continue

if __name__ == '__main__':
    asyncio.run(main())
