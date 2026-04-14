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

EMOJIS = ["✨", "🔭", "📡", "🛰", "👨‍🚀", "🛸", "🌍", "☄️", "👾"]

# ============================================================
# 🧠 МОДУЛЬ ИИ-ОБРАБОТКИ (Hardsub v5.2)
# ============================================================

def format_time(seconds):
    h = int(seconds // 3600); m = int((seconds % 3600) // 60); s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

def process_video_ai(video_url, is_youtube=False):
    try:
        filename = "input.mp4"
        if is_youtube:
            ydl_opts = {'format': 'best[ext=mp4]/best', 'outtmpl': filename, 'quiet': True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl: ydl.download([video_url])
        else:
            r = requests.get(video_url, timeout=100); open(filename, "wb").write(r.content)

        # РАСПОЗНАВАНИЕ
        result = model.transcribe(filename)
        segments = result.get('segments', [])
        
        srt_content = ""
        for i, seg in enumerate(segments):
            text_ru = translator.translate(seg['text'].strip())
            srt_content += f"{i+1}\n{format_time(seg['start'])} --> {format_time(seg['end'])}\n{text_ru}\n\n"
        
        with open("subs.srt", "w", encoding="utf-8") as f: f.write(srt_content)

        print("🔥 Впекаю аккуратные субтитры...")
        #FontSize=14 - компактно, MarginV=10 - в самый низ
        style = "FontSize=14,PrimaryColour=&H00FFFFFF,OutlineColour=&H000000,BorderStyle=1,Outline=1,Alignment=2,MarginV=10"
        subprocess.run(['ffmpeg', '-y', '-i', filename, '-vf', f"subtitles=subs.srt:force_style='{style}'", 
                        '-c:a', 'copy', '-preset', 'ultrafast', 'output.mp4'], check=True)
        return "output.mp4"
    except Exception as e:
        print(f"⚠️ Ошибка ИИ: {e}"); return filename if os.path.exists(filename) else None

# ============================================================
# 🛰️ ГЛОБАЛЬНЫЙ ПОИСК
# ============================================================

def get_world_video():
    choice = random.choice(['nasa', 'yt'])
    if choice == 'nasa':
        try:
            kw = random.choice(['Mars', 'ISS', 'Artemis', 'Galaxy', 'Jupiter'])
            res = requests.get(f"https://images-api.nasa.gov/search?q={kw}&media_type=video").json()
            item = random.choice(res['collection']['items'][:10])
            assets = requests.get(f"https://images-api.nasa.gov/asset/{item['data'][0]['nasa_id']}").json()
            video_url = next(a['href'] for a in assets['collection']['items'] if '~medium.mp4' in a['href'])
            return {'url': video_url, 'title': item['data'][0]['title'], 'is_yt': False, 'source': 'NASA Archive', 'desc': item['data'][0].get('description', '')}
        except: return None
    else:
        name, c_id = random.choice(list(GLOBAL_CHANNELS.items()))
        try:
            res = requests.get(f"https://www.youtube.com/feeds/videos.xml?channel_id={c_id}", timeout=20)
            entry = ET.fromstring(res.content).find('{http://www.w3.org/2005/Atom}entry')
            v_id = entry.find('{http://www.youtube.com/xml/schemas/2009}videoId').text
            return {'url': f"https://www.youtube.com/watch?v={v_id}", 'title': entry.find('{http://www.w3.org/2005/Atom}title').text, 'is_yt': True, 'source': name, 'desc': ''}
        except: return None

# ============================================================
# 🎬 ЗАПУСК
# ============================================================

def main():
    video = get_world_video()
    if not video: return
    
    db = open(DB_FILE, 'r').read() if os.path.exists(DB_FILE) else ""
    if video['url'] in db: return

    print(f"🎬 Работаю над роликом: {video['title']}")
    
    processed_path = process_video_ai(video['url'], is_youtube=video['is_yt'])
    if not processed_path: return

    t_ru = translator.translate(video['title'])
    d_ru = translator.translate('. '.join(video['desc'].split('.')[:2]) + '.') if video['desc'] else "Увлекательные кадры из космоса."

    # ОФОРМЛЕНИЕ ОПИСАНИЯ
    rand_emoji = random.choice(EMOJIS)
    rand_emoji2 = random.choice(EMOJIS)
    
    caption = (
        f"🎬 <b>КОСМИЧЕСКИЙ КИНОТЕАТР {rand_emoji}</b>\n"
        f"🌟 <b>{t_ru.upper()}</b>\n"
        f"─────────────────────\n\n"
        f"🛰 <b>ОБЪЕКТ:</b> {video['source']}\n"
        f"{rand_emoji2} <b>СЮЖЕТ:</b> {d_ru}\n\n"
        f"🎙 <b>ПЕРЕВОД:</b> ИИ-синхрон (Whisper)\n\n"
        f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
    )

    with open(processed_path, 'rb') as v:
        r = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo", 
                          files={"video": v}, data={"chat_id": CHANNEL_NAME, "caption": caption, "parse_mode": "HTML", "supports_streaming": True})
        
        if r.status_code == 200:
            open(DB_FILE, 'a').write(f"\n{video['url']}")
            print("🎉 Выпуск опубликован!")

if __name__ == '__main__': main()
