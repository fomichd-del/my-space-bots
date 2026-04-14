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

SEARCH_KEYWORDS = ['Mars Rover', 'ISS Tour', 'Saturn Rings', 'SpaceX Starship', 'Black Hole', 'Earth']

# ============================================================
# 📝 МОДУЛЬ СУБТИТРОВ И ОБРАБОТКИ
# ============================================================

def create_srt(text):
    """Создает файл субтитров .srt"""
    # Разбиваем длинный текст на фразы по 35 символов
    words = text.split()
    lines = []
    current_line = []
    for word in words:
        current_line.append(word)
        if len(' '.join(current_line)) > 35:
            lines.append(' '.join(current_line))
            current_line = []
    if current_line: lines.append(' '.join(current_line))
    
    # Формируем блоки по 2 строки (для удобства чтения)
    srt_content = ""
    for i in range(0, len(lines), 2):
        chunk = "\n".join(lines[i:i+2])
        start_sec = i * 3
        end_sec = start_sec + 5
        srt_content += f"{(i//2)+1}\n00:00:{start_sec:02d},000 --> 00:00:{end_sec:02d},000\n{chunk}\n\n"
    
    with open("subs.srt", "w", encoding="utf-8") as f:
        f.write(srt_content)
    return "subs.srt"

def embed_subtitles(video_url, translated_text):
    """Скачивает видео и вшивает субтитры через ffmpeg"""
    try:
        print("📥 Загрузка видео...")
        r = requests.get(video_url, stream=True, timeout=60)
        with open("input.mp4", "wb") as f:
            for chunk in r.iter_content(chunk_size=8192): f.write(chunk)
        
        create_srt(translated_text)
        print("🎞 Вшивка субтитров...")
        # Используем кодек mov_text для MP4 субтитров (понимается Телеграмом)
        cmd = [
            'ffmpeg', '-y', '-i', 'input.mp4', '-i', 'subs.srt',
            '-c', 'copy', '-c:s', 'mov_text', '-metadata:s:s:0', 'language=rus', 'output.mp4'
        ]
        subprocess.run(cmd, check=True)
        return "output.mp4"
    except Exception as e:
        print(f"⚠️ Ошибка обработки: {e}")
        return "input.mp4"

# ============================================================
# 🖌 МОДУЛЬ АФИШ (Обложка)
# ============================================================

def create_poster(img_url):
    try:
        res = requests.get(img_url, timeout=20)
        img = Image.open(io.BytesIO(res.content)).convert('RGB')
        img.thumbnail((320, 320))
        draw = ImageDraw.Draw(img, 'RGBA')
        text = "🚀 КИНОТЕАТР"
        # Рисуем простую подпись
        draw.rectangle([(0, img.height-40), (img.width, img.height)], fill=(0,0,0,180))
        draw.text((10, img.height-30), text, fill="white")
        
        buf = io.BytesIO()
        img.save(buf, format='JPEG')
        buf.seek(0)
        return buf
    except: return None

# ============================================================
# 🛰️ ПОИСК (NASA Library)
# ============================================================

def get_video():
    kw = random.choice(SEARCH_KEYWORDS)
    try:
        url = f"https://images-api.nasa.gov/search?q={kw}&media_type=video"
        res = requests.get(url, timeout=30).json()
        items = res['collection']['items']
        for item in items[:10]:
            nasa_id = item['data'][0]['nasa_id']
            assets = requests.get(f"https://images-api.nasa.gov/asset/{nasa_id}").json()
            links = [a['href'] for a in assets['collection']['items']]
            video = next((l for l in links if '~medium.mp4' in l), None)
            thumb = next((l for l in links if '~medium.jpg' in l), None)
            if video and thumb:
                return {'url': video, 'img': thumb, 'title': item['data'][0]['title'], 'desc': item['data'][0].get('description', '')}
    except: return None

# ============================================================
# 🎬 ЗАПУСК
# ============================================================

def main():
    video = get_video()
    if not video: return
    
    db = ""
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r') as f: db = f.read()
    if video['url'] in db: return

    print(f"✅ Найдено: {video['title']}")
    t_ru = translator.translate(video['title'])
    d_ru = translator.translate('. '.join(video['desc'].split('.')[:3]) + '.')
    
    # Обработка
    processed_path = embed_subtitles(video['url'], d_ru)
    poster = create_poster(video['img'])
    
    caption = (f"🎬 <b>КИНОТЕАТР: {t_ru.upper()}</b>\n\n"
               f"📖 <b>О ЧЕМ:</b> {d_ru}\n\n"
               f"💬 <i>(Включите субтитры в плеере)</i>\n\n"
               f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>")

    with open(processed_path, 'rb') as v:
        files = {"video": v}
        if poster: files["thumbnail"] = ("thumb.jpg", poster, "image/jpeg")
        
        payload = {"chat_id": CHANNEL_NAME, "caption": caption, "parse_mode": "HTML", "supports_streaming": True}
        r = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo", files=files, data=payload)
        
        if r.status_code == 200:
            with open(DB_FILE, 'a') as f: f.write(f"\n{video['url']}")
            print("🎉 Видео с субтитрами отправлено!")

if __name__ == '__main__':
    main()
