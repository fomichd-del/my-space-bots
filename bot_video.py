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
# ⚙️ НАСТРОЙКИ ЦУП
# ============================================================
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHANNEL_NAME   = '@vladislav_space'
DB_FILE        = "last_video_date.txt"

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}

translator = GoogleTranslator(source='auto', target='ru')
model = whisper.load_model("tiny")
VOICE = "ru-RU-SvetlanaNeural"
VOICE_RATE = "-10%" 
VOICE_LIMIT = 540 

SOURCES = [
    {'n': 'SpaceX (Запуски)', 't': 'yt', 'id': 'UC_MhefFv_XW3c66m7ZAnxHA'},
    {'n': 'VideoFromSpace (Клипы)', 't': 'yt', 'id': 'UC6_OitvS-L0m_uVndA-K8lA'},
    {'n': 'NASA JPL (Марсоходы)', 't': 'yt', 'id': 'UC99RW7X_XzM_C6P6z_pXlAw'},
    {'n': 'Space.com (Новости)', 't': 'rss', 'u': 'https://www.space.com/feeds/all'},
    {'n': 'Phys.org (Астрономия)', 't': 'rss', 'u': 'https://phys.org/rss-feed/space-news/'},
    {'n': 'ESO (Европа)', 't': 'rss', 'u': 'https://www.eso.org/public/videos/feed/'},
    {'n': 'ESA (Открытия)', 't': 'rss', 'u': 'https://www.esa.int/rssfeed/Videos'},
    {'n': 'JAXA (Япония)', 't': 'yt', 'id': 'UC1S_S6G_9A440VUM_KOn6Zg'},
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
    for f in ["input.mp4", "output.mp4", "voice_final.mp3", "silent_base.mp3"]:
        if os.path.exists(f): os.remove(f)
    if os.path.exists("voice"): shutil.rmtree("voice")
    os.makedirs("voice", exist_ok=True)

async def build_voice_track(segments, total_duration):
    inputs = []; filter_parts = []; valid_count = 0
    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-t", str(total_duration + 5), "silent_base.mp3"], capture_output=True)
    inputs.extend(["-i", "silent_base.mp3"])
    for i, seg in enumerate(segments[:40]):
        try:
            path = f"voice/v_{valid_count}.mp3"
            await edge_tts.Communicate(safe_translate(seg.get('text', '')), VOICE, rate=VOICE_RATE).save(path)
            if os.path.exists(path) and os.path.getsize(path) > 100:
                start_ms = int(seg['start'] * 1000) + 50
                inputs.extend(["-i", path])
                filter_parts.append(f"[{valid_count+1}:a]adelay={start_ms}|{start_ms}[a{valid_count}]")
                valid_count += 1
        except: continue
    if valid_count < 1: return None
    labels = "".join([f"[a{i}]" for i in range(valid_count)])
    amix_filter = f"[0:a]{labels}amix=inputs={valid_count+1}:duration=longest[out]"
    cmd = ["ffmpeg", "-y"] + inputs + ["-filter_complex", f"{';'.join(filter_parts)};{amix_filter}", "-map", "[out]", "voice_final.mp3"]
    subprocess.run(cmd, check=True, capture_output=True)
    return "voice_final.mp3"

async def process_video_async(video_url, is_yt):
    f_in, f_out = "input.mp4", "output.mp4"
    clear_workspace()
    try:
        ydl_opts = {'format': 'best[height<=720][ext=mp4]', 'outtmpl': f_in, 'quiet': True, 'noplaylist': True}
        if is_yt or "youtube" in video_url:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl: ydl.download([video_url])
        else:
            r = requests.get(video_url, headers=HEADERS, timeout=60)
            with open(f_in, "wb") as f: f.write(r.content)
        
        if not os.path.exists(f_in) or os.path.getsize(f_in) < 1000: return None, None
        dur_out = subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", f_in])
        dur = float(dur_out.decode().strip())
        res = model.transcribe(f_in)
        segments = res.get('segments', [])
        if segments and dur <= VOICE_LIMIT:
            voice_file = await build_voice_track(segments, dur)
            if voice_file:
                cmd = ["ffmpeg", "-y", "-i", f_in, "-i", voice_file, "-filter_complex", "[0:a]volume=0.1[bg];[1:a]volume=3.0[v];[bg][v]amix=inputs=2:duration=first[outa]", "-map", "0:v", "-map", "[outa]", "-c:v", "copy", "-c:a", "aac", f_out]
                subprocess.run(cmd, check=True)
                return f_out, "voice"
        return f_in, "original"
    except: return None, None

# ============================================================
# 🎬 ГЛАВНЫЙ ЦИКЛ
# ============================================================

async def main():
    print("🎬 [ЦУП] v31.0 'Nebula Guard' запущен...")
    
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r') as f: lines = [l.strip() for l in f.readlines() if l.strip()]
        if len(lines) > 100:
            with open(DB_FILE, 'w') as f: f.write("\n".join(lines[-70:]))

    db = open(DB_FILE, 'r').read() if os.path.exists(DB_FILE) else ""
    pool = SOURCES.copy()
    random.shuffle(pool)
    pool.sort(key=lambda x: x['t'] == 'nasa_api')

    emergency_fallback = None

    for s in pool:
        try:
            print(f"📡 Сектор: {s['n']}...")
            video_list = []
            if s['t'] == 'nasa_api':
                if db.strip().split('\n')[-1].startswith("nasa_"): continue
                nasa_res = requests.get(f"https://images-api.nasa.gov/search?q=space&media_type=video").json()
                for item in nasa_res['collection']['items'][:5]:
                    v_id = item['data'][0]['nasa_id']
                    v_url_data = requests.get(f"https://images-api.nasa.gov/asset/{v_id}").json()
                    v_url = next(a['href'] for a in v_url_data['collection']['items'] if '~medium.mp4' in a['href'])
                    v_obj = {'url': v_url, 'title': item['data'][0]['title'], 'is_yt': False, 'desc': item['data'][0].get('description', ''), 'id': f"nasa_{v_id}", 'src': s['n']}
                    if f"nasa_{v_id}" not in db: video_list.append(v_obj); break
                    elif not emergency_fallback: emergency_fallback = v_obj
            else:
                url_f = s['u'] if 'u' in s else f"https://www.youtube.com/feeds/videos.xml?channel_id={s['id']}"
                res = requests.get(url_f, headers=HEADERS, timeout=25)
                if res.status_code != 200: continue
                
                root = ET.fromstring(res.content)
                # Универсальный поиск элементов (RSS и Atom)
                items = root.findall('.//item') or root.findall('{http://www.w3.org/2005/Atom}entry')
                for item in items[:5]:
                    # Ищем ссылку
                    link_node = item.find('link')
                    link = link_node.text if link_node is not None and link_node.text else link_node.get('href') if link_node is not None else ""
                    if not link:
                        enc = item.find('.//enclosure')
                        link = enc.get('url') if enc is not None else ""
                    
                    if not link: continue
                    if link in db: continue
                    
                    # Ищем заголовок (с учетом пространства имен Atom)
                    title_node = item.find('title') or item.find('{http://www.w3.org/2005/Atom}title')
                    title = title_node.text if title_node is not None else "КОСМИЧЕСКОЕ СОБЫТИЕ"
                    
                    # Ищем описание
                    desc_node = item.find('description') or item.find('{http://www.w3.org/2005/Atom}summary')
                    desc = desc_node.text if desc_node is not None else ""
                    
                    v_obj = {'url': link, 'title': title, 'is_yt': 'youtube' in link or 'youtu.be' in link, 'desc': desc, 'id': link, 'src': s['n']}
                    video_list.append(v_obj); break

            for v in video_list:
                path, mode = await process_video_async(v['url'], v['is_yt'])
                if not path: continue
                caption = (f"⭐ <b>{super_clean(safe_translate(v['title'])).upper()}</b>\n\n🪐 <b>ОБЪЕКТ:</b> {v['src']}\n🔊 <b>ЗВУК:</b> {('Перевод' if mode=='voice' else 'Оригинал')}\n─────────────────────\n📖 <b>СЮЖЕТ:</b> {super_clean(safe_translate(v['desc'][:380]))}...\n\n🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>")
                with open(path, 'rb') as f_v:
                    r = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo", files={"video": f_v}, data={"chat_id": CHANNEL_NAME, "caption": caption, "parse_mode": "HTML"}, timeout=180)
                if r.status_code == 200:
                    with open(DB_FILE, 'a') as f: f.write(f"\n{v['id']}")
                    print("🎉 Опубликовано!"); return
        except Exception as e:
            print(f"⚠️ Сбой в секторе {s['n']}: {e}")
            continue

    if emergency_fallback:
        path, mode = await process_video_async(emergency_fallback['url'], emergency_fallback['is_yt'])
        if path:
            caption = (f"🛰 <b>АРХИВНЫЙ ВЫПУСК: {super_clean(safe_translate(emergency_fallback['title'])).upper()}</b>\n\n🪐 <b>ИСТОЧНИК:</b> {emergency_fallback['src']}\n🔊 <b>ЗВУК:</b> {('Перевод' if mode=='voice' else 'Оригинал')}\n─────────────────────\n📖 <b>СЮЖЕТ:</b> {super_clean(safe_translate(emergency_fallback['desc'][:380]))}...\n\n🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>")
            requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo", files={"video": open(path, 'rb')}, data={"chat_id": CHANNEL_NAME, "caption": caption, "parse_mode": "HTML"})

if __name__ == '__main__':
    asyncio.run(main())
