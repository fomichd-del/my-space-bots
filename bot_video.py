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

print("🚀 [ЦУП] Развертывание v164.2 'Hybrid Core'. Возврат к стабильным гипер-коридорам...")

# ============================================================
# ⚙️ КОНФИГУРАЦИЯ
# ============================================================
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY') 
CHANNEL_NAME   = '@vladislav_space'
DB_FILE        = "last_video_date.txt"
SOURCE_LOG     = "last_source.txt"
SAFE_LIMIT_MB  = 46 

# Точный путь к Deno в среде GitHub Actions
DENO_BIN = "/home/runner/.deno/bin/deno"
JS_CONF = {'deno': {}}
if os.path.exists(DENO_BIN):
    JS_CONF = {'deno': {'path': DENO_BIN}}

whisper_model = None

# Звездный фильтр
SPACE_KEYWORDS = [
    'космос', 'планета', 'звезда', 'галактика', 'марс', 'юпитер', 'сатурн', 
    'вселенная', 'астрономия', 'телескоп', 'млечный путь', 'черная дыра', 
    'астероид', 'метеорит', 'луна', 'солнце', 'ракета', 'spacex', 'nasa', 'роскосмос',
    'инопланет', 'орбита', 'мкс', 'космонавт', 'астронавт'
]

# Ротация User-Agent (маскировка)
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_4_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (iPad; CPU OS 17_4_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Mobile/15E148 Safari/604.1'
]

# Фразы Марти (расширенный список, ничего не удалено)
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
    "Ррр-гав! Мой журнал полон открытий, делюсь лучшим! 📒✨",
    "Гав! Если черная дыра засасывает всё, засосет ли она мою любимую косточку? 🤔🐾", 
    "Тяв! На радаре вспышка сверхновой! Или это просто кто-то включил фонарик? 🔦🌌", 
    "Ррр-гав! По теории струн, где-то есть Вселенная, где собаки выгуливают людей! 🐕🪐", 
    "Гав! Загружаю данные в канал. Скорость — варп 9! Держитесь крепче! 🚀💨", 
    "Тяв! Космическая радиация мне не страшна, у меня шерсть с защитой от альфа-частиц! 🛡️🐩"
]

def get_smart_summary(text):
    if not text or len(text.strip()) < 5: 
        return "Интересные подробности и визуальные доказательства — внутри ролика! Включайте скорее! ✨"
    
    text = re.sub(r'http\S+', '', text)
    text = re.sub(r'#\S+', '', text)
    text = html.unescape(text)
    
    junk = ['vk.com', 'ok.ru', 't.me', 'подписывайтесь', 'подпишись', 'наш канал', 'vpn', 'amnezia', 'сайт:', 'facebook', 'instagram', 'twitter']
    lines = [l.strip() for l in text.split('\n') if len(l.strip()) > 25 and not any(j in l.lower() for j in junk)]
    lines = [l for l in lines if not re.match(r'^\d{1,2}:\d{2}', l)]
    
    full = " ".join(lines)
    sentences = re.split(r'(?<=[.!?]) +', full)
    res = " ".join([s.strip() for s in sentences if len(s) > 35][:2])
    
    if len(res) < 30:
        res = full[:200].strip()
        if not res:
            res = "Невероятные космические явления запечатлены в этом видео. Смотрим! 🚀"
            
    return html.escape(res)

# ВОЗВРАЩАЕМ ИДЕАЛЬНО РАБОТАЮЩИЙ ПОИСК ПРОКСИ
def get_fast_proxy():
    print("🛰 [ЦУП] Поиск гипер-коридора (быстрый сканер)...")
    url = "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=5000&country=all&ssl=all&anonymity=all"
    try:
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            proxies = resp.text.strip().split('\n')
            random.shuffle(proxies)
            for p in proxies[:60]:
                p_str = f"http://{p.strip()}"
                try:
                    requests.get("https://www.google.com", proxies={"https": p_str, "http": p_str}, timeout=2)
                    print(f"✅ Коридор подтвержден: {p.strip()}")
                    return p_str
                except: continue
    except: pass
    print("⚠️ Коридоры недоступны, переходим на прямое соединение.")
    return None

async def process_mission(v_id, title, desc_raw, is_russian=False, source_name=""):
    global whisper_model, JS_CONF
    
    if source_name == "ADME":
        search_text = (title + " " + desc_raw).lower()
        if not any(word in search_text for word in SPACE_KEYWORDS):
            print(f"⏭ [ЦУП] Объект ADME {v_id} не прошел звездный фильтр. Пропускаем.")
            return False

    f_raw, f_final = "raw_video.mp4", "final_video.mp4"
    for f in [f_raw, f_final, "subs.srt"]:
        if os.path.exists(f): os.remove(f)

    try:
        v_url = f"https://www.youtube.com/watch?v={v_id}"
        proxy = get_fast_proxy()
        
        print(f"📡 [ЦУП] Анализ объекта {v_id} ({source_name})...")
        temp_opts = {
            'quiet': True, 
            'js_runtimes': JS_CONF,
            'proxy': proxy if proxy else None,
            'user_agent': random.choice(USER_AGENTS),
            'socket_timeout': 15, 
            'nocheckcertificate': True
        }
        
        with yt_dlp.YoutubeDL(temp_opts) as ydl:
            info = ydl.extract_info(v_url, download=False)
            duration = info.get('duration', 1)
            filesize = info.get('filesize_approx', 0) / (1024 * 1024)
            # Отсекаем трансляции, чтобы не висеть 6 часов
            if info.get('is_live') or info.get('live_status') == 'is_upcoming':
                print("⏭ [ЦУП] Это трансляция или премьера. Ждать не будем, пропускаем.")
                return False

        h_limit = 720
        if duration > 1800 or filesize > 800: h_limit = 240
        elif duration > 900 or filesize > 500: h_limit = 360
        elif duration > 480 or filesize > 300: h_limit = 480
        
        print(f"⚖️ ТТХ: {duration}с | ~{filesize:.1f}Мб -> Лимит: {h_limit}p")

        ydl_opts = {
            'format': f'bestvideo[height<={h_limit}][ext=mp4]+bestaudio[ext=m4a]/best[height<={h_limit}]',
            'outtmpl': f_raw, 
            'quiet': False, 
            'js_runtimes': JS_CONF,
            'retries': 15, 
            'fragment_retries': 30, 
            'continuedl': True,
            'proxy': proxy if proxy else None,
            'socket_timeout': 15,
            'user_agent': random.choice(USER_AGENTS)
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl: ydl.download([v_url])
        
        if not os.path.exists(f_raw): return False
        raw_mb = os.path.getsize(f_raw) / (1024 * 1024)

        has_subs, mode_tag = False, "🎙 ОРИГИНАЛЬНАЯ ОЗВУЧКА"
        if not is_russian:
            print("🧠 [ЦУП] Запуск Whisper...")
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

        if is_russian and raw_mb < SAFE_LIMIT_MB:
            f_to_send = f_raw
        else:
            target_br = int((SAFE_LIMIT_MB * 1024 * 1024 * 8) / duration * 0.75)
            v_br = max(120000, min(target_br, 2200000))
            vf = "subtitles=subs.srt:force_style='FontSize=20,BorderStyle=3'" if has_subs else f"scale=-2:{h_limit}"
            
            subprocess.run([
                'ffmpeg', '-y', '-i', f_raw, '-vf', vf, 
                '-c:v', 'libx264', '-b:v', str(v_br), '-preset', 'ultrafast', 
                '-max_muxing_queue_size', '1024',
                '-movflags', '+faststart',
                '-pix_fmt', 'yuv420p',
                '-c:a', 'aac', '-b:a', '64k', f_final
            ])
            f_to_send = f_final if os.path.exists(f_final) else f_raw

        final_mb = os.path.getsize(f_to_send) / (1024 * 1024)
        print(f"📊 [ЦУП] Финальный вес: {final_mb:.2f} Мб")

        ru_title = title if is_russian else GoogleTranslator(source='auto', target='ru').translate(title)
        summary = get_smart_summary(desc_raw if is_russian else GoogleTranslator(source='auto', target='ru').translate(desc_raw))
        ru_title_safe = html.escape(ru_title)
        
        caption = (
            f"<b>{mode_tag}</b>\n\n🎬 <b>{ru_title_safe.upper()}</b>\n"
            f"──────────────────────\n\n🚀 <b>В ЭТОМ ВЫПУСКЕ:</b>\n<i>{summary}</i>\n\n"
            f"<b>Марти:</b> <i>{random.choice(MARTY_QUOTES)}</i>\n\n📡 <a href='https://t.me/vladislav_space'>ДНЕВНИК ЮНОГО КОСМОНАВТА</a>"
        )

        with open(f_to_send, 'rb') as v:
            # Отправка с параметром supports_streaming="true" для мгновенного воспроизведения
            r = requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo", 
                files={"video": v}, 
                data={
                    "chat_id": CHANNEL_NAME, 
                    "caption": caption, 
                    "parse_mode": "HTML",
                    "supports_streaming": "true" 
                }, 
                timeout=600
            )
            return r.status_code == 200
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
        {'n': 'Роскосмос ТВ', 'cid': '@tvroscosmos', 'ru': True},
        {'n': 'Hubbler', 'cid': '@Hubbler', 'ru': True},
        {'n': 'Cosmosprosto', 'cid': '@cosmosprosto', 'ru': True},
        {'n': 'ADME', 'cid': '@ADME_RU', 'ru': True}
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
