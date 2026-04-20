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

print("🚀 [ЦУП] Системы v174.0 'Diagnostic' активны. Марти включил рацию на полную!")

# Настройки (Золотой стандарт)
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY') 
YOUTUBE_COOKIES = os.getenv('YOUTUBE_COOKIES') 
CHANNEL_NAME   = '@vladislav_space'
DB_FILE        = "last_video_date.txt"
SOURCE_LOG     = "last_source.txt"
SAFE_LIMIT_MB  = 46 

INTRO_FILE = "intro.png"
OUTRO_FILE = "intro0.png"

whisper_model = None

SPACE_KEYWORDS = ['космос', 'планета', 'звезда', 'галактика', 'марс', 'юпитер', 'сатурн', 'вселенная', 'астрономия', 'телескоп', 'млечный путь', 'черная дыра', 'астероид', 'метеорит', 'луна', 'солнце', 'ракета', 'spacex', 'nasa', 'роскосмос', 'инопланет', 'орбита', 'мкс', 'космонавт', 'астронавт', 'марсоход', 'starship']
USER_AGENTS = ['Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36']

MARTY_QUOTES = [
    "Гав! Засек неопознанный летающий объект! 🛸",
    "Ррр-гав! Все системы в норме, летим к звездам! ✨",
    "Тяв! Командор, я нашел лучшие кадры из глубокого космоса! 🛰️",
    "Гав! Мой хвост вибрирует от мощности этой ракеты! 🚀",
    "Ррр-гав! Взломал код Вселенной, несите косточку! 🦴",
    "Гав! Вижу Марс, он такой же рыжий, как моя любимая игрушка! 🟠",
    "Тяв! Космическая пыль не помеха для моего носа! 🐕",
    "Гав! Пролетаем через туманность, выглядит эпично! 🌌",
    "Ррр-гав! Выхожу в открытый космос без скафандра, я же супер-пес! 🧑‍🚀",
    "Тяв! Командор, связь с Землей стабильна, передаю данные! 📡",
    "Гав! На этой планете точно есть жизнь, я слышу шорох! 👽",
    "Ррр-гав! Стартуем через 3... 2... 1... Поехали! 💥",
    "Тяв! Галактика под моим присмотром, спите спокойно! 💤",
    "Гав! Я проверил битрейт, он такой же четкий, как мой лай! 💎",
    "Ррр-гав! Кажется, я нашел планету из чистого сыра! 🧀",
    "Тяв! Подключаю нейросети для перевода инопланетного лая! 🧠",
    "Гав! Владислав, смотрите какой ракурс! Просто космос! 📸",
    "Ррр-гав! Мои лапы готовы к высадке на Луну! 🌙",
    "Тяв! Космический ветер дует прямо в уши, обожаю это чувство! 💨",
    "Гав! Миссия выполнена, возвращаюсь на базу за наградой! 🏆"
]

def get_smart_summary(text):
    if not text: return "Тайны космоса ждут вас внутри этого выпуска! ✨"
    text = re.sub(r'http\S+', '', text); text = re.sub(r'#\S+', '', text); text = html.unescape(text)
    junk = ['vk.com', 'ok.ru', 't.me', 'подписывайтесь', 'подпишись', 'наш канал', 'vpn', 'amnezia', 'сайт:', 'facebook', 'instagram', 'twitter', 'скачать', 'скачивай', 'ссылк', 'спонсор', 'реклама', 'промокод', 'скидк', 'boosty', 'patreon', 'поддержать', 'курсы', 'telegram', 'страхован', 'полис', 'кинопоиск', 'плей-офф', 'кхл', 'билет', 'т-банк', 'тинькофф']
    lines = [l.strip() for l in text.split('\n') if len(l.strip()) > 25 and not any(j in l.lower() for j in junk)]
    lines = [l for l in lines if not re.match(r'^\d{1,2}:\d{2}', l)]
    full = " ".join(lines); sentences = re.split(r'(?<=[.!?]) +', full)
    res = " ".join([s.strip() for s in sentences if len(s) > 35][:2])
    if not res or len(res) < 15: res = "Погружаемся в тайны Вселенной в новом выпуске! Приятного просмотра."
    return res.replace('<', '«').replace('>', '»').replace('&', 'и')

def get_fast_proxy():
    url = "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=5000&country=all&ssl=all&anonymity=all"
    try:
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            proxies = resp.text.strip().split('\n'); random.shuffle(proxies)
            for p in proxies[:15]:
                p_str = f"http://{p.strip()}"
                try: requests.get("https://www.google.com", proxies={"https": p_str}, timeout=2); return p_str
                except: continue
    except: pass
    return None

async def process_mission(v_id, title, desc_raw, is_russian=False, source_name=""):
    global whisper_model
    if source_name in ["EVLSPACE", "ADME_RU"]:
        search_text = (title + " " + (desc_raw if desc_raw else "")).lower()
        if not any(word in search_text for word in SPACE_KEYWORDS): 
            print(f"⏭ [ЦУП] Объект {v_id} не прошел космо-фильтр."); return False
            
    f_raw, f_final, f_thumb, f_cookies = "raw_video.mp4", "final_video.mp4", "thumb.jpg", "cookies.txt"
    for f in [f_raw, f_final, "subs.srt", f_thumb, f_cookies]:
        if os.path.exists(f): os.remove(f)

    if YOUTUBE_COOKIES:
        with open(f_cookies, "w", encoding="utf-8") as f: f.write(YOUTUBE_COOKIES)

    try:
        v_url = f"https://www.youtube.com/watch?v={v_id}"
        proxy = get_fast_proxy()
        print(f"📡 [ЦУП] Анализ объекта {v_id}...")
        
        base_ydl_opts = {
            'quiet': True, 'proxy': proxy if proxy else None,
            'user_agent': random.choice(USER_AGENTS),
            'nocheckcertificate': True,
            'js_runtimes': {'node': {}}, 
            'remote_components': ['ejs:github'], 
            'socket_timeout': 40,
            'extractor_args': {'youtube': {'player_client': ['tv', 'web'], 'player_skip': ['configs']}},
            'sleep_interval': random.uniform(5, 10)
        }
        if os.path.exists(f_cookies): base_ydl_opts['cookiefile'] = f_cookies
        
        with yt_dlp.YoutubeDL(base_ydl_opts) as ydl:
            try: info = ydl.extract_info(v_url, download=False)
            except Exception as e: print(f"⚠️ Ошибка YouTube API: {e}"); return False
            duration = info.get('duration', 0)
            filesize = (info.get('filesize') or info.get('filesize_approx') or 0) / (1024 * 1024)
            print(f"⏱ Длительность: {duration} сек. Вес: {filesize:.1f} Мб")

        if duration > 3600: 
            print("⚠️ Видео слишком длинное (> 1 часа). Пропускаем."); return False
        if duration == 0:
            print("⚠️ Не удалось определить длительность. Возможно, стрим или блок."); return False

        h_limit = 720
        if duration > 1800 or filesize > 800: h_limit = 240
        elif duration > 900 or filesize > 500: h_limit = 360
        elif duration > 480 or filesize > 300: h_limit = 480
        
        w_limit = {240: 426, 360: 640, 480: 854, 720: 1280}.get(h_limit, 426)

        print(f"📥 Начинаю загрузку (Лимит {h_limit}p)...")
        with yt_dlp.YoutubeDL({**base_ydl_opts, 'format': f'bestvideo[height<={h_limit}][ext=mp4]+bestaudio[ext=m4a]/best[height<={h_limit}]', 'outtmpl': f_raw}) as ydl:
            ydl.download([v_url])
            
        if not os.path.exists(f_raw): 
            print("⚠️ Файл не был скачан. Прокси подвел?"); return False
        
        has_subs = False
        if not is_russian:
            print("🧠 Whisper... (Перевод)"); if whisper_model is None: whisper_model = whisper.load_model("base")
            res = whisper_model.transcribe(f_raw); segments = res.get('segments', [])
            if segments:
                srt_data = []
                for i, seg in enumerate(segments):
                    t_start = time.strftime('%H:%M:%S,000', time.gmtime(seg['start']))
                    t_end = time.strftime('%H:%M:%S,000', time.gmtime(seg['end']))
                    text = GoogleTranslator(source='auto', target='ru').translate(seg['text'].strip())
                    srt_data.append(f"{i+1}\n{t_start} --> {t_end}\n{text}\n\n")
                with open("subs.srt", "w", encoding="utf-8") as fs: fs.write("".join(srt_data))
                has_subs = True

        print("🎬 Монтаж 'Космического Сэндвича'...")
        target_total_bps = int((44 * 1024 * 1024 * 8) / (duration + 4))
        v_br = max(40000, min(target_total_bps - 32000, 2000000))
        
        if os.path.exists(INTRO_FILE) and os.path.exists(OUTRO_FILE):
            filter_pad = f"scale={w_limit}:{h_limit}:force_original_aspect_ratio=decrease,pad={w_limit}:{h_limit}:(ow-iw)/2:(oh-ih)/2,setsar=1"
            ff_cmd = ['ffmpeg', '-y', '-loop', '1', '-t', '2', '-i', INTRO_FILE, '-i', f_raw, '-loop', '1', '-t', '2', '-i', OUTRO_FILE, '-filter_complex', f"[0:v]{filter_pad}[v0];[1:v]{'subtitles=subs.srt:' if has_subs else ''}{filter_pad}[v1];[2:v]{filter_pad}[v2];[v0][v1][v2]concat=n=3:v=1:a=0[v];[1:a]adelay=2000|2000:all=1[a]", '-map', '[v]', '-map', '[a]', '-c:v', 'libx264', '-b:v', str(v_br), '-preset', 'ultrafast', '-c:a', 'aac', '-b:a', '32k', '-ar', '44100', f_final]
        else:
            vf = f"{'subtitles=subs.srt:' if has_subs else ''}scale=-2:{h_limit}"
            ff_cmd = ['ffmpeg', '-y', '-i', f_raw, '-vf', vf, '-c:v', 'libx264', '-b:v', str(v_br), '-preset', 'ultrafast', '-c:a', 'aac', '-b:a', '32k', f_final]
        
        subprocess.run(ff_cmd); f_to_send = f_final if os.path.exists(f_final) else f_raw

        # Превью
        if os.path.exists(INTRO_FILE): subprocess.run(['ffmpeg', '-y', '-i', INTRO_FILE, '-vf', 'scale=320:-1', f_thumb], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else: subprocess.run(['ffmpeg', '-y', '-i', f_to_send, '-ss', '00:00:01.000', '-vframes', '1', '-vf', 'scale=320:-1', f_thumb], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        ru_title = (title if is_russian else GoogleTranslator(source='auto', target='ru').translate(title)).replace('<', '«').replace('>', '»')
        summary = get_smart_summary(desc_raw if is_russian else GoogleTranslator(source='auto', target='ru').translate(desc_raw))
        caption = f"<b>{'🎙 ОРИГИНАЛ' if is_russian else '📝 ПЕРЕВОД'}</b>\n\n🎬 <b>{ru_title.upper()}</b>\n──────────────────────\n\n🚀 <b>В ЭТОМ ВЫПУСКЕ:</b>\n<i>{summary}</i>\n\n<b>Марти:</b> <i>{random.choice(MARTY_QUOTES)}</i>\n\n📡 <a href='https://t.me/vladislav_space'>ДНЕВНИК ЮНОГО КОСМОНАВТА</a>"

        with open(f_to_send, 'rb') as v:
            files = {"video": v}
            if os.path.exists(f_thumb): files["thumbnail"] = open(f_thumb, 'rb')
            requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo", files=files, data={"chat_id": CHANNEL_NAME, "caption": caption, "parse_mode": "HTML", "supports_streaming": "true"}, timeout=600)
            print("✅ ПОБЕДА! Видео отправлено."); return True
    except Exception as e: print(f"⚠️ Сбой миссии: {e}"); return False

async def main():
    db = open(DB_FILE, 'r').read() if os.path.exists(DB_FILE) else ""
    last_s = open(SOURCE_LOG, 'r').read().strip() if os.path.exists(SOURCE_LOG) else ""
    SOURCES = [{'n': 'ADME_RU', 'cid': '@ADME_RU', 'ru': True}, {'n': 'SpaceX Fan', 'cid': '@spacexfan420', 'ru': True}, {'n': 'Rocket Hub', 'cid': '@rockethubspace', 'ru': True}, {'n': 'NASA', 'cid': '@NASAJPL', 'ru': False}, {'n': 'KOSMO', 'cid': '@off_kosmo', 'ru': True}, {'n': 'EVLSPACE', 'cid': '@EVLSPACE', 'ru': True}, {'n': 'ночнаянаука-ц4ш', 'cid': '@ночнаянаука-ц4ш', 'ru': True}, {'n': 'Hubbler', 'cid': '@Hubbler', 'ru': True}, {'n': 'Cosmosprosto', 'cid': '@cosmosprosto', 'ru': True}]
    random.shuffle(SOURCES)
    for s in SOURCES:
        if s['n'] == last_s: continue
        print(f"🛰 [ЦУП] Смена сектора: {s['n']}...")
        try:
            url = f"https://www.googleapis.com/youtube/v3/channels?part=contentDetails&forHandle={s['cid'].replace('@','')}&key={YOUTUBE_API_KEY}"
            res = requests.get(url).json(); up_id = res['items'][0]['contentDetails']['relatedPlaylists']['uploads']
            vids_resp = requests.get(f"https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&playlistId={up_id}&maxResults=3&key={YOUTUBE_API_KEY}").json()
            vids = [{'id': i['snippet']['resourceId']['videoId'], 'title': i['snippet']['title'], 'desc': i['snippet']['description']} for i in vids_resp.get('items', [])]
            for v in vids:
                if v['id'] not in db:
                    if await process_mission(v['id'], v['title'], v['desc'], s['ru'], s['n']):
                        with open(DB_FILE, 'a') as f: f.write(f"\n{v['id']}")
                        with open(SOURCE_LOG, 'w') as f: f.write(s['n']); return
        except Exception as e: print(f"⚠️ Ошибка источника {s['n']}: {e}"); continue

if __name__ == '__main__': asyncio.run(main())
