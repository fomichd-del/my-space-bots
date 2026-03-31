import requests
import os

# ============================================================
# ⚙️ НАСТРОЙКИ (МАКСИМАЛЬНАЯ НАДЕЖНОСТЬ)
# ============================================================
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHANNEL_NAME   = '@vladislav_space'

# Принудительно используем DEMO_KEY, чтобы исключить влияние "призрачного" ключа
NASA_API_KEY = "DEMO_KEY" 

def get_earth_data():
    """Получает данные о свежих снимках Земли."""
    # План А: Через официальный шлюз NASA (исправлен регистр на EPIC)
    avail_url = f"https://api.nasa.gov/EPIC/api/natural/available?api_key={NASA_API_KEY}"
    # План Б: Напрямую с сервера проекта (если шлюз барахлит)
    backup_url = "https://epic.gsfc.nasa.gov/api/natural/available"
    
    try:
        print(f"📡 Запрос к API EPIC (Режим: {NASA_API_KEY})...")
        resp = requests.get(avail_url, timeout=15)
        
        # Если План А выдал 404, пробуем План Б
        if resp.status_code != 200:
            print(f"🔄 План А не сработал ({resp.status_code}). Пробуем План Б...")
            resp = requests.get(backup_url, timeout=15)
            
        if resp.status_code != 200:
            print(f"❌ Ошибка API: {resp.status_code}")
            return None, None
            
        dates = resp.json()
        if not dates:
            return None, None
            
        last_date = dates[-1] 
        print(f"📅 Найдена свежая дата: {last_date}")
        
        # Запрашиваем метаданные за эту дату (используем заглавные EPIC)
        data_url = f"https://api.nasa.gov/EPIC/api/natural/date/{last_date}?api_key={NASA_API_KEY}"
        shots_resp = requests.get(data_url, timeout=15)
        
        if shots_resp.status_code != 200:
            # Резервный запрос метаданных
            data_url = f"https://epic.gsfc.nasa.gov/api/natural/date/{last_date}"
            shots_resp = requests.get(data_url, timeout=15)

        shots = shots_resp.json()
        if not shots: return None, None
            
        latest_shot = shots[-1]
        file_name = latest_shot['image']
        coords = latest_shot['centroid_coordinates']
        
        # Ссылка на изображение (папка png)
        p = last_date.split("-")
        image_url = f"https://epic.gsfc.nasa.gov/archive/natural/{p[0]}/{p[1]}/{p[2]}/png/{file_name}.png"
        
        caption = (
            f"🌍 <b>ПЛАНЕТА ЗЕМЛЯ ИЗ КОСМОСА</b>\n"
            f"─────────────────────\n\n"
            f"📍 Координаты центра: <b>{round(coords['lat'], 2)}°, {round(coords['lon'], 2)}°</b>\n"
            f"⏰ Время съемки: <b>{latest_shot['date']}</b>\n\n"
            f"🛰️ Камера: <b>EPIC (спутник DSCOVR)</b>\n\n"
            f"⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
            f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
        )
        return image_url, caption
        
    except Exception as e:
        print(f"⚠️ Ошибка: {e}")
        return None, None

def send_photo(photo_url, caption):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    payload = {'chat_id': CHANNEL_NAME, 'photo': photo_url, 'caption': caption, 'parse_mode': 'HTML'}
    r = requests.post(url, data=payload)
    print(f"📡 Статус Telegram: {r.status_code}")

if __name__ == '__main__':
    print("--- 🏁 Старт Earth Bot ---")
    url, text = get_earth_data()
    if url and text:
        send_photo(url, text)
    else:
        print("📭 Данных пока нет. EPIC обновляется с задержкой.")
