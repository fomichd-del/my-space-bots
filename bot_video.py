import requests
import os
import random
import time
import urllib.parse
import io
import subprocess
import whisper # Нейросеть для распознавания речи
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
# Загружаем модель Whisper (tiny - самая быстрая для GitHub)
model = whisper.load_model("tiny")

SEARCH_KEYWORDS = ['Mars Rover', 'ISS Tour', 'SpaceX Launch', 'Moon Mission', 'Black Hole']

# ============================================================
# 🧠 МОДУЛЬ ИИ-ПЕРЕВОДА (Whisper)
# ============================================================

def format_time(seconds):
    """Форматирует секунды в формат SRT: 00:00:00,000"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

def transcribe_and_translate(video_path):
    """Слушает видео и создает перевод по секундам"""
    print("🧠 ИИ начинает слушать видео...")
    # 1. Распознаем речь (Whisper сам поймет язык и переведет в текст)
    result = model.transcribe(video_path)
    segments = result.get('segments', [])
    
    if not segments:
        return None

    print(f"📝 Распознано {len(segments)} фраз. Начинаю перевод...")
    srt_content = ""
    
    for i, seg in enumerate(segments):
        start = format_time(seg['start'])
        end = format_time(seg['end'])
        text_en = seg['text'].strip()
        
        # Переводим каждую фразу на русский
        try:
            text_ru = translator.translate(text_en)
        except:
            text_ru = text_en
            
        srt_content += f"{i+1}\n{start} --> {end}\n{text_ru}\n\n"
    
    with open("subs.srt", "w", encoding="utf-8") as f:
        f.write(srt_content)
    return "subs.srt"

def burn_subtitles(video_url):
    """Главный процесс: скачка, прослушка, вшивка"""
    try:
        print("📥 Загрузка видео...")
        r = requests.get(video_url, stream=True, timeout=120)
        with open("input.mp4", "wb") as f:
            for chunk in r.iter_content(chunk_size=8192): f.write(chunk)
        
        # Запускаем ИИ
        srt_file = transcribe_and_translate("input.mp4")
        
        if srt_file:
            print("🔥 Впекаю ИИ-субтитры в видео...")
            style = "FontSize=22,PrimaryColour=&H00FFFF,OutlineColour=&H000000,BorderStyle=1,Outline=2,Alignment=2,MarginV=20"
            cmd = [
                'ffmpeg', '-y', '-i', 'input.mp4', 
                '-vf', f"subtitles=subs.srt:force_style='{style}'", 
                '-c:a', 'copy', '-preset', 'ultrafast', 'output.mp4'
            ]
            subprocess.run(cmd, check=True)
            return "output.mp4"
        return "input.mp4"
    except Exception as e:
        print(f"⚠️ Ошибка ИИ-перевода: {e}")
        return "input.mp4"

# ============================================================
# 🖌 АФИША И ПОИСК (Оставляем проверенное)
# ============================================================

def create_poster(img_url):
    try:
        res = requests.get(img_url, timeout=20)
        img = Image.open(io.BytesIO(res.content)).convert('RGB')
        img.thumbnail((400, 400))
        draw = ImageDraw.Draw(img, 'RGBA')
        draw.rectangle([(0, img.height-45), (img.width, img.height)], fill=(0,0,0,180))
        draw.text((15, img.height-33), "🎬 ИИ-ПЕРЕВОД: ОНЛАЙН", fill="#00FFFF")
        buf = io.BytesIO()
        img.save(buf, format='JPEG')
        buf.seek(0)
        return buf
    except: return None

def get_nasa_video():
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
                return {'url': video, 'img': thumb, 'title': item['data'][0]['title']}
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

    print(f"🎬 ИИ-перевод ролика: {video['title']}")
    
    # 1. Запускаем ИИ-обработку звука
    processed_path = burn_subtitles(video['url'])
    
    # 2. Переводим заголовок
    t_ru = translator.translate(video['title'])
    poster = create_poster(video['img'])
    
    caption = (f"🎬 <b>{t_ru.upper()}</b>\n\n"
               f"🎙 <b>Голос переведен ИИ (Whisper)</b>\n"
               f"📺 <i>Смотрите со включенным звуком!</i>\n\n"
               f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>")

    with open(processed_path, 'rb') as v:
        files = {"video": v}
        if poster: files["thumbnail"] = ("thumb.jpg", poster, "image/jpeg")
        
        payload = {"chat_id": CHANNEL_NAME, "caption": caption, "parse_mode": "HTML", "supports_streaming": True}
        r = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo", files=files, data=payload)
        
        if r.status_code == 200:
            with open(DB_FILE, 'a') as f: f.write(f"\n{video['url']}")
            print("🎉 Видео с ИИ-переводом голоса опубликовано!")

if __name__ == '__main__':
    main()
