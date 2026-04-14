import requests
import os
import random
import time
import xml.etree.ElementTree as ET
import subprocess
import whisper
import yt_dlp
import io
from deep_translator import GoogleTranslator

# ============================================================
# ⚙️ НАСТРОЙКИ
# ============================================================
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
NASA_API_KEY   = os.getenv('NASA_API_KEY') or "DEMO_KEY"
CHANNEL_NAME   = '@vladislav_space'
DB_FILE        = "last_video_date.txt"

translator = GoogleTranslator(source='auto', target='ru')
model = whisper.load_model("tiny")

SOURCES = [
    {'name': 'ESO (Наука и факты)', 'type': 'rss', 'url': 'https://www.eso.org/public/videos/feed/'},
    {'name': 'ESA (Европейская наука)', 'type': 'rss', 'url': 'https://www.esa.int/rssfeed/Videos'},
    {'name': 'Роскосмос', 'type': 'yt', 'id': 'UCp7fGZ8Z9zX_lZpY_l475_g'},
    {'name': 'SpaceX (Технологии)', 'type': 'yt', 'id': 'UC_h_S6G_9A440VUM_KOn6Zg'},
    {'name': 'NASA (Архив)', 'type': 'nasa_api'},
    {'name': 'ISRO (Индия)', 'type': 'yt', 'id': 'UC16vrn4PmwzOm_8atGYU8YQ'},
    {'name': 'JAXA (Япония)', 'type': 'yt', 'id': 'UC1S_S6G_9A440VUM_KOn6Zg'},
    {'name': 'SciNews (Открытия)', 'type': 'yt', 'id': 'UCu3WicZMcXpUksat9yU859g'},
    {'name': 'Space.com (Наука)', 'type': 'yt', 'id': 'UC6PnFayKstU9O_2uU_9rS7w'}
]

# ============================================================
# 🧠 УЛУЧШЕННАЯ ОБРАБОТКА (Сжатие до 50МБ)
# ============================================================

def format_time(seconds):
    h = int(seconds // 3600); m = int((seconds % 3600) // 60); s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

def process_video_ai(video_url, is_youtube=False):
    filename = "input.mp4"
    output = "output.mp4"
    try:
        if is_youtube:
            print(f"📥 Качаю компактную версию (720p max)...")
            ydl_opts = {
                # Выбираем лучшее видео, но не выше 720p, чтобы влезть в лимит 50МБ
                'format': 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best',
                'outtmpl': filename, 'quiet': True
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl: ydl.download([video_url])
        else:
            r = requests.get(video_url, timeout=120)
            with open(filename, "wb") as f: f.write(r.content)

        # Распознавание Whisper
        result = model.transcribe(filename)
        segments = result.get('segments', [])
        
        if segments:
            srt_content = ""
            for i, seg in enumerate(segments):
                text_ru = translator.translate(seg['text'].strip())
                srt_content += f"{i+1}\n{format_time(seg['start'])} --> {format_time(seg['end'])}\n{text_ru}\n\n"
            with open("subs.srt", "w", encoding="utf-8") as f: f.write(srt_content)

            print("🔥 Впекаю субтитры со сжатием...")
            # ПАРАМЕТРЫ СЖАТИЯ: -crf 28 и битрейт 1M помогут удержать файл в пределах 50МБ
            style = "FontSize=14,PrimaryColour=&H00FFFFFF,OutlineColour=&H000000,BorderStyle=1,Outline=1,Alignment=2,MarginV=10"
            cmd = [
                'ffmpeg', '-y', '-i', filename, 
                '-vf', f"subtitles=subs.srt:force_style='{style}'", 
                '-c:v', 'libx264', '-crf', '28', '-preset', 'ultrafast',
                '-c:a', 'aac', '-b:a', '128k', output
            ]
            subprocess.run(cmd, check=True)
            
            # Проверка итогового веса
            file_size = os.path.getsize(output) / (1024 * 1024)
            print(f"📦 Итоговый вес: {file_size:.2f} МБ")
            
            if file_size > 49.5:
                print("❌ Файл слишком тяжелый для Telegram ( > 50MB).")
                return None
            return output
        return filename
    except Exception as e:
        print(f"⚠️ Ошибка: {e}"); return None

# ============================================================
# 🔭 ПОИСК И ГЛАВНАЯ ЛОГИКА
# ============================================================

def fetch_content(source):
    try:
        if source['type'] == 'rss':
            res = requests.get(source['url'], timeout=20)
            root = ET.fromstring(res.content)
            item = root.find('.//item') or root.find('{http://www.w3.org/2005/Atom}entry')
            if 'eso.org' in source['url']:
                video_url = item.find('.//enclosure').get('url') if item.find('.//enclosure') is not None else None
                return {'url': video_url, 'title': item.find('title').text, 'is_yt': False}
            return {'url': item.find('link').text, 'title': item.find('title').text, 'is_yt': True}
        elif source['type'] == 'yt':
            url = f"https://www.youtube.com/feeds/videos.xml?channel_id={source['id']}"
            res = requests.get(url, timeout=20)
            entry = ET.fromstring(res.content).find('{http://www.w3.org/2005/Atom}entry')
            v_id = entry.find('{http://www.youtube.com/xml/schemas/2009}videoId').text
            return {'url': f"https://www.youtube.com/watch?v={v_id}", 'title': entry.find('{http://www.w3.org/2005/Atom}title').text, 'is_yt': True}
        elif source['type'] == 'nasa_api':
            kw = random.choice(['Black Hole', 'Exoplanet', 'Galaxy', 'Science'])
            res = requests.get(f"https://images-api.nasa.gov/search?q={kw}&media_type=video").json()
            item = random.choice(res['collection']['items'][:10])
            assets = requests.get(f"https://images-api.nasa.gov/asset/{item['data'][0]['nasa_id']}").json()
            video_url = next(a['href'] for a in assets['collection']['items'] if '~medium.mp4' in a['href'])
            return {'url': video_url, 'title': item['data'][0]['title'], 'is_yt': False}
    except: return None

def main():
    print("🎬 [ЦУП] Глобальный Радар v5.7 (Анти-вес) запущен...")
    db = open(DB_FILE, 'r').read() if os.path.exists(DB_FILE) else ""
    pool = SOURCES.copy()
    random.shuffle(pool)

    for source in pool:
        print(f"📡 Проверяю: {source['name']}...")
        content = fetch_content(source)
        if content and content['url'] and content['url'] not in db:
            processed_path = process_video_ai(content['url'], is_youtube=content['is_yt'])
            if not processed_path: continue

            t_ru = translator.translate(content['title'])
            caption = (f"🎬 <b>КОСМИЧЕСКИЙ КИНОТЕАТР</b>\n"
                       f"🌟 <b>{t_ru.upper()}</b>\n"
                       f"─────────────────────\n\n"
                       f"🔭 <b>ИСТОЧНИК:</b> {source['name']}\n"
                       f"🎙 <b>ПЕРЕВОД:</b> ИИ-синхрон (Whisper)\n\n"
                       f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>")

            with open(processed_path, 'rb') as v:
                r = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo", 
                                  files={"video": v}, data={"chat_id": CHANNEL_NAME, "caption": caption, "parse_mode": "HTML", "supports_streaming": True})
                if r.status_code == 200:
                    open(DB_FILE, 'a').write(f"\n{content['url']}")
                    print("🎉 Выпуск опубликован!")
                    return
                else:
                    print(f"❌ Сбой ТГ ({r.status_code}): {r.text}")

if __name__ == '__main__': main()
