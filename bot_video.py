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
import re
import shutil
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
VOICE_LIMIT = 450 # 7.5 минут

SOURCES = [
    {'n': 'ESO (Европа - Наука)', 't': 'rss', 'u': 'https://www.eso.org/public/videos/feed/'},
    {'n': 'ESA (Наука Европы)', 't': 'rss', 'u': 'https://www.esa.int/rssfeed/Videos'},
    {'n': 'JAXA (Космос Японии)', 't': 'yt', 'id': 'UC1S_S6G_9A440VUM_KOn6Zg'},
    {'n': 'ISRO (Миссии Индии)', 't': 'yt', 'id': 'UC16vrn4PmwzOm_8atGYU8YQ'},
    {'n': 'Роскосмос (Россия)', 't': 'yt', 'id': 'UCp7fGZ8Z9zX_lZpY_l475_g'},
    {'n': 'SciNews (Мировые факты)', 't': 'yt', 'id': 'UCu3WicZMcXpUksat9yU859g'},
    {'n': 'Hubble (Открытия)', 't': 'rss', 'u': 'https://hubblesite.org/rss/news'},
    {'n': 'NASA (Архив)', 't': 'nasa_api'}
]

# ============================================================
# 🛠 БРОНИРОВАННЫЕ УТИЛИТЫ
# ============================================================

def super_clean(text, *args):
    """Очистка текста. Теперь принимает любое кол-во аргументов, чтобы не падать"""
    if not text: return ""
    # Удаляем все HTML теги и ссылки
    text = re.sub(r'<[^>]+>', '', str(text))
    text = re.sub(r'http\S+', '', text)
    # Оставляем только чистый текст, безопасный для Telegram
    return html.escape(html.unescape(text)).strip()

def clear_workspace():
    """Полная зачистка перед стартом"""
    for f in ["input.mp4", "output.mp4", "voice_final.mp3"]:
        if os.path.exists(f):
            try: os.remove(f)
            except: pass
    if os.path.exists("voice"):
        try: shutil.rmtree("voice")
        except: pass
    os.makedirs("voice", exist_ok=True)

# ============================================================
# 🎙 МОДУЛЬ ОЗВУЧКИ (v8.6 - БЕЗ ПРЕРЫВАНИЙ)
# ============================================================

async def build_voice_track(segments):
    """Создает монолитный файл озвучки"""
    print(f"🎙 Светлана начинает запись {len(segments[:70])} фрагментов...")
    inputs = []
    filter_parts = []
    valid_count = 0
    
    for i, seg in enumerate(segments[:70]):
        try:
            phrase = seg['text'].strip()
            if len(phrase) < 2: continue
            
            path = f"voice/v_{valid_count}.mp3"
            t_text = translator.translate(phrase)
            
            # Генерируем аудио файл
            communicate = edge_tts.Communicate(t_text, VOICE)
            await communicate.save(path)
            
            # Добавляем в очередь монтажа
            start_ms = int(seg['start'] * 1000)
            inputs.extend(["-i", path])
            filter_parts.append(f"[{valid_count}:a]adelay={start_ms}|{start_ms}[a{valid_count}]")
            valid_count += 1
        except Exception as e:
            print(f"⚠️ Ошибка фрагмента {i}: {e}")
            continue
    
    if valid_count == 0: return None
    
    # Склеиваем все кусочки в один голос
    labels = "".join([f"[a{i}]" for i in range(valid_count)])
    amix_filter = f"{';'.join(filter_parts)};{labels}amix=inputs={valid_count}:duration=first:dropout_transition=0[out]"
    
    cmd = ["ffmpeg", "-y"] + inputs + ["-filter_complex", amix_filter, "-map", "[out]", "-c:a", "libmp3lame", "voice_final.mp3"]
    subprocess.run(cmd, check=True)
    return "voice_final.mp3"

async def process_video_async(video_url, is_yt):
    """Асинхронный конвейер обработки"""
    f_in, f_out = "input.mp4", "output.mp4"
    clear_workspace()
    try:
        # 1. Загрузка
        ydl_opts = {'format': 'best[height<=720][ext=mp4]', 'outtmpl': f_in, 'quiet': True, 'noplaylist': True}
        if is_yt:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=True)
                if not info: return None, None
                dur = info.get('duration', 0)
        else:
            r = requests.get(video_url, timeout=120)
            with open(f_in, "wb") as f: f.write(r.content)
            dur = float(subprocess.check_output(f"ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 {f_in}", shell=True))

        # 2. Анализ Whisper
        print("🧠 ИИ анализирует речь...")
        res = model.transcribe(f_in)
        segments = res.get('segments', [])
        
        # 3. Озвучка
        if segments and dur <= VOICE_LIMIT:
            voice_file = await build_voice_track(segments)
            if voice_file and os.path.exists(voice_file):
                print("🎬 Финальный монтаж...")
                # Накладываем голос (1) на видео (0)
                cmd = ["ffmpeg", "-y", "-i", f_in, "-i", voice_file, 
                       "-filter_complex", "[0:a]volume=0.2[bg];[bg][1:a]amix=inputs=2:duration=first[outa]", 
                       "-map", "0:v", "-map", "[outa]", "-c:v", "copy", "-c:a", "aac", f_out]
                subprocess.run(cmd, check=True)
                return f_out, "voice"
        
        return f_in, "original"
    except Exception as e:
        print(f"❌ Сбой конвейера: {e}")
        return None, None

# ============================================================
# 🎬 ГЛАВНЫЙ МОДУЛЬ
# ============================================================

def main():
    print("🎬 [ЦУП] v8.6 'Infinity' запущен...")
    db = open(DB_FILE, 'r').read() if os.path.exists(DB_FILE) else ""
    
    pool = SOURCES.copy()
    random.shuffle(pool)

    for s in pool:
        try:
            print(f"📡 Сектор: {s['n']}...")
            url_f = s['u'] if 'u' in s else f"https://www.youtube.com/feeds/videos.xml?channel_id={s['id']}"
            res = requests.get(url_f, headers={'User-Agent': 'Mozilla/5.0'}, timeout=20)
            if "<?xml" not in res.text[:100]: continue
            
            root = ET.fromstring(res.content)
            items = root.findall('.//item') or root.findall('{http://www.w3.org/2005/Atom}entry')
            
            for item in items[:3]:
                link = ""
                if s['t'] == 'rss':
                    lt = item.find('.//enclosure')
                    link = lt.get('url') if lt is not None else item.find('link').text
                else:
                    v_node = item.find('{http://www.youtube.com/xml/schemas/2009}videoId')
                    if v_node is not None: link = f"https://www.youtube.com/watch?v={v_node.text}"
                
                if link and link not in db:
                    title_node = item.find('title')
                    desc_node = item.find('description') or item.find('{http://www.w3.org/2005/Atom}summary')
                    
                    title = title_node.text if title_node is not None else "Событие"
                    desc = desc_node.text if desc_node is not None else ""
                    
                    print(f"✅ Найдено: {title}")
                    # ЗАПУСК
                    path, mode = asyncio.run(process_video_async(link, 'youtube' in link))
                    
                    if not path: continue

                    # Формируем описание с защитой от лишних аргументов
                    t_ru = super_clean(translator.translate(title).upper())
                    d_ru = super_clean(translator.translate(desc[:300])) if desc else "Новости из глубин космоса."
                    if len(d_ru) > 170: d_ru = d_ru[:170] + "..."

                    caption = (
                        f"🎬 <b>{t_ru}</b>\n"
                        f"─────────────────────\n"
                        f"🪐 <b>ОБЪЕКТ:</b> {super_clean(s['n'])}\n"
                        f"🔊 <b>ЗВУК:</b> {('Голос Светланы' if mode=='voice' else 'Оригинал')}\n"
                        f"─────────────────────\n"
                        f"📖 {d_ru}\n\n"
                        f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
                    )

                    with open(path, 'rb') as v:
                        r = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo", 
                                          files={"video": v}, 
                                          data={"chat_id": CHANNEL_NAME, "caption": caption, "parse_mode": "HTML", "supports_streaming": True}, 
                                          timeout=120)
                    
                    if r.status_code == 200:
                        open(DB_FILE, 'a').write(f"\n{link}")
                        print("🎉 УСПЕШНО!")
                        return
        except Exception as e:
            print(f"⚠️ Сбой в {s['n']}: {e}")
            continue

if __name__ == '__main__': main()
