import requests
import os
import sys
import json
import re
import time
import random
from deep_translator import GoogleTranslator

# --- НАСТРОЙКИ ---
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
NASA_API_KEY   = os.getenv('NASA_API_KEY') or "DEMO_KEY"
CHANNEL_NAME   = '@vladislav_space'

# Файлы памяти
DB_APOD_IMG = "last_cosmo_image.txt"
DB_APOD_VID = "last_cosmo_video.txt"
DB_LIBRARY  = "last_cosmo_library.txt" # Для архивов Webb, Hubble, ESA

# Источники для архива
SOURCES = [
    {"name": "James Webb", "query": "James Webb telescope"},
    {"name": "Hubble", "query": "Hubble telescope"},
    {"name": "ESA", "query": "European Space Agency"},
    {"name": "NASA Archive", "query": "nebula galaxy"}
]

def get_short_facts(text, icons):
    """Разбивает описание на 3 интересных факта"""
    if not text: return "Детали скоро появятся! 🔭"
    # Очистка от лишних пробелов и переносов
    text = text.replace('\n', ' ').strip()
    sentences = [s.strip() for s in text.split('. ') if len(s.strip()) > 10]
    top_facts = sentences[:3]
    
    formatted_list = []
    for i, fact in enumerate(top_facts):
        clean_fact = fact.rstrip('.')
        icon = icons[i] if i < len(icons) else "✨"
        formatted_list.append(f"{icon} {clean_fact}.")
    return "\n\n".join(formatted_list)

def clean_video_url(url):
    """Превращает embed-ссылки в обычные для Telegram"""
    if 'youtube.com/embed/' in url:
        video_id = url.split('/')[-1].split('?')[0]
        return f"https://www.youtube.com/watch?v={video_id}"
    return url

def get_nasa_apod(target_type):
    """Источник №1: NASA APOD (Картина дня)"""
    url = f"https://api.nasa.gov/planetary/apod?api_key={NASA_API_KEY}"
    try:
        res = requests.get(url, timeout=15).json()
        if res.get('media_type') == target_type:
            return {
                'id': res.get('date'),
                'title': res.get('title'),
                'desc': res.get('explanation'),
                'url': res.get('url'),
                'source': 'NASA APOD'
            }
    except: pass
    return None

def get_nasa_library(target_type):
    """Источник №2-5: NASA Image Library (Webb, Hubble, ESA, Archive)"""
    source = random.choice(SOURCES)
    media_type = 'image' if target_type == 'image' else 'video'
    url = f"https://images-api.nasa.gov/search?q={source['query']}&media_type={media_type}"
    
    try:
        res = requests.get(url, timeout=15).json()
        items = res['collection']['items']
        random.shuffle(items) # Чтобы каждый раз было разное
        
        # Загружаем базу отправленных из библиотеки
        sent_ids = []
        if os.path.exists(DB_LIBRARY):
            with open(DB_LIBRARY, 'r') as f: sent_ids = f.read().splitlines()

        for item in items[:15]:
            nasa_id = item['data'][0]['nasa_id']
            if nasa_id not in sent_ids:
                # Получаем прямую ссылку на файл
                asset_url = f"https://images-api.nasa.gov/asset/{nasa_id}"
                links = requests.get(asset_url).json()['collection']['items']
                # Выбираем лучшее качество (обычно первое или второе в списке)
                file_url = links[0]['href']
                if target_type == 'video': # Для видео ищем mp4
                    file_url = next((l['href'] for l in links if l['href'].endswith('.mp4')), file_url)

                return {
                    'id': nasa_id,
                    'title': item['data'][0].get('title'),
                    'desc': item['data'][0].get('description'),
                    'url': file_url,
                    'source': source['name']
                }
    except: pass
    return None

def send_to_telegram(target_type):
    """Оркестратор отправки"""
    # 1. Пытаемся взять APOD (Картину дня)
    data = get_nasa_apod(target_type)
    db_file = DB_APOD_IMG if target_type == 'image' else DB_APOD_VID
    is_archive = False

    # Проверка APOD на повтор
    if data:
        if os.path.exists(db_file):
            with open(db_file, 'r') as f:
                if f.read().strip() == data['id']:
                    print(f"🔄 APOD за сегодня уже был. Переключаюсь на глубокий космос...")
                    data = None # Сбрасываем, чтобы пойти в архив

    # 2. Если APOD уже был или не подошел тип — идем в Библиотеку (Webb/Hubble/ESA/NASA)
    if not data:
        print(f"📡 Запуск поиска в архивах {target_type}...")
        data = get_nasa_library(target_type)
        is_archive = True
        db_file = DB_LIBRARY

    if not data:
        print("❌ Не удалось найти новый контент ни в одном источнике.")
        return

    # --- ПОДГОТОВКА ТЕКСТА ---
    try:
        translator = GoogleTranslator(source='en', target='ru')
        ru_title = translator.translate(data['title'])
        ru_desc = translator.translate(data['desc'][:1000]) # Ограничение для переводчика
        icons = ["🎬", "🎥", "🌠"] if target_type == 'video' else ["🚀", "🪐", "🔭"]
        facts = get_short_facts(ru_desc, icons)
    except:
        ru_title = data['title']
        facts = "Удивительный объект зафиксирован нашими датчиками! 🛰️"

    header = f"{'🎬 <b>ВИДЕО:</b>' if target_type == 'video' else '🌌'} <b>{ru_title.upper()}</b>\n─────────────────────\n\n"
    body = f"<b>ГЛАВНОЕ:</b>\n\n{facts}\n\n"
    footer = f"🔭 <b>Источник:</b> {data['source']}\n👉 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
    full_text = header + body + footer

    # --- ОТПРАВКА ---
    if target_type == 'image':
        payload = {'chat_id': CHANNEL_NAME, 'photo': data['url'], 'caption': full_text, 'parse_mode': 'HTML'}
        r = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto", json=payload)
    else:
        # Двухэтапная отправка для видео (Комментарии + Видео сверху)
        video_url = clean_video_url(data['url'])
        # Шаг 1: Текст
        payload_init = {'chat_id': CHANNEL_NAME, 'text': full_text, 'parse_mode': 'HTML', 'link_preview_options': {'is_disabled': True}}
        r_init = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", json=payload_init)
        
        if r_init.status_code == 200:
            msg_id = r_init.json()['result']['message_id']
            time.sleep(1)
            # Шаг 2: Редактируем (добавляем плеер сверху)
            hidden_link = f"<a href='{video_url}'>\u200b</a>"
            payload_edit = {
                'chat_id': CHANNEL_NAME, 'message_id': msg_id, 'text': hidden_link + full_text, 
                'parse_mode': 'HTML', 'link_preview_options': {'is_disabled': False, 'url': video_url, 'show_above_text': True, 'prefer_large_media': True}
            }
            r = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/editMessageText", json=payload_edit)
        else: r = r_init

    # --- СОХРАНЕНИЕ ПАМЯТИ ---
    if r.status_code == 200:
        mode = 'a' if is_archive else 'w' # В архив дописываем, в APOD перезаписываем дату
        with open(db_file, mode, encoding='utf-8') as f:
            f.write(f"{data['id']}\n")
        print(f"✅ Успешно отправлено из источника: {data['source']}")
    else:
        print(f"❌ Ошибка: {r.text}")

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else 'image'
    send_to_telegram(mode)
