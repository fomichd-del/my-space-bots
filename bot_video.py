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
import io
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

# ГРАНИЦА: Видео короче этого времени (в секундах) будут озвучены
VOICE_LIMIT = 300 # 5 минут

SOURCES = [
    {'n': 'ESO (Наука Европы)', 't': 'rss', 'u': 'https://www.eso.org/public/videos/feed/'},
    {'n': 'ESA (Открытия)', 't': 'rss', 'u': 'https://www.esa.int/rssfeed/Videos'},
    {'n': 'Hubble/Webb (Космос)', 't': 'rss', 'u': 'https://hubblesite.org/rss/news'},
    {'n': 'Deep Sky Videos', 't': 'yt', 'id': 'UCRuC-LqegePz9B5zY_71vgg'},
    {'n': 'PBS Space Time', 't': 'yt', 'id': 'UC7_gcs09iThXybpVgjHZ_7g'},
    {'n': 'JAXA (Япония)', 't': 'yt', 'id': 'UC1S_S6G_9A440VUM_KOn6Zg'},
    {'n': 'ISRO (Индия)', 't': 'yt', 'id': 'UC16vrn4PmwzOm_8atGYU8YQ'},
    {'n': 'Роскосмос', 't': 'yt', 'id': 'UCp7fGZ8Z9zX_lZpY_l475_g'},
    {'n': 'SciNews (Мир)', 't': 'yt', 'id': 'UCu3WicZMcXpUksat9yU859g'}
]

def clean_html(text): return html.escape(text) if text else ""

def format_time(seconds):
    h = int(seconds // 3600); m = int((seconds % 3600) // 60); s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

# ============================================================
# 🎙 МОДУЛЬ ОЗВУЧКИ (TTS)
# ============================================================

async def create_voice_overlay(segments):
    if not os.path.exists("voice"): os.makedirs("voice")
    filter_complex = ""; inputs = []
    for i, seg in enumerate(segments):
        try:
            text_ru = translator.translate(seg['text'].strip())
            path = f"voice/v_{i}.mp3"
            await edge_tts.Communicate(text_ru, VOICE).save(path)
            start_ms = int(seg['start'] * 1000)
            inputs.append(f"-i {path}")
            filter_complex += f"[{i+1}:a]adelay={start_ms}|{start_ms}[a{i}];"
        except: continue
    if not inputs: return None
    labels = "".join([f"[a{i}]" for i in range(len(inputs))])
    cmd = f"ffmpeg -y {' '.join(inputs)} -filter_complex \"{filter_complex}{labels}amix=inputs={len(inputs)}:dropout_transition=0:normalize=0[out]\" -map \"[out]\" voiceover.mp3"
    subprocess.run(cmd, shell=True, check=True)
    return "voiceover.mp3"

# ============================================================
# 🛠 ГИБРИДНЫЙ ПРОЦЕССОР
# ============================================================

def process_video_hybrid(video_url, is_youtube=False):
    f_in, f_out = "input.mp4", "output.mp4"
    mode = "subtitles"
    try:
        # 1. Загрузка и проверка длительности
        ydl_opts = {'format': 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]', 'outtmpl': f_in, 'quiet': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            duration = info.get('duration', 0)
        
        if duration == 0: duration = float(subprocess.check_output(f"ffprobe -i {f_in} -show_entries format=duration -v quiet -of csv='p=0'", shell=True))
        
        # 2. Распознавание Whisper
        res = model.transcribe(f_in); segments = res.get('segments', [])
        if not segments: return f_in, "оригинал"

        # 3. ВЫБОР РЕЖИМА
        if duration <= VOICE_LIMIT:
            print(f"🎙 Режим ОЗВУЧКИ (Длительность: {duration} сек)")
            loop = asyncio.get_event_loop()
            voice_file = loop.run_until_complete(create_voice_overlay(segments))
            if voice_file:
                cmd = f"ffmpeg -y -i {f_in} -i {voice_file} -filter_complex \"[0:a]volume=0.15[bg];[bg][1:a]amix=inputs=2:duration=first[outa]\" -map 0:v -map \"[outa]\" -c:v libx264 -crf 28 -preset ultrafast -c:a aac -b:a 128k {f_out}"
                subprocess.run(cmd, shell=True, check=True)
                return f_out, "озвучка"
        
        print(f"📝 Режим СУБТИТРОВ (Длительность: {duration} сек)")
        srt = ""
        for i, s in enumerate(segments):
            t_ru = translator.translate(s['text'].strip())
            srt += f"{i+1}\n{format_time(s['start'])} --> {format_time(s['end'])}\n{t_ru}\n\n"
        open("subs.srt", "w", encoding="utf-8").write(srt)
        style = "FontSize=14,PrimaryColour=&H00FFFFFF,OutlineColour=&H000000,BorderStyle=1,Outline=1,Alignment=2,MarginV=10"
        subprocess.run(['ffmpeg', '-y', '-i', f_in, '-vf', f"subtitles=subs.srt:force_style='{style}'", '-c:v', 'libx264', '-crf', '28', '-preset', 'ultrafast', '-c:a', 'copy', f_out], check=True)
        return f_out, "субтитры"

    except Exception as e:
        print(f"❌ Ошибка: {e}"); return None, None

# ============================================================
# 🎬 ГЛАВНАЯ ЛОГИКА
# ============================================================

def fetch_content(source):
    try:
        if source['t'] == 'rss':
            res = requests.get(source['u'], timeout=20); root = ET.fromstring(res.content)
            item = root.find('.//item') or root.find('{http://www.w3.org/2005/Atom}entry')
            link = item.find('.//enclosure').get('url') if item.find('.//enclosure') is not None else item.find('link').text
            return {'url': link, 'title': item.find('title').text, 'is_yt': ('youtube' in (link or '')), 'desc': item.find('description').text if item.find('description') is not None else ''}
        elif source['t'] == 'yt':
            res = requests.get(f"https://www.youtube.com/feeds/videos.xml?channel_id={source['id']}", timeout=20)
            entry = ET.fromstring(res.content).find('{http://www.w3.org/2005/Atom}entry')
            v_id = entry.find('{http://www.youtube.com/xml/schemas/2009}videoId').text
            return {'url': f"https://www.youtube.com/watch?v={v_id}", 'title': entry.find('{http://www.w3.org/2005/Atom}title').text, 'is_yt': True, 'desc': ''}
    except: return None

def main():
    db = open(DB_FILE, 'r').read() if os.path.exists(DB_FILE) else ""
    pool = SOURCES.copy(); random.shuffle(pool)
    for s in pool:
        content = fetch_content(s)
        if content and content['url'] and content['url'] not in db:
            path, mode_name = process_video_hybrid(content['url'], is_youtube=content['is_yt'])
            if not path: continue
            
            t_ru = clean_html(translator.translate(content['title']).upper())
            mode_label = "🔊 Русская озвучка" if mode_name == "озвучка" else "📝 Русские субтитры"
            caption = (f"🎬 <b>{t_ru}</b>\n─────────────────────\n🪐 <b>ЦЕЛЬ:</b> {clean_html(s['n'])}\n{mode_label}\n─────────────────────\n🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>")
            
            with open(path, 'rb') as v:
                r = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo", files={"video": v}, data={"chat_id": CHANNEL_NAME, "caption": caption, "parse_mode": "HTML", "supports_streaming": True})
                if r.status_code == 200:
                    open(DB_FILE, 'a').write(f"\n{content['url']}")
                    return

if __name__ == '__main__': main()
