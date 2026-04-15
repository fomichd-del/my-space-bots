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

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'}

translator = GoogleTranslator(source='auto', target='ru')
model = whisper.load_model("tiny")
VOICE_LIMIT = 600 

SOURCES = [
    {'n': 'SpaceX (Маск)', 't': 'yt', 'id': 'UC_MhefFv_XW3c66m7ZAnxHA'},
    {'n': 'VideoFromSpace', 't': 'yt', 'id': 'UC6_OitvS-L0m_uVndA-K8lA'},
    {'n': 'NASA JPL', 't': 'yt', 'id': 'UC99RW7X_XzM_C6P6z_pXlAw'},
    {'n': 'Cosmos News', 't': 'yt', 'id': 'UCvWf7MIdV_9X9_pG_Q8Xzog'},
    {'n': 'Space.com', 't': 'rss', 'u': 'https://www.space.com/feeds/all'},
    {'n': 'Phys.org', 't': 'rss', 'u': 'https://phys.org/rss-feed/space-news/'},
    {'n': 'ESO (Европа)', 't': 'rss', 'u': 'https://www.eso.org/public/videos/feed/'},
    {'n': 'Hubble (Хаббл)', 't': 'rss', 'u': 'https://hubblesite.org/rss/news'},
    {'n': 'Universe Today', 't': 'rss', 'u': 'https://www.universetoday.com/feed/'},
    {'n': 'NASA (Архив)', 't': 'nasa_api'}
]

# ============================================================
# 🛠 МОДУЛЬ БЕЗОПАСНОСТИ
# ============================================================

def safe_translate(text):
    if not text or len(str(text)) < 3: return text
    try: return translator.translate(str(text))
    except: return text

def super_clean(text):
    if not text: return ""
    text = re.sub(r'<[^>]+>', '', str(text)).replace('&', 'и')
    return html.escape(html.unescape(text)).strip()

def get_node_text(item, tags, default="Без названия"):
    """Безопасно ищет текст в XML узлах"""
    for tag in tags:
        node = item.find(tag)
        if node is not None and (node.text or node.get('href')):
            return node.text if node.text else node.get('href')
    return default

def clear_workspace():
    for f in ["input.mp4", "output.mp4", "subs.srt"]:
        if os.path.exists(f): 
            try: os.remove(f)
            except: pass

# ============================================================
# 🎬 ОБРАБОТКА ВИДЕО ( v43.0 )
# ============================================================

async def process_video_v43(video_url):
    f_in, f_out = "input.mp4", "output.mp4"
    clear_workspace()
    try:
        ydl_opts = {'format': 'best[height<=720][ext=mp4]', 'outtmpl': f_in, 'quiet': True, 'noplaylist': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            if not info: return None, "error"
        
        # Генерация субтитров
        res = model.transcribe(f_in)
        segments = res.get('segments', [])
        
        if segments:
            # Создаем SRT
            srt_data = ""
            for i, seg in enumerate(segments):
                s = time.strftime('%H:%M:%S,000', time.gmtime(seg['start']))
                e = time.strftime('%H:%M:%S,000', time.gmtime(seg['end']))
                txt = safe_translate(seg.get('text', '').strip())
                srt_data += f"{i+1}\n{s} --> {e}\n{txt}\n\n"
            
            with open("subs.srt", "w", encoding="utf-8") as f: f.write(srt_data)
            
            # Вшиваем субтитры (Белый текст, черная обводка)
            cmd = [
                "ffmpeg", "-y", "-i", f_in, 
                "-vf", "subtitles=subs.srt:force_style='FontSize=18,PrimaryColour=&HFFFFFF,OutlineColour=&H000000,BorderStyle=1,Outline=1'", 
                "-c:a", "copy", f_out
            ]
            subprocess.run(cmd, check=True, capture_output=True)
            return f_out, "subs"
        
        return f_in, "original"
    except Exception as e:
        print(f"⚠️ Ошибка обработки: {e}")
        return None, "error"

# ============================================================
# 🛰 ГЛАВНЫЙ ЗАПУСК
# ============================================================

async def main():
    print("🎬 [ЦУП] v43.0 'Nebula Nova' активирована...")
    
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r') as f: lines = [l.strip() for l in f.readlines() if l.strip()]
        if len(lines) > 150:
            with open(DB_FILE, 'w') as f: f.write("\n".join(lines[-100:]))

    db = open(DB_FILE, 'r').read() if os.path.exists(DB_FILE) else ""
    pool = SOURCES.copy()
    random.shuffle(pool)

    for s in pool:
        try:
            print(f"📡 Сектор: {s['n']}...")
            video_list = []
            
            if s['t'] == 'nasa_api':
                res = requests.get(f"https://images-api.nasa.gov/search?q=space&media_type=video").json()
                items = res.get('collection', {}).get('items', [])
                for item in items[:5]:
                    data = item.get('data', [{}])[0]
                    v_id = data.get('nasa_id')
                    if not v_id or f"nasa_{v_id}" in db: continue
                    assets = requests.get(f"https://images-api.nasa.gov/asset/{v_id}").json()
                    v_url = next((a['href'] for a in assets['collection']['items'] if '~medium.mp4' in a['href']), None)
                    if v_url:
                        video_list.append({'url': v_url, 'title': data.get('title', 'NASA News'), 'desc': data.get('description', ''), 'id': f"nasa_{v_id}"})
                        break
            else:
                url_f = s['u'] if 'u' in s else f"https://www.youtube.com/feeds/videos.xml?channel_id={s['id']}"
                res = requests.get(url_f, headers=HEADERS, timeout=25)
                root = ET.fromstring(res.content)
                items = root.findall('.//item') or root.findall('{http://www.w3.org/2005/Atom}entry')
                for item in items[:5]:
                    link = get_node_text(item, ['link', '{http://www.w3.org/2005/Atom}link'])
                    if not link or link in db: continue
                    
                    title = get_node_text(item, ['title', '{http://www.w3.org/2005/Atom}title'], "Космическое событие")
                    desc = get_node_text(item, ['description', '{http://www.w3.org/2005/Atom}summary', '{http://www.w3.org/2005/Atom}content'], "")
                    
                    video_list.append({'url': link, 'title': title, 'desc': desc, 'id': link})
                    break

            for v in video_list:
                path, mode = await process_video_v43(v['url'])
                if not path or mode == "error":
                    with open(DB_FILE, 'a') as f: f.write(f"\n{v['id']}")
                    continue
                
                t_ru = super_clean(safe_translate(v['title']).upper())
                d_ru = super_clean(safe_translate(v['desc'][:900]))
                
                # ЯРКОЕ И КАЧЕСТВЕННОЕ ОПИСАНИЕ (v43.0)
                caption = (
                    f"🚀 <b>{t_ru}</b>\n\n"
                    f"🛰 <b>Миссия:</b> {s['n']}\n"
                    f"🎬 <b>Формат:</b> Видео с русскими субтитрами\n"
                    f"─────────────────────\n"
                    f"🪐 <b>ИНФОРМАЦИОННАЯ СВОДКА:</b>\n\n"
                    f"{d_ru[:500]}...\n\n"
                    f"✨ <i>Космос становится ближе с каждым кадром!</i>\n"
                    f"🔭 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
                )

                with open(path, 'rb') as f_v:
                    r = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo", files={"video": f_v}, data={"chat_id": CHANNEL_NAME, "caption": caption, "parse_mode": "HTML"}, timeout=300)
                
                if r.status_code == 200:
                    with open(DB_FILE, 'a') as f: f.write(f"\n{v['id']}")
                    print(f"🎉 Готово: {v['title']}"); return
        except Exception as e:
            print(f"⚠️ Ошибка сектора: {e}")
            continue

if __name__ == '__main__':
    asyncio.run(main())
