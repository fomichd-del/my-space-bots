import requests
import os
import random
import time
import xml.etree.ElementTree as ET
import urllib.parse
import io
from datetime import datetime
from deep_translator import GoogleTranslator
# Библиотеки Pillow для рисования афиш
from PIL import Image, ImageDraw, ImageFont

# ============================================================
# ⚙️ НАСТРОЙКИ
# ============================================================
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
NASA_API_KEY   = os.getenv('NASA_API_KEY') or "DEMO_KEY"
CHANNEL_NAME   = '@vladislav_space'
DB_FILE        = "last_video_date.txt"

translator = GoogleTranslator(source='auto', target='ru')

# ВСЕ МИРОВЫЕ КАНАЛЫ (YouTube RSS) - используем как запасной вариант
GLOBAL_CHANNELS = {
    'Роскосмос': 'UCp7fGZ8Z9zX_lZpY_l475_g',
    'SpaceX': 'UC_h_S6G_9A440VUM_KOn6Zg',
    'ISRO (Индия)': 'UC16vrn4PmwzOm_8atGYU8YQ',
    'JAXA (Япония)': 'UC1S_S6G_9A440VUM_KOn6Zg',
    'ESA (Европа)': 'UC8u9uH_V83_Fns70cyJK_Iw',
    'NASA Video': 'UCOpNcN46zbB0AgvW4t6OMvA'
}

SEARCH_KEYWORDS = ['Mars', 'ISS', 'Artemis', 'Galaxy', 'Rocket', 'Jupiter', 'Earth from Space']

def clean_url(url):
    """Исправляет ссылки для Telegram (http -> https + кодировка)"""
    if not url: return url
    url = url.replace("http://", "https://")
    parsed = list(urllib.parse.urlparse(url))
    parsed[2] = urllib.parse.quote(parsed[2])
    return urllib.parse.urlunparse(parsed)

# ============================================================
# 🖌 МОДУЛЬ АФИШ (Рисуем обложку для видео)
# ============================================================

def create_poster(img_url, provider_name):
    """Качает превью и рисует на нем заголовок 'Кинотеатр'"""
    try:
        # 1. Качаем превью в память
        res = requests.get(img_url, timeout=20)
        img = Image.open(io.BytesIO(res.content)).convert('RGB')
        
        # Оптимальный размер для ТГ обложки (до 320px по большей стороне)
        img.thumbnail((320, 320))
        width, height = img.size
        
        # 2. Создаем слой для рисования
        draw = ImageDraw.Draw(img, 'RGBA')
        
        # 3. Настраиваем шрифты (стандартные для Linux)
        try:
            font_main = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(height * 0.15))
        except:
            font_main = ImageFont.load_default()

        # 4. Пишем текст (лаконично, т.к. обложка маленькая)
        text_main = "🚀 КИНОТЕАТР"
        
        # Центрируем и пишем с обводкой
        w_main = draw.textlength(text_main, font=font_main)
        x = (width - w_main) / 2
        y = height * 0.7
        
        # Обводка
        draw.text((x-1, y-1), text_main, fill="black", font=font_main)
        draw.text((x+1, y-1), text_main, fill="black", font=font_main)
        draw.text((x-1, y+1), text_main, fill="black", font=font_main)
        draw.text((x+1, y+1), text_main, fill="black", font=font_main)
        # Основной текст
        draw.text((x, y), text_main, fill="white", font=font_main)
        
        # 5. Сохраняем готовую обложку в память (BytesIO)
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='JPEG', quality=80)
        img_byte_arr.seek(0)
        return img_byte_arr

    except Exception as e:
        print(f"⚠️ Ошибка рисования афиши: {e}")
        return None

# ============================================================
# 🛰️ МОДУЛИ ПОИСКА (Приоритет прямым MP4 файлам)
# ============================================================

def get_nasa_library():
    """Архивы NASA (прямые MP4 + ищем превью)"""
    kw = random.choice(SEARCH_KEYWORDS)
    print(f"📡 [SCANNER] Поиск NASA: {kw}...")
    try:
        url = f"https://images-api.nasa.gov/search?q={kw}&media_type=video"
        res = requests.get(url, timeout=30).json()
        items = res['collection']['items']
        
        for item in items[:15]:
            nasa_id = item['data'][0]['nasa_id']
            assets = requests.get(f"https://images-api.nasa.gov/asset/{nasa_id}", timeout=20).json()
            asset_list = [a['href'] for a in assets['collection']['items']]
            
            # Ищем видео (предпочтительно medium)
            video_url = None
            for link in asset_list:
                if '~medium.mp4' in link: video_url = link; break
            if not video_url:
                for link in asset_list:
                    if '~orig.mp4' in link or '.mp4' in link: video_url = link; break
            
            # Ищем превью
            img_url = None
            for link in asset_list:
                if '~medium.jpg' in link or '~large.jpg' in link: img_url = link; break
            
            if video_url and img_url:
                return {'url': clean_url(video_url), 'img': clean_url(img_url),
                        'title': item['data'][0]['title'], 'desc': item['data'][0].get('description', ''), 
                        'source': 'NASA Library'}
    except: return None

# ============================================================
# 🎬 ГЛАВНАЯ ЛОГИКА (Используем sendVideo + thumbnail)
# ============================================================

def send():
    print("🎬 [ЦУП] Кинотеатр v4.6 'Финальный Плеер' Запуск...")
    
    # В этой версии мы работаем ТОЛЬКО с прямыми MP4 файлами (NASA Lib), 
    # т.к. YouTube нельзя отправить через sendVideo с обложкой.
    video = get_nasa_library()
    
    sent_data = ""
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r', encoding='utf-8') as f: sent_data = f.read()

    if video and video['url'] not in sent_data:
        print(f"✅ [PROCESS] Найдено: {video['title']}. Перевожу...")
        t_ru = translator.translate(video['title'])
        d_ru = translator.translate('. '.join(video['desc'].split('.')[:3]) + '.')
        
        caption = (f"🎬 <b>КОСМИЧЕСКИЙ КИНОТЕАТР: {t_ru.upper()}</b>\n\n"
                    f"📖 <b>О ЧЕМ:</b> {d_ru}\n\n"
                    f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>")

        # 🖌 РИСУЕМ ОБЛОЖКУ
        print("🖌 Рисую уникальную обложку...")
        poster_file = create_poster(video['img'], video['source'])
        
        # ПОДГОТОВКА ФАЙЛОВ ДЛЯ ОТПРАВКИ
        files = {
            "video": (urllib.parse.unquote(os.path.basename(video['url'])), requests.get(video['url'], stream=True).raw, "video/mp4")
        }
        
        payload = {
            "chat_id": CHANNEL_NAME,
            "caption": caption,
            "parse_mode": "HTML",
            "supports_streaming": True # Позволяет смотреть видео без полной загрузки
        }

        if poster_file:
            print("🖼 Обложка готова. Отправляю видео со встроенным плеером...")
            files["thumbnail"] = ("thumb.jpg", poster_file, "image/jpeg")
        else:
            print("⚠️ Обложка не удалась. Шлем видео со стандартной обложкой...")

        # Используем sendVideo
        try:
            r = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo", files=files, data=payload, timeout=120)
            
            if r.status_code == 200:
                with open(DB_FILE, 'a', encoding='utf-8') as f: f.write(f"\n{video['url']}")
                print(f"🎉 Выпуск опубликован с нативным плеером!")
                return
            else:
                print(f"❌ Ошибка ТГ: {r.text}")
        except Exception as e:
            print(f"❌ Критическая ошибка отправки: {e}")

    else:
        print("🛑 Новых MP4 видео в NASA Library пока нет. Пропускаю.")

if __name__ == '__main__':
    send()
