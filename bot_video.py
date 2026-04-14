import requests
import os
import random
import time
import xml.etree.ElementTree as ET
import urllib.parse
import io
import subprocess
import json
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

SEARCH_KEYWORDS = ['Mars Rover', 'ISS Tour', 'Saturn Rings', 'SpaceX Starship', 'Galaxy', 'Jupiter', 'Nebula']

# ============================================================
# 📝 МОДУЛЬ ДИНАМИЧЕСКИХ СУБТИТРОВ
# ============================================================

def get_video_duration(filename):
    """Узнает длительность видео в секундах через ffprobe"""
    try:
        cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', filename]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        return float(result.stdout)
    except:
        return 30.0 # По умолчанию 30 сек

def create_dynamic_srt(text, duration):
    """Разбивает текст на части и распределяет их по времени видео"""
    words = text.split()
    # Разбиваем на блоки по 5 слов
    chunks = [" ".join(words[i:i+5]) for i in range(0, len(words), 5)]
    if not chunks: return None
    
    # Считаем, сколько времени выделить на каждый блок
    time_per_chunk = duration / len(chunks)
    srt_content = ""
    
    for i, chunk in enumerate(chunks):
        start_time = i * time_per_chunk
        end_time = (i + 1) * time_per_chunk
        
        # Форматируем время в 00:00:00,000
        def format_time(seconds):
            h = int(seconds // 3600)
            m = int((seconds % 3600) // 60)
            s = int(seconds % 60)
            ms = int((seconds - int(seconds)) * 1000)
            return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

        srt_content += f"{i+1}\n{format_time(start_time)} --> {format_time(end_time)}\n{chunk}\n\n"
    
    with open("subs.srt", "w", encoding="utf-8") as f:
        f.write(srt_content)
    return "subs.srt"

def burn_subtitles(video_url, translated_text):
    """Впекает динамические субтитры в видео"""
    try:
        print("📥 Загрузка видео...")
        r = requests.get(video_url, stream=True, timeout=60)
        with open("input.mp4", "wb") as f:
            for chunk in r.iter_content(chunk_size=8192): f.write(chunk)
        
        duration = get_video_duration("input.mp4")
        create_dynamic_srt(translated_text, duration)
        
        print(f"🔥 Вшиваю динамические субтитры ({int(duration)} сек)...")
        # Стиль: FontSize=24, желтый текст, черная обводка (Outline), позиция снизу
        style = "FontSize=22,PrimaryColour=&H00FFFF,OutlineColour=&H000000,BorderStyle=1,Outline=2,Alignment=2,MarginV=25"
        cmd = [
            'ffmpeg', '-y', '-i', 'input.mp4', 
            '-vf', f"subtitles=subs.srt:force_style='{style}'", 
            '-c:a', 'copy', '-preset', 'ultrafast', 'output.mp4'
        ]
        subprocess.run(cmd, check=True)
        return "output.mp4"
    except Exception as e:
        print(f"⚠️ Ошибка: {e}")
        return "input.mp4"

# ============================================================
# 🖌 МОДУЛЬ АФИШИ
# ============================================================

def create_poster(img_url):
    try:
        res = requests.get(img_url, timeout=20)
        img = Image.open(io.BytesIO(res.content)).convert('RGB')
        img.thumbnail((400, 400))
        draw = ImageDraw.Draw(img, 'RGBA')
        draw.rectangle([(0, img.height-45), (img.width, img.height)], fill=(0,0,0,180))
        draw.text((15, img.height-35), "🎬 КОСМИЧЕСКИЙ КИНОТЕАТР", fill="#00FFFF")
        buf = io.BytesIO()
        img.save(buf, format='JPEG')
        buf.seek(0)
        return buf
    except: return None

# ============================================================
# 🛰️ ПОИСК NASA
# ============================================================

def get_nasa_video():
    kw = random.choice(SEARCH_KEYWORDS)
    try:
        url = f"https://images-api.nasa.gov/search?q={kw}&media_type=video"
        res = requests.get(url, timeout=30).json()
        items = res['collection']['items']
        for item in items[:15]:
            nasa_id = item['data'][0]['nasa_id']
            assets = requests.get(f"https://images-api.nasa.gov/asset/{nasa_id}").json()
            links = [a['href'] for a in assets['collection']['items']]
            video = next((l for l in links if '~medium.mp4' in l), None)
            thumb = next((l for l in links if '~medium.jpg' in l or '~large.jpg' in l), None)
            if video and thumb:
                return {'url': video, 'img': thumb, 'title': item['data'][0]['title'], 'desc': item['data'][0].get('description', '')}
    except: return None

# ============================================================
# 🎬 ЗАПУСК
# ============================================================

def main():
    video = get_nasa_video()
    if not video: return
    
    db = ""
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r') as f: db = f.read()
    if video['url'] in db: return

    print(f"🎬 Готовлю выпуск: {video['title']}")
    
    t_ru = translator.translate(video['title'])
    # Берем чуть больше текста для динамики
    d_ru = translator.translate('. '.join(video['desc'].split('.')[:5]) + '.')
    
    processed_path = burn_subtitles(video['url'], d_ru)
    poster = create_poster(video['img'])
    
    caption = (f"🎬 <b>{t_ru.upper()}</b>\n\n"
               f"📖 {translator.translate('. '.join(video['desc'].split('.')[:2]) + '.')}\n\n"
               f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>")

    with open(processed_path, 'rb') as v:
        files = {"video": v}
        if poster: files["thumbnail"] = ("thumb.jpg", poster, "image/jpeg")
        
        payload = {"chat_id": CHANNEL_NAME, "caption": caption, "parse_mode": "HTML", "supports_streaming": True}
        r = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo", files=files, data=payload)
        
        if r.status_code == 200:
            with open(DB_FILE, 'a') as f: f.write(f"\n{video['url']}")
            print("🎉 Выпуск с динамическим переводом опубликован!")

if __name__ == '__main__':
    main()
