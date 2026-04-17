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
from datetime import datetime
from deep_translator import GoogleTranslator

# ============================================================
# ⚙️ КОНФИГУРАЦИЯ v144.2 (Precision Orbit)
# ============================================================
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY') 
CHANNEL_NAME   = '@vladislav_space'
DB_FILE        = "last_video_date.txt"
SOURCE_LOG     = "last_source.txt"
MAX_FILE_SIZE_BYTES = 46 * 1024 * 1024 

# Ключевые слова для фильтрации AdMe (только космос)
SPACE_KEYWORDS = ['космос', 'вселенная', 'планета', 'звезд', 'галактик', 'астероид', 'черная дыра', 'марса', 'луна', 'солнц', 'космическ']

try:
    model = whisper.load_model("base")
except:
    model = None

MARTY_QUOTES = [
    "Гав! Настроил антенны на новые частоты! 📡🐩",
    "Ррр-гав! Отфильтровал лишнее, оставил только звезды! ✨",
    "Тяв! Новые сектора изучены, летим дальше! 🐾"
]

# ============================================================
# 🛠 ИНСТРУМЕНТЫ
# ============================================================

def get_short_facts(text):
    if not text: return "Подробности миссии смотрите в ролике! ✨"
    text = re.sub(r'http\S+', '', text)
    text = re.sub(r'#\S+', '', text)
    text = html.unescape(text).strip()
    sentences = [s.strip() for s in text.split('.') if len(s.strip()) > 10]
    summary = ". ".join(sentences[:2]) 
    if len(summary) > 300: summary = summary[:297] + "..."
    return summary + "." if summary else "Свежие кадры прямо с орбиты! 🪐"

def get_fast_proxy():
    print("🛰 [ЦУП] Поиск свободного коридора...")
    url = "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            proxies = resp.text.strip().split('\n')
            random.shuffle(proxies)
            for p in proxies[:20]:
                p = p.strip()
                try:
                    requests.get("https://www.google.com", proxies={"https": f"http://{p}"}, timeout=3)
                    return f"http://{p}"
                except: continue
    except: pass
    return None

# ============================================================
# 🎬 ПРОЦЕССОР
# ============================================================

async def process_mission_v144(v_id, title, desc_raw, is_russian=False, source_name=""):
    f_raw, f_final = "raw_video.mp4", "final_video.mp4"
    for f in [f_raw, f_final, "subs.srt"]:
        if os.path.exists(f): os.remove(f)

    try:
        v_url = f"https://www.youtube.com/watch?v={v_id}"
        proxy = get_fast_proxy()
        
        modern_args = ['player_client=mweb', 'player_skip=webpage']
        info_opts = {'quiet': True, 'extractor_args': {'youtube': modern_args}}
        if proxy: info_opts['proxy'] = proxy

        with yt_dlp.YoutubeDL(info_opts) as ydl:
            time.sleep(random.randint(5, 10))
            info = ydl.extract_info(v_url, download=False)
            duration = info.get('duration', 600)

        res_limit = 360 if duration > 900 else 480
        ydl_opts = {
            'format': f'bestvideo[height<={res_limit}][ext=mp4]+bestaudio[ext=m4a]/best[height<={res_limit}]',
            'outtmpl': f_raw, 'quiet': True, 'extractor_args': {'youtube': modern_args}
        }
        if proxy: ydl_opts['proxy'] = proxy

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([v_url])

        if not os.path.exists(f_raw) or os.path.getsize(f_raw) < 100000: return False

        has_subs = False
        mode_tag = "🎙 ОРИГИНАЛЬНАЯ ОЗВУЧКА"
        if not is_russian and model:
            print(f"🎙 Whisper: Перевод вещания {source_name}...")
            mode_tag = "📝 ПЕРЕВОД (СУБТИТРЫ)"
            res = model.transcribe(f_raw)
            srt = ""
            for i, seg in enumerate(res.get('segments', [])):
                t_ru = GoogleTranslator(source='auto', target='ru').translate(seg['text'].strip())
                srt += f"{i+1}\n{time.strftime('%H:%M:%S,000', time.gmtime(seg['start']))} --> {time.strftime('%H:%M:%S,000', time.gmtime(seg['end']))}\n{t_ru}\n\n"
            with open("subs.srt", "w", encoding="utf-8") as fs: fs.write(srt)
            has_subs = True

        target_br = int((MAX_FILE_SIZE_BYTES * 8) / duration) - 128000
        v_br = max(100000, min(target_br, 1500000))
        vf = "subtitles=subs.srt:force_style='FontSize=20,BorderStyle=3,BackColour=&H80000000'" if has_subs else "scale=trunc(iw/2)*2:trunc(ih/2)*2"
        
        subprocess.run(['ffmpeg', '-y', '-i', f_raw, '-vf', vf, '-c:v', 'libx264', '-b:v', str(v_br), '-preset', 'ultrafast', '-c:a', 'aac', '-b:a', '128k', f_final], capture_output=True)

        clean_title = (title if is_russian else GoogleTranslator(source='auto', target='ru').translate(title)).upper()
        desc_ru = get_short_facts(desc_raw if is_russian else GoogleTranslator(source='auto', target='ru').translate(desc_raw))
        
        caption = (
            f"<b>{mode_tag}</b>\n\n🎬 <b>{clean_title}</b>\n"
            f"─────────────────────\n\n🪐 <b>О ЧЕМ РОЛИК:</b>\n<i>{desc_ru}</i>\n\n"
            f"🐩 <b>Марти:</b> <i>{random.choice(MARTY_QUOTES)}</i>\n\n"
            f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
        )

        with open(f_final if os.path.exists(f_final) else f_raw, 'rb') as v:
            r = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo", 
                              files={"video": v}, data={"chat_id": CHANNEL_NAME, "caption": caption, "parse_mode": "HTML"}, timeout=600)
            return r.status_code == 200
    except: return False

# ============================================================
# 📡 НАВИГАТОР
# ============================================================

def get_videos(cid):
    try:
        url = f"https://www.googleapis.com/youtube/v3/channels?part=contentDetails&forHandle={cid.replace('@','')}&key={YOUTUBE_API_KEY}"
        up_id = requests.get(url).json()['items'][0]['contentDetails']['relatedPlaylists']['uploads']
        url_v = f"https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&playlistId={up_id}&maxResults=5&key={YOUTUBE_API_KEY}"
        return [{'id': i['snippet']['resourceId']['videoId'], 'title': i['snippet']['title'], 'desc': i['snippet']['description']} for i in requests.get(url_v).json()['items']]
    except: return []

async def main():
    print("🎬 [ЦУП] v144.2 'Precision Orbit' запуск...")
    db = open(DB_FILE, 'r').read() if os.path.exists(DB_FILE) else ""
    last_s = open(SOURCE_LOG, 'r').read().strip() if os.path.exists(SOURCE_LOG) else ""

    SOURCES = [
        {'n': 'KOSMO', 'cid': '@off_kosmo', 'ru': True},
        {'n': 'Ночная наука', 'cid': '@ночнаянаука-ц4ш', 'ru': True},
        {'n': 'AdMe', 'cid': '@AdMe', 'ru': True, 'filter': True},
        {'n': 'SpaceX Fan', 'cid': '@spacexfan420', 'ru': False},
        {'n': 'NASA', 'cid': '@NASAJPL', 'ru': False},
        {'n': 'ESO Observatory', 'cid': '@ESOobservatory', 'ru': False},
        {'n': 'Роскосмос ТВ', 'cid': '@tvroscosmos', 'ru': True}
    ]
    random.shuffle(SOURCES)
    
    for s in SOURCES:
        if s['n'] == last_s: continue
        print(f"📡 Сектор: {s['n']}")
        vids = get_videos(s['cid'])
        for v in vids:
            if v['id'] not in db:
                # Проверка фильтра для AdMe
                if s.get('filter'):
                    full_text = (v['title'] + v['desc']).lower()
                    if not any(kw in full_text for kw in SPACE_KEYWORDS):
                        print(f"⏭ Пропуск: ролик не о космосе ({v['title']})")
                        continue
                
                if await process_mission_v144(v['id'], v['title'], v['desc'], s['ru'], s['n']):
                    with open(DB_FILE, 'a') as f: f.write(f"\n{v['id']}")
                    with open(SOURCE_LOG, 'w') as f: f.write(s['n'])
                    print("🎉 Миссия успешно завершена!"); return
    print("🛰 Горизонт чист.")

if __name__ == '__main__':
    asyncio.run(main())
