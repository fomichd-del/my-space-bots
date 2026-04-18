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

print("🚀 [ЦУП] Системы инициализированы. Развертывание v148.0 'Super Nova'...")

# ============================================================
# ⚙️ КОНФИГУРАЦИЯ v148.0 (Full Logic + Marty 2.0)
# ============================================================
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY') 
CHANNEL_NAME   = '@vladislav_space'
DB_FILE        = "last_video_date.txt"
SOURCE_LOG     = "last_source.txt"
SAFE_LIMIT_MB  = 42 

SPACE_KEYWORDS = ['космос', 'вселенная', 'планета', 'звезд', 'галактик', 'астероид', 'черная дыра', 'марса', 'луна', 'солнц', 'космическ', 'spacex', 'nasa', 'телескоп', 'мкс', 'astronomy', 'universe', 'telescope']

# Список публичных узлов Cobalt API для обхода блокировок YouTube
COBALT_INSTANCES = [
    "https://cobalt.api.v0l.io",
    "https://api.cobalt.tools",
    "https://cobalt-api.lunar.icu"
]

whisper_model = None

# ПОЛНЫЙ СПИСОК ЦИТАТ МАРТИ
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
# 🛠 УЛЬТРА-ОЧИСТКА ТЕКСТА
# ============================================================

def get_smart_summary(text):
    if not text: return "Интересные подробности — внутри ролика! ✨"
    text = re.sub(r'http\S+', '', text)
    text = re.sub(r'#\S+', '', text)
    text = html.unescape(text)
    junk = ['vk.com', 'ok.ru', 't.me', 'подписывайтесь', 'подпишись', 'наш канал', 'поддержать', 'amnezia', 'vpn', 'сотрудничество']
    lines = [l.strip() for l in text.split('\n') if len(l.strip()) > 20 and not any(j in l.lower() for j in junk)]
    full = " ".join(lines)
    sentences = re.split(r'(?<=[.!?]) +', full)
    res = " ".join([s.strip() for s in sentences if len(s) > 30][:2])
    return res if len(res) > 30 else full[:220].strip()

def download_via_shadow_bridge(v_url, quality):
    payload = {
        "url": v_url,
        "videoQuality": str(quality),
        "downloadMode": "video",
        "noWatermark": True
    }
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    
    nodes = COBALT_INSTANCES.copy()
    random.shuffle(nodes)
    for api in nodes:
        try:
            print(f"🛰 [ЦУП] Попытка захвата через: {api}...")
            r = requests.post(f"{api}/api/json", json=payload, headers=headers, timeout=30)
            if r.status_code == 200 and "url" in r.json():
                direct_url = r.json()["url"]
                print("🔗 Поток найден! Начинаю загрузку...")
                v_data = requests.get(direct_url, stream=True, timeout=120)
                with open("raw_video.mp4", "wb") as f:
                    for chunk in v_data.iter_content(chunk_size=8192):
                        f.write(chunk)
                return True
        except: continue
    return False

# ============================================================
# 🎬 ОСНОВНОЙ ПРОЦЕССОР
# ============================================================

async def process_mission_v148(v_id, title, desc_raw, is_russian=False, source_name=""):
    global whisper_model
    f_raw, f_final = "raw_video.mp4", "final_video.mp4"
    for f in [f_raw, f_final, "subs.srt"]:
        if os.path.exists(f): os.remove(f)

    try:
        v_url = f"https://www.youtube.com/watch?v={v_id}"
        
        # 1. РАЗВЕДКА (Direct Stream)
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(v_url, download=False)
            duration = info.get('duration', 1)

        # 2. ВЫБОР КАЧЕСТВА
        h_limit = 720
        if duration > 1800: h_limit = 360
        elif duration > 900: h_limit = 480
        
        # 3. ЗАХВАТ ЧЕРЕЗ ТЕНЕВОЙ МОСТ
        print(f"📡 [ЦУП] Взлом шлюза YouTube для {v_id}...")
        if not download_via_shadow_bridge(v_url, h_limit):
            return False
            
        raw_mb = os.path.getsize(f_raw) / (1024 * 1024)
        print(f"⚖️ Вес объекта: {raw_mb:.1f} Мб")

        # 4. ПЕРЕВОД (WHISPER)
        has_subs, mode_tag = False, "🎙 ОРИГИНАЛЬНАЯ ОЗВУЧКА"
        if not is_russian:
            if whisper_model is None:
                print("🧠 [ЦУП] Инициализация Whisper...")
                whisper_model = whisper.load_model("base")
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

        # 5. СЖАТИЕ FFmpeg
        target_br = int((SAFE_LIMIT_MB * 1024 * 1024 * 8) / duration * 0.75)
        v_br = max(120000, min(target_br, 2000000))
        vf = "subtitles=subs.srt:force_style='FontSize=20,BorderStyle=3,BackColour=&H80000000'" if has_subs else "scale=trunc(iw/2)*2:trunc(ih/2)*2"
        subprocess.run(['ffmpeg', '-y', '-i', f_raw, '-vf', vf, '-c:v', 'libx264', '-b:v', str(v_br), '-preset', 'ultrafast', '-c:a', 'aac', '-b:a', '48k', f_final], capture_output=True)
        f_to_send = f_final if os.path.exists(f_final) else f_raw

        # 6. ОФОРМЛЕНИЕ И ТРАНСЛЯЦИЯ
        summary = get_smart_summary(desc_raw if is_russian else GoogleTranslator(source='auto', target='ru').translate(desc_raw))
        clean_title = (title if is_russian else GoogleTranslator(source='auto', target='ru').translate(title)).upper()
        
        caption = (
            f"<b>{mode_tag}</b>\n\n"
            f"🎬 <b>{clean_title}</b>\n"
            f"──────────────────────\n\n"
            f"🚀 <b>О ЧЕМ МИССИЯ:</b>\n"
            f"<i>{summary}</i>\n\n"
            f"<b>Марти:</b> <i>{random.choice(MARTY_QUOTES)}</i>\n\n"
            f"📡 <a href='https://t.me/vladislav_space'>ДНЕВНИК ЮНОГО КОСМОНАВТА</a>"
        )

        with open(f_to_send, 'rb') as v:
            r = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo", files={"video": v}, data={"chat_id": CHANNEL_NAME, "caption": caption, "parse_mode": "HTML"}, timeout=600)
            return r.status_code == 200
    except Exception as e:
        print(f"⚠️ Ошибка: {e}"); return False

# ============================================================
# 🛰 ГЛАВНЫЙ ЦИКЛ
# ============================================================

async def main():
    print(f"🎬 [ЦУП] v148.0 'Super Nova' запуск систем...")
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
                    if await process_mission_v148(v['id'], v['title'], v['desc'], s['ru'], s['n']):
                        with open(DB_FILE, 'a') as f: f.write(f"\n{v['id']}")
                        with open(SOURCE_LOG, 'w') as f: f.write(s['n'])
                        print("✅ Посылка доставлена!"); return
        except: continue
    print("🛰 Горизонт чист.")

if __name__ == '__main__':
    asyncio.run(main())
