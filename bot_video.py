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

# МАКСИМАЛЬНЫЙ СПИСОК МИРОВЫХ КАНАЛОВ
CHANNELS = {
    'Роскосмос': 'UCp7fGZ8Z9zX_lZpY_l475_g',
    'SpaceX': 'UC_h_S6G_9A440VUM_KOn6Zg',
    'NASA Video': 'UCOpNcN46zbB0AgvW4t6OMvA',
    'ESA (Европа)': 'UC8u9uH_V83_Fns70cyJK_Iw',
    'ISRO (Индия)': 'UC16vrn4PmwzOm_8atGYU8YQ',
    'JAXA (Япония)': 'UC1S_S6G_9A440VUM_KOn6Zg',
    'SciNews (Китай/Мир)': 'UCu3WicZMcXpUksat9yU859g',
    'Blue Origin': 'UCOpNcN46zbB0AgvW4t6OMvA',
    'Virgin Galactic': 'UCpWfRCH-Nst_X6TIsiO476w',
    'VideoFromSpace': 'UCFid-F6idL1p4pZ-o4PZ-oQ',
    'Space.com': 'UC6PnFayKstU9O_2uU_9rS7w',
    'Cosmos News': 'UCu3WicZMcXpUksat9yU859g'
}

def format_time(seconds):
    h = int(seconds // 3600); m = int((seconds % 3600) // 60); s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

# ============================================================
# 🧠 ИИ-ОБРАБОТКА (Улучшенная)
# ============================================================

def process_video_ai(video_url, is_youtube=False):
    try:
        filename = "input.mp4"
        if is_youtube:
            print(f"📥 Качаю с YouTube: {video_url}")
            ydl_opts = {
                'format': 'best[ext=mp4]/best', 
                'outtmpl': filename, 
                'quiet': True,
                'match_filter': yt_dlp.utils.match_filter_func("duration > 30 & duration < 600") # Без Shorts
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl: ydl.download([video_url])
        else:
            r = requests.get(video_url, timeout=120)
            with open(filename, "wb") as f: f.write(r.content)

        print("🧠 ИИ Whisper слушает аудио...")
        result = model.transcribe(filename)
        segments = result.get('segments', [])
        
        if segments:
            srt_content = ""
            for i, seg in enumerate(segments):
                text_ru = translator.translate(seg['text'].strip())
                srt_content += f"{i+1}\n{format_time(seg['start'])} --> {format_time(seg['end'])}\n{text_ru}\n\n"
            with open("subs.srt", "w", encoding="utf-8") as f: f.write(srt_content)

            print("🔥 Впекаю перевод...")
            style = "FontSize=14,PrimaryColour=&H00FFFFFF,OutlineColour=&H000000,BorderStyle=1,Outline=1,Alignment=2,MarginV=10"
            subprocess.run(['ffmpeg', '-y', '-i', filename, '-vf', f"subtitles=subs.srt:force_style='{style}'", 
                            '-c:a', 'copy', '-preset', 'ultrafast', 'output.mp4'], check=True)
            return "output.mp4"
        return filename
    except Exception as e:
        print(f"⚠️ Сбой ИИ: {e}"); return filename if os.path.exists(filename) else None

# ============================================================
# 🛰️ АГРЕССИВНЫЙ ГЛОБАЛЬНЫЙ ПОИСК
# ============================================================

def get_video_from_rss(name, c_id):
    try:
        url = f"https://www.youtube.com/feeds/videos.xml?channel_id={c_id}"
        res = requests.get(url, timeout=20)
        root = ET.fromstring(res.content)
        entry = root.find('{http://www.w3.org/2005/Atom}entry')
        if entry is not None:
            v_id = entry.find('{http://www.youtube.com/xml/schemas/2009}videoId').text
            return {'url': f"https://www.youtube.com/watch?v={v_id}", 'title': entry.find('{http://www.w3.org/2005/Atom}title').text, 'source': name, 'is_yt': True}
    except: return None

def get_global_search_video():
    """Fallback: Поиск по всему YouTube за последние 24 часа"""
    print("🔭 Включаю глобальный радар по всему YouTube...")
    try:
        ydl_opts = {
            'quiet': True,
            'extract_flat': True,
            'force_generic_extractor': True,
        }
        query = random.choice(["space launch today", "astronomy news 2026", "mars mission update"])
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Ищем 5 самых свежих видео по теме
            search_results = ydl.extract_info(f"ytsearch5:{query}", download=False)
            for entry in search_results['entries']:
                return {'url': entry['url'], 'title': entry['title'], 'source': 'Global Space News', 'is_yt': True}
    except: return None

# ============================================================
# 🎬 ГЛАВНАЯ ЛОГИКА
# ============================================================

def main():
    print("🎬 [ЦУП] Глобальный Радар запущен...")
    db = open(DB_FILE, 'r').read() if os.path.exists(DB_FILE) else ""

    # Сначала проверяем ВСЕ официальные каналы
    print("📡 Сканирую официальные агентства мира...")
    candidates = []
    
    # Перемешиваем список, чтобы каждый раз не начинать с Роскосмоса
    items = list(CHANNELS.items())
    random.shuffle(items)

    for name, c_id in items:
        video = get_video_from_rss(name, c_id)
        if video and video['url'] not in db:
            candidates.append(video)
            if len(candidates) >= 3: break # Нашли достаточно вариантов

    # Если официальные каналы молчат, идем в Глобальный Поиск
    if not candidates:
        video = get_global_search_video()
        if video and video['url'] not in db:
            candidates.append(video)

    if not candidates:
        print("🛑 В мире за этот час ничего нового не опубликовано.")
        return

    # Берем самое интересное из найденного
    video = candidates[0]
    print(f"✅ Цель захвачена: {video['title']} от {video['source']}")
    
    processed_path = process_video_ai(video['url'], is_youtube=video['is_yt'])
    if not processed_path: return

    t_ru = translator.translate(video['title'])
    
    caption = (
        f"🎬 <b>КОСМИЧЕСКИЙ КИНОТЕАТР</b>\n"
        f"🌟 <b>{t_ru.upper()}</b>\n"
        f"─────────────────────\n\n"
        f"🛰 <b>ИСТОЧНИК:</b> {video['source']}\n"
        f"🎙 <b>ПЕРЕВОД:</b> ИИ Whisper (Синхрон)\n\n"
        f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
    )

    with open(processed_path, 'rb') as v:
        r = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo", 
                          files={"video": v}, data={"chat_id": CHANNEL_NAME, "caption": caption, "parse_mode": "HTML", "supports_streaming": True})
        
        if r.status_code == 200:
            open(DB_FILE, 'a').write(f"\n{video['url']}")
            print("🎉 Видео отправлено!")
        else:
            print(f"❌ Ошибка ТГ: {r.text}")

if __name__ == '__main__': main()
