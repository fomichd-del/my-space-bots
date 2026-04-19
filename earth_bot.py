import requests
import os
import random
import json
import time
from datetime import datetime
from deep_translator import GoogleTranslator

# ============================================================
# ⚙️ НАСТРОЙКИ (ЦУП, системы готовы!)
# ============================================================
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHANNEL_NAME   = '@vladislav_space'
NASA_API_KEY   = os.getenv('NASA_API_KEY') or "DEMO_KEY" 
HISTORY_FILE   = 'last_earth_id.txt'
SAFE_LIMIT_MB  = 46  # Наш жесткий лимит

translator = GoogleTranslator(source='auto', target='ru')

# ============================================================
# 🧠 ВПОМОГАТЕЛЬНЫЕ СИСТЕМЫ
# ============================================================

def is_already_sent(image_id):
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            return str(image_id) in f.read()
    return False

def save_sent_id(image_id):
    with open(HISTORY_FILE, 'a', encoding='utf-8') as f:
        f.write(f"{image_id}\n")

def download_and_check(url, file_name):
    """Скачивает файл и проверяет его вес"""
    try:
        r = requests.get(url, stream=True, timeout=30)
        if r.status_code == 200:
            with open(file_name, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            size_mb = os.path.getsize(file_name) / (1024 * 1024)
            if size_mb <= SAFE_LIMIT_MB:
                return True, size_mb
            else:
                print(f"⚠️ Файл слишком тяжелый: {size_mb:.1f} MB")
                os.remove(file_name)
    except Exception as e:
        print(f"❌ Ошибка загрузки: {e}")
    return False, 0

# ============================================================
# 🌍 РЕЖИМЫ ПОИСКА ЗЕМЛИ
# ============================================================

def get_epic_data():
    """Режим 1: Полный диск Земли (NASA EPIC) - PNG качество"""
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
        # Берем именно PNG для максимального качества
        img_url = f"https://epic.gsfc.nasa.gov/archive/natural/{p[0]}/{p[1]}/{p[2]}/png/{img_id}.png"
        
        caption = (
            f"🌍 <b>ЗЕМЛЯ: ВИД ИЗ ТОЧКИ ЛАГРАНЖА (L1)</b>\n"
            f"─────────────────────\n"
            f"Прием! На связи глубокий космос. Этот снимок передал аппарат <b>DSCOVR</b> с дистанции 1,5 миллиона километров.\n\n"
            f"💎 <b>КАЧЕСТВО:</b> Мы скачали этот кадр в исходном PNG-формате, чтобы вы могли рассмотреть каждый облачный вихрь нашего общего дома.\n\n"
            f"📅 Дата съемки: <b>{last_date}</b>\n\n"
            f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
        )
        return img_url, caption, img_id, f"earth_{img_id}.png"
    except: return None, None, None, None

def get_extensive_library_data():
    """Режим 2: Художественные виды с орбиты (NASA Library)"""
    queries = [
        "Earth from ISS high resolution", "Blue Marble Earth", 
        "Stunning Earth sunset from space", "Night lights of Europe from space",
        "Hurricane eye from orbit", "Aurora Borealis from ISS",
        "Earth and Moon high res", "Pacific Ocean from space ISS"
    ]
    q = random.choice(queries)
    url = f"https://images-api.nasa.gov/search?q={q}&media_type=image"
    
    try:
        res = requests.get(url, timeout=25).json()
        items = res['collection']['items']
        random.shuffle(items)

        for item in items[:20]:
            nasa_id = item['data'][0]['nasa_id']
            if not is_already_sent(nasa_id):
                # NASA Library хранит разные размеры по ссылке в collection.json
                collection_url = item['href']
                sizes = requests.get(collection_url).json()
                # Ищем самый большой файл (обычно заканчивается на ~orig.jpg или ~orig.png)
                img_url = next((s for s in sizes if "~orig" in s), sizes[0])
                
                title_en = item['data'][0]['title']
                desc_en = item['data'][0].get('description', 'Потрясающий вид на планету.')

                title_ru = translator.translate(title_en)
                desc_ru = translator.translate('. '.join(desc_en.split('.')[:3]) + '.')
                
                caption = (
                    f"🛰 <b>ОРБИТАЛЬНЫЙ ЭКСКЛЮЗИВ: {title_ru.upper()}</b>\n"
                    f"─────────────────────\n\n"
                    f"📖 <b>О КМДРЕ:</b> {desc_ru}\n\n"
                    f"✨ <i>Вглядитесь в эту глубину! С орбиты МКС границы исчезают, и остается только яркая, живая планета в черном океане звезд.</i>\n\n"
                    f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
                )
                ext = img_url.split('.')[-1].split('?')[0]
                return img_url, caption, nasa_id, f"orbit_{nasa_id}.{ext}"
        return None, None, None, None
    except: return None, None, None, None

# ============================================================
# 📤 ЦИКЛ ОТПРАВКИ
# ============================================================

def post_to_telegram():
    mode = random.choice(["EPIC", "LIBRARY"])
    print(f"🛰 Инициализация режима: {mode}")
    
    data_provider = get_epic_data if mode == "EPIC" else get_extensive_library_data
    url, cap, img_id, local_file = data_provider()
    
    if not url: # План Б
        url, cap, img_id, local_file = get_extensive_library_data() if mode == "EPIC" else get_epic_data()

    if url and img_id:
        print(f"📥 Загрузка оригинала: {url}")
        success, size = download_and_check(url, local_file)
        
        if success:
            keyboard = {
                "inline_keyboard": [
                    [{"text": "🛰 МКС: ПРЯМОЙ ЭФИР", "url": "https://www.n2yo.com/space-station/"}],
                    [{"text": "🌍 ГЛАЗА ЗЕМЛИ (3D КАРТА)", "url": "https://eyes.nasa.gov/apps/earth/"}]
                ]
            }

            # Отправляем именно как ДОКУМЕНТ, чтобы сохранить разрешение
            with open(local_file, 'rb') as doc:
                files = {'document': doc}
                payload = {
                    'chat_id': CHANNEL_NAME,
                    'caption': cap,
                    'parse_mode': 'HTML',
                    'reply_markup': json.dumps(keyboard)
                }
                
                r = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendDocument", data=payload, files=files)
            
            if r.status_code == 200:
                save_sent_id(img_id)
                print(f"✅ Миссия выполнена! Файл {size:.1f}MB отправлен.")
            else:
                print(f"❌ Телеграм отклонил запрос: {r.text}")
            
            if os.path.exists(local_file): os.remove(local_file)
        else:
            print("🚫 Не удалось подготовить файл нужного качества.")
    else:
        print("📭 На сегодня новых снимков Земли в архивах нет.")

if __name__ == '__main__':
    print("🚀 [ЦУП] Инженер поддержки на связи. Развертывание системы Earth-HiRes...")
    post_to_telegram()
