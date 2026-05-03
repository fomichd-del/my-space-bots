import requests
import os
import random
from datetime import datetime
from deep_translator import GoogleTranslator

# ============================================================
# ⚙️ НАСТРОЙКИ (ЦУП: Мощность на 100%)
# ============================================================
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHANNEL_NAME   = '@vladislav_space'
NASA_API_KEY   = os.getenv('NASA_API_KEY') or "DEMO_KEY" 
HISTORY_FILE   = 'last_earth_id.txt'

translator = GoogleTranslator(source='auto', target='ru')

# Ссылка на нового бота эксперта
EXPERT_LINK = "https://t.me/Marty_Help_Bot?start=channel_post"

def is_already_sent(image_id):
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            return str(image_id) in f.read()
    return False

def save_sent_id(image_id):
    with open(HISTORY_FILE, 'a', encoding='utf-8') as f:
        f.write(f"{image_id}\n")

# ============================================================
# 🌍 ИСТОЧНИКИ: EPIC (ПОЛНЫЙ ДИСК) И LIBRARY (ДЕТАЛИ)
# ============================================================

def get_epic_data():
    """Источник 1: Весь земной шар с расстояния 1.5 млн км"""
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
        
        preview = f"https://epic.gsfc.nasa.gov/archive/natural/{p[0]}/{p[1]}/{p[2]}/jpg/{img_id}.jpg"
        original = f"https://epic.gsfc.nasa.gov/archive/natural/{p[0]}/{p[1]}/{p[2]}/png/{img_id}.png"
        
        caption = (
            f"🌍 <b>ЗЕМЛЯ: ГЛОБАЛЬНЫЙ ВИД</b>\n"
            f"─────────────────────\n\n"
            f"Прием! Этот кадр передал аппарат <b>DSCOVR</b>. Мы видим планету целиком, как хрупкий оазис в пустоте.\n\n"
            f"📍 <b>Ракурс:</b> Точка Лагранжа L1 (1.5 млн км от нас).\n"
            f"📅 <b>Дата:</b> {last_date}\n\n"
            f"📡 <b>СВЯЗЬ С БАЗОЙ:</b>\n"
            f"└ 🤖 <a href='{EXPERT_LINK}'><b>Спросить эксперта Марти о Земле</b></a>\n\n"
            f"🛰 <b>ИНСТРУМЕНТЫ ШТУРМАНА:</b>\n"
            f"├ 📥 <a href='{original}'>Скачать оригинал (Hi-Res PNG)</a>\n"
            f"├ 📹 <a href='https://www.n2yo.com/space-station/'>МКС: Прямой эфир + Карта</a>\n"
            f"└ 🌐 <a href='https://eyes.nasa.gov/apps/earth/'>Глаза Земли (3D Карта)</a>\n\n"
            f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
        )
        return preview, original, caption, img_id
    except: return None, None, None, None

def get_extensive_library_data():
    """Источник 2: Эпические виды с орбиты и МКС (Максимум разнообразия)"""
    queries = [
        "Earth night lights ISS", "Earth aurora space station", 
        "Hurricane from space", "Earth limb atmosphere",
        "Sahara desert from orbit", "Himalayas space photography",
        "Great Barrier Reef from space", "Earth sunrise space station",
        "Moon and Earth from space", "City lights at night from orbit"
    ]
    q = random.choice(queries)
    url = f"https://images-api.nasa.gov/search?q={q}&media_type=image"
    
    try:
        res = requests.get(url, timeout=25).json()
        items = res['collection']['items']
        random.shuffle(items)

        for item in items[:30]:
            nasa_id = item['data'][0]['nasa_id']
            if not is_already_sent(nasa_id):
                asset_url = item['href']
                assets = requests.get(asset_url).json()
                
                original = next((a for a in assets if "~orig" in a), assets[0])
                preview = next((a for a in assets if "~large" in a), original)
                
                title_en = item['data'][0]['title']
                desc_en = item['data'][0].get('description', '')

                title_ru = translator.translate(title_en)
                desc_ru = translator.translate('. '.join(desc_en.split('.')[:2]) + '.')
                
                caption = (
                    f"🛰 <b>ОРБИТАЛЬНЫЙ РЕПОРТАЖ: {title_ru.upper()}</b>\n"
                    f"─────────────────────\n\n"
                    f"📖 <b>О КАДРЕ:</b> {desc_ru}\n\n"
                    f"✨ <i>С этой высоты Земля кажется живым существом. Каждое фото — напоминание о том, как прекрасен наш дом.</i>\n\n"
                    f"📡 <b>СВЯЗЬ С БАЗОЙ:</b>\n"
                    f"└ 🤖 <a href='{EXPERT_LINK}'><b>Спросить эксперта Марти о кадре</b></a>\n\n"
                    f"🛰 <b>ИНСТРУМЕНТЫ ШТУРМАНА:</b>\n"
                    f"├ 📥 <a href='{original}'>Скачать оригинал (Hi-Res)</a>\n"
                    f"├ 📹 <a href='https://www.n2yo.com/space-station/'>МКС: Прямой эфир + Карта</a>\n"
                    f"└ 🌐 <a href='https://eyes.nasa.gov/apps/earth/'>Глаза Земли (3D Карта)</a>\n\n"
                    f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
                )
                return preview, original, caption, nasa_id
        return None, None, None, None
    except: return None, None, None, None

# ============================================================
# 📤 ПОСТИНГ
# ============================================================

def post_to_telegram():
    mode = random.choices(["EPIC", "LIBRARY"], weights=[30, 70])[0]
    print(f"📡 Режим: {mode}")
    
    provider = get_epic_data if mode == "EPIC" else get_extensive_library_data
    preview, original, cap, img_id = provider()
    
    if not preview:
        preview, original, cap, img_id = get_extensive_library_data() if mode == "EPIC" else get_epic_data()

    if preview and img_id:
        payload = {
            'chat_id': CHANNEL_NAME, 
            'photo': preview, 
            'caption': cap, 
            'parse_mode': 'HTML'
        }
        
        try:
            r = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto", json=payload)
            if r.status_code == 200:
                save_sent_id(img_id)
                print(f"✅ Успешно опубликовано: {img_id}")
            else:
                print(f"❌ Ошибка Telegram: {r.text}")
        except Exception as e:
            print(f"❌ Ошибка сети: {e}")
    else:
        print("📭 Новых кадров не найдено.")

if __name__ == '__main__':
    post_to_telegram()
