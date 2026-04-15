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
from deep_translator import GoogleTranslator

# ============================================================
# ⚙️ НАСТРОЙКИ ЦУП
# ============================================================
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHANNEL_NAME   = '@vladislav_space'
DB_FILE        = "last_video_date.txt"

translator = GoogleTranslator(source='auto', target='ru')
model = whisper.load_model("tiny")
VOICE = "ru-RU-SvetlanaNeural"
VOICE_LIMIT = 420 

# МИРОВЫЕ ИСТОЧНИКИ (NASA вынесена в самый конец)
WORLD_SOURCES = [
    {'n': 'ESO (Наука Европы)', 't': 'rss', 'u': 'https://www.eso.org/public/videos/feed/'},
    {'n': 'ESA (Открытия Европы)', 't': 'rss', 'u': 'https://www.esa.int/rssfeed/Videos'},
    {'n': 'JAXA (Космос Японии)', 't': 'yt', 'id': 'UC1S_S6G_9A440VUM_KOn6Zg'},
    {'n': 'ISRO (Миссии Индии)', 't': 'yt', 'id': 'UC16vrn4PmwzOm_8atGYU8YQ'},
    {'n': 'Роскосмос (Россия)', 't': 'yt', 'id': 'UCp7fGZ8Z9zX_lZpY_l475_g'},
    {'n': 'SciNews (Мировые факты)', 't': 'yt', 'id': 'UCu3WicZMcXpUksat9yU859g'},
    {'n': 'Hubble (Глубокий космос)', 't': 'rss', 'u': 'https://hubblesite.org/rss/news'}
]
NASA_SOURCE = {'n': 'NASA (Архив)', 't': 'nasa_api'}

def clean_html(text):
    if not text: return ""
    return html.escape(text).replace('&lt;b&gt;', '<b>').replace('&lt;/b&gt;', '</b>')

# ============================================================
# 🎙 МОДУЛЬ ОБРАБОТКИ
# ============================================================

async def build_voice(segments):
    if not os.path.exists("voice"): os.makedirs("voice")
    inputs = []; filter_script = ""
    for i, seg in enumerate(segments[:100]):
        try:
            path = f"voice/v_{i}.mp3"
            await edge_tts.Communicate(translator.translate(seg['text']), VOICE).save(path)
            inputs.append(f"-i {path}")
            filter_script += f"[{i+1}:a]adelay={int(seg['start']*1000)}|{int(seg['start']*1000)}[a{i}];"
        except: continue
    if not inputs: return None
    labels = "".join([f"[a{i}]" for i in range(len(inputs))])
    cmd = f"ffmpeg -y {' '.join(inputs)} -filter_complex \"{filter_script}{labels}amix=inputs={len(inputs)}:duration=first\" voice_final.mp3"
    subprocess.run(cmd, shell=True, check=True)
    return "voice_final.mp3"

def process_video_master(video_url, is_yt):
    f_in, f_out = "input.mp4", "output.mp4"
    try:
        if is_yt:
            with yt_dlp.YoutubeDL({'format': 'best[height<=720]', 'outtmpl': f_in, 'quiet': True}) as ydl:
                info = ydl.extract_info(video_url, download=True)
                dur = info.get('duration', 0)
        else:
            r = requests.get(video_url, timeout=120); open(f_in, "wb").write(r.content)
            dur = float(subprocess.check_output(f"ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 {f_in}", shell=True))

        res = model.transcribe(f_in); segments = res.get('segments', [])
        if not segments: return f_in, "original"

        if dur <= VOICE_LIMIT:
            voice_file = asyncio.run(build_voice(segments))
            if voice_file:
                subprocess.run(f"ffmpeg -y -i {f_in} -i {voice_file} -filter_complex \"[0:a]volume=0.15[bg];[bg][1:a]amix=inputs=2:duration=first[out]\" -map 0:v -map \"[out]\" -c:v libx264 -crf 28 -preset ultrafast {f_out}", shell=True, check=True)
                return f_out, "voice"
        return f_in, "original"
    except: return None, None

# ============================================================
# 🔭 ГЛОБАЛЬНЫЙ СКАНЕР (ВЕСЬ МИР)
# ============================================================

def get_world_content(db):
    sources = WORLD_SOURCES.copy()
    random.shuffle(sources)
    sources.append(NASA_SOURCE) # NASA в самом хвосте

    for s in sources:
        try:
            print(f"📡 Сектор: {s['n']}...")
            if s['t'] == 'rss':
                res = requests.get(s['u'], timeout=20); root = ET.fromstring(res.content)
                items = root.findall('.//item') or root.findall('{http://www.w3.org/2005/Atom}entry')
                for item in items[:5]: # Проверяем последние 5
                    link = item.find('.//enclosure').get('url') if item.find('.//enclosure') is not None else item.find('link').text
                    if link not in db:
                        return {'url': link, 'title': item.find('title').text, 'is_yt': 'youtube' in link, 'source': s['n'], 'desc': item.find('description').text if item.find('description') is not None else ''}
            elif s['t'] == 'yt':
                res = requests.get(f"https://www.youtube.com/feeds/videos.xml?channel_id={s['id']}", timeout=20)
                entries = ET.fromstring(res.content).findall('{http://www.w3.org/2005/Atom}entry')
                for entry in entries[:5]:
                    link = f"https://www.youtube.com/watch?v={entry.find('{http://www.youtube.com/xml/schemas/2009}videoId').text}"
                    if link not in db:
                        return {'url': link, 'title': entry.find('{http://www.w3.org/2005/Atom}title').text, 'is_yt': True, 'source': s['n'], 'desc': ''}
        except: continue
    return None

def main():
    db = open(DB_FILE, 'r').read() if os.path.exists(DB_FILE) else ""
    video = get_world_content(db)
    
    if not video:
        print("🛑 Новых событий во всем мире не найдено.")
        return

    path, mode = process_video_master(video['url'], video['is_yt'])
    
    t_ru = clean_html(translator.translate(video['title']).upper())
    d_ru = clean_html(translator.translate('. '.join(video['desc'].split('.')[:2]) + '.')) if video['desc'] else "Уникальный репортаж о событиях в открытом космосе."
    mode_icon = "🔊" if mode == "voice" else "📹"
    
    caption = (
        f"🌌 <b>{t_ru}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🛰 <b>ОБЪЕКТ:</b> {clean_html(video['source'])}\n"
        f"{mode_icon} <b>ПЕРЕВОД:</b> {('Голосовой' if mode=='voice' else 'Оригинал')}\n\n"
        f"📖 <b>СЮЖЕТ:</b> {d_ru}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
    )

    if path:
        with open(path, 'rb') as v:
            r = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo", files={"video": v}, data={"chat_id": CHANNEL_NAME, "caption": caption, "parse_mode": "HTML", "supports_streaming": True})
    else:
        # Fallback: Если видео не обработалось, шлем текст
        r = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", data={"chat_id": CHANNEL_NAME, "text": f"🎥 <b>НОВОЕ ВИДЕО: {t_ru}</b>\n\n{caption}\n\n🔗 <a href='{video['url']}'>СМОТРЕТЬ</a>", "parse_mode": "HTML"})

    if r.status_code == 200:
        open(DB_FILE, 'a').write(f"\n{video['url']}")

if __name__ == '__main__': main()
