import os
import random
import time
import subprocess
import whisper
import yt_dlp
import asyncio
import html
import re
import requests
import xml.etree.ElementTree as ET
from deep_translator import GoogleTranslator

# ============================================================
# ⚙️ КОНФИГУРАЦИЯ v110.0
# ============================================================
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
NASA_API_KEY   = os.getenv('NASA_API_KEY')
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
CHANNEL_NAME   = '@vladislav_space'
DB_FILE        = "last_video_date.txt"

translator = GoogleTranslator(source='auto', target='ru')
try:
    model = whisper.load_model("tiny")
except:
    model = None

# ============================================================
# 🛠 СИСТЕМЫ ОБРАБОТКИ ТЕКСТА
# ============================================================

def safe_translate(text):
    if not text or len(str(text)) < 5: return str(text) if text else ""
    try: return translator.translate(str(text))
    except: return str(text)

def super_clean(text):
    if not text: return ""
    text = re.sub(r'http\S+', '', str(text))
    text = re.sub(r'<[^>]+>', '', text)
    return html.escape(html.unescape(text)).strip()

# ============================================================
# 🎬 ЛАБОРАТОРИЯ МОНТАЖА И СЖАТИЯ (v110.0)
# ============================================================

async def process_video_ultra(video_url):
    video_url = video_url.strip().replace(" ", "%20")
    print(f"🎬 [ЦУП] Захват цели: {video_url}")
    
    f_in, f_out, f_final = "input.mp4", "output.mp4", "final_compressed.mp4"
    for f in [f_in, f_out, f_final, "subs.srt"]:
        if os.path.exists(f): os.remove(f)

    try:
        ydl_opts = {'format': 'best[height<=720]', 'outtmpl': f_in, 'quiet': True, 'noplaylist': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
        
        if not os.path.exists(f_in): return None, "error"

        # 🎙 ГЕНЕРАЦИЯ СУБТИТРОВ
        srt_data = ""
        if model:
            res = model.transcribe(f_in)
            for i, seg in enumerate(res.get('segments', [])):
                s = time.strftime('%H:%M:%S,000', time.gmtime(seg.get('start', 0)))
                e = time.strftime('%H:%M:%S,000', time.gmtime(seg.get('end', 0)))
                txt = safe_translate(seg.get('text', ''))
                if txt: srt_data += f"{i+1}\n{s} --> {e}\n{txt}\n\n"
        
        if srt_data:
            with open("subs.srt", "w", encoding="utf-8") as fs: fs.write(srt_data)
            # 🎞 СЖАТИЕ ДО 49 МБ + СУБТИТРЫ (Двухпроходное кодирование)
            # Мы ставим битрейт около 1.5M, чтобы точно влезть в 50 МБ
            cmd = [
                "ffmpeg", "-y", "-i", f_in, 
                "-vf", "subtitles=subs.srt:force_style='FontSize=16,PrimaryColour=&HFFFFFF,OutlineColour=&H000000,BorderStyle=1'",
                "-vcodec", "libx264", "-crf", "28", "-maxrate", "2M", "-bufsize", "4M", 
                "-preset", "ultrafast", "-c:a", "aac", "-b:a", "128k", f_final
            ]
            subprocess.run(cmd, capture_output=True)
            return f_final, "subs"
        
        return f_in, "original"
    except Exception as e:
        print(f"⚠️ Сбой монтажа: {e}")
        return None, "error"

# ============================================================
# 🛰 ГЛОБАЛЬНЫЙ СКАНЕР (v110.0 - 2026 ГОД)
# ============================================================

async def main():
    print("🚀 [ЦУП] v110.0 'Titan Cluster' активирована...")
    if not os.path.exists(DB_FILE): open(DB_FILE, 'w').close()
    db = open(DB_FILE, 'r').read()

    START_2026 = "2026-01-01T00:00:00Z"

    SOURCES = [
        {'n': 'Роскосмос 🇷🇺', 'id': 'UCOm4M6L_L7xOovvS_I-k__A', 't': 'yt'},
        {'n': 'SpaceX 🇺🇸', 'id': 'UC_MhefFv_XW3c66m7ZAnxHA', 't': 'yt'},
        {'n': 'NASA TV 🛰️', 'id': 'UCOpNcN46zbL++h_Z270F9iQ', 't': 'yt'},
        {'n': 'ISRO 🇮🇳', 'id': 'UC_3S8_D0yV9M2E7c4p5zUQA', 't': 'yt'},
        {'n': 'ESA 🇪🇺', 'u': 'https://www.esa.int/rssfeed/Videos', 't': 'rss'},
        {'n': 'ESO 🔭', 'u': 'https://www.eso.org/public/videos/feed/', 't': 'rss'}
    ]

    random.shuffle(SOURCES)

    for s in SOURCES:
        try:
            print(f"📡 Сканирование (2026+): {s['n']}...")
            v_list = []

            if s['t'] == 'yt' and YOUTUBE_API_KEY:
                # Фильтр на дату публикации после 01.01.2026
                url = f"https://www.googleapis.com/youtube/v3/search?key={YOUTUBE_API_KEY}&channelId={s['id']}&part=snippet,id&order=date&maxResults=5&type=video&publishedAfter={START_2026}"
                r = requests.get(url).json()
                for item in r.get('items', []):
                    v_id = item['id']['videoId']
                    if v_id not in db:
                        v_list.append({'url': f"https://www.youtube.com/watch?v={v_id}", 'title': item['snippet']['title'], 'desc': item['snippet']['description'], 'id': v_id})

            elif s['t'] == 'rss':
                res = requests.get(s['u'], timeout=20)
                root = ET.fromstring(res.content)
                for item in root.findall('.//item')[:5]:
                    link = item.find('link').text
                    if link not in db:
                        v_url = link
                        encl = item.find('enclosure')
                        if encl is not None: v_url = encl.get('url')
                        v_list.append({'url': v_url, 'title': item.find('title').text, 'desc': item.find('description').text if item.find('description') is not None else "", 'id': link})

            for v in v_list:
                path, mode = await process_video_ultra(v['url'])
                if not path: continue

                # КРАСОЧНОЕ ОФОРМЛЕНИЕ
                t_ru = super_clean(safe_translate(v['title']).upper())
                d_ru = super_clean(safe_translate(v['desc']))
                
                # Извлекаем главные факты (первые 3 предложения)
                facts = d_ru.split('.')[:3]
                facts_text = ". ".join(facts) + "."

                caption = (
                    f"✨ <b>{t_ru}</b>\n\n"
                    f"🚀 <b>МИССИЯ:</b> {s['n']}\n"
                    f"📝 <b>СТАТУС:</b> {'Русские субтитры' if mode=='subs' else 'Оригинал'}\n"
                    f"─────────────────────\n"
                    f"🛰 <b>КЛЮЧЕВЫЕ ФАКТЫ:</b>\n"
                    f"• {facts_text}\n\n"
                    f"🔭 <i>Присоединяйся к путешествию в будущее!</i>\n"
                    f"🪐 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
                )

                with open(path, 'rb') as f_v:
                    requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo", 
                                    files={"video": f_v}, 
                                    data={"chat_id": CHANNEL_NAME, "caption": caption, "parse_mode": "HTML"}, timeout=400)
                
                with open(DB_FILE, 'a') as f: f.write(f"\n{v['id']}")
                print(f"🎉 ПОБЕДА! Видео опубликовано."); return
        except Exception as e:
            print(f"⚠️ Ошибка: {e}")
            continue

if __name__ == '__main__':
    asyncio.run(main())
