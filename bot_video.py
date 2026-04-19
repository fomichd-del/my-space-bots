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

print("🚀 [ЦУП] Системы переведены в режим 'Titanium Base v2.0'. Анти-краш плеера и чистый текст активированы...")

# ============================================================
# ⚙️ КОНФИГУРАЦИЯ
# ============================================================
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY') 
CHANNEL_NAME   = '@vladislav_space'
DB_FILE        = "last_video_date.txt"
SOURCE_LOG     = "last_source.txt"
SAFE_LIMIT_MB  = 46 

whisper_model = None

# Звездный фильтр для каналов со смешанным контентом
SPACE_KEYWORDS = [
    'космос', 'планета', 'звезда', 'галактика', 'марс', 'юпитер', 'сатурн', 
    'вселенная', 'астрономия', 'телескоп', 'млечный путь', 'черная дыра', 
    'астероид', 'метеорит', 'луна', 'солнце', 'ракета', 'spacex', 'nasa', 'роскосмос',
    'инопланет', 'орбита', 'мкс', 'космонавт', 'астронавт', 'марсоход', 'starship'
]

# Список современных User-Agent для маскировки
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0'
]

MARTY_QUOTES = [
    "Гав! Вижу цель — свежие новости с орбиты доставлены! 🚀🐾",
    "Ррр-гав! Хвост виляет со скоростью света от такого видео! ✨",
    "Тяв! Проверил обшивку — ни одной космической кошки на борту! 🛰️",
    "Гав! В космосе никто не услышит твой лай, но мой пост увидят все! 🌌",
    "Тяв! Обнаружил планету, похожую на гигантский теннисный мяч! 🎾🌍",
    "Гав! Навострил уши — ловлю сигналы из самых дальних галактик! 📡",
    "Ррр-гав! Эта миссия пахнет успехом и немного звездной пылью! 🐕🌠",
    "Гав! Передал данные быстрее, чем летит метеорит! ☄️🐾",
    "Тяв! Командор, я проверил: на Луне сыра нет, только пыль! 🌑",
    "Гав! В невесомости мои уши смешно разлетаются, но я на посту! 👂",
    "Ррр-гав! Защищаю канал от скуки лучше, чем нейросеть! 🛡️",
    "Тяв! Если увидите в небе комету — это я за ней погнался! 🐕💨",
    "Гав! Мой нос подсказывает: это видео станет хитом на Земле! 👃",
    "Гав! Даже в скафандре я выгляжу потрясающе, согласны? 🧑‍🚀",
    "Ррр-гав! Слежу за приборами, пока Командор изучает карту! 🕹️",
    "Тяв! Это видео такое классное, что я чуть не сгрыз антенну! 📺",
    "Гав! Проложил путь сквозь пояс астероидов, не благодарите! 🗺️",
    "Ррр-гав! Встретил инопланетян — они тоже любят ласку! 👽",
    "Тяв! На борту порядок, все косточки пересчитаны! 🦴✅",
    "Гав! Летим к звездам! Пристегните ремни, лапы и хвосты! 🚀🐾",
    "Ррр-гав! Мой журнал полон открытий, делюсь лучшим! 📒✨"
]

def get_smart_summary(text):
    if not text: return "Интересные подробности — внутри ролика! ✨"
    text = re.sub(r'http\S+', '', text)
    text = re.sub(r'#\S+', '', text)
    text = html.unescape(text)
    
    # 🔥 Расширенный агрессивный фильтр от мусора и рекламы
    junk = [
        'vk.com', 'ok.ru', 't.me', 'подписывайтесь', 'подпишись', 'наш канал', 
        'vpn', 'amnezia', 'сайт:', 'facebook', 'instagram', 'twitter',
        'скачать', 'скачивай', 'ссылк', 'спонсор', 'реклама', 'промокод', 
        'скидк', 'boosty', 'patreon', 'поддержать', 'курсы', 'telegram'
    ]
    
    lines = [l.strip() for l in text.split('\n') if len(l.strip()) > 25 and not any(j in l.lower() for j in junk)]
    lines = [l for l in lines if not re.match(r'^\d{1,2}:\d{2}', l)]
    full = " ".join(lines)
    sentences = re.split(r'(?<=[.!?]) +', full)
    res = " ".join([s.strip() for s in sentences if len(s) > 35][:2])
    res = res if len(res) > 30 else full[:200].strip()
    
    # Если после фильтрации описание оказалось пустым
    if not res or len(res) < 15:
        res = "Погружаемся в тайны Вселенной в новом выпуске! Приятного просмотра."
    
    # 100% Защита от поломки HTML в Telegram
    return res.replace('<', '«').replace('>', '»').replace('&', 'и')

def get_fast_proxy():
    print("🛰 [ЦУП] Поиск гипер-коридора...")
    url = "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=5000&country=all&ssl=all&anonymity=all"
    try:
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            proxies = resp.text.strip().split('\n')
            random.shuffle(proxies)
            for p in proxies[:60]:
                p_str = f"http://{p.strip()}"
                try:
                    requests.get("https://www.google.com", proxies={"https": p_str}, timeout=2)
                    return p_str
                except: continue
    except: pass
    return None

async def process_mission(v_id, title, desc_raw, is_russian=False, source_name=""):
    global whisper_model
    
    # --- 🛡 ЗВЕЗДНЫЙ ФИЛЬТР (Для EVLSPACE и т.д.) ---
    if source_name == "EVLSPACE":
        search_text = (title + " " + (desc_raw if desc_raw else "")).lower()
        if not any(word in search_text for word in SPACE_KEYWORDS):
            print(f"⏭ [ЦУП] Объект {source_name} ({v_id}) не прошел фильтр (не о космосе). Пропускаем.")
            return False
            
    f_raw, f_final, f_thumb = "raw_video.mp4", "final_video.mp4", "thumb.jpg"
    for f in [f_raw, f_final, "subs.srt", f_thumb]:
        if os.path.exists(f): os.remove(f)

    try:
        v_url = f"https://www.youtube.com/watch?v={v_id}"
        proxy = get_fast_proxy()
        
        # --- 1. РАЗВЕДКА И АНТИ-БАН ---
        print(f"📡 [ЦУП] Анализ объекта {v_id} ({source_name})...")
        
        # Специальные параметры для обхода "Sign in to confirm you're not a bot"
        base_ydl_opts = {
            'quiet': True, 
            'proxy': proxy if proxy else None,
            'user_agent': random.choice(USER_AGENTS),
            'nocheckcertificate': True,
            'extractor_args': {'youtube': {'client': ['android', 'ios', 'tv', 'web']}}, 
            'sleep_interval': 1,
            'max_sleep_interval': 3
        }
        
        with yt_dlp.YoutubeDL(base_ydl_opts) as ydl:
            try:
                info = ydl.extract_info(v_url, download=False)
            except Exception as e:
                print(f"⚠️ Ошибка доступа к видео (возможно блокировка IP): {e}")
                return False
                
            duration = info.get('duration', 1)
            filesize = (info.get('filesize') or info.get('filesize_approx') or 0) / (1024 * 1024)

        # Отсекаем только полнометражные фильмы > 1 часа
        if duration > 3600:
            print(f"⏭ [ЦУП] ОТМЕНА: Ролик слишком длинный ({int(duration//60)} мин). Пропускаем фильмы.")
            return False

        h_limit = 720
        if duration > 1800 or filesize > 800: h_limit = 240
        elif duration > 900 or filesize > 500: h_limit = 360
        elif duration > 480 or filesize > 300: h_limit = 480
        
        print(f"⚖️ ТТХ: {duration}с | ~{filesize:.1f}Мб -> Лимит: {h_limit}p")

        # --- 2. ЗАХВАТ ---
        download_opts = base_ydl_opts.copy()
        download_opts.update({
            'format': f'bestvideo[height<={h_limit}][ext=mp4]+bestaudio[ext=m4a]/best[height<={h_limit}]',
            'outtmpl': f_raw, 
            'quiet': False, 
            'retries': 15, 
            'fragment_retries': 30
        })

        with yt_dlp.YoutubeDL(download_opts) as ydl: 
            ydl.download([v_url])
        
        if not os.path.exists(f_raw): return False
        raw_mb = os.path.getsize(f_raw) / (1024 * 1024)

        # --- 3. WHISPER ---
        has_subs, mode_tag = False, "🎙 ОРИГИНАЛЬНАЯ ОЗВУЧКА"
        if not is_russian:
            print("🧠 [ЦУП] Запуск Whisper для перевода...")
            if whisper_model is None: whisper_model = whisper.load_model("base")
            res = whisper_model.transcribe(f_raw)
            if len(res.get('text', '').strip()) > 15:
                mode_tag = "📝 ПЕРЕВОД (СУБТИТРЫ)"
                srt = ""
                for i, seg in enumerate(res.get('segments', [])):
                    t_ru = GoogleTranslator(source='auto', target='ru').translate(seg['text'].strip())
                    srt += f"{i+1}\n{time.strftime('%H:%M:%S,000', time.gmtime(seg['start']))} --> {time.strftime('%H:%M:%S,000', time.gmtime(seg['end']))}\n{t_ru}\n\n"
                with open("subs.srt", "w", encoding="utf-8") as fs: fs.write(srt)
                has_subs = True

        # --- 4. УПАКОВКА (ГЛУБОКОЕ СЖАТИЕ) ---
        if is_russian and raw_mb < SAFE_LIMIT_MB:
            print(f"🚀 [ЦУП] Экспресс-маршрут: {raw_mb:.1f}Мб проходит без сжатия.")
            f_to_send = f_raw
        else:
            # Целимся в 44 Мб для страховки. Разрешаем падать битрейту очень низко для длинных роликов.
            target_total_bps = int((44 * 1024 * 1024 * 8) / duration)
            a_br_bps = 64000 if duration <= 1500 else 32000 # Звук хуже, если ролик длиннее 25 мин
            target_v_bps = target_total_bps - a_br_bps
            
            # Разрешаем сжатие видео до 40 kbps (спасет ролики до 55 минут)
            v_br = max(40000, min(target_v_bps, 2200000))
            a_br = '64k' if duration <= 1500 else '32k'
            
            vf = "subtitles=subs.srt:force_style='FontSize=20,BorderStyle=3'" if has_subs else f"scale=-2:{h_limit}"
            
            print(f"⚙️ [ЦУП] Запуск FFmpeg (Видео: {v_br//1000} kbps | Аудио: {a_br})...")
            # 🔥 Внедрены параметры для стабильности плеера: -g 60, -profile:a aac_low, -ar 44100
            subprocess.run([
                'ffmpeg', '-y', '-i', f_raw, '-vf', vf, 
                '-c:v', 'libx264', '-b:v', str(v_br), '-preset', 'ultrafast', 
                '-g', '60',
                '-max_muxing_queue_size', '1024',
                '-movflags', '+faststart',
                '-c:a', 'aac', '-profile:a', 'aac_low', '-ar', '44100', '-b:a', a_br, f_final
            ])
            f_to_send = f_final if os.path.exists(f_final) else f_raw

        # --- 4.5 СОЗДАНИЕ ОБЛОЖКИ (Анти-Белый Экран) ---
        print("📸 [ЦУП] Создаем превью...")
        subprocess.run([
            'ffmpeg', '-y', '-i', f_to_send, 
            '-ss', '00:00:02.000', 
            '-vframes', '1', 
            '-vf', 'scale=320:-1', 
            '-q:v', '2', 
            f_thumb
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # --- 5. ТЕЛЕМЕТРИЯ И ОТПРАВКА ---
        final_mb = os.path.getsize(f_to_send) / (1024 * 1024)
        print(f"📊 [ЦУП] Финальный вес: {final_mb:.2f} Мб")

        # Очистка заголовка
        ru_title = title if is_russian else GoogleTranslator(source='auto', target='ru').translate(title)
        ru_title = ru_title.replace('<', '«').replace('>', '»').replace('&', 'и')
        
        summary = get_smart_summary(desc_raw if is_russian else GoogleTranslator(source='auto', target='ru').translate(desc_raw))
        
        caption = (
            f"<b>{mode_tag}</b>\n\n🎬 <b>{ru_title.upper()}</b>\n"
            f"──────────────────────\n\n🚀 <b>В ЭТОМ ВЫПУСКЕ:</b>\n<i>{summary}</i>\n\n"
            f"<b>Марти:</b> <i>{random.choice(MARTY_QUOTES)}</i>\n\n📡 <a href='https://t.me/vladislav_space'>ДНЕВНИК ЮНОГО КОСМОНАВТА</a>"
        )

        with open(f_to_send, 'rb') as v:
            files_to_send = {"video": v}
            thumb_file = None
            
            if os.path.exists(f_thumb):
                thumb_file = open(f_thumb, 'rb')
                files_to_send["thumbnail"] = thumb_file

            try:
                r = requests.post(
                    f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo", 
                    files=files_to_send, 
                    data={
                        "chat_id": CHANNEL_NAME, 
                        "caption": caption, 
                        "parse_mode": "HTML",
                        "supports_streaming": "true" 
                    }, 
                    timeout=600
                )
                return r.status_code == 200
            finally:
                if thumb_file:
                    thumb_file.close()
                    
    except Exception as e:
        print(f"⚠️ Сбой систем: {e}"); return False

async def main():
    db = open(DB_FILE, 'r').read() if os.path.exists(DB_FILE) else ""
    last_s = open(SOURCE_LOG, 'r').read().strip() if os.path.exists(SOURCE_LOG) else ""
    
    SOURCES = [
        {'n': 'SpaceX Fan', 'cid': '@spacexfan420', 'ru': True},
        {'n': 'Rocket Hub', 'cid': '@rockethubspace', 'ru': True},
        {'n': 'NASA', 'cid': '@NASAJPL', 'ru': False},
        {'n': 'KOSMO', 'cid': '@off_kosmo', 'ru': True},
        {'n': 'EVLSPACE', 'cid': '@EVLSPACE', 'ru': True},
        {'n': 'ночнаянаука-ц4ш', 'cid': '@ночнаянаука-ц4ш', 'ru': True},
        {'n': 'Hubbler', 'cid': '@Hubbler', 'ru': True},
        {'n': 'Cosmosprosto', 'cid': '@cosmosprosto', 'ru': True}
    ]
    
    random.shuffle(SOURCES)
    for s in SOURCES:
        if s['n'] == last_s: continue
        try:
            url = f"https://www.googleapis.com/youtube/v3/channels?part=contentDetails&forHandle={s['cid'].replace('@','')}&key={YOUTUBE_API_KEY}"
            res = requests.get(url).json()
            up_id = res['items'][0]['contentDetails']['relatedPlaylists']['uploads']
            vids = [{'id': i['snippet']['resourceId']['videoId'], 'title': i['snippet']['title'], 'desc': i['snippet']['description']} for i in requests.get(f"https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&playlistId={up_id}&maxResults=3&key={YOUTUBE_API_KEY}").json()['items']]
            for v in vids:
                if v['id'] not in db:
                    if await process_mission(v['id'], v['title'], v['desc'], s['ru'], s['n']):
                        with open(DB_FILE, 'a') as f: f.write(f"\n{v['id']}")
                        with open(SOURCE_LOG, 'w') as f: f.write(s['n'])
                        print("✅ Победа!"); return
        except: continue
    print("🛰 Горизонт чист.")

if __name__ == '__main__':
    asyncio.run(main())
