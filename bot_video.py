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

print("🚀 [ЦУП] Развертывание v161.0 'Quantum Sensor'. Системы активированы...")

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

MARTY_QUOTES = [
    "Гав! Вижу цель — свежие новости с орбиты доставлены! 🚀🐾",
    "Ррр-гав! Хвост виляет со скоростью света от такого крутого видео! ✨",
    "Тяв! Проверил обшивку — ни одной космической кошки на борту! 🛰️",
    "Гав! В космосе никто не услышит твой лай, но мой пост увидят все! 🌌",
    "Тяв! Обнаружил планету, похожую на гигантский теннисный мяч! 🎾🌍",
    "Гав! Навострил уши — ловлю сигналы из самых дальних галактик! 📡",
    "Ррр-гав! Эта миссия пахнет успехом и немного звездной пылью! 🐕🌠",
    "Гав! Передал данные быстрее, чем летит метеорит! ☄️🐾",
    "Тяв! Командор, я проверил: на Луне сыра нет, только пыль и кратеры! 🧀🌑",
    "Гав! В невесомости мои уши смешно разлетаются, но я всё равно на посту! 🛸👂",
    "Ррр-гав! Защищаю канал от скуки лучше, чем любая нейросеть! 🛡️🐾",
    "Тяв! Если увидите в небе комету — это я за ней погнался! 🐕💨",
    "Гав! Мой нос подсказывает: это видео станет хитом на Земле! 🌍👃",
    "Гав! Даже в скафандре я выгляжу потрясающе, согласны? 🧑‍🚀🐩",
    "Ррр-гав! Слежу за приборами, пока Командор изучает карту созвездий! 🕹️🐾",
    "Тяв! Это видео такое классное, что я чуть не сгрыз антенну от радости! 📺🦴",
    "Гав! Проложил кратчайший путь сквозь пояс астероидов, не благодарите! 🗺️🪨",
    "Ррр-гав! Встретил инопланетян — они тоже любят, когда их чешут за ушком! 👽🐕",
    "Тяв! На борту идеальный порядок, все косточки пересчитаны и спрятаны! 🦴✅",
    "Гав! Летим к звездам! Пристегните ремни, лапы и хвосты! 🚀🐾",
    "Ррр-гав! Мой бортовой журнал полон открытий, делюсь самым лучшим! 📒✨"
]

def get_smart_summary(text):
    if not text: return "Интересные подробности — внутри ролика! ✨"
    text = re.sub(r'http\S+', '', text); text = re.sub(r'#\S+', '', text)
    text = html.unescape(text)
    junk = ['vk.com', 'ok.ru', 't.me', 'подписывайтесь', 'подпишись', 'наш канал', 'vpn', 'amnezia', 'сайт:']
    lines = [l.strip() for l in text.split('\n') if len(l.strip()) > 20 and not any(j in l.lower() for j in junk)]
    full = " ".join(lines)
    sentences = re.split(r'(?<=[.!?]) +', full)
    res = " ".join([s.strip() for s in sentences if len(s) > 30][:2])
    return res if len(res) > 30 else full[:200].strip()

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
    f_raw, f_final = "raw_video.mp4", "final_video.mp4"
    for f in [f_raw, f_final, "subs.srt"]:
        if os.path.exists(f): os.remove(f)

    try:
        v_url = f"https://www.youtube.com/watch?v={v_id}"
        proxy = get_fast_proxy()
        
        print(f"📡 [ЦУП] Анализ объекта {v_id} ({source_name})...")
        temp_opts = {
            'quiet': True, 
            'js_runtimes': ['deno'],
            'proxy': proxy if proxy else None,
            'nocheckcertificate': True
        }
        
        with yt_dlp.YoutubeDL(temp_opts) as ydl:
            info = ydl.extract_info(v_url, download=False)
            duration = info.get('duration', 1)
            filesize = info.get('filesize_approx', 0) / (1024 * 1024)

        h_limit = 720
        if duration > 1800 or filesize > 800: h_limit = 240
        elif duration > 900 or filesize > 500: h_limit = 360
        elif duration > 480 or filesize > 300: h_limit = 480
        
        print(f"⚖️ ТТХ: {duration}с | ~{filesize:.1f}Мб -> Лимит: {h_limit}p")

        ydl_opts = {
            'format': f'bestvideo[height<={h_limit}][ext=mp4]+bestaudio[ext=m4a]/best[height<={h_limit}]',
            'outtmpl': f_raw, 'quiet': False, 
            'js_runtimes': ['deno'],
            'retries': 20, 'fragment_retries': 40, 'continuedl': True,
            'proxy': proxy if proxy else None,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl: ydl.download([v_url])
        
        if not os.path.exists(f_raw): return False
        raw_mb = os.path.getsize(f_raw) / (1024 * 1024)

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

        if is_russian and raw_mb < SAFE_LIMIT_MB:
            print(f"🚀 [ЦУП] Экспресс-маршрут: {raw_mb:.1f}Мб проходит без сжатия.")
            f_to_send = f_raw
        else:
            target_br = int((SAFE_LIMIT_MB * 1024 * 1024 * 8) / duration * 0.75)
            v_br = max(120000, min(target_br, 2200000))
            vf = "subtitles=subs.srt:force_style='FontSize=20,BorderStyle=3'" if has_subs else f"scale=-2:{h_limit}"
            
            print(f"⚙️ [ЦУП] Запуск FFmpeg (Сжатие {duration}с)...")
            subprocess.run([
                'ffmpeg', '-y', '-i', f_raw, '-vf', vf, 
                '-c:v', 'libx264', '-b:v', str(v_br), '-preset', 'ultrafast', 
                '-max_muxing_queue_size', '1024',
                '-c:a', 'aac', '-b:a', '64k', f_final
            ])
            f_to_send = f_final if os.path.exists(f_final) else f_raw

        ru_title = title if is_russian else GoogleTranslator(source='auto', target='ru').translate(title)
        summary = get_smart_summary(desc_raw if is_russian else GoogleTranslator(source='auto', target='ru').translate(desc_raw))
        
        caption = (
            f"<b>{mode_tag}</b>\n\n"
            f"🎬 <b>{ru_title.upper()}</b>\n"
            f"──────────────────────\n\n"
            f"🚀 <b>В ЭТОМ ВЫПУСКЕ:</b>\n"
            f"<i>{summary}</i>\n\n"
            f"<b>Марти:</b> <i>{random.choice(MARTY_QUOTES)}</i>\n\n"
            f"📡 <a href='https://t.me/vladislav_space'>ДНЕВНИК ЮНОГО КОСМОНАВТА</a>"
        )

        with open(f_to_send, 'rb') as v:
            r = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo", 
                              files={"video": v}, 
                              data={"chat_id": CHANNEL_NAME, "caption": caption, "parse_mode": "HTML"}, 
                              timeout=600)
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
