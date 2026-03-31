import requests
import os

# ============================================================
# ⚙️ НАСТРОЙКИ И ПРОВЕРКА КЛЮЧА
# ============================================================
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHANNEL_NAME   = '@vladislav_space'

# Получаем ключ из секретов GitHub
raw_key = os.getenv('NASA_API_KEY')

# Проверяем: если ключ пустой, None или содержит технические символы GitHub
if not raw_key or raw_key.strip() == "" or raw_key.startswith('$'):
    print("ℹ️ Личный ключ NASA не найден. Используем запасной: DEMO_KEY")
    NASA_API_KEY = 'DEMO_KEY'
else:
    print("✅ Используем личный ключ NASA.")
    NASA_API_KEY = raw_key

def get_earth_data():
    """Получает данные о свежих снимках Земли и метаданные."""
    # 1. Узнаем доступные даты
    avail_url = f"https://api.nasa.gov/epic/api/natural/available?api_key={NASA_API_KEY}"
    
    try:
        print(f"📡 Запрос к API EPIC...")
        resp = requests.get(avail_url, timeout=15)
        
        if resp.status_code != 200:
            print(f"❌ Ошибка API: {resp.status_code}")
            return None, None  # Возвращаем пару, чтобы не было ошибки распаковки
            
        dates = resp.json()
        if not dates:
            return None, None
            
        last_date = dates[-1] # Самая свежая дата
        print(f"📅 Найдена дата: {last_date}")
        
        # 2. Получаем список снимков за эту дату
        data_url = f"https://api.nasa.gov/epic/api/natural/date/{last_date}?api_key={NASA_API_KEY}"
        shots = requests.get(data_url, timeout=15).json()
        
        if not shots:
            return None, None
            
        # Берем последний кадр дня
        latest_shot = shots[-1]
        file_name = latest_shot['image']
        coords = latest_shot['centroid_coordinates']
        
        # Собираем ссылку на качественный PNG
        p = last_date.split("-")
        image_url = f"https://epic.gsfc.nasa.gov/archive/natural/{p[0]}/{p[1]}/{p[2]}/png/{file_name}.png"
        
        # Формируем текст (стиль 3 факта)
        caption = (
            f"🌍 <b>ПЛАНЕТА ЗЕМЛЯ ИЗ КОСМОСА</b>\n"
            f"─────────────────────\n\n"
            f"📍 Координаты центра: <b>{round(coords['lat'], 2)}°, {round(coords['lon'], 2)}°</b>\n\n"
            f"⏰ Время съемки: <b>{latest_shot['date']}</b>\n\n"
            f"🛰️ Спутник: <b>DSCOVR (камера EPIC)</b>\n\n"
            f"⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
            f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
        )
        return image_url, caption
        
    except Exception as e:
        print(f"⚠️ Произошла ошибка: {e}")
        return None, None

def send_photo(photo_url, caption):
    """Отправка в Telegram."""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    payload = {
        'chat_id': CHANNEL_NAME, 
        'photo': photo_url, 
        'caption': caption, 
        'parse_mode': 'HTML'
    }
    r = requests.post(url, data=payload)
    print(f"📡 Статус Telegram: {r.status_code}")

if __name__ == '__main__':
    print("--- 🏁 Старт Earth Bot ---")
    url, text = get_earth_data()
    
    if url and text:
        send_photo(url, text)
    else:
        print("📭 Данных за последние дни пока нет. Попробуем в следующий раз!")
    print("--- 🏁 Работа завершена ---")
