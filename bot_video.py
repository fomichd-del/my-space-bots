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
# ⚙️ КОНФИГУРАЦИЯ v130.0 (Prime Release)
# ============================================================
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
NASA_API_KEY   = os.getenv('NASA_API_KEY')
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY') # Больше не тратим квоты, но оставляем для yt-dlp
CHANNEL_NAME   = '@vladislav_space'
DB_FILE        = "last_video_date.txt"
SOURCE_LOG     = "last_source.txt"

translator = GoogleTranslator(source='auto', target='ru')
try:
    model = whisper.load_model("base")
except:
    model = None

# 🐩 КОММЕНТАРИИ ШТУРМАНА МАРТИ
MARTY_QUOTES = [
    "Гав! Пока переводил это видео, чуть не улетел на орбиту! 🚀🐩",
    "Ррр-гав! Этот ролик точно заслуживает космической косточки! 🦴✨",
    "Гав-гав! Надеваю скафандр, я готов лететь туда! 🧑‍🚀🐾",
    "Даже мой хвост завилял со скоростью света от таких кадров! ☄️🐕",
    "Гав! Надеюсь, на тех планетах тоже есть пудели! 🛸🐩",
    "Уф! От этих видов я даже забыл, где зарыл свой лунный камень! 🌕🐾",
    "Тяв! Центр управления, полет нормальный, хвост по ветру! 🛰️🐕"
]

# ============================================================
# 🛠 ИНСТРУМЕНТЫ
# ============================================================

def safe_translate(text):
    if not text or len(str(text)) < 2: return ""
    try: return translator.translate(text)
    except: return text

def super_clean(text):
    if not text: return "Космические подробности остались за кадром..."
    text = re.sub(r'http\S+', '', str(text)) 
    text = re.sub(r'<[^>]+>', '', text)      
    return html.escape(html.unescape(text)).strip()

def get_short_facts(text):
    """Обрезает длинное описание до 1-2 самых важных предложений"""
    clean_text = super_clean(text)
    sentences = [s.strip() for s in clean_text.split('. ') if s.strip()]
    if not sentences: return "Без описания, но выглядит невероятно!"
    fact_block = sentences[0] + '.'
    if len(sentences) > 1 and len(fact_block) < 100:
        fact_block += ' ' + sentences[1] + '.'
    return fact_block

# ============================================================
# 🎬 ПРОЦЕССОР (ЗАХВАТ, СУБТИТРЫ И МОНТАЖ)
# ============================================================

async def process_mission_v130(v_url, title, desc, source_name, is_russian=False):
    f_raw, f_final = "raw_video.mp4", "final_video.mp4"
    for f in [f_raw, f_final, "subs.srt"]:
        if os.path.exists(f): os.remove(f)

    try:
        print(f"📥 [ЦУП] Захват объекта: {v_url}")
        is_direct = any(v_url.lower().endswith(ext) for ext in ['.mp4', '.m4v', '.mov'])
        
        # --- СКАЧИВАНИЕ ---
        if is_direct:
            r = requests.get(v_url, stream=True, timeout=120)
            with open(f_raw, 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024*1024): f.write(chunk)
        else:
            ydl_opts = {
                'format': 'bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480]/best',
                'outtmpl': f_raw, 
                'quiet': True,
                'no_warnings': True,
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'download_ranges': lambda info, dict: [{'start_time': 0, 'end_time': 420}] # 7 минут макс
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([v_url])

        if not os.path.exists(f_raw) or os.path.getsize(f_raw) < 100000:
            print("❌ ОШИБКА: Файл поврежден.")
            return False

        # --- НЕЙРОСЕТЬ И СУБТИТРЫ ---
        mode_label = "🎵 МУЗЫКА КОСМОСА (БЕЗ СЛОВ) 🎵"
        has_subs = False
        
        if is_russian:
            mode_label = "🎙 ОРИГИНАЛЬНАЯ ОЗВУЧКА 🎙"
        elif model:
            print("🎙 Whisper: Прослушивание аудиодорожки...")
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
                    mode_label = "📝 РУССКИЕ СУБТИТРЫ ОТ ЦУП 📝"
                    has_subs = True

        # --- МОНТАЖ И РЕНДЕР ---
        prob = subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', f_raw])
        target_br = int((47 * 8 * 1024 * 1024) / float(prob)) - 128000
        
        # BorderStyle=3 создает черную непрозрачную подложку под текстом! Перекрывает любые вшитые англ. субтитры.
        vf = "subtitles=subs.srt:force_style='FontSize=22,PrimaryColour=&HFFFFFF,BorderStyle=3,BackColour=&H80000000,Outline=1,Shadow=0'" if has_subs else "scale=trunc(iw/2)*2:trunc(ih/2)*2"
        
        print("⚙️ FFmpeg: Сборка финального видео...")
        subprocess.run(['ffmpeg', '-y', '-i', f_raw, '-vf', vf, '-c:v', 'libx264', '-b:v', str(max(target_br, 200000)), '-preset', 'ultrafast', '-c:a', 'aac', '-b:a', '128k', f_final], capture_output=True)
        
        # --- ФОРМИРОВАНИЕ ПОСТА (КОСМО-СТИЛЬ) ---
        clean_title = (title if is_russian else safe_translate(title)).upper()
        facts = get_short_facts(desc if is_russian else safe_translate(desc))
        marty_comment = random.choice(MARTY_QUOTES)

        caption = (
            f"<b>{mode_label}</b>\n\n"
            f"🎬 <b>{clean_title}</b>\n"
            f"─────────────────────\n\n"
            f"🛰 <b>ИСТОЧНИК:</b> {source_name}\n\n"
            f"🪐 <b>ГЛАВНОЕ:</b>\n"
            f"🔹 {facts}\n\n"
            f"🐩 <b>Марти передает:</b>\n"
            f"<i>{marty_comment}</i>\n\n"
            f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
        )

        # --- ОТПРАВКА ---
        print("🚀 Отправка в Telegram...")
        with open(f_final if os.path.exists(f_final) else f_raw, 'rb') as v:
            r = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo", 
                              files={"video": v}, data={"chat_id": CHANNEL_NAME, "caption": caption, "parse_mode": "HTML"}, timeout=450)
            return r.status_code == 200
            
    except Exception as e:
        print(f"⚠️ Системный сбой при обработке: {e}")
        return False

# ============================================================
# 🛰 СКАНЕР (УМНЫЕ RSS-ЛЕНТЫ)
# ============================================================

async def main():
    print("🎬 [ЦУП] v130.0 'Prime Release' активирована...")
    if not os.path.exists(DB_FILE): open(DB_FILE, 'w').close()
    if not os.path.exists(SOURCE_LOG): open(SOURCE_LOG, 'w').write("None")
    db = open(DB_FILE, 'r').read()
    last_source = open(SOURCE_LOG, 'r').read().strip()

    # t: 'yt_rss' означает скрытую RSS ленту YouTube (бесплатно, без API, работает всегда)
    SOURCES = [
        {'n': 'KOSMO', 'cid': 'UC8M_itU9f_v7Yp7mQo-879A', 't': 'yt_rss', 'ru': True},
        {'n': '2081 / 208I', 'cid': 'UCMZp-X_lYfN0-n_9n9_vXpw', 't': 'yt_rss', 'ru': True},
        {'n': 'AdMe Космос', 'cid': 'UCB_S_1BIn3Y_t9Uf9Msn6Bw', 't': 'yt_rss', 'ru': True},
        {'n': 'Роскосмос', 'cid': 'UCOm4M6L_L7xOovvS_I-k__A', 't': 'yt_rss', 'ru': True},
        {'n': 'SpaceX News', 'cid': 'UC_MhefFv_XW3c66m7ZAnxHA', 't': 'yt_rss', 'ru': False},
        {'n': 'NASA JPL', 'cid': 'UC99RW7X_XzM_C6P6z_pXlAw', 't': 'yt_rss', 'ru': False},
        {'n': 'ESO Observatory', 'u': 'https://www.eso.org/public/videos/feed/', 't': 'rss', 'ru': False}
    ]

    random.shuffle(SOURCES)
    PRIO = ['KOSMO', '2081 / 208I', 'AdMe Космос']
    SOURCES.sort(key=lambda x: x['n'] not in PRIO)

    for s in SOURCES:
        if s['n'] == last_source and len(SOURCES) > 1: continue
        
        try:
            print(f"\n📡 Сканирую сектор: {s['n']}...")
            
            # --- ВЕТКА YOUTUBE (БЕЗ API) ---
            if s['t'] == 'yt_rss':
                url = f"https://www.youtube.com/feeds/videos.xml?channel_id={s['cid']}"
                res = requests.get(url, timeout=30)
                root = ET.fromstring(res.content)
                namespaces = {'atom': 'http://www.w3.org/2005/Atom', 'media': 'http://search.yahoo.com/mrss/'}
                
                items = root.findall('.//atom:entry', namespaces)
                print(f"🔍 Найдено сигналов: {len(items)}")
                
                for entry in items[:15]:
                    title = entry.find('atom:title', namespaces).text
                    link = entry.find('atom:link', namespaces).attrib['href']
                    v_id = link.split('v=')[-1]
                    
                    desc_elem = entry.find('.//media:description', namespaces)
                    desc = desc_elem.text if desc_elem is not None else ""
                    
                    if v_id not in db:
                        if await process_mission_v130(link, title, desc, s['n'], s['ru']):
                            with open(DB_FILE, 'a') as f: f.write(f"\n{v_id}")
                            with open(SOURCE_LOG, 'w') as f: f.write(s['n'])
                            print(f"🎉 Миссия успешно завершена!")
                            return
                            
            # --- ВЕТКА ПРЯМЫХ ВИДЕО (ESO) ---
            elif s['t'] == 'rss':
                res = requests.get(s['u'], timeout=30)
                root = ET.fromstring(res.content)
                items = root.findall('.//item')
                print(f"🔍 Найдено сигналов: {len(items)}")
                
                for item in items[:15]:
                    link = item.find('link').text
                    if link not in db:
                        encl = item.find('enclosure')
                        v_url = encl.get('url') if encl is not None else link
                        title = item.find('title').text
                        desc = item.find('description').text
                        
                        if await process_mission_v130(v_url, title, desc, s['n'], s['ru']):
                            with open(DB_FILE, 'a') as f: f.write(f"\n{link}")
                            with open(SOURCE_LOG, 'w') as f: f.write(s['n'])
                            print(f"🎉 Миссия успешно завершена!")
                            return
                            
        except Exception as e:
            print(f"⚠️ Ошибка в секторе {s['n']}: {e}")
            continue

if __name__ == '__main__':
    asyncio.run(main())
