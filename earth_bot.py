import requests
import os
import time
import json

# ============================================================
# ⚙️ НАСТРОЙКИ
# ============================================================
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
NASA_API_KEY   = os.getenv('NASA_API_KEY') or "DEMO_KEY"
CHANNEL_NAME   = '@vladislav_space'

def get_earth_data():
    """Получает свежее фото Земли с защитой от сбоев."""
    # Шаг 1: Узнаем доступные даты
    avail_url = f"https://api.nasa.gov/epic/api/natural/available?api_key={NASA_API_KEY}"
    
    for attempt in range(3):
        try:
            print(f"Попытка {attempt + 1}: Запрос доступных дат EPIC...")
            resp = requests.get(avail_url, timeout=15)
            if resp.status_code != 200:
                time.sleep(60)
                continue
            
            dates = resp.json()
            last_date = dates[-1]
            
            # Шаг 2: Получаем данные о фото за эту дату
            data_url = f"https://api.nasa.gov/epic/api/natural/date/{last_date}?api_key={NASA_API_KEY}"
            photos = requests.get(data_url).json()
            latest_shot = photos[-1]
            
            file_name = latest_shot['image']
            p = last_date.split("-") # [год, месяц, день]
            
            # Шаг 3: Собираем ссылку
            image_url = f"https://epic.gsfc.nasa.gov/archive/natural/{p[0]}/{p[1]}/{p[2]}/png/{file_name}.png"
            caption = "🌍 <b>Планета Земля сегодня</b>\n\nВид с камеры EPIC (NASA) 🛰️"
            
            return image_url, caption

        except Exception as e:
            print(f"⚠️ Ошибка: {e}")
            time.sleep(60)
    return None, None

def send_earth_photo(photo_url, caption):
    """Отправляет фото в Telegram."""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    payload = {
        'chat_id': CHANNEL_NAME,
        'photo': photo_url,
        'caption': caption,
        'parse_mode': 'HTML'
    }
    requests.post(url, data=payload)

if __name__ == '__main__':
    url, text = get_earth_data()
    if url:
        send_earth_photo(url, text)
