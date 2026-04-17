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
# ⚙️ КОНФИГУРАЦИЯ v131.1 (Diagnostic Patch)
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

async def process_mission_v131(v_url, title, desc, source_name, is_russian=False):
    f_raw, f_final = "raw_video.mp4", "final_video.mp4"
    for f in [f_raw, f_final, "subs.srt"]:
        if os.path.exists(f): os.remove(f)

    try:
        print(f"📥 [ЦУП] Захват объекта: {v_url}")
        is_direct = any(v_url.lower().endswith(ext) for ext in ['.mp4', '.m4v', '.mov'])
        
        if is_direct:
            headers = {'User-Agent': 'Mozilla/5.0'}
            r = requests.get(v_url, stream=True, timeout=120, headers=headers)
            with open(f_raw, 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024*1024): f.write(chunk)
        else:
            ydl_opts = {
                'format': 'bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480]/best',
                'outtmpl': f_raw, 
                'quiet': True,
                'no_warnings': True,
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'download_ranges': lambda info, dict: [{'start_time': 0, 'end_time': 420}]
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([v_url])

        if not os.path.exists(f_raw) or os.path.getsize(f_raw) < 100000:
            print("❌ ОШИБКА: Файл поврежден или не скачан.")
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

        prob = subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', f_raw])
        target_br = int((47 * 8 * 1024 * 1024) / float(prob)) - 128000
        
        vf = "subtitles=subs.srt:force_style='FontSize=22,PrimaryColour=&HFFFFFF,BorderStyle=3,BackColour=&H80000000,Outline=1,Shadow=0'" if has_subs else "scale=trunc(iw/2)*2:trunc(ih/2)*2"
        
        print("⚙️ FFmpeg: Сборка финального видео...")
        subprocess.run(['ffmpeg', '-y', '-i', f_raw, '-vf', vf, '-c:v', 'libx264', '-b:v', str(max(target_br, 200000)), '-preset', 'ultrafast', '-c:a', 'aac', '-b:a', '128k', f_final], capture_output=True)
        
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

        print("🚀 Отправка в Telegram...")
        with open(f_final if os.path.exists(f_final) else f_raw, 'rb') as v:
            r = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo", 
                              files={"video": v}, data={"chat_id": CHANNEL_NAME, "caption": caption, "parse_mode": "HTML"}, timeout=450)
            return r.status_code == 200
            
    except Exception as e:
        print(f"⚠️ Системный сбой при обработке: {e}")
        return False

# ============================================================
# 📡 ДВОЙНОЙ ЗАХВАТ (RSS + API РЕЗЕРВ)
# ============================================================

def get_youtube_videos(channel_id):
    items = []
    # ПОПЫТКА 1: RSS с маскировкой под браузер
    try:
        url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'}
        res = requests.get(url, headers=headers, timeout=15)
        
        if res.status_code == 200 and '<?xml' in res.text:
            root = ET.fromstring(res.content)
            namespaces = {'atom': 'http://www.w3.org/2005/Atom', 'media': 'http://search.yahoo.com/mrss/'}
            entries = root.findall('.//atom:entry', namespaces)
            for entry in entries[:15]:
                link = entry.find('atom:link', namespaces).attrib['href']
                desc_elem = entry.find('.//media:description', namespaces)
                items.append({
                    'id': link.split('v=')[-1],
                    'url': link,
                    'title': entry.find('atom:title', namespaces).text,
                    'desc': desc_elem.text if desc_elem is not None else ""
                })
            if items: 
                print("   ✅ RSS-канал прочитан успешно.")
                return items
        else:
            print(f"   🛡️ YouTube заблокировал RSS (Код {res.status_code}). Включаю API-резерв...")
    except Exception as e:
        print(f"   ⚠️ Ошибка соединения RSS: {e}. Включаю API-резерв...")

    # ПОПЫТКА 2: Надежный API метод
    if not YOUTUBE_API_KEY: 
        print("   ❌ ОШИБКА: Секретный ключ YOUTUBE_API_KEY не загружен!")
        return []
        
    try:
        print("   🔄 Запрос через официальный YouTube API...")
        url_ch = f"https://www.googleapis.com/youtube/v3/channels?part=contentDetails&id={channel_id}&key={YOUTUBE_API_KEY}"
        res_ch = requests.get(url_ch, timeout=15).json()
        
        # ДИАГНОСТИКА: Печатаем ошибку, если она есть
        if 'error' in res_ch:
            print(f"   ❌ ОШИБКА API (Запрос канала): {res_ch['error']['message']}")
            return []
            
        if 'items' not in res_ch or not res_ch['items']:
            print("   ⚠️ API вернул пустой ответ (канал не найден или скрыт).")
            return []
            
        uploads_id = res_ch['items'][0]['contentDetails']['relatedPlaylists']['uploads']

        url_pl = f"https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&playlistId={uploads_id}&maxResults=15&key={YOUTUBE_API_KEY}"
        res_pl = requests.get(url_pl, timeout=15).json()
        
        if 'error' in res_pl:
            print(f"   ❌ ОШИБКА API (Запрос плейлиста): {res_pl['error']['message']}")
            return []

        for item in res_pl.get('items', []):
            snippet = item['snippet']
            v_id = snippet['resourceId']['videoId']
            items.append({
                'id': v_id,
                'url': f"https://www.youtube.com/watch?v={v_id}",
                'title': snippet['title'],
                'desc': snippet['description']
            })
            
        print(f"   ✅ API отработало: найдено {len(items)} видео.")
        return items
        
    except Exception as e:
        print(f"   ❌ Критический API-сбой: {e}")
        return []

# ============================================================
# 🛰 СКАНЕР
# ============================================================

async def main():
    print("🎬 [ЦУП] v131.1 'Diagnostic Patch' активирована...")
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
    PRIO = ['KOSMO', '2081 / 208I', 'AdMe Космос']
    SOURCES.sort(key=lambda x: x['n'] not in PRIO)

    for s in SOURCES:
        if s['n'] == last_source and len(SOURCES) > 1: continue
        
        try:
            print(f"\n📡 Сканирую сектор: {s['n']}...")
            
            # --- ВЕТКА YOUTUBE ---
            if s['t'] == 'yt':
                videos = get_youtube_videos(s['cid'])
                for v in videos:
                    if v['id'] not in db:
                        if await process_mission_v131(v['url'], v['title'], v['desc'], s['n'], s['ru']):
                            with open(DB_FILE, 'a') as f: f.write(f"\n{v['id']}")
                            with open(SOURCE_LOG, 'w') as f: f.write(s['n'])
                            print(f"🎉 Миссия успешно завершена!")
                            return
                            
            # --- ВЕТКА ПРЯМЫХ ВИДЕО (ESO) ---
            elif s['t'] == 'rss':
                headers = {'User-Agent': 'Mozilla/5.0'}
                res = requests.get(s['u'], headers=headers, timeout=30)
                if '<?xml' not in res.text[:100] and '<rss' not in res.text[:100]:
                    print("   ⚠️ Неверный формат ленты (ожидался XML). Пропуск.")
                    continue
                    
                root = ET.fromstring(res.content)
                items = root.findall('.//item')
                print(f"   🔍 Найдено сигналов: {len(items)}")
                
                for item in items[:15]:
                    link = item.find('link').text
                    if link not in db:
                        encl = item.find('enclosure')
                        v_url = encl.get('url') if encl is not None else link
                        title = item.find('title').text
                        desc = item.find('description').text
                        
                        if await process_mission_v131(v_url, title, desc, s['n'], s['ru']):
                            with open(DB_FILE, 'a') as f: f.write(f"\n{link}")
                            with open(SOURCE_LOG, 'w') as f: f.write(s['n'])
                            print(f"🎉 Миссия успешно завершена!")
                            return
                            
        except Exception as e:
            print(f"⚠️ Ошибка в секторе {s['n']}: {e}")
            continue

if __name__ == '__main__':
    asyncio.run(main())
