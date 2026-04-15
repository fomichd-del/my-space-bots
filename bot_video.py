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

# Обновленный "стелс-заголовок"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
    'Accept': 'application/xml,text/xml,application/xhtml+xml,text/html;q=0.9,text/plain;q=0.8'
}

translator = GoogleTranslator(source='auto', target='ru')
model = whisper.load_model("tiny")
VOICE_LIMIT = 600 

SOURCES = [
    {'n': 'SpaceX (Запуски Илона)', 't': 'yt', 'id': 'UC_MhefFv_XW3c66m7ZAnxHA'},
    {'n': 'VideoFromSpace (Клипы)', 't': 'yt', 'id': 'UC6_OitvS-L0m_uVndA-K8lA'},
    {'n': 'NASA JPL (Технологии)', 't': 'yt', 'id': 'UC99RW7X_XzM_C6P6z_pXlAw'},
    {'n': 'Cosmos News (Дайджест)', 't': 'yt', 'id': 'UCvWf7MIdV_9X9_pG_Q8Xzog'},
    {'n': 'Space.com (Репортажи)', 't': 'rss', 'u': 'https://www.space.com/feeds/all'},
    {'n': 'Phys.org (Астрофизика)', 't': 'rss', 'u': 'https://phys.org/rss-feed/space-news/'},
    {'n': 'ESO (Европа)', 't': 'rss', 'u': 'https://www.eso.org/public/videos/feed/'},
    {'n': 'Hubble (Хаббл)', 't': 'rss', 'u': 'https://hubblesite.org/rss/news'},
    {'n': 'NASA (Архив)', 't': 'nasa_api'}
]

# ============================================================
# 🛠 ТЕХНИЧЕСКИЙ ОТСЕК
# ============================================================

def safe_translate(text):
    if not text or len(str(text)) < 3: return text
    try: return translator.translate(str(text))
    except: return text

def super_clean(text):
    if not text: return ""
    text = re.sub(r'<[^>]+>', '', str(text)).replace('&', 'и')
    return html.escape(html.unescape(text)).strip()

def clear_workspace():
    for f in ["input.mp4", "output.mp4", "subs.srt"]:
        if os.path.exists(f): 
            try: os.remove(f)
            except: pass

# ============================================================
# 🎬 ОБРАБОТКА ( v44.0 )
# ============================================================

async def process_video_v44(video_url):
    f_in, f_out = "input.mp4", "output.mp4"
    clear_workspace()
    try:
        ydl_opts = {'format': 'best[height<=720][ext=mp4]', 'outtmpl': f_in, 'quiet': True, 'noplaylist': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            if not info: return None, "error"
        
        # Субтитры через Whisper
        res = model.transcribe(f_in)
        segments = res.get('segments', [])
        
        if segments:
            srt_data = ""
            for i, seg in enumerate(segments):
                s = time.strftime('%H:%M:%S,000', time.gmtime(seg['start']))
                e = time.strftime('%H:%M:%S,000', time.gmtime(seg['end']))
                txt = safe_translate(seg.get('text', '').strip())
                srt_data += f"{i+1}\n{s} --> {e}\n{txt}\n\n"
            
            with open("subs.srt", "w", encoding="utf-8") as f: f.write(srt_data)
            
            # Вшиваем субтитры
            cmd = [
                "ffmpeg", "-y", "-i", f_in, 
                "-vf", "subtitles=subs.srt:force_style='FontSize=18,PrimaryColour=&HFFFFFF,OutlineColour=&H000000,BorderStyle=1,Outline=1'", 
                "-c:a", "copy", f_out
            ]
            subprocess.run(cmd, check=True, capture_output=True)
            return f_out, "subs"
        
        return f_in, "original"
    except Exception as e:
        print(f"⚠️ Сбой монтажа: {e}")
        return None, "error"

# ============================================================
# 🛰 ГЛАВНЫЙ ЦИКЛ
# ============================================================

async def main():
    print("🎬 [ЦУП] v44.0 'Stellar Aegis' активирована...")
    
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r') as f: lines = [l.strip() for l in f.readlines() if l.strip()]
        if len(lines) > 150:
            with open(DB_FILE, 'w') as f: f.write("\n".join(lines[-100:]))

    db = open(DB_FILE, 'r').read() if os.path.exists(DB_FILE) else ""
    pool = SOURCES.copy()
    random.shuffle(pool)

    for s in pool:
        try:
            print(f"📡 Сканирование сектора: {s['n']}...")
            video_list = []
            
            if s['t'] == 'nasa_api':
                try:
                    res = requests.get(f"https://images-api.nasa.gov/search?q=universe&media_type=video").json()
                    for item in res['collection']['items'][:5]:
                        v_id = item['data'][0]['nasa_id']
                        if f"nasa_{v_id}" in db: continue
                        assets = requests.get(f"https://images-api.nasa.gov/asset/{v_id}").json()
                        v_url = next(a['href'] for a in assets['collection']['items'] if '~medium.mp4' in a['href'])
                        video_list.append({'url': v_url, 'title': item['data'][0]['title'], 'desc': item['data'][0].get('description', ''), 'id': f"nasa_{v_id}"})
                        break
                except: continue
            else:
                url_f = s['u'] if 'u' in s else f"https://www.youtube.com/feeds/videos.xml?channel_id={s['id']}"
                res = requests.get(url_f, headers=HEADERS, timeout=25)
                
                # 🛡️ ПУЛЕНЕПРОБИВАЕМЫЙ ПАРСИНГ XML (v44.0)
                try:
                    root = ET.fromstring(res.content)
                except Exception as e:
                    print(f"❌ Сектор {s['n']} прислал невалидный код. Пропуск.")
                    continue

                items = root.findall('.//item') or root.findall('{http://www.w3.org/2005/Atom}entry')
                for item in items[:5]:
                    link_node = item.find('link')
                    link = link_node.text if link_node is not None and link_node.text else link_node.get('href')
                    if not link or link in db: continue
                    
                    title_node = item.find('title') or item.find('{http://www.w3.org/2005/Atom}title')
                    title = title_node.text if title_node is not None else "Космическая находка"
                    
                    desc_node = item.find('description') or item.find('{http://www.w3.org/2005/Atom}summary')
                    desc_text = desc_node.text if desc_node is not None else ""
                    
                    video_list.append({'url': link, 'title': title, 'desc': desc_text, 'id': link})
                    break

            for v in video_list:
                path, mode = await process_video_v44(v['url'])
                if not path or mode == "error":
                    with open(DB_FILE, 'a') as f: f.write(f"\n{v['id']}")
                    continue
                
                t_ru = super_clean(safe_translate(v['title']).upper())
                d_ru = super_clean(safe_translate(v['desc'][:900]))
                
                # ЯРКОЕ, СТРУКТУРИРОВАННОЕ ОПИСАНИЕ
                caption = (
                    f"🚀 <b>{t_ru}</b>\n\n"
                    f"🛰 <b>Миссия:</b> {s['n']}\n"
                    f"📝 <b>Формат:</b> Видео с переводом (субтитры)\n"
                    f"─────────────────────\n"
                    f"🪐 <b>ИНФОРМАЦИОННЫЙ ДАЙДЖЕСТ:</b>\n\n"
                    f"{d_ru[:500]}...\n\n"
                    f"✨ <i>Погрузись в тайны Вселенной вместе с нами!</i>\n"
                    f"🔭 <a href='https://t.me/vladislav_space'>Подпишись на Дневник</a>"
                )

                with open(path, 'rb') as f_v:
                    r = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo", files={"video": f_v}, data={"chat_id": CHANNEL_NAME, "caption": caption, "parse_mode": "HTML"}, timeout=300)
                
                if r.status_code == 200:
                    with open(DB_FILE, 'a') as f: f.write(f"\n{v['id']}")
                    print(f"🎉 Опубликовано: {v['title']}"); return
        except Exception as e:
            print(f"⚠️ Сбой сектора: {e}")
            continue

if __name__ == '__main__':
    asyncio.run(main())
