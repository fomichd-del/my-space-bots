import requests
import os
import random
import time
import xml.etree.ElementTree as ET
import subprocess
import whisper
import yt_dlp
import io
from datetime import datetime
from deep_translator import GoogleTranslator
from PIL import Image, ImageDraw, ImageFont

# ============================================================
# ⚙️ НАСТРОЙКИ
# ============================================================
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
NASA_API_KEY   = os.getenv('NASA_API_KEY') or "DEMO_KEY"
CHANNEL_NAME   = '@vladislav_space'
DB_FILE        = "last_video_date.txt"

translator = GoogleTranslator(source='auto', target='ru')
model = whisper.load_model("tiny")

GLOBAL_CHANNELS = {
    'Роскосмос': 'UCp7fGZ8Z9zX_lZpY_l475_g',
    'SpaceX': 'UC_h_S6G_9A440VUM_KOn6Zg',
    'ISRO (Индия)': 'UC16vrn4PmwzOm_8atGYU8YQ',
    'ESA (Европа)': 'UC8u9uH_V83_Fns70cyJK_Iw',
    'NASA Video': 'UCOpNcN46zbB0AgvW4t6OMvA',
    'JAXA (Япония)': 'UC1S_S6G_9A440VUM_KOn6Zg'
}

# ============================================================
# 🧠 ИИ-ОБРАБОТКА (Whisper + FFmpeg)
# ============================================================

def format_time(seconds):
    h = int(seconds // 3600); m = int((seconds % 3600) // 60); s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

def process_video_ai(video_url, is_youtube=False):
    """Качает видео, слушает и вшивает ИИ-субтитры"""
    try:
        filename = "input.mp4"
        if is_youtube:
            print(f"📥 Качаю видео с YouTube: {video_url}")
            ydl_opts = {'format': 'best[ext=mp4]/best', 'outtmpl': filename, 'quiet': True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl: ydl.download([video_url])
        else:
            print(f"📥 Качаю прямой файл: {video_url}")
            r = requests.get(video_url, timeout=100); open(filename, "wb").write(r.content)

        print("🧠 ИИ слушает дорожку...")
        result = model.transcribe(filename)
        segments = result.get('segments', [])
        
        srt_content = ""
        for i, seg in enumerate(segments):
            text_ru = translator.translate(seg['text'].strip())
            srt_content += f"{i+1}\n{format_time(seg['start'])} --> {format_time(seg['end'])}\n{text_ru}\n\n"
        
        with open("subs.srt", "w", encoding="utf-8") as f: f.write(srt_content)

        print("🔥 Вшиваю перевод...")
        style = "FontSize=22,PrimaryColour=&H00FFFF,OutlineColour=&H000000,BorderStyle=1,Outline=2,Alignment=2,MarginV=25"
        subprocess.run(['ffmpeg', '-y', '-i', filename, '-vf', f"subtitles=subs.srt:force_style='{style}'", 
                        '-c:a', 'copy', '-preset', 'ultrafast', 'output.mp4'], check=True)
        return "output.mp4"
    except Exception as e:
        print(f"⚠️ Ошибка ИИ: {e}"); return filename if os.path.exists(filename) else None

# ============================================================
# 🛰️ ГЛОБАЛЬНЫЙ ПОИСК
# ============================================================

def get_world_video():
    """Ищет видео либо в NASA, либо в мировых YouTube-каналах"""
    if random.choice([True, False]):
        # NASA Library
        print("📡 Ищу в архивах NASA...")
        try:
            kw = random.choice(['Mars', 'ISS', 'Artemis', 'Galaxy'])
            res = requests.get(f"https://images-api.nasa.gov/search?q={kw}&media_type=video").json()
            item = random.choice(res['collection']['items'][:10])
            assets = requests.get(f"https://images-api.nasa.gov/asset/{item['data'][0]['nasa_id']}").json()
            video_url = next(a['href'] for a in assets['collection']['items'] if '~medium.mp4' in a['href'])
            return {'url': video_url, 'title': item['data'][0]['title'], 'is_yt': False, 'source': 'NASA'}
        except: return None
    else:
        # YouTube World
        name, c_id = random.choice(list(GLOBAL_CHANNELS.items()))
        print(f"📡 Ищу в {name}...")
        try:
            res = requests.get(f"https://www.youtube.com/feeds/videos.xml?channel_id={c_id}", timeout=20)
            entry = ET.fromstring(res.content).find('{http://www.w3.org/2005/Atom}entry')
            v_id = entry.find('{http://www.youtube.com/xml/schemas/2009}videoId').text
            return {'url': f"https://www.youtube.com/watch?v={v_id}", 'title': entry.find('{http://www.w3.org/2005/Atom}title').text, 'is_yt': True, 'source': name}
        except: return None

# ============================================================
# 🎬 ЗАПУСК
# ============================================================

def main():
    video = get_world_video()
    if not video: return
    
    db = open(DB_FILE, 'r').read() if os.path.exists(DB_FILE) else ""
    if video['url'] in db: return

    print(f"🎬 Старт выпуска: {video['title']} ({video['source']})")
    
    processed_path = process_video_ai(video['url'], is_youtube=video['is_yt'])
    if not processed_path: return

    t_ru = translator.translate(video['title'])
    caption = (f"🎬 <b>{t_ru.upper()}</b>\n\n"
               f"🌎 <b>Источник:</b> {video['source']}\n"
               f"🎙 <b>Перевод:</b> ИИ (Whisper)\n\n"
               f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>")

    with open(processed_path, 'rb') as v:
        r = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo", 
                          files={"video": v}, data={"chat_id": CHANNEL_NAME, "caption": caption, "parse_mode": "HTML", "supports_streaming": True})
        
        if r.status_code == 200:
            open(DB_FILE, 'a').write(f"\n{video['url']}")
            print("🎉 Глобальный выпуск опубликован!")

if __name__ == '__main__': main()
