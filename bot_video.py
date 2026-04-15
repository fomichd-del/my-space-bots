import requests
import os
import random
import time
import xml.etree.ElementTree as ET
import subprocess
import whisper
import yt_dlp
import asyncio
import edge_tts
import html
import re
import shutil
from deep_translator import GoogleTranslator

# ============================================================
# ⚙️ НАСТРОЙКИ
# ============================================================
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHANNEL_NAME   = '@vladislav_space'
DB_FILE        = "last_video_date.txt"

translator = GoogleTranslator(source='auto', target='ru')
model = whisper.load_model("tiny")
VOICE = "ru-RU-SvetlanaNeural"
VOICE_LIMIT = 420 

SOURCES = [
    {'n': 'ESO (Наука Европы)', 't': 'rss', 'u': 'https://www.eso.org/public/videos/feed/'},
    {'n': 'ESA (Европейская наука)', 't': 'rss', 'u': 'https://www.esa.int/rssfeed/Videos'},
    {'n': 'JAXA (Япония)', 't': 'yt', 'id': 'UC1S_S6G_9A440VUM_KOn6Zg'},
    {'n': 'ISRO (Индия)', 't': 'yt', 'id': 'UC16vrn4PmwzOm_8atGYU8YQ'},
    {'n': 'Роскосмос (Россия)', 't': 'yt', 'id': 'UCp7fGZ8Z9zX_lZpY_l475_g'},
    {'n': 'SciNews (Мировые факты)', 't': 'yt', 'id': 'UCu3WicZMcXpUksat9yU859g'},
    {'n': 'Hubble (Открытия)', 't': 'rss', 'u': 'https://hubblesite.org/rss/news'},
    {'n': 'NASA (Архив)', 't': 'nasa_api'}
]

# ============================================================
# 🛠 ЗАЩИЩЕННЫЕ ФУНКЦИИ
# ============================================================

def super_clean(text):
    if not text: return ""
    text = re.sub(r'<[^>]+>', '', str(text)) # Вырезаем теги
    text = re.sub(r'http\S+', '', text)      # Вырезаем ссылки
    return html.unescape(text).strip()

def safe_get_text(element, tag_name):
    """Безопасное извлечение текста из XML тега"""
    if element is None: return ""
    tag = element.find(tag_name)
    return tag.text if tag is not None else ""

def clear_workspace():
    for f in ["input.mp4", "output.mp4", "voice_final.mp3"]:
        if os.path.exists(f): os.remove(f)
    if os.path.exists("voice"): shutil.rmtree("voice")
    os.makedirs("voice", exist_ok=True)

# ============================================================
# 🎙 МОДУЛЬ СВЕТЛАНЫ (v8.2)
# ============================================================

async def build_voice_track(segments):
    inputs = []; filter_parts = []; valid_count = 0
    for i, seg in enumerate(segments[:75]): # Лимит 75 фраз для стабильности
        try:
            phrase = super_clean(seg['text'])
            if len(phrase) < 3: continue
            
            path = f"voice/v_{valid_count}.mp3"
            await edge_tts.Communicate(translator.translate(phrase), VOICE).save(path)
            
            inputs.extend(["-i", path])
            start_ms = int(seg['start'] * 1000)
            filter_parts.append(f"[{valid_count}:a]adelay={start_ms}|{start_ms}[a{valid_count}]")
            valid_count += 1
        except: continue
    
    if valid_count == 0: return None
    labels = "".join([f"[a{i}]" for i in range(valid_count)])
    amix = f"amix=inputs={valid_count}:duration=first:dropout_transition=0"
    cmd = ["ffmpeg", "-y"] + inputs + ["-filter_complex", f"{';'.join(filter_parts)};{labels}{amix}[out]", "-map", "[out]", "voice_final.mp3"]
    subprocess.run(cmd, check=True)
    return "voice_final.mp3"

def process_video_master(video_url, is_yt):
    f_in, f_out = "input.mp4", "output.mp4"
    clear_workspace()
    try:
        ydl_opts = {'format': 'best[height<=720][ext=mp4]', 'outtmpl': f_in, 'quiet': True, 'noplaylist': True}
        if is_yt:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=True)
                dur = info.get('duration', 0)
        else:
            r = requests.get(video_url, timeout=120); open(f_in, "wb").write(r.content)
            dur = float(subprocess.check_output(f"ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 {f_in}", shell=True))

        res = model.transcribe(f_in)
        segments = res.get('segments', [])
        
        if segments and dur <= VOICE_LIMIT:
            voice_track = asyncio.run(build_voice_track(segments))
            if voice_track:
                cmd = ["ffmpeg", "-y", "-i", f_in, "-i", voice_track, "-filter_complex", "[0:a]volume=0.2[bg];[bg][1:a]amix=inputs=2:duration=first[outa]", "-map", "0:v", "-map", "[outa]", "-c:v", "copy", "-c:a", "aac", f_out]
                subprocess.run(cmd, check=True)
                return f_out, "voice"
        return f_in, "original"
    except Exception as e:
        print(f"⚠️ Ошибка обработки: {e}"); return None, None

# ============================================================
# 🎬 ГЛАВНЫЙ ЦИКЛ (Бронированный Поиск)
# ============================================================

def main():
    print("🎬 [ЦУП] v8.2 'Бронированный Спутник' запущен...")
    db = open(DB_FILE, 'r').read() if os.path.exists(DB_FILE) else ""
    pool = SOURCES.copy()
    random.shuffle(pool)

    candidates = []

    # Собираем всех кандидатов из всех источников
    for s in pool:
        try:
            url_fetch = s['u'] if 'u' in s else f"https://www.youtube.com/feeds/videos.xml?channel_id={s['id']}"
            res = requests.get(url_fetch, headers={'User-Agent': 'Mozilla/5.0'}, timeout=20)
            if "<?xml" not in res.text[:100]: continue
            
            root = ET.fromstring(res.content)
            if s['t'] == 'rss':
                items = root.findall('.//item') or root.findall('{http://www.w3.org/2005/Atom}entry')
                for item in items[:5]:
                    link_tag = item.find('.//enclosure')
                    link = link_tag.get('url') if link_tag is not None else safe_get_text(item, 'link')
                    if link and link not in db:
                        candidates.append({'url': link, 'title': safe_get_text(item, 'title'), 'is_yt': 'youtube' in link, 'source': s['n'], 'desc': safe_get_text(item, 'description')})
            else:
                for entry in root.findall('{http://www.w3.org/2005/Atom}entry')[:3]:
                    v_id = safe_get_text(entry, '{http://www.youtube.com/xml/schemas/2009}videoId')
                    link = f"https://www.youtube.com/watch?v={v_id}"
                    if v_id and link not in db:
                        candidates.append({'url': link, 'title': safe_get_text(entry, 'title'), 'is_yt': True, 'source': s['n'], 'desc': ''})
        except: continue

    # Приоритет мировым новостям (не NASA)
    candidates.sort(key=lambda x: "NASA" in x['source'])

    for video in candidates:
        print(f"🛰 Пробую выпустить: {video['title']} ({video['source']})")
        path, mode = process_video_master(video['url'], video['is_yt'])
        if not path: continue

        t_ru = super_clean(translator.translate(video['title']).upper())
        d_ru = super_clean(translator.translate(video['desc'][:300])) if video['desc'] else "Новые горизонты науки."
        d_ru = (d_ru[:160] + '...') if len(d_ru) > 160 else d_ru

        caption = (f"🎬 <b>{t_ru}</b>\n─────────────────────\n🪐 <b>ОБЪЕКТ:</b> {video['source']}\n🔊 <b>ЗВУК:</b> {('Голос Светланы' if mode=='voice' else 'Оригинал')}\n─────────────────────\n📖 {d_ru}\n\n🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>")

        with open(path, 'rb') as v:
            r = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo", files={"video": v}, data={"chat_id": CHANNEL_NAME, "caption": caption, "parse_mode": "HTML", "supports_streaming": True})
            if r.status_code == 200:
                open(DB_FILE, 'a').write(f"\n{video['url']}")
                print("🎉 УСПЕХ! Видео в канале."); return
            else: print(f"❌ ТГ ошибка: {r.text}")

if __name__ == '__main__': main()
