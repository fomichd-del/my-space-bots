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
from deep_translator import GoogleTranslator

# ============================================================
# ⚙️ НАСТРОЙКИ
# ============================================================
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHANNEL_NAME   = '@vladislav_space'
DB_FILE        = "last_video_date.txt"

translator = GoogleTranslator(source='auto', target='ru')
model = whisper.load_model("tiny")
VOICE = "ru-RU-SvetlanaNeural"
VOICE_LIMIT = 420 

# МИРОВЫЕ ИСТОЧНИКИ
SOURCES = [
    {'n': 'ESO (Наука Европы)', 't': 'rss', 'u': 'https://www.eso.org/public/videos/feed/'},
    {'n': 'ESA (Европейская наука)', 't': 'rss', 'u': 'https://www.esa.int/rssfeed/Videos'},
    {'n': 'JAXA (Япония)', 't': 'yt', 'id': 'UC1S_S6G_9A440VUM_KOn6Zg'},
    {'n': 'ISRO (Индия)', 't': 'yt', 'id': 'UC16vrn4PmwzOm_8atGYU8YQ'},
    {'n': 'Роскосмос (Россия)', 't': 'yt', 'id': 'UCp7fGZ8Z9zX_lZpY_l475_g'},
    {'n': 'SciNews (Мировые факты)', 't': 'yt', 'id': 'UCu3WicZMcXpUksat9yU859g'},
    {'n': 'Hubble (Открытия)', 't': 'rss', 'u': 'https://hubblesite.org/rss/news'},
    {'n': 'NASA (Архив)', 't': 'nasa_api'}
]

# ============================================================
# 🛠 МОДУЛЬ ОЧИСТКИ ТЕКСТА
# ============================================================

def clean_text(text):
    if not text: return ""
    # Удаляем абсолютно всё внутри скобок < > (теги, картинки, ссылки)
    text = re.sub(r'<[^>]+>', '', text)
    # Удаляем остатки прямых ссылок http/https
    text = re.sub(r'http\S+', '', text)
    # Очищаем от HTML-сущностей и лишних пробелов
    text = html.unescape(text).strip()
    return text

# ============================================================
# 🎙 ИСПРАВЛЕННЫЙ МОНТАЖ (v7.9)
# ============================================================

async def build_voice_final(segments):
    if not os.path.exists("voice"): os.makedirs("voice")
    inputs = []
    filter_script = ""
    valid_count = 0
    
    for i, seg in enumerate(segments[:80]):
        try:
            phrase = seg['text'].strip()
            if len(phrase) < 3: continue
            
            path = f"voice/v_{valid_count}.mp3"
            text_ru = translator.translate(phrase)
            await edge_tts.Communicate(text_ru, VOICE).save(path)
            
            inputs.append(f"-i {path}")
            start_ms = int(seg['start'] * 1000)
            
            # ВАЖНО: Индекс входа для озвучки начинается с 1 (0 - это видео)
            input_idx = valid_count + 1
            filter_script += f"[{input_idx}:a]adelay={start_ms}|{start_ms}[a{valid_count}];"
            valid_count += 1
        except: continue
    
    if valid_count == 0: return None
    
    labels = "".join([f"[a{i}]" for i in range(valid_count)])
    # Смешиваем все в один поток
    cmd = f"ffmpeg -y {' '.join(inputs)} -filter_complex \"{filter_script}{labels}amix=inputs={valid_count}:duration=first\" voice_final.mp3"
    subprocess.run(cmd, shell=True, check=True)
    return "voice_final.mp3"

def process_video_master(video_url, is_yt):
    f_in, f_out = "input.mp4", "output.mp4"
    try:
        # ЗАГРУЗКА
        ydl_opts = {'format': 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]', 'outtmpl': f_in, 'quiet': True}
        if is_yt:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=True)
                dur = info.get('duration', 0)
        else:
            r = requests.get(video_url, timeout=120); open(f_in, "wb").write(r.content)
            dur = float(subprocess.check_output(f"ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 {f_in}", shell=True))

        # ТРАНСКРИБАЦИЯ
        res = model.transcribe(f_in); segments = res.get('segments', [])
        
        # ОЗВУЧКА
        if segments and dur <= VOICE_LIMIT:
            print(f"🎙 Синтез голоса ({int(dur)} сек)...")
            voice_file = asyncio.run(build_voice_final(segments))
            if voice_file:
                # Накладываем Светлану на оригинал
                subprocess.run(f"ffmpeg -y -i {f_in} -i {voice_file} -filter_complex \"[0:a]volume=0.2[bg];[bg][1:a]amix=inputs=2:duration=first\" -c:v copy -c:a aac -b:a 128k {f_out}", shell=True, check=True)
                return f_out, "voice"
        
        return f_in, "original"
    except Exception as e:
        print(f"⚠️ Сбой обработки видео: {e}"); return None, None

# ============================================================
# 🛰 СКАНЕР ИСТОЧНИКОВ
# ============================================================

def main():
    print("🎬 [ЦУП] v7.9 'Космический Щит' запущен...")
    db = open(DB_FILE, 'r').read() if os.path.exists(DB_FILE) else ""
    
    # Перемешиваем для честного мирового поиска
    pool = SOURCES.copy()
    random.shuffle(pool)

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}

    for s in pool:
        try:
            print(f"📡 Поиск в секторе: {s['n']}...")
            video = None
            if s['t'] == 'rss':
                res = requests.get(s['u'], headers=headers, timeout=20)
                # Проверка: если пришёл не XML, а HTML-ошибка — пропускаем
                if '<?xml' not in res.text[:100]: continue
                
                root = ET.fromstring(res.content)
                items = root.findall('.//item') or root.findall('{http://www.w3.org/2005/Atom}entry')
                for item in items[:5]:
                    link = item.find('.//enclosure').get('url') if item.find('.//enclosure') is not None else item.find('link').text
                    if link and link not in db:
                        video = {'url': link, 'title': clean_text(item.find('title').text), 'is_yt': 'youtube' in link, 'source': s['n'], 'desc': item.find('description').text or ''}
                        break
            elif s['t'] == 'yt':
                res = requests.get(f"https://www.youtube.com/feeds/videos.xml?channel_id={s['id']}", headers=headers, timeout=20)
                if '<?xml' not in res.text[:100]: continue
                
                entries = ET.fromstring(res.content).findall('{http://www.w3.org/2005/Atom}entry')
                for entry in entries[:3]:
                    link = f"https://www.youtube.com/watch?v={entry.find('{http://www.youtube.com/xml/schemas/2009}videoId').text}"
                    if link not in db:
                        video = {'url': link, 'title': clean_text(entry.find('title').text), 'is_yt': True, 'source': s['n'], 'desc': ''}
                        break

            if video:
                path, mode = process_video_master(video['url'], video['is_yt'])
                if not path: continue

                # ПЕРЕВОД И ОФОРМЛЕНИЕ
                t_ru = clean_text(translator.translate(video['title']).upper())
                raw_desc = clean_text(video['desc'][:400])
                d_ru = clean_text(translator.translate(raw_desc)) if raw_desc else "Новые кадры из глубин Вселенной."
                if len(d_ru) > 180: d_ru = d_ru[:180] + "..."

                caption = (
                    f"🎬 <b>{t_ru}</b>\n"
                    f"─────────────────────\n"
                    f"🪐 <b>ИСТОЧНИК:</b> {s['n']}\n"
                    f"🔊 <b>ЗВУК:</b> {('Русский голос' if mode=='voice' else 'Оригинал')}\n"
                    f"─────────────────────\n"
                    f"📖 {d_ru}\n\n"
                    f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
                )

                with open(path, 'rb') as v:
                    r = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo", 
                                      files={"video": v}, data={"chat_id": CHANNEL_NAME, "caption": caption, "parse_mode": "HTML", "supports_streaming": True})
                    if r.status_code == 200:
                        open(DB_FILE, 'a').write(f"\n{video['url']}")
                        print("🎉 Выпуск опубликован!")
                        return
        except Exception as e:
            print(f"⚠️ Ошибка источника {s['n']}: {e}")
            continue

if __name__ == '__main__': main()
