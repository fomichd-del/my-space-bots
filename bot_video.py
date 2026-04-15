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
from deep_translator import GoogleTranslator

# ============================================================
# ⚙️ КОНФИГУРАЦИЯ ЦУП
# ============================================================
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHANNEL_NAME   = '@vladislav_space'
DB_FILE        = "last_video_date.txt"

translator = GoogleTranslator(source='auto', target='ru')

# Загрузка нейросети (Tiny - баланс скорости и качества)
try:
    model = whisper.load_model("tiny")
except:
    model = None

# ============================================================
# 🛠 ВСПОМОГАТЕЛЬНЫЕ СИСТЕМЫ
# ============================================================

def safe_translate(text):
    if not text or len(str(text)) < 5: return str(text) if text else ""
    try: return translator.translate(str(text))
    except: return str(text)

def super_clean(text):
    if not text: return ""
    text = re.sub(r'http\S+', '', str(text)) # Убираем ссылки из текста
    text = re.sub(r'<[^>]+>', '', text)      # Убираем HTML
    try: text = html.unescape(text)
    except: pass
    return html.escape(text).strip()

# ============================================================
# 🎬 ЛАБОРАТОРИЯ МОНТАЖА (Субтитры + Видео)
# ============================================================

async def process_video(video_url):
    f_in, f_out = "input.mp4", "output.mp4"
    for f in [f_in, f_out, "subs.srt"]:
        if os.path.exists(f): os.remove(f)

    try:
        # v70.0 использует "умную" загрузку
        ydl_opts = {
            'format': 'best[height<=720][ext=mp4]', 
            'outtmpl': f_in, 
            'quiet': True, 
            'noplaylist': True,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
        
        if not os.path.exists(f_in) or os.path.getsize(f_in) < 20000: return None, "error"

        if model:
            print("🎙 Whisper: Генерирую субтитры...")
            res = model.transcribe(f_in)
            segments = res.get('segments', [])
            if segments:
                srt_data = ""
                for i, seg in enumerate(segments):
                    s = time.strftime('%H:%M:%S,000', time.gmtime(seg.get('start', 0)))
                    e = time.strftime('%H:%M:%S,000', time.gmtime(seg.get('end', 0)))
                    txt = safe_translate(seg.get('text', ''))
                    if txt: srt_data += f"{i+1}\n{s} --> {e}\n{txt}\n\n"
                
                if srt_data:
                    with open("subs.srt", "w", encoding="utf-8") as fs: fs.write(srt_data)
                    # Вшиваем субтитры (белый текст, черная обводка)
                    subprocess.run(["ffmpeg", "-y", "-i", f_in, "-vf", "subtitles=subs.srt:force_style='FontSize=18,OutlineColour=&H000000,BorderStyle=1'", "-c:a", "copy", f_out], capture_output=True)
                    if os.path.exists(f_out): return f_out, "subs"
        
        return f_in, "original"
    except Exception as e:
        print(f"⚠️ Ошибка в лаборатории: {e}")
        return (f_in if os.path.exists(f_in) else None), "original"

# ============================================================
# 🛰 ГЛАВНЫЙ ЦИКЛ ( v70.0 )
# ============================================================

async def main():
    print("🎬 [ЦУП] v70.0 'Final Frontier' активирована...")
    
    if not os.path.exists(DB_FILE): open(DB_FILE, 'w').close()
    db = open(DB_FILE, 'r').read()

    # Список каналов YouTube (самый надежный источник сейчас)
    CHANNELS = [
        {'n': 'SpaceX', 'url': 'https://www.youtube.com/@SpaceX/videos'},
        {'n': 'NASA', 'url': 'https://www.youtube.com/@NASA/videos'},
        {'n': 'JPL', 'url': 'https://www.youtube.com/@nasajpl/videos'},
        {'n': 'VideoFromSpace', 'url': 'https://www.youtube.com/@VideoFromSpace/videos'},
        {'n': 'ESA', 'url': 'https://www.youtube.com/@EuropeanSpaceAgency/videos'}
    ]

    random.shuffle(CHANNELS)

    for ch in CHANNELS:
        try:
            print(f"📡 Сканирую канал: {ch['n']}...")
            
            # v70.0 использует yt-dlp для получения списка видео (минуя XML)
            ydl_opts_list = {
                'extract_flat': True, 
                'quiet': True, 
                'playlist_items': '1,2,3', # Берем только 3 последних видео
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'
            }
            
            with yt_dlp.YoutubeDL(ydl_opts_list) as ydl:
                result = ydl.extract_info(ch['url'], download=False)
                if 'entries' not in result: continue
                
                for entry in result['entries']:
                    v_url = entry.get('url') or f"https://www.youtube.com/watch?v={entry.get('id')}"
                    v_id = entry.get('id')
                    
                    if not v_id or v_id in db: continue

                    print(f"🎯 Найдено видео: {entry.get('title')}")

                    # ОБРАБОТКА
                    path, mode = await process_video(v_url)
                    if not path:
                        with open(DB_FILE, 'a') as f: f.write(f"\n{v_id}")
                        continue

                    # ПЕРЕВОД И ОФОРМЛЕНИЕ
                    t_ru = super_clean(safe_translate(entry.get('title', 'Космическое событие')).upper())
                    d_ru = super_clean(safe_translate(entry.get('description', '')[:1000]))
                    status = "🎬 С русскими субтитрами" if mode == "subs" else "🔊 Оригинальный звук"

                    caption = (
                        f"⭐ <b>{t_ru}</b>\n\n"
                        f"🛰 <b>ИСТОЧНИК:</b> {ch['n']}\n"
                        f"📝 <b>СТАТУС:</b> {status}\n"
                        f"─────────────────────\n"
                        f"🪐 <b>ИНФОРМАЦИЯ:</b>\n\n"
                        f"{d_ru[:500]}...\n\n"
                        f"✨ <i>Космос становится ближе с каждым кадром!</i>\n"
                        f"🔭 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
                    )

                    # ОТПРАВКА
                    with open(path, 'rb') as f_v:
                        r = requests.post(
                            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo",
                            files={"video": f_v},
                            data={"chat_id": CHANNEL_NAME, "caption": caption, "parse_mode": "HTML"},
                            timeout=300
                        )
                    
                    if r.status_code == 200:
                        with open(DB_FILE, 'a') as f: f.write(f"\n{v_id}")
                        print("🎉 УСПЕХ! Полет нормальный."); return
                    else:
                        print(f"❌ Ошибка Telegram: {r.text}")

        except Exception as e:
            print(f"⚠️ Сбой канала {ch['n']}: {e}")
            continue

if __name__ == '__main__':
    asyncio.run(main())
