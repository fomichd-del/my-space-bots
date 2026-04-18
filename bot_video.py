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

print("🚀 [ЦУП] Системы инициализированы. Запуск v147.7...")

# ============================================================
# ⚙️ КОНФИГУРАЦИЯ v147.7 (Shield of Purity Protocol)
# ============================================================
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY') 
CHANNEL_NAME   = '@vladislav_space'
DB_FILE        = "last_video_date.txt"
SOURCE_LOG     = "last_source.txt"
SAFE_LIMIT_MB  = 42 

SPACE_KEYWORDS = ['космос', 'вселенная', 'планета', 'звезд', 'галактик', 'астероид', 'черная дыра', 'марса', 'луна', 'солнц', 'космическ', 'spacex', 'nasa', 'телескоп', 'мкс', 'astronomy', 'universe', 'telescope']

whisper_model = None

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
# 🛠 УЛЬТРА-ОЧИСТКА ТЕКСТА (БЕЗ СПАМА И РЕКЛАМЫ)
# ============================================================

def get_smart_summary(text):
    if not text: return "Интересные подробности — внутри ролика! ✨"
    
    # 1. Вырезаем ссылки, хештеги и лишние символы
    text = re.sub(r'http\S+', '', text)
    text = re.sub(r'#\S+', '', text)
    text = html.unescape(text)
    
    # 2. Расширенный список рекламного и мусорного контента
    junk_patterns = [
        'vk.com', 'ok.ru', 't.me', 'vk:', 'ok:', 'telegram:', 'rutube:', 
        'подписывайтесь', 'подпишись', 'наш канал', 'нашем канале',
        'поддержать нас', 'поддержать проект', 'донаты', 'amnezia', 
        'интернет', 'vpn', 'реклама', 'сотрудничество', 'по вопросам',
        'facebook', 'instagram', 'twitter', 'boosty', 'patreon',
        'выпуски каждую неделю', 'жми на колокольчик', 'наш сайт'
    ]
    
    lines = text.split('\n')
    clean_lines = []
    
    for line in lines:
        line = line.strip()
        # Пропускаем пустые, короткие или рекламные строки
        if len(line) < 20: continue 
        if any(junk in line.lower() for junk in junk_patterns): continue
        # Убираем странные символы в начале строк (точки, тире, стрелочки)
        line = re.sub(r'^[•\-\.\d\s►✅]+', '', line)
        clean_lines.append(line)
    
    # Собираем осмысленные предложения
    full_text = " ".join(clean_lines)
    sentences = re.split(r'(?<=[.!?]) +', full_text)
    
    # Ищем первые два предложения, которые похожи на описание фактов
    meaningful = []
    for s in sentences:
        s = s.strip()
        if len(s) > 30 and not any(junk in s.lower() for junk in junk_patterns):
            meaningful.append(s)
            if len(meaningful) >= 2: break
            
    summary = " ".join(meaningful)
    if not summary or len(summary) < 40:
        # Если фильтр всё съел, берем первые 200 символов очищенного текста
        summary = full_text[:200].strip()
        
    return summary if summary else "Свежий отчет из глубин космоса! 🪐"

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
# 🎬 ПРОЦЕССОР (v147.7 Shield)
# ============================================================

async def process_mission_v147(v_id, title, desc_raw, is_russian=False, source_name=""):
    global whisper_model
    f_raw, f_final = "raw_video.mp4", "final_video.mp4"
    for f in [f_raw, f_final, "subs.srt"]:
        if os.path.exists(f): os.remove(f)

    try:
        v_url = f"https://www.youtube.com/watch?v={v_id}"
        proxy = get_fast_proxy()
        
        # Разведка (Direct Stream)
        print(f"📡 [ЦУП] Анализ объекта {v_id} ({source_name})...")
        temp_opts = {'quiet': True, 'js_runtimes': {'deno': {}}}
        if proxy: temp_opts['proxy'] = proxy
        with yt_dlp.YoutubeDL(temp_opts) as ydl:
            info = ydl.extract_info(v_url, download=False)
            duration = info.get('duration', 1)

        # Выбор качества
        h_limit = 720
        if duration > 1800: h_limit = 240
        elif duration > 900: h_limit = 360
        elif duration > 480: h_limit = 480
        
        print(f"🎯 Режим: {h_limit}p (Время: {duration}с)")

        # Захват
        ydl_opts = {
            'format': f'bestvideo[height<={h_limit}][ext=mp4]+bestaudio[ext=m4a]/best[height<={h_limit}]',
            'outtmpl': f_raw, 'quiet': True, 'js_runtimes': {'deno': {}},
            'retries': 15, 'fragment_retries': 30, 'continuedl': True
        }
        if proxy: ydl_opts['proxy'] = proxy

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([v_url])
        
        if not os.path.exists(f_raw): return False
        raw_mb = os.path.getsize(f_raw) / (1024 * 1024)

        # Обработка Whisper (только для иностранных)
        has_subs, mode_tag = False, "🎙 ОРИГИНАЛЬНАЯ ОЗВУЧКА"
        if not is_russian:
            if whisper_model is None:
                print("🧠 [ЦУП] Загрузка Whisper (Base)...")
                whisper_model = whisper.load_model("base")
            
            print(f"🎙 Whisper: Перевод...")
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

        # Упаковка
        if raw_mb < SAFE_LIMIT_MB and not has_subs:
            f_to_send = f_raw
        else:
            print(f"⚙️ Глубокая упаковка...")
            target_br = int((SAFE_LIMIT_MB * 1024 * 1024 * 8) / duration * 0.75)
            v_br = max(120000, min(target_br, 2000000))
            vf = "subtitles=subs.srt:force_style='FontSize=20,BorderStyle=3,BackColour=&H80000000'" if has_subs else f"scale=-2:{h_limit}"
            subprocess.run(['ffmpeg', '-y', '-i', f_raw, '-vf', vf, '-c:v', 'libx264', '-b:v', str(v_br), '-preset', 'ultrafast', '-c:a', 'aac', '-b:a', '48k', f_final], capture_output=True)
            f_to_send = f_final

        # ОФОРМЛЕНИЕ
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

        final_mb = os.path.getsize(f_to_send) / (1024 * 1024)
        print(f"📡 Отправка ({final_mb:.1f} Мб)...")
        
        with open(f_to_send, 'rb') as v:
            r = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo", files={"video": v}, data={"chat_id": CHANNEL_NAME, "caption": caption, "parse_mode": "HTML"}, timeout=600)
            if r.status_code == 200:
                print("✅ Миссия выполнена успешно!")
                return True
            else:
                print(f"❌ Ошибка Telegram: {r.text}"); return False
    except Exception as e:
        print(f"⚠️ Сбой систем: {e}"); return False

# ============================================================
# 🛰 ГЛАВНЫЙ ЦИКЛ (ИСТОЧНИКИ v147.7)
# ============================================================

async def main():
    print(f"🎬 [ЦУП] v147.7 'Phantom Shield' запуск...")
    db = open(DB_FILE, 'r').read() if os.path.exists(DB_FILE) else ""
    last_s = open(SOURCE_LOG, 'r').read().strip() if os.path.exists(SOURCE_LOG) else ""

    SOURCES = [
        {'n': 'SpaceX Fan', 'cid': '@spacexfan420', 'ru': True}, # ТЕПЕРЬ RU
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
                    if await process_mission_v147(v['id'], v['title'], v['desc'], s['ru'], s['n']):
                        with open(DB_FILE, 'a') as f: f.write(f"\n{v['id']}")
                        with open(SOURCE_LOG, 'w') as f: f.write(s['n'])
                        return
        except: continue
    print("🛰 Горизонт чист.")

if __name__ == '__main__':
    asyncio.run(main())
