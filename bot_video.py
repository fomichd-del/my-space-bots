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
import re # Для очистки мусора
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

# МИРОВОЙ СПИСОК (NASA В КОНЦЕ)
SOURCES = [
    {'n': 'ESO (Европа - Наука)', 't': 'rss', 'u': 'https://www.eso.org/public/videos/feed/'},
    {'n': 'ESA (Европейская наука)', 't': 'rss', 'u': 'https://www.esa.int/rssfeed/Videos'},
    {'n': 'JAXA (Космос Японии)', 't': 'yt', 'id': 'UC1S_S6G_9A440VUM_KOn6Zg'},
    {'n': 'ISRO (Миссии Индии)', 't': 'yt', 'id': 'UC16vrn4PmwzOm_8atGYU8YQ'},
    {'n': 'Роскосмос (Россия)', 't': 'yt', 'id': 'UCp7fGZ8Z9zX_lZpY_l475_g'},
    {'n': 'SciNews (Мировые факты)', 't': 'yt', 'id': 'UCu3WicZMcXpUksat9yU859g'},
    {'n': 'Hubble (Открытия)', 't': 'rss', 'u': 'https://hubblesite.org/rss/news'},
    {'n': 'NASA (Архив)', 't': 'nasa_api'}
]

# ============================================================
# 🛠 МОЩНАЯ ОЧИСТКА ТЕКСТА
# ============================================================

def clean_text(text):
    if not text: return ""
    # Убираем все HTML теги (типа <img>, <a> и тд)
    text = re.sub(r'<[^>]+>', '', text)
    # Убираем странные символы и экранируем для Telegram
    text = html.escape(text)
    return text.strip()

def format_time(seconds):
    h = int(seconds // 3600); m = int((seconds % 3600) // 60); s = int(seconds % 60)
    return f"{h:02d}:{m:02d}:{s:02d},000"

# ============================================================
# 🎙 СТАБИЛЬНЫЙ МОНТАЖ
# ============================================================

async def build_voice(segments):
    if not os.path.exists("voice"): os.makedirs("voice")
    inputs = []; filter_script = ""
    # Ограничиваем до 70 фраз, чтобы не упал сервер
    for i, seg in enumerate(segments[:70]):
        try:
            path = f"voice/v_{i}.mp3"
            clean_phrase = clean_text(seg['text'])
            await edge_tts.Communicate(translator.translate(clean_phrase), VOICE).save(path)
            inputs.append(f"-i {path}")
            filter_script += f"[{i+1}:a]adelay={int(seg['start']*1000)}|{int(seg['start']*1000)}[a{i}];"
        except: continue
    if not inputs: return None
    labels = "".join([f"[a{i}]" for i in range(len(inputs))])
    # Упрощенная команда склейки
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
        if not segments: return f_in, "оригинал"

        if dur <= VOICE_LIMIT:
            voice_file = asyncio.run(build_voice(segments))
            if voice_file:
                # МАКСИМАЛЬНО ЛЕГКАЯ КОМАНДА СВЕДЕНИЯ
                subprocess.run(f"ffmpeg -y -i {f_in} -i {voice_file} -filter_complex \"[0:a]volume=0.2[bg];[bg][1:a]amix=inputs=2:duration=first\" -c:v copy -c:a aac {f_out}", shell=True, check=True)
                return f_out, "голос"
        return f_in, "оригинал"
    except: return None, None

# ============================================================
# 🎬 ОСНОВНОЙ СКАНЕР
# ============================================================

def main():
    print("🎬 [ЦУП] Запуск v7.7 'Космический Стандарт'...")
    db = open(DB_FILE, 'r').read() if os.path.exists(DB_FILE) else ""
    
    random.shuffle(SOURCES)
    for s in SOURCES:
        try:
            print(f"📡 Сектор: {s['n']}...")
            video = None
            if s['t'] == 'rss':
                res = requests.get(s['u'], timeout=20); root = ET.fromstring(res.content)
                items = root.findall('.//item') or root.findall('{http://www.w3.org/2005/Atom}entry')
                for item in items[:3]:
                    link = item.find('.//enclosure').get('url') if item.find('.//enclosure') is not None else item.find('link').text
                    if link and link not in db:
                        video = {'url': link, 'title': item.find('title').text, 'is_yt': 'youtube' in link, 'source': s['n'], 'desc': item.find('description').text or ''}
                        break
            elif s['t'] == 'yt':
                res = requests.get(f"https://www.youtube.com/feeds/videos.xml?channel_id={s['id']}", timeout=20)
                entry = ET.fromstring(res.content).find('{http://www.w3.org/2005/Atom}entry')
                link = f"https://www.youtube.com/watch?v={entry.find('{http://www.youtube.com/xml/schemas/2009}videoId').text}"
                if link not in db:
                    video = {'url': link, 'title': entry.find('title').text, 'is_yt': True, 'source': s['n'], 'desc': ''}

            if video:
                path, mode = process_video_master(video['url'], video['is_yt'])
                if not path: continue

                # Оформление
                title_ru = clean_text(translator.translate(video['title']).upper())
                # Берем только первые 150 символов сюжета, чтобы не было простыни
                desc_ru = clean_text(translator.translate(video['desc'][:300])) if video['desc'] else "Новые горизонты и научные открытия."
                desc_ru = (desc_ru[:150] + '...') if len(desc_ru) > 150 else desc_ru

                caption = (
                    f"🎬 <b>{title_ru}</b>\n"
                    f"─────────────────────\n"
                    f"🔭 <b>ИСТОЧНИК:</b> {clean_text(s['n'])}\n"
                    f"🔊 <b>ПЕРЕВОД:</b> {('Голосовой' if mode=='voice' else 'Оригинал')}\n"
                    f"─────────────────────\n"
                    f"📖 <b>СЮЖЕТ:</b> {desc_ru}\n\n"
                    f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
                )

                with open(path, 'rb') as v:
                    r = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo", files={"video": v}, data={"chat_id": CHANNEL_NAME, "caption": caption, "parse_mode": "HTML", "supports_streaming": True})
                    if r.status_code == 200:
                        open(DB_FILE, 'a').write(f"\n{video['url']}")
                        return
        except: continue

if __name__ == '__main__': main()
