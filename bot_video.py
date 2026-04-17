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
# ⚙️ КОНФИГУРАЦИЯ v140.0 (Mirror Proxy Protocol)
# ============================================================
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY') 
CHANNEL_NAME   = '@vladislav_space'
DB_FILE        = "last_video_date.txt"
SOURCE_LOG     = "last_source.txt"

MAX_FILE_SIZE = 48.5 * 1024 * 1024 

SPACE_KEYWORDS = ['космос', 'вселенн', 'планет', 'звезд', 'галактик', 'луна', 'марс', 'черная дыра', 'астроном', 'телескоп', 'nasa', 'spacex', 'роскосмос', 'астероид', 'комета']

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
    "Тяв! Центр управления, полет нормальный, хвост по ветру! 🛰️🐕",
    "Гав! Если увидишь там инопланетян — передавай им мой привет! 🛸🐾"
]

# ============================================================
# 🛠 ИНСТРУМЕНТЫ
# ============================================================

def safe_translate(text):
    if not text or len(str(text)) < 2: return ""
    try: return translator.translate(text)
    except: return text

def super_clean(text):
    if not text: return "Космические подробности в видео! ✨"
    text = re.sub(r'http\S+', '', str(text)) 
    text = re.sub(r'<[^>]+>', '', text)      
    return html.escape(html.unescape(text)).strip()

def get_short_facts(text):
    clean_text = super_clean(text)
    sentences = [s.strip() for s in clean_text.split('. ') if s.strip()]
    if not sentences: return "Смотрите в этом выпуске невероятные кадры Вселенной! 🌠"
    fact_block = sentences[0] + '.'
    if len(sentences) > 1 and len(fact_block) < 130:
        fact_block += ' ' + sentences[1] + '.'
    return fact_block

# ============================================================
# 🎬 УМНЫЙ ПРОЦЕССОР (СИСТЕМА ЗЕРКАЛ)
# ============================================================

async def process_mission_v140(v_id_or_url, title, desc, source_name, is_russian=False):
    f_raw, f_final = "raw_video.mp4", "final_video.mp4"
    for f in [f_raw, f_final, "subs.srt"]:
        if os.path.exists(f): os.remove(f)

    try:
        is_direct = any(v_id_or_url.lower().endswith(ext) for ext in ['.mp4', '.m4v', '.mov'])
        duration = 600

        # --- БЛОК 1: ЗАХВАТ ВИДЕО ---
        if is_direct:
            print(f"📥 [ЦУП] Прямая загрузка (ESO): {v_id_or_url}")
            r = requests.get(v_id_or_url, stream=True, timeout=300)
            with open(f_raw, 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024*1024): f.write(chunk)
        else:
            v_id = v_id_or_url.split('v=')[-1] if 'v=' in v_id_or_url else v_id_or_url
            print(f"📥 [ЦУП] Объект {v_id}. Включаю систему зеркал...")
            
            # Список независимых серверов для обхода блокировки
            MIRRORS = [
                f"https://yewtu.be/watch?v={v_id}",
                f"https://invidious.nerdvpn.de/watch?v={v_id}",
                f"https://inv.tux.pizza/watch?v={v_id}",
                f"https://invidious.flokinet.to/watch?v={v_id}",
                f"https://piped.video/watch?v={v_id}"
            ]
            random.shuffle(MIRRORS)
            
            success = False
            ydl_opts = {
                'format': 'bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480]/best',
                'outtmpl': f_raw, 
                'quiet': True,
                'no_warnings': True
            }

            for mirror in MIRRORS:
                try:
                    print(f"   🔄 Скрытый запрос через: {mirror}")
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        # Пытаемся получить длительность для пережатия
                        try:
                            info = ydl.extract_info(mirror, download=False)
                            duration = info.get('duration', 600)
                        except: pass
                        # Скачиваем файл через зеркало
                        ydl.download([mirror])
                        
                    if os.path.exists(f_raw) and os.path.getsize(f_raw) > 100000:
                        success = True
                        print("   ✅ Захват успешен!")
                        break
                except Exception as e:
                    print("   ⚠️ Зеркало недоступно, переключаю на следующее...")
                    if os.path.exists(f_raw): os.remove(f_raw)

            if not success:
                print("❌ Все зеркала заблокированы.")
                return False

        # --- БЛОК 2: РАСЧЕТ БИТРЕЙТА И ПЕРЕВОД ---
        if is_direct:
            try:
                prob = subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', f_raw])
                duration = float(prob)
            except: duration = 600

        target_total_bitrate = (MAX_FILE_SIZE * 8) / duration
        video_bitrate = int(target_total_bitrate - 128000) 
        final_v_bitrate = max(100000, min(video_bitrate, 2500000))
        print(f"⚖️ Расчет: длительность {duration}с, целевой битрейт {final_v_bitrate//1000}kbps")

        has_subs = False
        mode_tag = "🎙 ОРИГИНАЛЬНАЯ ОЗВУЧКА 🎙"
        
        if not is_russian and model:
            print("🎙 Whisper: Перевод зарубежного вещания...")
            mode_tag = "📝 РУССКИЕ СУБТИТРЫ 📝"
            res = model.transcribe(f_raw)
            srt = ""
            for i, seg in enumerate(res.get('segments', [])):
                txt_ru = safe_translate(seg['text'].strip())
                if txt_ru:
                    s, e = time.strftime('%H:%M:%S,000', time.gmtime(seg['start'])), time.strftime('%H:%M:%S,000', time.gmtime(seg['end']))
                    srt += f"{i+1}\n{s} --> {e}\n{txt_ru}\n\n"
            if srt:
                with open("subs.srt", "w", encoding="utf-8") as fs: fs.write(srt)
                has_subs = True
        elif not is_russian:
            mode_tag = "🎵 МУЗЫКА КОСМОСА 🎵"

        vf = "subtitles=subs.srt:force_style='FontSize=22,BorderStyle=3,BackColour=&H80000000'" if has_subs else "scale=trunc(iw/2)*2:trunc(ih/2)*2"
        print(f"⚙️ FFmpeg: Генерация нативного видео...")
        subprocess.run(['ffmpeg', '-y', '-i', f_raw, '-vf', vf, '-c:v', 'libx264', '-b:v', str(final_v_bitrate), '-preset', 'ultrafast', '-c:a', 'aac', '-b:a', '128k', f_final], capture_output=True)

        clean_title = (title if is_russian else safe_translate(title)).upper()
        facts = get_short_facts(desc if is_russian else safe_translate(desc))
        marty_comment = random.choice(MARTY_QUOTES)

        caption = (
            f"<b>{mode_tag}</b>\n\n"
            f"🎬 <b>{clean_title}</b>\n"
            f"─────────────────────\n\n"
            f"🪐 <b>ГЛАВНОЕ:</b>\n"
            f"🔹 {facts}\n\n"
            f"🐩 <b>Марти передает:</b>\n"
            f"<i>{marty_comment}</i>\n\n"
            f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
        )

        with open(f_final if os.path.exists(f_final) else f_raw, 'rb') as v:
            requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo", 
                          files={"video": v}, data={"chat_id": CHANNEL_NAME, "caption": caption, "parse_mode": "HTML"}, timeout=600)
            return True
    except Exception as e:
        print(f"⚠️ Сбой: {e}")
        return False

# ============================================================
# 📡 НАВИГАТОР
# ============================================================

def get_youtube_videos(channel_handle, filter_space=False):
    items = []
    try:
        handle = channel_handle.replace('@', '')
        url_h = f"https://www.googleapis.com/youtube/v3/channels?part=id,contentDetails&forHandle={handle}&key={YOUTUBE_API_KEY}"
        res_h = requests.get(url_h).json()
        ch_id = res_h['items'][0]['id']
        up_id = res_h['items'][0]['contentDetails']['relatedPlaylists']['uploads']
        
        url_pl = f"https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&playlistId={up_id}&maxResults=10&key={YOUTUBE_API_KEY}"
        for it in requests.get(url_pl).json().get('items', []):
            snip = it['snippet']
            if filter_space and not any(w in (snip['title'] + snip['description']).lower() for w in SPACE_KEYWORDS): continue
            v_id = snip['resourceId']['videoId']
            # Передаем только ID, URL соберет система зеркал
            items.append({'id': v_id, 'title': snip['title'], 'desc': snip['description']})
    except: pass
    return items

async def main():
    print("🎬 [ЦУП] v140.0 'Mirror Proxy Protocol' запуск...")
    if not os.path.exists(DB_FILE): open(DB_FILE, 'w').close()
    if not os.path.exists(SOURCE_LOG): open(SOURCE_LOG, 'w').write("None")
    db = open(DB_FILE, 'r').read()
    last_source = open(SOURCE_LOG, 'r').read().strip()

    SOURCES = [
        {'n': 'KOSMO', 'cid': '@off_kosmo', 'ru': True, 'f': False},
        {'n': 'ADME', 'cid': '@ADME_RU', 'ru': True, 'f': True},
        {'n': '2081', 'cid': '@2081-li', 'ru': True, 'f': False},
        {'n': 'Наука', 'cid': '@ночнаянаука-ц4ш', 'ru': True, 'f': False},
        {'n': 'Интересно', 'cid': '@space-interesting', 'ru': True, 'f': False},
        {'n': 'Роскосмос', 'cid': '@roscosmos', 'ru': True, 'f': False},
        {'n': 'NASA JPL', 'cid': '@NASAJPL', 'ru': False, 'f': False},
        {'n': 'SpaceX', 'cid': '@SpaceX', 'ru': False, 'f': False},
        {'n': 'ESO', 'u': 'https://www.eso.org/public/videos/feed/', 'ru': False, 'f': False}
    ]

    random.shuffle(SOURCES)
    for s in SOURCES:
        if s['n'] == last_source: continue
        try:
            print(f"\n📡 Сектор: {s['n']}...")
            videos = []
            if 'u' in s: 
                root = ET.fromstring(requests.get(s['u']).content)
                for item in root.findall('.//item')[:10]:
                    link = item.find('link').text
                    if link not in db:
                        v_url = item.find('enclosure').get('url') if item.find('enclosure') is not None else link
                        videos.append({'id': link, 'title': item.find('title').text, 'desc': item.find('description').text})
            else: 
                videos = get_youtube_videos(s['cid'], s['f'])

            for v in videos:
                if v['id'] not in db:
                    # Для YouTube передаем ID, для ESO передаем прямую ссылку v['url']
                    target = v.get('url', v['id'])
                    if await process_mission_v140(target, v['title'], v['desc'], s['n'], s['ru']):
                        with open(DB_FILE, 'a') as f: f.write(f"\n{v['id']}")
                        with open(SOURCE_LOG, 'w') as f: f.write(s['n'])
                        print("🎉 Миссия выполнена!"); return
        except Exception as e: 
            print(f"Ошибка в секторе {s['n']}: {e}")
            continue

if __name__ == '__main__':
    asyncio.run(main())
