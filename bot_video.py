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
VOICE = "ru-RU-SvetlanaNeural"
VOICE_LIMIT = 420 # Озвучиваем ролики до 7 минут. Все что длиннее - СУБТИТРЫ.

# ГЛОБАЛЬНЫЕ ИСТОЧНИКИ (NASA в самом конце!)
SOURCES = [
    {'n': 'ESO (Европа - Наука)', 't': 'rss_direct', 'u': 'https://www.eso.org/public/videos/feed/'},
    {'n': 'ESA (Европейская наука)', 't': 'rss_direct', 'u': 'https://www.esa.int/rssfeed/Videos'},
    {'n': 'Hubble/Webb (Открытия)', 't': 'rss_direct', 'u': 'https://hubblesite.org/rss/news'},
    {'n': 'JAXA (Япония)', 't': 'yt', 'id': 'UC1S_S6G_9A440VUM_KOn6Zg'},
    {'n': 'ISRO (Индия)', 't': 'yt', 'id': 'UC16vrn4PmwzOm_8atGYU8YQ'},
    {'n': 'Роскосмос (Россия)', 't': 'yt', 'id': 'UCp7fGZ8Z9zX_lZpY_l475_g'},
    {'n': 'SciNews (Мировая наука)', 't': 'yt', 'id': 'UCu3WicZMcXpUksat9yU859g'},
    {'n': 'Space.com (Факты)', 't': 'yt', 'id': 'UC6PnFayKstU9O_2uU_9rS7w'},
    {'n': 'NASA (Архивы)', 't': 'nasa_api'} # NASA ТЕПЕРЬ ПОСЛЕДНЯЯ В ОЧЕРЕДИ
]

def clean_html(text): return html.escape(text) if text else ""

def format_time(seconds):
    h = int(seconds // 3600); m = int((seconds % 3600) // 60); s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

# ============================================================
# 🎙 МОДУЛЬ СТАБИЛЬНОГО ГОЛОСА (v7.4)
# ============================================================

async def build_voice_track(segments, duration):
    """Создает единый файл озвучки с учетом всех пауз"""
    if not os.path.exists("voice"): os.makedirs("voice")
    
    # Создаем файл-инструкцию для FFmpeg (filter_complex_script)
    filter_script = ""
    inputs = []
    
    # Берем максимум 150 сегментов для стабильности
    for i, seg in enumerate(segments[:150]):
        try:
            text_ru = translator.translate(seg['text'].strip())
            path = f"voice/v_{i}.mp3"
            await edge_tts.Communicate(text_ru, VOICE).save(path)
            
            start_ms = int(seg['start'] * 1000)
            inputs.append(f"-i {path}")
            filter_script += f"[{i}:a]adelay={start_ms}|{start_ms}[a{i}];"
        except: continue
    
    if not inputs: return None
    
    labels = "".join([f"[a{i}]" for i in range(len(inputs))])
    # Смешиваем все в один voice_final.mp3
    cmd = f"ffmpeg -y {' '.join(inputs)} -filter_complex \"{filter_script}{labels}amix=inputs={len(inputs)}:duration=first:dropout_transition=0\" voice_final.mp3"
    subprocess.run(cmd, shell=True, check=True)
    return "voice_final.mp3"

# ============================================================
# 🛠 ГИБРИДНЫЙ ПРОЦЕССОР (Мир + Факт)
# ============================================================

def process_video(video_url, is_youtube=False):
    f_in, f_out = "input.mp4", "output.mp4"
    try:
        if is_youtube:
            ydl_opts = {'format': 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]', 'outtmpl': f_in, 'quiet': True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=True)
                dur = info.get('duration', 0)
        else:
            r = requests.get(video_url, timeout=120); open(f_in, "wb").write(r.content)
            dur = float(subprocess.check_output(f"ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 {f_in}", shell=True))

        res = model.transcribe(f_in); segments = res.get('segments', [])
        if not segments: return f_in, "оригинал"

        # ВЫБОР РЕЖИМА: ГОЛОС ИЛИ ТЕКСТ
        if dur <= VOICE_LIMIT:
            print(f"🎙 Озвучиваю: {int(dur)} сек")
            loop = asyncio.get_event_loop()
            voice_file = loop.run_until_complete(build_voice_track(segments, dur))
            if voice_file:
                cmd = f"ffmpeg -y -i {f_in} -i {voice_file} -filter_complex \"[0:a]volume=0.15[bg];[bg][1:a]amix=inputs=2:duration=first\" -map 0:v -map \"[out]\" -c:v libx264 -crf 28 -preset ultrafast -c:a aac -b:a 128k {f_out}"
                # Упрощенная команда микширования
                subprocess.run(f"ffmpeg -y -i {f_in} -i {voice_file} -filter_complex \"[0:a]volume=0.2[b];[b][1:a]amix=inputs=2:duration=first\" -c:v copy {f_out}", shell=True, check=True)
                return f_out, "голос"

        # Режим СУБТИТРОВ
        print(f"📝 Субтитры: {int(dur)} сек")
        srt = ""
        for i, s in enumerate(segments):
            srt += f"{i+1}\n{format_time(s['start'])} --> {format_time(s['end'])}\n{translator.translate(s['text'].strip())}\n\n"
        open("subs.srt", "w", encoding="utf-8").write(srt)
        style = "FontSize=14,PrimaryColour=&H00FFFFFF,OutlineColour=&H000000,BorderStyle=1,Outline=1,Alignment=2,MarginV=10"
        subprocess.run(['ffmpeg', '-y', '-i', f_in, '-vf', f"subtitles=subs.srt:force_style='{style}'", '-c:v', 'libx264', '-crf', '28', '-preset', 'ultrafast', f_out], check=True)
        return f_out, "субтитры"

    except Exception as e:
        print(f"❌ Сбой: {e}"); return None, None

# ============================================================
# 🛰 ГЛОБАЛЬНЫЙ ПОИСК
# ============================================================

def get_video_source():
    db = open(DB_FILE, 'r').read() if os.path.exists(DB_FILE) else ""
    # Перемешиваем источники, чтобы NASA не была всегда первой в проверке
    random.shuffle(SOURCES) 
    
    for s in SOURCES:
        try:
            print(f"📡 Проверка сектора: {s['n']}...")
            video = None
            if s['t'] == 'rss_direct':
                res = requests.get(s['u'], timeout=20); root = ET.fromstring(res.content)
                item = root.find('.//item') or root.find('{http://www.w3.org/2005/Atom}entry')
                # Для ESO/ESA берем прямую ссылку на файл
                link = item.find('.//enclosure').get('url') if item.find('.//enclosure') is not None else item.find('link').text
                video = {'url': link, 'title': item.find('title').text, 'is_yt': False, 'source': s['n']}
            elif s['t'] == 'yt':
                res = requests.get(f"https://www.youtube.com/feeds/videos.xml?channel_id={s['id']}", timeout=20)
                entry = ET.fromstring(res.content).find('{http://www.w3.org/2005/Atom}entry')
                v_id = entry.find('{http://www.youtube.com/xml/schemas/2009}videoId').text
                video = {'url': f"https://www.youtube.com/watch?v={v_id}", 'title': entry.find('{http://www.w3.org/2005/Atom}title').text, 'is_yt': True, 'source': s['n']}
            elif s['t'] == 'nasa_api':
                res = requests.get(f"https://images-api.nasa.gov/search?q=universe&media_type=video").json()
                item = random.choice(res['collection']['items'][:5])
                assets = requests.get(f"https://images-api.nasa.gov/asset/{item['data'][0]['nasa_id']}").json()
                v_url = next(a['href'] for a in assets['collection']['items'] if '~medium.mp4' in a['href'])
                video = {'url': v_url, 'title': item['data'][0]['title'], 'is_yt': False, 'source': s['n']}

            if video and video['url'] not in db: return video
        except: continue
    return None

# ============================================================
# 🎬 ЗАПУСК
# ============================================================

def main():
    video = get_video_source()
    if not video:
        print("🛑 Новых событий во Вселенной не найдено."); return

    print(f"✅ Цель захвачена: {video['title']} от {video['source']}")
    path, mode = process_video(video['url'], is_youtube=video['is_yt'])
    if not path: return

    t_ru = clean_html(translator.translate(video['title']).upper())
    mode_label = "🔊 Голосовой перевод" if mode == "голос" else "📝 Русские субтитры"
    
    caption = (
        f"🎬 <b>{t_ru}</b>\n"
        f"─────────────────────\n"
        f"🌍 <b>ОБЪЕКТ:</b> {clean_html(video['source'])}\n"
        f"{mode_label}\n"
        f"─────────────────────\n"
        f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
    )

    with open(path, 'rb') as v:
        r = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo", files={"video": v}, data={"chat_id": CHANNEL_NAME, "caption": caption, "parse_mode": "HTML", "supports_streaming": True})
        if r.status_code == 200:
            open(DB_FILE, 'a').write(f"\n{video['url']}")
            print("🎉 Выпуск в канале!")

if __name__ == '__main__': main()
