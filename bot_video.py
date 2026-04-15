import requests
import os
import random
import time
import xml.etree.ElementTree as ET
import subprocess
import whisper
import yt_dlp
import asyncio
import edge_tts
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
VOICE = "ru-RU-SvetlanaNeural" # Мягкий женский голос

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

# ============================================================
# 🎙 МОДУЛЬ ГОЛОСОВОЙ ОЗВУЧКИ
# ============================================================

async def create_voice_segments(segments):
    """Генерирует аудиофайлы для каждой фразы перевода"""
    if not os.path.exists("voice"): os.makedirs("voice")
    
    inputs = []
    filter_chains = []
    
    for i, seg in enumerate(segments):
        text_ru = translator.translate(seg['text'].strip())
        path = f"voice/v_{i}.mp3"
        
        # Генерация речи
        communicate = edge_tts.Communicate(text_ru, VOICE)
        await communicate.save(path)
        
        start_ms = int(seg['start'] * 1000)
        inputs.append(f"-i {path}")
        # Настройка задержки каждой фразы
        filter_chains.append(f"[{i+1}:a]adelay={start_ms}|{start_ms}[v{i}]")
    
    return inputs, filter_chains

def process_video_voice(video_url, is_youtube=False):
    f_in, f_out = "input.mp4", "output.mp4"
    try:
        # Загрузка
        if is_youtube:
            ydl_opts = {
                'format': 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]',
                'outtmpl': f_in, 'quiet': True
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl: ydl.download([video_url])
        else:
            r = requests.get(video_url, timeout=120); open(f_in, "wb").write(r.content)

        # Распознавание Whisper
        res = model.transcribe(f_in)
        segments = res.get('segments', [])
        if not segments: return f_in # Если речи нет, шлем оригинал

        # Генерация голоса (async)
        loop = asyncio.get_event_loop()
        v_inputs, v_filters = loop.run_until_complete(create_voice_segments(segments))

        # Сборка аудиофильтра FFmpeg
        # Приглушаем оригинал до 15% громкости, когда накладываем перевод
        inputs_cmd = " ".join(v_inputs)
        mix_labels = "".join([f"[v{i}]" for i in range(len(v_filters))])
        amix_filter = f"{';'.join(v_filters)};[0:a]volume=0.15[bg];[bg]{mix_labels}amix=inputs={len(v_filters)+1}:duration=first[outa]"
        
        print("🎬 Финальный монтаж звука...")
        cmd = [
            'ffmpeg', '-y', '-i', f_in
        ] + v_inputs + [
            '-filter_complex', amix_filter,
            '-map', '0:v', '-map', '[outa]',
            '-c:v', 'libx264', '-crf', '28', '-preset', 'ultrafast',
            '-c:a', 'aac', '-b:a', '128k', f_out
        ]
        subprocess.run(cmd, check=True)
        
        if os.path.exists(f_out) and os.path.getsize(f_out) < 49*1024*1024:
            return f_out
        return f_in if os.path.getsize(f_in) < 49*1024*1024 else None
    except Exception as e:
        print(f"❌ Ошибка озвучки: {e}"); return None

# ============================================================
# 🔭 СИСТЕМА ПОИСКА
# ============================================================

def fetch_content(source):
    try:
        if source['t'] == 'rss':
            res = requests.get(source['u'], timeout=20); root = ET.fromstring(res.content)
            item = root.find('.//item') or root.find('{http://www.w3.org/2005/Atom}entry')
            if 'eso.org' in source['u']:
                link = item.find('.//enclosure').get('url') if item.find('.//enclosure') is not None else None
            else:
                link = item.find('link').text
            return {'url': link, 'title': item.find('title').text, 'is_yt': ('youtube' in (link or '')), 'desc': item.find('description').text if item.find('description') is not None else ''}
        elif source['t'] == 'yt':
            url = f"https://www.youtube.com/feeds/videos.xml?channel_id={source['id']}"
            res = requests.get(url, timeout=20)
            entry = ET.fromstring(res.content).find('{http://www.w3.org/2005/Atom}entry')
            v_id = entry.find('{http://www.youtube.com/xml/schemas/2009}videoId').text
            return {'url': f"https://www.youtube.com/watch?v={v_id}", 'title': entry.find('{http://www.w3.org/2005/Atom}title').text, 'is_yt': True, 'desc': ''}
        elif source['t'] == 'nasa_api':
            res = requests.get(f"https://images-api.nasa.gov/search?q=science&media_type=video").json()
            item = random.choice(res['collection']['items'][:5])
            assets = requests.get(f"https://images-api.nasa.gov/asset/{item['data'][0]['nasa_id']}").json()
            v_url = next(a['href'] for a in assets['collection']['items'] if '~medium.mp4' in a['href'])
            return {'url': v_url, 'title': item['data'][0]['title'], 'is_yt': False, 'desc': item['data'][0].get('description', '')}
    except: return None

# ============================================================
# 🎬 ГЛАВНАЯ ЛОГИКА
# ============================================================

def main():
    db = open(DB_FILE, 'r').read() if os.path.exists(DB_FILE) else ""
    pool = SOURCES.copy(); random.shuffle(pool)

    for s in pool:
        content = fetch_content(s)
        if content and content['url'] and content['url'] not in db:
            print(f"📡 Озвучиваю выпуск от {s['n']}...")
            path = process_video_voice(content['url'], is_youtube=content['is_yt'])
            if not path: continue

            t_ru = clean_html(translator.translate(content['title']).upper())
            d_ru = clean_html(translator.translate('. '.join(content['desc'].split('.')[:2]) + '.')) if content['desc'] else "Увлекательные факты о Вселенной."
            
            caption = (
                f"🎬 <b>{t_ru}</b>\n"
                f"─────────────────────\n"
                f"🪐 <b>ЦЕЛЬ:</b> {clean_html(s['n'])}\n\n"
                f"📖 <b>СЮЖЕТ:</b> {d_ru}\n"
                f"─────────────────────\n"
                f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
            )

            with open(path, 'rb') as v:
                r = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo", 
                                  files={"video": v}, data={"chat_id": CHANNEL_NAME, "caption": caption, "parse_mode": "HTML", "supports_streaming": True})
                if r.status_code == 200:
                    open(DB_FILE, 'a').write(f"\n{content['url']}")
                    print("🎉 Озвученное видео успешно отправлено!")
                    return

if __name__ == '__main__': main()
