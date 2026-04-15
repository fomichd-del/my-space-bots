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
# ⚙️ КОНФИГУРАЦИЯ v129.0
# ============================================================
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
NASA_API_KEY   = os.getenv('NASA_API_KEY')
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
CHANNEL_NAME   = '@vladislav_space'
DB_FILE        = "last_video_date.txt"
SOURCE_LOG     = "last_source.txt"

translator = GoogleTranslator(source='auto', target='ru')
try:
    model = whisper.load_model("base")
except:
    model = None

# ============================================================
# 🛠 ИНСТРУМЕНТЫ
# ============================================================

def safe_translate(text):
    if not text or len(str(text)) < 2: return ""
    try: return translator.translate(text)
    except: return text

def super_clean(text):
    if not text: return ""
    text = re.sub(r'http\S+', '', str(text)) 
    text = re.sub(r'<[^>]+>', '', text)      
    return html.escape(html.unescape(text)).strip()

# ============================================================
# 🎬 ПРОЦЕССОР (УЛУЧШЕННЫЙ ЗАХВАТ YOUTUBE)
# ============================================================

async def process_mission_v129(v_url, title, desc, source_name, is_russian=False):
    f_raw, f_final = "raw_video.mp4", "final_video.mp4"
    for f in [f_raw, f_final, "subs.srt"]:
        if os.path.exists(f): os.remove(f)

    try:
        print(f"📥 [ЦУП] Попытка захвата: {v_url}")
        is_direct = any(v_url.lower().endswith(ext) for ext in ['.mp4', '.m4v', '.mov'])
        
        if is_direct:
            r = requests.get(v_url, stream=True, timeout=120)
            with open(f_raw, 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024*1024): f.write(chunk)
        else:
            # Улучшенные опции для YouTube
            ydl_opts = {
                'format': 'bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480]/best',
                'outtmpl': f_raw, 
                'quiet': False, # Включаем лог для отладки
                'no_warnings': False,
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                'download_ranges': lambda info, dict: [{'start_time': 0, 'end_time': 480}] # 8 минут
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([v_url])

        if not os.path.exists(f_raw) or os.path.getsize(f_raw) < 100000:
            print("❌ ОШИБКА: Файл не скачан или поврежден.")
            return False

        # --- СУБТИТРЫ ---
        mode_label = "● 🛰 КОСМИЧЕСКАЯ ТИШИНА ●"
        has_subs = False
        if is_russian:
            mode_label = "● 🔊 ОРИГИНАЛЬНАЯ ОЗВУЧКА ●"
        elif model:
            print("🎙 Whisper: Поиск речи...")
            res = model.transcribe(f_raw)
            if res.get('text', '').strip():
                srt = ""
                for i, seg in enumerate(res['segments']):
                    txt_ru = safe_translate(seg['text'].strip())
                    if txt_ru:
                        s = time.strftime('%H:%M:%S,000', time.gmtime(seg['start']))
                        e = time.strftime('%H:%M:%S,000', time.gmtime(seg['end']))
                        srt += f"{i+1}\n{s} --> {e}\n{txt_ru}\n\n"
                if srt:
                    with open("subs.srt", "w", encoding="utf-8") as fs: fs.write(srt)
                    mode_label = "● 📝 СУБТИТРЫ ПОДГОТОВЛЕНЫ ●"
                    has_subs = True

        # --- МОНТАЖ ---
        prob = subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', f_raw])
        target_br = int((47 * 8 * 1024 * 1024) / float(prob)) - 128000
        vf = "subtitles=subs.srt:force_style='FontSize=20,Outline=3,BorderStyle=3'" if has_subs else "scale=trunc(iw/2)*2:trunc(ih/2)*2"
        subprocess.run(['ffmpeg', '-y', '-i', f_raw, '-vf', vf, '-c:v', 'libx264', '-b:v', str(max(target_br, 200000)), '-preset', 'ultrafast', '-c:a', 'aac', '-b:a', '128k', f_final], capture_output=True)
        
        # --- ПОСТ ---
        clean_title = (title if is_russian else safe_translate(title)).upper()
        facts = super_clean(desc if is_russian else safe_translate(desc)).split('. ')
        fact_block = "🔹 " + facts[0] + ('. ' + facts[1] if len(facts) > 1 else '...')

        caption = (f"<b>{mode_label}</b>\n\n🚀 <b>{clean_title}</b>\n\n"
                   f"🛰 <b>ИСТОЧНИК:</b> {source_name}\n─────────────────────\n"
                   f"🪐 <b>НАУЧНЫЕ ФАКТЫ:</b>\n\n{fact_block}\n\n"
                   f"🔭 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>")

        with open(f_final if os.path.exists(f_final) else f_raw, 'rb') as v:
            r = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo", 
                              files={"video": v}, data={"chat_id": CHANNEL_NAME, "caption": caption, "parse_mode": "HTML"}, timeout=450)
            return r.status_code == 200
    except Exception as e:
        print(f"⚠️ Ошибка процесса: {e}")
        return False

# ============================================================
# 🛰 СКАНЕР
# ============================================================

async def main():
    print("🎬 [ЦУП] v129.0 'Broad Spectrum' активирована...")
    if not os.path.exists(DB_FILE): open(DB_FILE, 'w').close()
    if not os.path.exists(SOURCE_LOG): open(SOURCE_LOG, 'w').write("None")
    db = open(DB_FILE, 'r').read()
    last_source = open(SOURCE_LOG, 'r').read().strip()

    SOURCES = [
        {'n': 'KOSMO', 'cid': 'UC8M_itU9f_v7Yp7mQo-879A', 't': 'yt', 'ru': True},
        {'n': '2081 / 208I', 'cid': 'UCMZp-X_lYfN0-n_9n9_vXpw', 't': 'yt', 'ru': True},
        {'n': 'AdMe Космос', 'cid': 'UCB_S_1BIn3Y_t9Uf9Msn6Bw', 't': 'yt', 'ru': True},
        {'n': 'Роскосмос', 'cid': 'UCOm4M6L_L7xOovvS_I-k__A', 't': 'yt', 'ru': True},
        {'n': 'SpaceX News', 'cid': 'UC_MhefFv_XW3c66m7ZAnxHA', 't': 'yt', 'ru': False},
        {'n': 'NASA JPL', 'cid': 'UC99RW7X_XzM_C6P6z_pXlAw', 't': 'yt', 'ru': False},
        {'n': 'ESO Observatory', 'u': 'https://www.eso.org/public/videos/feed/', 't': 'rss', 'ru': False}
    ]

    random.shuffle(SOURCES)
    # Приоритет новым каналам
    PRIO = ['KOSMO', '2081 / 208I', 'AdMe Космос']
    SOURCES.sort(key=lambda x: x['n'] not in PRIO)

    for s in SOURCES:
        if s['n'] == last_source and len(SOURCES) > 1: continue
        
        try:
            print(f"📡 Сектор: {s['n']}...")
            if s['t'] == 'yt':
                url = f"https://www.googleapis.com/youtube/v3/search?key={YOUTUBE_API_KEY}&channelId={s['cid']}&part=snippet&maxResults=50&type=video&q="
                res = requests.get(url).json()
                items = res.get('items', [])
                print(f"🔍 Видео на горизонте: {len(items)}")
                
                items.sort(key=lambda x: x['snippet']['publishedAt'], reverse=True)

                for item in items:
                    v_id = item['id']['videoId']
                    if v_id not in db:
                        if await process_mission_v129(f"https://www.youtube.com/watch?v={v_id}", item['snippet']['title'], item['snippet']['description'], s['n'], s['ru']):
                            with open(DB_FILE, 'a') as f: f.write(f"\n{v_id}")
                            with open(SOURCE_LOG, 'w') as f: f.write(s['n'])
                            print(f"🎉 Миссия завершена!"); return
            
            elif s['t'] == 'rss':
                res = requests.get(s['u'], timeout=30)
                root = ET.fromstring(res.content)
                for item in root.findall('.//item')[:15]:
                    link = item.find('link').text
                    if link not in db:
                        encl = item.find('enclosure')
                        v_url = encl.get('url') if encl is not None else link
                        if await process_mission_v129(v_url, item.find('title').text, item.find('description').text, s['n'], s['ru']):
                            with open(DB_FILE, 'a') as f: f.write(f"\n{link}")
                            with open(SOURCE_LOG, 'w') as f: f.write(s['n'])
                            print(f"🎉 Миссия завершена!"); return
        except Exception as e:
            print(f"⚠️ Ошибка: {e}")
            continue

if __name__ == '__main__':
    asyncio.run(main())
