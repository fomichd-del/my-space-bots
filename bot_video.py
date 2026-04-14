import requests
import os
import random
import time
import xml.etree.ElementTree as ET
import urllib.parse
import io
import subprocess
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

SEARCH_KEYWORDS = ['Mars Rover', 'ISS Tour', 'Saturn Rings', 'SpaceX Launch', 'Galaxy', 'Jupiter']

# ============================================================
# 📝 МОДУЛЬ "ВШИВАНИЯ" СУБТИТРОВ (HARD-SUB)
# ============================================================

def create_srt(text):
    """Создает временный файл субтитров"""
    words = text.split()
    lines = []
    curr = []
    for w in words:
        curr.append(w)
        if len(' '.join(curr)) > 30:
            lines.append(' '.join(curr))
            curr = []
    if curr: lines.append(' '.join(curr))
    
    # Формируем блоки по 2 строки, которые будут сменять друг друга
    srt_content = ""
    for i in range(0, len(lines), 2):
        chunk = "\n".join(lines[i:i+2])
        start = i * 2
        end = start + 4
        srt_content += f"{(i//2)+1}\n00:00:{start:02d},000 --> 00:00:{end:02d},000\n{chunk}\n\n"
    
    with open("subs.srt", "w", encoding="utf-8") as f:
        f.write(srt_content)
    return "subs.srt"

def burn_subtitles(video_url, translated_text):
    """Вшивает субтитры прямо в видеопоток (Hardsub)"""
    try:
        print("📥 Загрузка видео для обработки...")
        r = requests.get(video_url, stream=True, timeout=60)
        with open("input.mp4", "wb") as f:
            for chunk in r.iter_content(chunk_size=8192): f.write(chunk)
        
        create_srt(translated_text)
        
        print("🔥 Впекаю субтитры в видео (это займет немного времени)...")
        # Используем фильтр 'subtitles'. 
        # force_style настраивает внешний вид: крупный шрифт, желтый цвет для заметности
        style = "FontSize=20,PrimaryColour=&H00FFFF,OutlineColour=&H000000,BorderStyle=1,Outline=2"
        cmd = [
            'ffmpeg', '-y', '-i', 'input.mp4', 
            '-vf', f"subtitles=subs.srt:force_style='{style}'", 
            '-c:a', 'copy', '-preset', 'ultrafast', 'output.mp4'
        ]
        subprocess.run(cmd, check=True)
        return "output.mp4"
    except Exception as e:
        print(f"⚠️ Ошибка впекания: {e}")
        return "input.mp4"

# ============================================================
# 🖌 МОДУЛЬ ОБЛОЖКИ (АФИША)
# ============================================================

def create_poster(img_url):
    try:
        res = requests.get(img_url, timeout=20)
        img = Image.open(io.BytesIO(res.content)).convert('RGB')
        img.thumbnail((400, 400))
        draw = ImageDraw.Draw(img, 'RGBA')
        draw.rectangle([(0, img.height-50), (img.width, img.height)], fill=(0,0,0,160))
        draw.text((20, img.height-35), "🚀 КИНОТЕАТР ПРЕДСТАВЛЯЕТ", fill="white")
        buf = io.BytesIO()
        img.save(buf, format='JPEG')
        buf.seek(0)
        return buf
    except: return None

# ============================================================
# 🛰️ ПОИСК
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
            thumb = next((l for l in links if '~medium.jpg' in l), None)
            if video and thumb:
                return {'url': video, 'img': thumb, 'title': item['data'][0]['title'], 'desc': item['data'][0].get('description', '')}
    except: return None

# ============================================================
# 🎬 ГЛАВНЫЙ ЗАПУСК
# ============================================================

def main():
    video = get_nasa_video()
    if not video: return
    
    db = ""
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r') as f: db = f.read()
    if video['url'] in db: return

    print(f"🎬 Работаю над выпуском: {video['title']}")
    
    # Перевод
    t_ru = translator.translate(video['title'])
    d_ru = translator.translate('. '.join(video['desc'].split('.')[:3]) + '.')
    
    # Вшиваем субтитры (теперь они будут всегда на экране)
    processed_path = burn_subtitles(video['url'], d_ru)
    poster = create_poster(video['img'])
    
    caption = (f"🎬 <b>{t_ru.upper()}</b>\n\n"
               f"📖 {d_ru}\n\n"
               f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>")

    with open(processed_path, 'rb') as v:
        files = {"video": v}
        if poster: files["thumbnail"] = ("thumb.jpg", poster, "image/jpeg")
        
        payload = {"chat_id": CHANNEL_NAME, "caption": caption, "parse_mode": "HTML", "supports_streaming": True}
        r = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo", files=files, data=payload)
        
        if r.status_code == 200:
            with open(DB_FILE, 'a') as f: f.write(f"\n{video['url']}")
            print("🎉 Видео с автоматическим переводом отправлено!")

if __name__ == '__main__':
    main()
