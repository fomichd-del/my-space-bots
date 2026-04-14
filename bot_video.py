import requests
import os
import random
import time
import xml.etree.ElementTree as ET
import urllib.parse
import io
import subprocess # Для работы с ffmpeg
from datetime import datetime
from deep_translator import GoogleTranslator
from PIL import Image, ImageDraw, ImageFont

# ============================================================
# ⚙️ НАСТРОЙКИ
# ============================================================
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
NASA_API_KEY   = os.getenv('NASA_API_KEY') or "DEMO_KEY"
CHANNEL_NAME   = '@vladislav_space'
DB_FILE        = "last_video_date.txt"

translator = GoogleTranslator(source='auto', target='ru')

# ============================================================
# 📝 МОДУЛЬ СУБТИТРОВ (.srt)
# ============================================================

def create_srt(text):
    """Создает файл субтитров, который висит на экране"""
    # Разбиваем текст на короткие строки
    lines = [text[i:i+40] for i in range(0, len(text), 40)]
    full_text = "\n".join(lines[:4]) # Берем первые 4 строки для экрана
    
    # Формат SRT: номер, время начала --> конца, текст
    srt_content = (
        "1\n"
        "00:00:01,000 --> 00:00:30,000\n" # Показываем первые 30 секунд
        f"{full_text}\n"
    )
    with open("subs.srt", "w", encoding="utf-8") as f:
        f.write(srt_content)
    return "subs.srt"

# ============================================================
# 🛰️ ПОИСК И ОБРАБОТКА ВИДЕО
# ============================================================

def get_nasa_library():
    # ... (код поиска NASA Library из версии 4.6 остается таким же) ...
    # Ищем видео, получаем видео_url и img_url
    # (для краткости опустим, берем из 4.6)
    pass 

# ВНИМАНИЕ: Здесь я показываю саму логику «впекания» субтитров

def process_video_with_subs(video_url, translated_text):
    """Качает видео и добавляет в него субтитры через ffmpeg"""
    try:
        print("📥 Скачиваю видео для обработки...")
        res = requests.get(video_url, stream=True)
        with open("input.mp4", "wb") as f:
            for chunk in res.iter_content(chunk_size=8192):
                f.write(chunk)
        
        # Создаем файл субтитров
        create_srt(translated_text)
        
        print("🎞 Вшиваю субтитры...")
        # Команда ffmpeg: берем видео и сабы, упаковываем в один файл
        cmd = [
            'ffmpeg', '-y', '-i', 'input.mp4', '-i', 'subs.srt',
            '-c', 'copy', '-c:s', 'mov_text', 'output.mp4'
        ]
        subprocess.run(cmd, check=True)
        return "output.mp4"
    except Exception as e:
        print(f"❌ Ошибка обработки видео: {e}")
        return "input.mp4" # Если не вышло, шлем оригинал

# ============================================================
# 🎬 ГЛАВНАЯ ЛОГИКА (v4.7)
# ============================================================

def send():
    # ... (логика выбора видео) ...
    # Допустим, мы нашли видео и перевели текст: t_ru, d_ru
    
    # Обрабатываем видео (добавляем сабы)
    video_path = process_video_with_subs(video['url'], d_ru)
    
    # Рисуем афишу (как в 4.6)
    poster_file = create_poster(video['img'], video['source'])
    
    with open(video_path, 'rb') as v_file:
        files = {"video": v_file}
        if poster_file:
            files["thumbnail"] = ("thumb.jpg", poster_file, "image/jpeg")
            
        payload = {
            "chat_id": CHANNEL_NAME,
            "caption": f"🎬 <b>{t_ru.upper()}</b>\n\n{d_ru}\n\n🚀 @vladislav_space",
            "parse_mode": "HTML",
            "supports_streaming": True
        }
        
        r = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo", files=files, data=payload)
        # ... (сохранение в базу и лог) ...

