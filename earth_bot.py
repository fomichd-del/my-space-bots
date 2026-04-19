import requests
import os
import random
import json
from datetime import datetime
from deep_translator import GoogleTranslator

# ============================================================
# ⚙️ НАСТРОЙКИ (ЦУП: Системы на максимуме)
# ============================================================
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHANNEL_NAME   = '@vladislav_space'
NASA_API_KEY   = os.getenv('NASA_API_KEY') or "DEMO_KEY" 
HISTORY_FILE   = 'last_earth_id.txt'

translator = GoogleTranslator(source='auto', target='ru')

# ============================================================
# 🧠 СИСТЕМА ПАМЯТИ
# ============================================================

def is_already_sent(image_id):
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            return str(image_id) in f.read()
    return False

def save_sent_id(image_id):
    with open(HISTORY_FILE, 'a', encoding='utf-8') as f:
        f.write(f"{image_id}\n")

# ============================================================
# 🎨 ГЕНЕРАТОР "СОЧНЫХ" ЭПИТЕТОВ
# ============================================================

def get_vivid_intro():
    intros = [
        "Взгляните на это великолепие! ✨",
        "Наша планета — истинный шедевр Вселенной. 💎",
        "Невероятный кадр, от которого захватывает дух... 🌌",
        "Космический репортаж специально для наших штурманов! 🛰",
        "Тишина и величие Земли из бездны космоса. 🌏"
    ]
    return random.choice(intros)

# ============================================================
# 🌍 РЕЖИМЫ ПОИСКА
# ============================================================

def get_epic_data():
    """Режим 1: Полный диск Земли из точки L1"""
    url = f"https://api.nasa.gov/EPIC/api/natural/available?api_key={NASA_API_KEY}"
    try:
        dates = requests.get(url, timeout=20).json()
        last_date = dates[-1]
        data_url = f"https://api.nasa.gov/EPIC/api/natural/date/{last_date}?api_key={NASA_API_KEY}"
        shots = requests.get(data_url, timeout=20).json()
        
        available_shots = [s for s in shots if not is_already_sent(s['image'])]
        if not available_shots: return None, None, None, None
        
        shot = random.choice(available_shots)
        img_id = shot['image']
        p = last_date.split("-")
        
        # Ссылка для превью (JPG) и для оригинала (PNG)
        preview_url = f"https://epic.gsfc.nasa.gov/archive/natural/{p[0]}/{p[1]}/{p[2]}/jpg/{img_id}.jpg"
        original_url = f"https://epic.gsfc.nasa.gov/archive/natural/{p[0]}/{p[1]}/{p[2]}/png/{img_id}.png"
        
        caption = (
            f"🌍 <b>ЗЕМЛЯ: ВИД ИЗ ТОЧКИ ЛАГРАНЖА (L1)</b>\n"
            f"─────────────────────\n\n"
            f"{get_vivid_intro()}\n\n"
            f"Этот снимок сделал спутник <b>DSCOVR</b> с расстояния 1.5 млн км. Перед вами — вся планета целиком, "
            f"парящая в бесконечной пустоте как драгоценный сапфир.\n\n"
            f"📅 Дата: <b>{last_date}</b>\n\n"
            f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
        )
        return preview_url, original_url, caption, img_id
    except: return None, None, None, None

def get_extensive_library_data():
    """Режим 2: Самые зрелищные виды Земли (Детально)"""
    queries = [
        "Earth from space ISS 8k", "Blue Marble high resolution", 
        "Night lights of Earth city", "Atmosphere of Earth from space",
        "Hurricane from orbit", "Earth horizon sunset",
        "Australia from space", "Himalayas from space ISS"
    ]
    q = random.choice(queries)
    url = f"https://images-api.nasa.gov/search?q={q}&media_type=image"
    
    try:
        res = requests.get(url, timeout=25).json()
        items = res['collection']['items']
        random.shuffle(items)

        for item in items[:25]:
            nasa_id = item['data'][0]['nasa_id']
            if not is_already_sent(nasa_id):
                # Получаем все варианты ссылок
                asset_url = item['href']
                assets = requests.get(asset_url).json()
                
                # Оригинал и превью (ищем самое большое)
                original_url = next((a for a in assets if "~orig" in a), assets[0])
                preview_url = next((a for a in assets if "~large" in a), original_url)
                
                title_en = item['data'][0]['title']
                desc_en = item['data'][0].get('description', 'Потрясающий кадр нашей планеты.')

                title_ru = translator.translate(title_en)
                desc_ru = translator.translate('. '.join(desc_en.split('.')[:3]) + '.')
                
                caption = (
                    f"🛰 <b>ОРБИТАЛЬНЫЙ РЕПОРТАЖ: {title_ru.upper()}</b>\n"
                    f"─────────────────────\n\n"
                    f"{get_vivid_intro()}\n\n"
                    f"📖 <b>О КАДРЕ:</b> {desc_ru}\n\n"
                    f"🔭 <i>Этот снимок передает невероятную мощь и хрупкость нашего дома. Рассмотрите детали — они поражают!</i>\n\n"
                    f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
                )
                return preview_url, original_url, caption, nasa_id
        return None, None, None, None
    except: return None, None, None, None

# ============================================================
# 📤 ГЛАВНАЯ ФУНКЦИЯ (ПОСТИНГ)
# ============================================================

def post_to_telegram():
    mode = random.choice(["EPIC", "LIBRARY"])
    print(f"📡 Запуск сканирования. Режим: {mode}")
    
    provider = get_epic_data if mode == "EPIC" else get_extensive_library_data
    preview, original, cap, img_id = provider()
    
    # План Б
    if not preview:
        provider = get_extensive_library_data if mode == "EPIC" else get_epic_data
        preview, original, cap, img_id = provider()

    if preview and img_id:
        keyboard = {
            "inline_keyboard": [
                [{"text": "📥 СКАЧАТЬ В ПОЛНОМ КАЧЕСТВЕ", "url": original}],
                [{"text": "🛰 МКС: ПРЯМОЙ ЭФИР", "url": "https://www.n2yo.com/space-station/"}],
                [{"text": "🌍 ГЛАЗА ЗЕМЛИ (3D КАРТА)", "url": "https://eyes.nasa.gov/apps/earth/"}]
            ]
        }

        payload = {
            'chat_id': CHANNEL_NAME, 
            'photo': preview, 
            'caption': cap, 
            'parse_mode': 'HTML',
            'reply_markup': json.dumps(keyboard)
        }
        
        try:
            r = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto", json=payload)
            if r.status_code == 200:
                save_sent_id(img_id)
                print(f"✅ Успешно опубликовано! ID: {img_id}")
            else:
                print(f"❌ Ошибка Telegram: {r.text}")
        except Exception as e:
            print(f"❌ Системный сбой: {e}")
    else:
        print("📭 Новых кадров не обнаружено. Продолжаем мониторинг.")

if __name__ == '__main__':
    print("🚀 [ЦУП] Инженер поддержки: Инициализация модуля Earth-Vivid-HiRes...")
    post_to_telegram()
