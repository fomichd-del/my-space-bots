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

print("🚀 [ЦУП] Системы переведены в режим 'v170.0 Branded Edition'. Активация Intro/Outro и расширенных логов...")

# Настройки базы
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY') 
YOUTUBE_COOKIES = os.getenv('YOUTUBE_COOKIES') 
CHANNEL_NAME   = '@vladislav_space'
DB_FILE        = "last_video_date.txt"
SOURCE_LOG     = "last_source.txt"
SAFE_LIMIT_MB  = 46 

whisper_model = None

SPACE_KEYWORDS = ['космос', 'планета', 'звезда', 'галактика', 'марс', 'юпитер', 'сатурн', 'вселенная', 'астрономия', 'телескоп', 'млечный путь', 'черная дыра', 'астероид', 'метеорит', 'луна', 'солнце', 'ракета', 'spacex', 'nasa', 'роскосмос', 'инопланет', 'орбита', 'мкс', 'космонавт', 'астронавт', 'марсоход', 'starship']
USER_AGENTS = ['Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36']

# 🔥 Расширенный список выражений Марти (20 фраз)
MARTY_QUOTES = [
    "Гав! Теперь мой процессор работает правильно! 🧩🚀",
    "Ррр-гав! Вижу чистый горизонт событий! ✨",
    "Тяв! Командор, Node.js запущен, летим к звездам! 🛰️",
    "Гав! Вижу цель — новая галактика! Погнали! 🌌",
    "Тяв! Мои уши уловили сигнал из глубокого космоса! 📡",
    "Ррр-мяу... ой, то есть Гав! Сверхсветовая скорость активирована! 🚀",
    "Гав! Нашел косточку на обратной стороне Луны! 🦴🌘",
    "Тяв! Экипаж, пристегните ремни, мы входим в атмосферу! ☄️",
    "Гав! Все системы работают четко, как мои инстинкты! 🐾",
    "Ррр-гав! Звезды светят ярко, но наш канал — ярче! 🌟",
    "Гав! Загрузил данные прямо в облако... в настоящее облако Ориона! ☁️✨",
    "Тяв! Я проверил шлюзы — к полету готов! 🛸",
    "Гав! Марти на связи, помех не обнаружено! 🐕‍🚀",
    "Ррр-гав! Этот ролик горячее, чем поверхность Солнца! ☀️",
    "Гав! Я обнюхал этот файл — вирусов нет, только космос! 🧼🛰️",
    "Тяв! Прыжок через червоточину прошел успешно! 🌪️",
    "Гав! Вижу кольца Сатурна, они прекрасны! 🪐",
    "Ррр-гав! Командор, я поймал метеорит! Принести? 🐾☄️",
    "Тяв! Ракета заправлена, видео готово, Марти счастлив! 🧪🚀",
    "Гав! Одна маленькая лапа для собаки, один большой прыжок для канала! 🐾🌠"
]

def get_smart_summary(text):
    if not text: return "Интересные подробности — внутри ролика! ✨"
    text = re.sub(r'http\S+', '', text); text = re.sub(r'#\S+', '', text); text = html.unescape(text)
    junk = ['vk.com', 'ok.ru', 't.me', 'подписывайтесь', 'подпишись', 'наш канал', 'vpn', 'amnezia', 'сайт:', 'facebook', 'instagram', 'twitter', 'скачать', 'скачивай', 'ссылк', 'спонсор', 'реклама', 'промокод', 'скидк', 'boosty', 'patreon', 'поддержать', 'курсы', 'telegram']
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
            for p in proxies[:20]:
                p_str = f"http://{p.strip()}"
                try: requests.get("https://www.google.com", proxies={"https": p_str}, timeout=2); return p_str
                except: continue
    except: pass
    return None

async def process_mission(v_id, title, desc_raw, is_russian=False, source_name=""):
    global whisper_model
    if source_name in ["EVLSPACE", "ADME_RU"]:
        search_text = (title + " " + (desc_raw if desc_raw else "")).lower()
        if not any(word in search_text for word in SPACE_KEYWORDS): return False
            
    f_raw, f_final, f_thumb, f_cookies = "raw_video.mp4", "final_video.mp4", "thumb.jpg", "cookies.txt"
    f_intro, f_outro = "intro.png", "intro0.png"
    for f in [f_raw, f_final, "subs.srt", f_thumb, f_cookies]:
        if os.path.exists(f): os.remove(f)

    if YOUTUBE_COOKIES:
        with open(f_cookies, "w", encoding="utf-8") as f: f.write(YOUTUBE_COOKIES)

    try:
        v_url = f"https://www.youtube.com/watch?v={v_id}"
        proxy = get_fast_proxy()
        print(f"📡 [ЦУП] Анализ объекта {v_id} ({source_name})...")
        
        base_ydl_opts = {
            'quiet': True, 'proxy': proxy if proxy else None,
            'user_agent': random.choice(USER_AGENTS),
            'nocheckcertificate': True,
            'js_runtimes': {'node': {}}, 
            'remote_components': ['ejs:github'], 
            'extractor_args': {'youtube': {'player_client': ['tv', 'web'], 'player_skip': ['configs']}},
            'sleep_interval': random.uniform(5, 10)
        }
        if os.path.exists(f_cookies): base_ydl_opts['cookiefile'] = f_cookies
        
        with yt_dlp.YoutubeDL(base_ydl_opts) as ydl:
            try: info = ydl.extract_info(v_url, download=False)
            except Exception as e: print(f"⚠️ Ошибка доступа: {e}"); return False
            
            duration = info.get('duration', 1)
            orig_size = (info.get('filesize') or info.get('filesize_approx') or 0) / (1024 * 1024)
            print(f"⚖️ ТТХ: {duration}с | ~{orig_size:.1f}Мб")

        if duration > 3600: return False

        h_limit = 720
        if duration > 1800 or orig_size > 800: h_limit = 240
        elif duration > 900 or orig_size > 500: h_limit = 360
        elif duration > 480 or orig_size > 300: h_limit = 480
        
        download_opts = base_ydl_opts.copy()
        download_opts.update({
            'format': f'bestvideo[height<={h_limit}][ext=mp4]+bestaudio[ext=m4a]/best[height<={h_limit}]',
            'outtmpl': f_raw, 'quiet': False
        })
        with yt_dlp.YoutubeDL(download_opts) as ydl: ydl.download([v_url])
        if not os.path.exists(f_raw): return False
        
        has_subs = False
        if not is_russian:
            print("🧠 Whisper..."); if whisper_model is None: whisper_model = whisper.load_model("base")
            res = whisper_model.transcribe(f_raw)
            if len(res.get('text', '').strip()) > 15:
                srt = ""; [srt.update(f"{i+1}\n{time.strftime('%H:%M:%S,000', time.gmtime(seg['start']))} --> {time.strftime('%H:%M:%S,000', time.gmtime(seg['end']))}\n{GoogleTranslator(source='auto', target='ru').translate(seg['text'].strip())}\n\n") for i, seg in enumerate(res.get('segments', []))]
                with open("subs.srt", "w", encoding="utf-8") as fs: fs.write(srt)
                has_subs = True

        # 🔥 ГЕНЕРАЦИЯ БРЕНДИРОВАННОГО ВИДЕО (Intro + Main + Outro)
        print("🎬 Монтаж заставок и сжатие...")
        target_total_bps = int((44 * 1024 * 1024 * 8) / (duration + 4)) # +4 сек на заставки
        v_br = max(40000, min(target_total_bps - 32000, 2200000))
        
        # Сложный фильтр FFmpeg: масштабируем картинки под видео, накладываем субтитры, склеиваем
        filter_complex = f"[1:v]scale=-2:{h_limit}"
        if has_subs: filter_complex += ",subtitles=subs.srt:force_style='FontSize=20,BorderStyle=3'"
        filter_complex += f"[mainv]; [0:v]scale=-2:{h_limit},setsar=1[introv]; [2:v]scale=-2:{h_limit},setsar=1[outrov]; [introv][mainv][outrov]concat=n=3:v=1:a=0[outv]"

        cmd = [
            'ffmpeg', '-y',
            '-loop', '1', '-t', '2', '-i', f_intro if os.path.exists(f_intro) else f_raw, # Интро
            '-i', f_raw, # Основное видео
            '-loop', '1', '-t', '2', '-i', f_outro if os.path.exists(f_outro) else f_raw, # Финал
            '-filter_complex', filter_complex,
            '-map', '[outv]', '-map', '1:a?', # Берем склеенное видео и звук из оригинала
            '-c:v', 'libx264', '-b:v', str(v_br), '-preset', 'ultrafast', '-movflags', '+faststart',
            '-c:a', 'aac', '-b:a', '32k', f_final
        ]
        subprocess.run(cmd)
        f_to_send = f_final if os.path.exists(f_final) else f_raw

        # В качестве обложки всегда используем intro.png, если оно есть
        if os.path.exists(f_intro):
            subprocess.run(['ffmpeg', '-y', '-i', f_intro, '-vf', 'scale=320:-1', f_thumb], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            subprocess.run(['ffmpeg', '-y', '-i', f_to_send, '-ss', '00:00:02', '-vframes', '1', '-vf', 'scale=320:-1', f_thumb])

        ru_title = (title if is_russian else GoogleTranslator(source='auto', target='ru').translate(title)).replace('<', '«').replace('>', '»').replace('&', 'и')
        summary = get_smart_summary(desc_raw if is_russian else GoogleTranslator(source='auto', target='ru').translate(desc_raw))
        caption = f"<b>{'🎙 ОРИГИНАЛ' if is_russian else '📝 ПЕРЕВОД'}</b>\n\n🎬 <b>{ru_title.upper()}</b>\n──────────────────────\n\n🚀 <b>В ЭТОМ ВЫПУСКЕ:</b>\n<i>{summary}</i>\n\n<b>Марти:</b> <i>{random.choice(MARTY_QUOTES)}</i>\n\n📡 <a href='https://t.me/vladislav_space'>ДНЕВНИК ЮНОГО КОСМОНАВТА</a>"

        with open(f_to_send, 'rb') as v:
            files = {"video": v}
            if os.path.exists(f_thumb): files["thumbnail"] = open(f_thumb, 'rb')
            r = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo", files=files, data={"chat_id": CHANNEL_NAME, "caption": caption, "parse_mode": "HTML", "supports_streaming": "true"}, timeout=600)
            return r.status_code == 200
    except Exception as e: print(f"⚠️ Сбой: {e}"); return False
    finally:
        for f in [f_cookies, f_raw, f_final, f_thumb, "subs.srt"]:
            if os.path.exists(f): os.remove(f)

async def main():
    db = open(DB_FILE, 'r').read() if os.path.exists(DB_FILE) else ""
    last_s = open(SOURCE_LOG, 'r').read().strip() if os.path.exists(SOURCE_LOG) else ""
    SOURCES = [{'n': 'ADME_RU', 'cid': '@ADME_RU', 'ru': True}, {'n': 'SpaceX Fan', 'cid': '@spacexfan420', 'ru': True}, {'n': 'Rocket Hub', 'cid': '@rockethubspace', 'ru': True}, {'n': 'NASA', 'cid': '@NASAJPL', 'ru': False}, {'n': 'KOSMO', 'cid': '@off_kosmo', 'ru': True}, {'n': 'EVLSPACE', 'cid': '@EVLSPACE', 'ru': True}, {'n': 'ночнаянаука-ц4ш', 'cid': '@ночнаянаука-ц4ш', 'ru': True}, {'n': 'Hubbler', 'cid': '@Hubbler', 'ru': True}, {'n': 'Cosmosprosto', 'cid': '@cosmosprosto', 'ru': True}]
    random.shuffle(SOURCES)
    for s in SOURCES:
        if s['n'] == last_s: continue
        try:
            url = f"https://www.googleapis.com/youtube/v3/channels?part=contentDetails&forHandle={s['cid'].replace('@','')}&key={YOUTUBE_API_KEY}"
            res = requests.get(url).json(); up_id = res['items'][0]['contentDetails']['relatedPlaylists']['uploads']
            vids = [{'id': i['snippet']['resourceId']['videoId'], 'title': i['snippet']['title'], 'desc': i['snippet']['description']} for i in requests.get(f"https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&playlistId={up_id}&maxResults=3&key={YOUTUBE_API_KEY}").json()['items']]
            for v in vids:
                if v['id'] not in db:
                    if await process_mission(v['id'], v['title'], v['desc'], s['ru'], s['n']):
                        with open(DB_FILE, 'a') as f: f.write(f"\n{v['id']}")
                        with open(SOURCE_LOG, 'w') as f: f.write(s['n']); return
        except: continue

if __name__ == '__main__': asyncio.run(main())
