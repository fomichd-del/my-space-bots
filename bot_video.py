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

print("🚀 [ЦУП] Системы инициализированы. Развертывание v154.0 'Event Horizon'...")

# ============================================================
# ⚙️ КОНФИГУРАЦИЯ v154.0 (Client Spoofing Protocol)
# ============================================================
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY') 
CHANNEL_NAME   = '@vladislav_space'
DB_FILE        = "last_video_date.txt"
SOURCE_LOG     = "last_source.txt"
SAFE_LIMIT_MB  = 42 

SPACE_KEYWORDS = ['космос', 'вселенная', 'планета', 'звезд', 'галактик', 'астероид', 'черная дыра', 'марса', 'луна', 'солнц', 'космическ', 'spacex', 'nasa', 'телескоп', 'мкс', 'astronomy', 'universe', 'telescope']

# Обновленные узлы захвата
COBALT_NODES = [
    "https://api.cobalt.tools",
    "https://cobalt.api.v0l.io",
    "https://cobalt.lunar.icu",
    "https://cobalt.qwedl.com",
    "https://api.cobalt.icu"
]

INVIDIOUS_NODES = [
    "https://yewtu.be",
    "https://inv.vern.cc",
    "https://iv.ggtyler.dev"
]

whisper_model = None

# ПОЛНЫЙ СПИСОК ЦИТАТ МАРТИ (21 ШТУКА)
MARTY_QUOTES = [
    "Гав! Вижу цель — свежие новости с орбиты доставлены! 🚀🐾",
    "Ррр-гав! Хвост виляет со скоростью света от такого крутого видео! ✨",
    "Тяв! Проверил обшивку — ни одной космической кошки на борту! 🛰️",
    "Гав! В космосе никто не услышит твой лай, но мой пост увидят все! 🌌",
    "Тяв! Обнаружил планету, похожую на гигантский теннисный мяч! Хочу туда! 🎾🌍",
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

# ============================================================
# 🛠 СУПЕР-ЗАХВАТ (v154.0)
# ============================================================

def get_video_details(v_id):
    try:
        url = f"https://www.googleapis.com/youtube/v3/videos?part=contentDetails&id={v_id}&key={YOUTUBE_API_KEY}"
        res = requests.get(url).json()
        if 'items' in res and res['items']:
            dur_str = res['items'][0]['contentDetails']['duration']
            match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', dur_str)
            h, m, s = [int(x) if x else 0 for x in match.groups()]
            return h * 3600 + m * 60 + s
    except: pass
    return 0

def download_via_stealth(v_url, quality):
    """Метод 1: Прямой захват с имитацией iOS/Android-клиента"""
    print(f"🛰 [ЦУП] Попытка стелс-захвата (Client Spoofing)...")
    f_raw = "raw_video.mp4"
    ydl_opts = {
        'format': f'bestvideo[height<={quality}][ext=mp4]+bestaudio[ext=m4a]/best[height<={quality}]',
        'outtmpl': f_raw, 'quiet': True, 'no_check_certificate': True,
        'extractor_args': {'youtube': ['player_client=ios,android_embedded', 'player_skip=webpage,configs']},
        'retries': 3
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl: ydl.download([v_url])
        return os.path.exists(f_raw)
    except: return False

def download_via_cobalt(v_url, quality):
    """Метод 2: Модернизированный Cobalt"""
    nodes = COBALT_NODES.copy()
    random.shuffle(nodes)
    for api in nodes:
        try:
            print(f"🛰 [ЦУП] Проба Cobalt-узла: {api}")
            payload = {"url": v_url, "videoQuality": str(quality), "noWatermark": True}
            r = requests.post(f"{api}/api/json", json=payload, headers={"Accept": "application/json", "Content-Type": "application/json", "Origin": "https://cobalt.tools"}, timeout=40)
            if r.status_code == 200 and "url" in r.json():
                v_data = requests.get(r.json()["url"], stream=True, timeout=300)
                with open("raw_video.mp4", "wb") as f:
                    for chunk in v_data.iter_content(chunk_size=1024*1024): f.write(chunk)
                return True
        except: continue
    return False

# ============================================================
# 🎬 ПРОЦЕССОР (v154.0 Event Horizon)
# ============================================================

async def process_mission_v154(v_id, title, desc_raw, duration, is_russian=False):
    global whisper_model
    f_raw, f_final = "raw_video.mp4", "final_video.mp4"
    for f in [f_raw, f_final, "subs.srt"]:
        if os.path.exists(f): os.remove(f)

    try:
        if duration > 2400: return False
        h_limit = 720
        if duration > 1200: h_limit = 360
        elif duration > 600: h_limit = 480
        
        v_url = f"https://www.youtube.com/watch?v={v_id}"
        print(f"🎯 План: {h_limit}p ({duration}с). Прорыв через горизонт...")
        
        # СТРАТЕГИЯ: Сначала пробуем Стелс (iOS), потом Cobalt
        if not download_via_stealth(v_url, h_limit):
            if not download_via_cobalt(v_url, h_limit):
                print("❌ Глухая оборона YouTube. Все туннели завалены.")
                return False
            
        raw_mb = os.path.getsize(f_raw) / (1024 * 1024)
        print(f"⚖️ Вес груза: {raw_mb:.1f} Мб")

        # Whisper (для иностранных)
        has_subs, mode_tag = False, "🎙 ОРИГИНАЛЬНАЯ ОЗВУЧКА"
        if not is_russian:
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
            else: mode_tag = "🎵 МУЗЫКА КОСМОСА"

        # Сжатие
        target_br = int((SAFE_LIMIT_MB * 1024 * 1024 * 8) / max(duration, 1) * 0.75)
        v_br = max(120000, min(target_br, 2000000))
        vf = "subtitles=subs.srt:force_style='FontSize=20,BorderStyle=3,BackColour=&H80000000'" if has_subs else "scale=trunc(iw/2)*2:trunc(ih/2)*2"
        subprocess.run(['ffmpeg', '-y', '-i', f_raw, '-vf', vf, '-c:v', 'libx264', '-b:v', str(v_br), '-preset', 'ultrafast', '-c:a', 'aac', '-b:a', '48k', f_final], capture_output=True)
        f_to_send = f_final if os.path.exists(f_final) else f_raw

        # Очистка и отправка
        text = re.sub(r'http\S+', '', desc_raw if is_russian else GoogleTranslator(source='auto', target='ru').translate(desc_raw))
        text = re.sub(r'#\S+', '', html.unescape(text))
        lines = [l.strip() for l in text.split('\n') if len(l.strip()) > 25 and not any(j in l.lower() for j in ['vk.com', 't.me', 'подпишись', 'vpn'])]
        summary = " ".join(lines[:2])

        caption = (
            f"<b>{mode_tag}</b>\n\n🎬 <b>{(title if is_russian else GoogleTranslator(source='auto', target='ru').translate(title)).upper()}</b>\n"
            f"──────────────────────\n\n🚀 <b>О ЧЕМ МИССИЯ:</b>\n<i>{summary[:250]}</i>\n\n"
            f"<b>Марти:</b> <i>{random.choice(MARTY_QUOTES)}</i>\n\n📡 <a href='https://t.me/vladislav_space'>ДНЕВНИК ЮНОГО КОСМОНАВТА</a>"
        )

        with open(f_to_send, 'rb') as v:
            r = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo", files={"video": v}, data={"chat_id": CHANNEL_NAME, "caption": caption, "parse_mode": "HTML"}, timeout=600)
            return r.status_code == 200
    except Exception as e:
        print(f"⚠️ Сбой: {e}"); return False

async def main():
    print(f"🎬 [ЦУП] v154.0 'Event Horizon' запуск систем...")
    db = open(DB_FILE, 'r').read() if os.path.exists(DB_FILE) else ""
    last_s = open(SOURCE_LOG, 'r').read().strip() if os.path.exists(SOURCE_LOG) else ""
    
    SOURCES = [
        {'n': 'SpaceX Fan', 'cid': '@spacexfan420', 'ru': True},
        {'n': 'Rocket Hub', 'cid': '@rockethubspace', 'ru': True},
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
            res = requests.get(url).json()
            up_id = res['items'][0]['contentDetails']['relatedPlaylists']['uploads']
            vids = [{'id': i['snippet']['resourceId']['videoId'], 'title': i['snippet']['title'], 'desc': i['snippet']['description']} for i in requests.get(f"https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&playlistId={up_id}&maxResults=3&key={YOUTUBE_API_KEY}").json()['items']]
            for v in vids:
                if v['id'] not in db:
                    if s.get('filter') and not any(kw in (v['title'] + v['desc']).lower() for kw in SPACE_KEYWORDS): continue
                    duration = get_video_details(v['id'])
                    if duration == 0: continue
                    if await process_mission_v154(v['id'], v['title'], v['desc'], duration, s['ru']):
                        with open(DB_FILE, 'a') as f: f.write(f"\n{v['id']}")
                        with open(SOURCE_LOG, 'w') as f: f.write(s['n'])
                        print("✅ Победа!"); return
        except: continue
    print("🛰 Горизонт чист.")

if __name__ == '__main__':
    asyncio.run(main())
