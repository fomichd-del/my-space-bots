import requests
import os
import random
import time
import xml.etree.ElementTree as ET
import subprocess
import whisper
import yt_dlp
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

# МАКСИМАЛЬНЫЙ СПИСОК МИРОВЫХ ИСТОЧНИКОВ (НАУКА + ВЕСЬ МИР)
SOURCES = [
    {'n': 'ESO (Научные открытия)', 't': 'rss', 'u': 'https://www.eso.org/public/videos/feed/'},
    {'n': 'ESA (Европейский космос)', 't': 'rss', 'u': 'https://www.esa.int/rssfeed/Videos'},
    {'n': 'Hubble/Webb (Тайны Вселенной)', 't': 'rss', 'u': 'https://hubblesite.org/rss/news'},
    {'n': 'Universe Today (Обучение)', 't': 'yt', 'id': 'UCZ3WicZMcXpUksat9yU859g'}, 
    {'n': 'JAXA (Японские технологии)', 't': 'yt', 'id': 'UC1S_S6G_9A440VUM_KOn6Zg'},
    {'n': 'ISRO (Индийская миссия)', 't': 'yt', 'id': 'UC16vrn4PmwzOm_8atGYU8YQ'},
    {'n': 'Роскосмос (Россия)', 't': 'yt', 'id': 'UCp7fGZ8Z9zX_lZpY_l475_g'},
    {'n': 'SciNews (Мировые события)', 't': 'yt', 'id': 'UCu3WicZMcXpUksat9yU859g'},
    {'n': 'Space.com (Факты и наука)', 't': 'yt', 'id': 'UC6PnFayKstU9O_2uU_9rS7w'},
    {'n': 'SpaceVidsNet (Глобальный мониторинг)', 't': 'yt', 'id': 'UCFid-F6idL1p4pZ-o4PZ-oQ'},
    {'n': 'NASA (Глобальные архивы)', 't': 'nasa_api'}
]

EMOJIS = ["👨‍🚀", "🧪", "🔭", "🌌", "🌍", "⚛️", "📡", "🛰", "🧠", "✨"]

# ============================================================
# 🛠 ТЕХНИЧЕСКИЙ БЛОК (Сжатие и Защита)
# ============================================================

def clean_html(text): return html.escape(text) if text else ""

def format_time(seconds):
    h = int(seconds // 3600); m = int((seconds % 3600) // 60); s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

def process_video_ai(video_url, is_youtube=False):
    f_in, f_out = "input.mp4", "output.mp4"
    try:
        if is_youtube:
            ydl_opts = {
                'format': 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]',
                'outtmpl': f_in, 'quiet': True, 'noplaylist': True
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl: ydl.download([video_url])
        else:
            r = requests.get(video_url, timeout=120); open(f_in, "wb").write(r.content)

        res = model.transcribe(f_in)
        if res.get('segments'):
            srt = ""
            for i, s in enumerate(res['segments']):
                t_ru = translator.translate(s['text'].strip())
                srt += f"{i+1}\n{format_time(s['start'])} --> {format_time(s['end'])}\n{t_ru}\n\n"
            open("subs.srt", "w", encoding="utf-8").write(srt)

            style = "FontSize=14,PrimaryColour=&H00FFFFFF,OutlineColour=&H000000,BorderStyle=1,Outline=1,Alignment=2,MarginV=10"
            subprocess.run(['ffmpeg', '-y', '-i', f_in, '-vf', f"subtitles=subs.srt:force_style='{style}'", 
                            '-c:v', 'libx264', '-crf', '28', '-preset', 'ultrafast', '-c:a', 'aac', '-b:a', '128k', f_out], check=True)
            return f_out if os.path.getsize(f_out) < 50*1024*1024 else None
        return f_in
    except: return None

# ============================================================
# 🔭 ГЛОБАЛЬНЫЙ СКАНЕР (Агрессивный поиск по всем странам)
# ============================================================

def get_best_global_video():
    print("📡 [SCANNER] Запуск глобального мониторинга мировых событий...")
    db = open(DB_FILE, 'r').read() if os.path.exists(DB_FILE) else ""
    candidates = []

    # Проверяем ВСЕ источники без исключения
    for s in SOURCES:
        try:
            video = None
            if s['t'] == 'rss':
                res = requests.get(s['u'], timeout=15)
                root = ET.fromstring(res.content)
                item = root.find('.//item') or root.find('{http://www.w3.org/2005/Atom}entry')
                link = item.find('.//enclosure').get('url') if item.find('.//enclosure') is not None else item.find('link').text
                video = {'url': link, 'title': item.find('title').text, 'is_yt': ('youtube' in link), 'source': s['n']}
            elif s['t'] == 'yt':
                res = requests.get(f"https://www.youtube.com/feeds/videos.xml?channel_id={s['id']}", timeout=15)
                entry = ET.fromstring(res.content).find('{http://www.w3.org/2005/Atom}entry')
                v_id = entry.find('{http://www.youtube.com/xml/schemas/2009}videoId').text
                video = {'url': f"https://www.youtube.com/watch?v={v_id}", 'title': entry.find('{http://www.w3.org/2005/Atom}title').text, 'is_yt': True, 'source': s['n']}
            elif s['t'] == 'nasa_api':
                res = requests.get(f"https://images-api.nasa.gov/search?q=astronomy&media_type=video").json()
                item = random.choice(res['collection']['items'][:5])
                assets = requests.get(f"https://images-api.nasa.gov/asset/{item['data'][0]['nasa_id']}").json()
                v_url = next(a['href'] for a in assets['collection']['items'] if '~medium.mp4' in a['href'])
                video = {'url': v_url, 'title': item['data'][0]['title'], 'is_yt': False, 'source': s['n']}

            if video and video['url'] not in db:
                candidates.append(video)
        except: continue

    if not candidates: return None
    
    # ПРИОРИТЕТ: Наука и мировые агентства (не NASA/SpaceX)
    random.shuffle(candidates)
    # Сначала ищем в списке что-то НЕ от NASA и SpaceX, если оно есть среди новых
    world_news = [c for c in candidates if "NASA" not in c['source'] and "SpaceX" not in c['source']]
    return world_news[0] if world_news else candidates[0]

# ============================================================
# 🎬 ГЛАВНАЯ ЛОГИКА
# ============================================================

def main():
    video = get_best_global_video()
    if not video:
        print("🛑 В мире за этот час новых космических событий не зафиксировано.")
        return

    print(f"✅ Цель захвачена: {video['title']} ({video['source']})")
    path = process_video_ai(video['url'], is_youtube=video['is_yt'])
    if not path: return

    t_ru = clean_html(translator.translate(video['title']).upper())
    e1, e2 = random.sample(EMOJIS, 2)
    
    caption = (
        f"{e1} <b>КОСМИЧЕСКИЙ КИНОТЕАТР</b> {e2}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📺 <b>{t_ru}</b>\n\n"
        f"🌍 <b>МЕСТО СОБЫТИЯ:</b> {clean_html(video['source'])}\n"
        f"🎙 <b>ПЕРЕВОД:</b> ИИ-синхрон (Whisper)\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
    )

    with open(path, 'rb') as v:
        r = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo", 
                          files={"video": v}, data={"chat_id": CHANNEL_NAME, "caption": caption, "parse_mode": "HTML", "supports_streaming": True})
        if r.status_code == 200:
            open(DB_FILE, 'a').write(f"\n{video['url']}")
            print("🎉 Глобальный выпуск опубликован!")

if __name__ == '__main__': main()
