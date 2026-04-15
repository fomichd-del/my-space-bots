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
# ⚙️ НАСТРОЙКИ
# ============================================================
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHANNEL_NAME   = '@vladislav_space'
DB_FILE        = "last_video_date.txt"

translator = GoogleTranslator(source='auto', target='ru')

try:
    model = whisper.load_model("tiny")
except:
    model = None

# ============================================================
# 🛠 СИСТЕМЫ ЖИЗНЕОБЕСПЕЧЕНИЯ
# ============================================================

def safe_translate(text):
    if not text or len(str(text)) < 5: return str(text) if text else ""
    try: return translator.translate(str(text))
    except: return str(text)

def super_clean(text):
    if not text: return ""
    text = re.sub(r'http\S+', '', str(text)) 
    text = re.sub(r'<[^>]+>', '', text)      
    try: text = html.unescape(text)
    except: pass
    return html.escape(text).strip()

# ============================================================
# 🎬 МОНТАЖНЫЙ ЦЕХ (v85.0 - ГИБКАЯ ЗАГРУЗКА)
# ============================================================

async def process_video(video_url):
    print(f"🎬 [МОНТАЖ] Захват цели: {video_url}")
    f_in, f_out = "input.mp4", "output.mp4"
    for f in [f_in, f_out, "subs.srt"]:
        if os.path.exists(f): os.remove(f)

    try:
        # Настройки для обхода блокировок YouTube на Actions
        ydl_opts = {
            'format': 'best[height<=720][ext=mp4]', 
            'outtmpl': f_in, 
            'quiet': True, 
            'noplaylist': True,
            'nocheckcertificate': True,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
        
        if not os.path.exists(f_in) or os.path.getsize(f_in) < 20000: return None, "error"

        if model:
            print("🎙 Генерирую русские субтитры...")
            res = model.transcribe(f_in)
            segments = res.get('segments', [])
            if segments:
                srt_data = ""
                for i, seg in enumerate(segments):
                    s = time.strftime('%H:%M:%S,000', time.gmtime(seg.get('start', 0)))
                    e = time.strftime('%H:%M:%S,000', time.gmtime(seg.get('end', 0)))
                    txt = safe_translate(seg.get('text', ''))
                    if txt: srt_data += f"{i+1}\n{s} --> {e}\n{txt}\n\n"
                
                if srt_data:
                    with open("subs.srt", "w", encoding="utf-8") as fs: fs.write(srt_data)
                    subprocess.run(["ffmpeg", "-y", "-i", f_in, "-vf", "subtitles=subs.srt:force_style='FontSize=18,OutlineColour=&H000000,BorderStyle=1'", "-c:a", "copy", f_out], capture_output=True)
                    if os.path.exists(f_out): return f_out, "subs"
        
        return f_in, "original"
    except Exception as e:
        print(f"⚠️ Ошибка загрузки: {e}")
        return None, "error"

# ============================================================
# 🛰 ГЛАВНЫЙ ЦИКЛ (ГИБРИДНЫЙ ПОИСК)
# ============================================================

async def main():
    print("🚀 [ЦУП] v85.0 'Cosmic Hybrid' запущен...")
    if not os.path.exists(DB_FILE): open(DB_FILE, 'w').close()
    db = open(DB_FILE, 'r').read()

    # Смешанные источники: YouTube + Прямые ленты
    SOURCES = [
        {'n': 'SpaceX (YouTube)', 'u': 'https://www.youtube.com/feeds/videos.xml?channel_id=UC_MhefFv_XW3c66m7ZAnxHA', 't': 'yt'},
        {'n': 'ESA Multimedia', 'u': 'https://www.esa.int/rssfeed/Videos', 't': 'rss_video'},
        {'n': 'NASA JPL (YouTube)', 'u': 'https://www.youtube.com/feeds/videos.xml?channel_id=UC99RW7X_XzM_C6P6z_pXlAw', 't': 'yt'},
        {'n': 'ESO Science (Direct)', 'u': 'https://www.eso.org/public/videos/feed/', 't': 'rss_video'},
        {'n': 'NASA Image (API)', 'u': 'nasa_api', 't': 'api'}
    ]

    random.shuffle(SOURCES)

    for s in SOURCES:
        try:
            print(f"📡 Сектор: {s['n']}...")
            video_list = []

            if s['t'] == 'api':
                res = requests.get(f"https://images-api.nasa.gov/search?q=mars&media_type=video").json()
                item = random.choice(res['collection']['items'][:5])
                v_id = item['data'][0]['nasa_id']
                if v_id not in db:
                    assets = requests.get(f"https://images-api.nasa.gov/asset/{v_id}").json()
                    v_url = next(a['href'] for a in assets['collection']['items'] if '~medium.mp4' in a['href'])
                    video_list.append({'url': v_url, 'title': item['data'][0]['title'], 'desc': item['data'][0].get('description', ''), 'id': v_id})

            else:
                res = requests.get(s['u'], timeout=30)
                root = ET.fromstring(res.content)
                items = root.findall('.//item') or root.findall('{http://www.w3.org/2005/Atom}entry')
                
                for item in items[:3]:
                    link = ""
                    # Пытаемся найти ссылку для YouTube (Atom) или RSS
                    l_node = item.find('{http://www.w3.org/2005/Atom}link')
                    link = l_node.get('href', '') if l_node is not None else (item.find('link').text if item.find('link') is not None else "")
                    
                    if not link or link in db: continue

                    title = (item.find('title') or item.find('{http://www.w3.org/2005/Atom}title')).text
                    desc_node = (item.find('description') or item.find('{http://www.w3.org/2005/Atom}summary'))
                    desc = desc_node.text if desc_node is not None else ""

                    # Для RSS проверяем наличие прямой ссылки на видео
                    if s['t'] == 'rss_video':
                        encl = item.find('enclosure')
                        if encl is not None: link = encl.get('url')

                    video_list.append({'url': link, 'title': title, 'desc': desc, 'id': link})
                    break

            for v in video_list:
                path, mode = await process_video(v['url'])
                if not path: continue

                t_ru = super_clean(safe_translate(v['title']).upper())
                d_ru = super_clean(safe_translate(v['desc'][:1200]))
                status = "🎬 Видео с субтитрами" if mode == "subs" else "🔊 Оригинальный звук"

                caption = (
                    f"⭐ <b>{t_ru}</b>\n\n"
                    f"🛰 <b>МИССИЯ:</b> {s['n']}\n"
                    f"📝 <b>ФОРМАТ:</b> {status}\n"
                    f"─────────────────────\n"
                    f"🪐 <b>ИНФОРМАЦИЯ:</b>\n\n"
                    f"{d_ru[:550]}...\n\n"
                    f"✨ <i>Границы Вселенной расширяются прямо сейчас!</i>\n"
                    f"🔭 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
                )

                with open(path, 'rb') as f_v:
                    r = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo", 
                                    files={"video": f_v}, 
                                    data={"chat_id": CHANNEL_NAME, "caption": caption, "parse_mode": "HTML"}, timeout=300)
                
                if r.status_code == 200:
                    with open(DB_FILE, 'a') as f: f.write(f"\n{v['id']}")
                    print("🎉 УСПЕХ! Пост опубликован."); return

        except Exception as e:
            print(f"⚠️ Сбой: {e}")
            continue

if __name__ == '__main__':
    asyncio.run(main())
