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

# МИРОВЫЕ ИСТОЧНИКИ (НАУКА, ОБУЧЕНИЕ, ФАКТЫ)
SOURCES = [
    {'n': 'ESO (Европейская обсерватория)', 't': 'rss', 'u': 'https://www.eso.org/public/videos/feed/'},
    {'n': 'ESA (Наука Европы)', 't': 'rss', 'u': 'https://www.esa.int/rssfeed/Videos'},
    {'n': 'Hubble/Webb (Открытия)', 't': 'rss', 'u': 'https://hubblesite.org/rss/news'},
    {'n': 'Deep Sky Videos (Обучение)', 't': 'yt', 'id': 'UCRuC-LqegePz9B5zY_71vgg'},
    {'n': 'PBS Space Time (Физика)', 't': 'yt', 'id': 'UC7_gcs09iThXybpVgjHZ_7g'},
    {'n': 'JAXA (Япония)', 't': 'yt', 'id': 'UC1S_S6G_9A440VUM_KOn6Zg'},
    {'n': 'ISRO (Индия)', 't': 'yt', 'id': 'UC16vrn4PmwzOm_8atGYU8YQ'},
    {'n': 'Роскосмос (Россия)', 't': 'yt', 'id': 'UCp7fGZ8Z9zX_lZpY_l475_g'},
    {'n': 'SciNews (Мировая наука)', 't': 'yt', 'id': 'UCu3WicZMcXpUksat9yU859g'},
    {'n': 'NASA (Научные архивы)', 't': 'nasa_api'}
]

def clean_html(text): return html.escape(text) if text else ""

def format_time(seconds):
    h = int(seconds // 3600); m = int((seconds % 3600) // 60); s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

# ============================================================
# 🧠 ОБРАБОТКА И СЖАТИЕ
# ============================================================

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
            if os.path.exists(f_out) and os.path.getsize(f_out) < 49*1024*1024: return f_out
        return f_in if os.path.getsize(f_in) < 49*1024*1024 else None
    except: return None

# ============================================================
# 🔭 ГЛОБАЛЬНЫЙ ПОИСК (Приоритет: Наука и Факты)
# ============================================================

def get_best_video():
    db = open(DB_FILE, 'r').read() if os.path.exists(DB_FILE) else ""
    candidates = []
    for s in SOURCES:
        try:
            v = None
            if s['t'] == 'rss':
                res = requests.get(s['u'], timeout=15)
                root = ET.fromstring(res.content)
                item = root.find('.//item') or root.find('{http://www.w3.org/2005/Atom}entry')
                link = item.find('.//enclosure').get('url') if item.find('.//enclosure') is not None else item.find('link').text
                v = {'url': link, 'title': item.find('title').text, 'is_yt': ('youtube' in link), 'source': s['n'], 'desc': item.find('description').text if item.find('description') is not None else ''}
            elif s['t'] == 'yt':
                res = requests.get(f"https://www.youtube.com/feeds/videos.xml?channel_id={s['id']}", timeout=15)
                entry = ET.fromstring(res.content).find('{http://www.w3.org/2005/Atom}entry')
                v_id = entry.find('{http://www.youtube.com/xml/schemas/2009}videoId').text
                v = {'url': f"https://www.youtube.com/watch?v={v_id}", 'title': entry.find('{http://www.w3.org/2005/Atom}title').text, 'is_yt': True, 'source': s['n'], 'desc': ''}
            elif s['t'] == 'nasa_api':
                res = requests.get(f"https://images-api.nasa.gov/search?q=discovery&media_type=video").json()
                item = random.choice(res['collection']['items'][:5])
                assets = requests.get(f"https://images-api.nasa.gov/asset/{item['data'][0]['nasa_id']}").json()
                v_url = next(a['href'] for a in assets['collection']['items'] if '~medium.mp4' in a['href'])
                v = {'url': v_url, 'title': item['data'][0]['title'], 'is_yt': False, 'source': s['n'], 'desc': item['data'][0].get('description', '')}

            if v and v['url'] not in db: candidates.append(v)
        except: continue

    if not candidates: return None
    random.shuffle(candidates)
    # Приоритет не-американским источникам
    world = [c for c in candidates if "NASA" not in c['source'] and "SpaceX" not in c['source']]
    return world[0] if world else candidates[0]

# ============================================================
# 🎬 ГЛАВНАЯ ЛОГИКА
# ============================================================

def main():
    video = get_best_video()
    if not video: return

    t_ru = clean_html(translator.translate(video['title']).upper())
    d_ru = clean_html(translator.translate('. '.join(video['desc'].split('.')[:2]) + '.')) if video['desc'] else "Уникальные кадры и научные факты о нашей Вселенной."
    
    # НОВОЕ ОФОРМЛЕНИЕ
    caption = (
        f"🎬 <b>{t_ru}</b>\n"
        f"─────────────────────\n"
        f"🪐 <b>ЦЕЛЬ:</b> {clean_html(video['source'])}\n\n"
        f"📖 <b>СЮЖЕТ:</b> {d_ru}\n"
        f"─────────────────────\n"
        f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
    )

    path = process_video_ai(video['url'], is_youtube=video['is_yt'])

    if path:
        with open(path, 'rb') as v:
            requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo", 
                          files={"video": v}, data={"chat_id": CHANNEL_NAME, "caption": caption, "parse_mode": "HTML", "supports_streaming": True})
    else:
        text = f"🎥 <b>{t_ru}</b>\n\n{caption}\n\n🔗 <a href='{video['url']}'>СМОТРЕТЬ В ОРИГИНАЛЕ</a>"
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", data={"chat_id": CHANNEL_NAME, "text": text, "parse_mode": "HTML"})

    open(DB_FILE, 'a').write(f"\n{video['url']}")

if __name__ == '__main__': main()
