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
model = whisper.load_model("tiny")
VOICE_LIMIT = 600 

SOURCES = [
    {'n': 'SpaceX (Миссии)', 't': 'yt', 'id': 'UC_MhefFv_XW3c66m7ZAnxHA'},
    {'n': 'VideoFromSpace', 't': 'yt', 'id': 'UC6_OitvS-L0m_uVndA-K8lA'},
    {'n': 'NASA JPL', 't': 'yt', 'id': 'UC99RW7X_XzM_C6P6z_pXlAw'},
    {'n': 'Space.com', 't': 'rss', 'u': 'https://www.space.com/feeds/all'},
    {'n': 'Phys.org', 't': 'rss', 'u': 'https://phys.org/rss-feed/space-news/'},
    {'n': 'ESO (Европа)', 't': 'rss', 'u': 'https://www.eso.org/public/videos/feed/'},
    {'n': 'Hubble (Хаббл)', 't': 'rss', 'u': 'https://hubblesite.org/rss/news'},
    {'n': 'Universe Today', 't': 'rss', 'u': 'https://www.universetoday.com/feed/'},
    {'n': 'NASA (Архив)', 't': 'nasa_api'}
]

# ============================================================
# 🛠 МОДУЛЬ АБСОЛЮТНОЙ БЕЗОПАСНОСТИ (v45.0)
# ============================================================

def safe_translate(text):
    """Никогда не возвращает None и не падает на пустых данных"""
    if not text or not isinstance(text, str) or len(text.strip()) < 2:
        return ""
    try:
        res = translator.translate(text)
        return res if res else text
    except:
        return text

def super_clean(text):
    """Никогда не падает на NoneType"""
    if not text or not isinstance(text, str):
        return ""
    text = re.sub(r'<[^>]+>', '', text).replace('&', 'и')
    text = html.unescape(text)
    return html.escape(text).strip()

def clear_workspace():
    for f in ["input.mp4", "output.mp4", "subs.srt"]:
        if os.path.exists(f): 
            try: os.remove(f)
            except: pass

# ============================================================
# 🎬 МОНТАЖНЫЙ ОТСЕК
# ============================================================

async def process_video_v45(video_url):
    f_in, f_out = "input.mp4", "output.mp4"
    clear_workspace()
    try:
        ydl_opts = {'format': 'best[height<=720][ext=mp4]', 'outtmpl': f_in, 'quiet': True, 'noplaylist': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            if not info: return None, "error"
        
        # Транскрибация
        res = model.transcribe(f_in)
        segments = res.get('segments', [])
        
        if segments and len(segments) > 0:
            srt_data = ""
            for i, seg in enumerate(segments):
                s = time.strftime('%H:%M:%S,000', time.gmtime(seg['start']))
                e = time.strftime('%H:%M:%S,000', time.gmtime(seg['end']))
                txt = safe_translate(seg.get('text', ''))
                if txt: srt_data += f"{i+1}\n{s} --> {e}\n{txt}\n\n"
            
            if srt_data:
                with open("subs.srt", "w", encoding="utf-8") as f: f.write(srt_data)
                # Вшиваем субтитры
                cmd = ["ffmpeg", "-y", "-i", f_in, "-vf", "subtitles=subs.srt", "-c:a", "copy", f_out]
                subprocess.run(cmd, check=True, capture_output=True)
                return f_out, "subs"
        
        return f_in, "original"
    except Exception as e:
        print(f"⚠️ Ошибка в отсеке монтажа: {e}")
        return None, "error"

# ============================================================
# 🛰 ГЛАВНЫЙ ЦИКЛ
# ============================================================

async def main():
    print("🎬 [ЦУП] v45.0 'Interstellar Resilience' активирована...")
    
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r') as f: lines = [l.strip() for l in f.readlines() if l.strip()]
        if len(lines) > 150:
            with open(DB_FILE, 'w') as f: f.write("\n".join(lines[-80:]))

    db = open(DB_FILE, 'r').read() if os.path.exists(DB_FILE) else ""
    pool = SOURCES.copy()
    random.shuffle(pool)

    for s in pool:
        try:
            print(f"📡 Сканирование горизонта событий: {s['n']}...")
            video_list = []
            
            if s['t'] == 'nasa_api':
                try:
                    res = requests.get(f"https://images-api.nasa.gov/search?q=space&media_type=video").json()
                    for item in res['collection']['items'][:5]:
                        data = item.get('data', [{}])[0]
                        v_id = data.get('nasa_id')
                        if not v_id or f"nasa_{v_id}" in db: continue
                        assets = requests.get(f"https://images-api.nasa.gov/asset/{v_id}").json()
                        v_url = next(a['href'] for a in assets['collection']['items'] if '~medium.mp4' in a['href'])
                        video_list.append({'url': v_url, 'title': data.get('title', 'NASA News'), 'desc': data.get('description', ''), 'id': f"nasa_{v_id}"})
                        break
                except: continue
            else:
                url_f = s['u'] if 'u' in s else f"https://www.youtube.com/feeds/videos.xml?channel_id={s['id']}"
                res = requests.get(url_f, headers=HEADERS, timeout=25)
                try:
                    root = ET.fromstring(res.content)
                except:
                    print(f"❌ Сектор {s['n']} недоступен (XML Error).")
                    continue

                items = root.findall('.//item') or root.findall('{http://www.w3.org/2005/Atom}entry')
                for item in items[:5]:
                    l_node = item.find('link')
                    link = l_node.text if l_node is not None and l_node.text else l_node.get('href') if l_node is not None else ""
                    if not link or link in db: continue
                    
                    t_node = item.find('title') or item.find('{http://www.w3.org/2005/Atom}title')
                    title = t_node.text if t_node is not None else "НОВОСТИ КОСМОСА"
                    
                    d_node = item.find('description') or item.find('{http://www.w3.org/2005/Atom}summary')
                    desc = d_node.text if d_node is not None else ""
                    
                    video_list.append({'url': link, 'title': title, 'desc': desc, 'id': link})
                    break

            for v in video_list:
                path, mode = await process_video_v45(v['url'])
                if not path or mode == "error":
                    with open(DB_FILE, 'a') as f: f.write(f"\n{v['id']}")
                    continue
                
                # Финальная сборка текста (v45.0 защита от None)
                clean_title = super_clean(safe_translate(v['title']).upper())
                if not clean_title: clean_title = "КОСМИЧЕСКИЙ РЕПОРТАЖ"
                
                clean_desc = super_clean(safe_translate(v['desc']))
                status = "🎬 Видео с субтитрами" if mode == "subs" else "🔊 Оригинальный звук"
                
                caption = (
                    f"🚀 <b>{clean_title}</b>\n\n"
                    f"🛰 <b>Миссия:</b> {s['n']}\n"
                    f"🎬 <b>Формат:</b> {status}\n"
                    f"─────────────────────\n"
                    f"🪐 <b>ИНФОРМАЦИОННАЯ СВОДКА:</b>\n\n"
                    f"{clean_desc[:500]}...\n\n"
                    f"✨ <i>Вселенная ждет своих исследователей!</i>\n"
                    f"🔭 <a href='https://t.me/vladislav_space'>Подписаться на Дневник</a>"
                )

                with open(path, 'rb') as f_v:
                    r = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo", files={"video": f_v}, data={"chat_id": CHANNEL_NAME, "caption": caption, "parse_mode": "HTML"}, timeout=300)
                
                if r.status_code == 200:
                    with open(DB_FILE, 'a') as f: f.write(f"\n{v['id']}")
                    print(f"🎉 Миссия выполнена: {v['id'][:15]}"); return
        except Exception as e:
            print(f"⚠️ Сбой сектора: {e}")
            continue

if __name__ == '__main__':
    asyncio.run(main())
