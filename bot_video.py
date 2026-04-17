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
# ⚙️ КОНФИГУРАЦИЯ v147.2 (Ultra Compression Protocol)
# ============================================================
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY') 
CHANNEL_NAME   = '@vladislav_space'
DB_FILE        = "last_video_date.txt"
SOURCE_LOG     = "last_source.txt"
SAFE_LIMIT_MB  = 40 

SPACE_KEYWORDS = ['космос', 'вселенная', 'планета', 'звезд', 'галактик', 'астероид', 'черная дыра', 'марса', 'луна', 'солнц', 'космическ', 'spacex', 'nasa', 'телескоп', 'мкс', 'astronomy', 'universe', 'telescope']

try:
    model = whisper.load_model("base")
except:
    model = None

MARTY_QUOTES = [
    "Гав! Видео было тяжелым, но я упаковал его как штурманскую карту! 📦🐩",
    "Ррр-гав! Включаю режим ультра-сжатия, прорвемся в Телеграм! ✨",
    "Тяв! Командор, даже 300 мегабайт теперь не преграда для нашей ракеты! 🐾",
    "Гав! Уменьшил картинку, зато сохранил всю суть миссии! 🛰️"
]

# ============================================================
# 🛠 ИНСТРУМЕНТЫ
# ============================================================

def get_short_facts(text):
    if not text: return "Подробности миссии смотрите в ролике! ✨"
    text = re.sub(r'http\S+', '', text).strip()
    text = html.unescape(text)
    return text[:250] + "..." if len(text) > 250 else text

def get_fast_proxy():
    print("🛰 [ЦУП] Поиск гипер-коридора...")
    url = "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=5000&country=all&ssl=all&anonymity=all"
    try:
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            proxies = resp.text.strip().split('\n')
            random.shuffle(proxies)
            for p in proxies[:30]:
                try:
                    requests.get("https://www.google.com", proxies={"https": f"http://{p.strip()}"}, timeout=2)
                    return f"http://{p.strip()}"
                except: continue
    except: pass
    return None

# ============================================================
# 🎬 ПРОЦЕССОР (v147.2 Ultra Compression)
# ============================================================

async def process_mission_v147(v_id, title, desc_raw, is_russian=False, source_name=""):
    f_raw, f_final = "raw_video.mp4", "final_video.mp4"
    for f in [f_raw, f_final, "subs.srt"]:
        if os.path.exists(f): os.remove(f)

    try:
        v_url = f"https://www.youtube.com/watch?v={v_id}"
        proxy = get_fast_proxy()
        
        modern_args = ['player_client=mweb', 'player_skip=webpage']
        ydl_opts = {
            'format': 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720]',
            'outtmpl': f_raw,
            'quiet': True,
            'extractor_args': {'youtube': modern_args},
            'js_runtimes': {'deno': {}},
            'retries': 20,
            'fragment_retries': 50,
            'continuedl': True
        }
        if proxy: ydl_opts['proxy'] = proxy

        print(f"📡 [ЦУП] Захват объекта: {v_id} ({source_name})...")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(v_url, download=True)
            duration = info.get('duration', 1)
            raw_size = os.path.getsize(f_raw)
            raw_mb = raw_size / (1024 * 1024)

        print(f"⚖️ Вес: {raw_mb:.1f}Мб, Длительность: {duration}сек")

        # Анализ Whisper (для иностранных)
        has_subs, mode_tag = False, "🎙 ОРИГИНАЛЬНАЯ ОЗВУЧКА"
        if not is_russian and model:
            print(f"🎙 Whisper: Анализ аудио...")
            res = model.transcribe(f_raw)
            if len(res.get('text', '').strip()) > 15:
                mode_tag = "📝 ПЕРЕВОД (СУБТИТРЫ)"
                srt = ""
                for i, seg in enumerate(res.get('segments', [])):
                    t_ru = GoogleTranslator(source='auto', target='ru').translate(seg['text'].strip())
                    srt += f"{i+1}\n{time.strftime('%H:%M:%S,000', time.gmtime(seg['start']))} --> {time.strftime('%H:%M:%S,000', time.gmtime(seg['end']))}\n{t_ru}\n\n"
                with open("subs.srt", "w", encoding="utf-8") as fs: fs.write(srt)
                has_subs = True
            else: mode_tag = "🎵 МУЗЫКА КОСМОСА"
        elif not is_russian: mode_tag = "🎵 МУЗЫКА КОСМОСА"

        # ЛОГИКА СЖАТИЯ v147.2 (Ultra)
        if raw_mb < SAFE_LIMIT_MB and not has_subs:
            print("🚀 Оригинал проходит по лимитам.")
            f_to_send = f_raw
        else:
            print("⚙️ Режим глубокой упаковки...")
            # Выбор разрешения на основе веса ИЛИ длительности
            if raw_mb > 180 or duration > 1800:
                scale = "scale=-2:240"
                print("📉 Режим: 240p (Ультра-экономия)")
            elif raw_mb > 100 or duration > 900:
                scale = "scale=-2:360"
                print("📉 Режим: 360p (Баланс)")
            else:
                scale = "scale=-2:480"
                print("📉 Режим: 480p (Стандарт)")

            # Жесткий расчет битрейта
            target_br = int((SAFE_LIMIT_MB * 1024 * 1024 * 8) / duration * 0.8)
            v_br = max(100000, min(target_br, 2000000))
            
            vf = f"subtitles=subs.srt:force_style='FontSize=20,BorderStyle=3,BackColour=&H80000000'" if has_subs else scale
            
            print(f"🛠 FFmpeg: Форсируем {v_br//1000}kbps...")
            subprocess.run(['ffmpeg', '-y', '-i', f_raw, '-vf', vf, '-c:v', 'libx264', '-b:v', str(v_br), '-preset', 'veryfast', '-c:a', 'aac', '-b:a', '64k', f_final], capture_output=True)
            f_to_send = f_final

        # ОТПРАВКА
        final_mb = os.path.getsize(f_to_send) / (1024 * 1024)
        print(f"📡 Отправка ({final_mb:.1f} Мб)...")
        
        clean_title = (title if is_russian else GoogleTranslator(source='auto', target='ru').translate(title)).upper()
        caption = (
            f"<b>{mode_tag}</b>\n\n🎬 <b>{clean_title}</b>\n─────────────────────\n\n"
            f"🪐 <b>О ЧЕМ РОЛИК:</b>\n<i>{get_short_facts(desc_raw if is_russian else GoogleTranslator(source='auto', target='ru').translate(desc_raw))}</i>\n\n"
            f"<b>Марти:</b> <i>{random.choice(MARTY_QUOTES)}</i>\n\n🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
        )

        with open(f_to_send, 'rb') as v:
            r = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo", files={"video": v}, data={"chat_id": CHANNEL_NAME, "caption": caption, "parse_mode": "HTML"}, timeout=600)
            if r.status_code == 200:
                print("✅ Успешная доставка!")
                return True
            else:
                print(f"❌ Ошибка Telegram: {r.text}")
                return False
    except Exception as e:
        print(f"⚠️ Сбой: {e}"); return False

async def main():
    print(f"🎬 [ЦУП] v147.2 'Ultra Compression' запуск...")
    db = open(DB_FILE, 'r').read() if os.path.exists(DB_FILE) else ""
    last_s = open(SOURCE_LOG, 'r').read().strip() if os.path.exists(SOURCE_LOG) else ""

    SOURCES = [
        {'n': 'Rocket Hub', 'cid': '@rockethubspace', 'ru': True},
        {'n': 'SpaceX Fan', 'cid': '@spacexfan420', 'ru': False},
        {'n': 'NASA', 'cid': '@NASAJPL', 'ru': False},
        {'n': 'KOSMO', 'cid': '@off_kosmo', 'ru': True},
        {'n': 'ESO Observatory', 'cid': '@ESOobservatory', 'ru': False},
        {'n': 'Ночная наука', 'cid': '@ночнаянаука-ц4ш', 'ru': True},
        {'n': 'Роскосмос ТВ', 'cid': '@tvroscosmos', 'ru': True},
        {'n': 'AdMe', 'cid': '@AdMe', 'ru': True, 'filter': True}
    ]
    random.shuffle(SOURCES)
    
    for s in SOURCES:
        if s['n'] == last_s: continue
        print(f"📡 Сектор: {s['n']}")
        try:
            url = f"https://www.googleapis.com/youtube/v3/channels?part=contentDetails&forHandle={s['cid'].replace('@','')}&key={YOUTUBE_API_KEY}"
            up_id = requests.get(url).json()['items'][0]['contentDetails']['relatedPlaylists']['uploads']
            vids = [{'id': i['snippet']['resourceId']['videoId'], 'title': i['snippet']['title'], 'desc': i['snippet']['description']} for i in requests.get(f"https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&playlistId={up_id}&maxResults=3&key={YOUTUBE_API_KEY}").json()['items']]
            for v in vids:
                if v['id'] not in db:
                    if s.get('filter') and not any(kw in (v['title'] + v['desc']).lower() for kw in SPACE_KEYWORDS): continue
                    if await process_mission_v147(v['id'], v['title'], v['desc'], s['ru'], s['n']):
                        with open(DB_FILE, 'a') as f: f.write(f"\n{v['id']}")
                        with open(SOURCE_LOG, 'w') as f: f.write(s['n'])
                        return
        except: continue
    print("🛰 Горизонт чист.")

if __name__ == '__main__':
    asyncio.run(main())
