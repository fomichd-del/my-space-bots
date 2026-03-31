import requests
import os
import json
from datetime import datetime

# ============================================================
# ⚙️ НАСТРОЙКИ
# ============================================================
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
# Используем два ключа: секретный из GitHub или DEMO_KEY как запасной
NASA_API_KEY   = os.getenv('NASA_API_KEY', 'DEMO_KEY')
CHANNEL_NAME   = '@vladislav_space'

def get_earth_data():
    """Получает самые свежие снимки Земли и метаданные к ним."""
    # 1. Узнаем, за какую последнюю дату есть снимки
    avail_url = f"https://api.nasa.gov/epic/api/natural/available?api_key={NASA_API_KEY}"
    
    try:
        dates_resp = requests.get(avail_url, timeout=15)
        if dates_resp.status_code != 200: return None
        
        last_date = dates_resp.json()[-1] # Берем самую свежую дату
        
        # 2. Получаем список снимков за эту дату
        data_url = f"https://api.nasa.gov/epic/api/natural/date/{last_date}?api_key={NASA_API_KEY}"
        shots = requests.get(data_url, timeout=15).json()
        latest_shot = shots[-1] # Берем последний кадр дня
        
        # Собираем данные для "3 фактов"
        file_name = latest_shot['image']
        coords = latest_shot['centroid_coordinates']
        # Расстояние от спутника до Земли (в км)
        dist = int(latest_shot['dscovr_j2000_position']['z'] / 1) # Примерный расчет
        
        # Формируем ссылку на PNG-файл
        p = last_date.split("-")
        image_url = f"https://epic.gsfc.nasa.gov/archive/natural/{p[0]}/{p[1]}/{p[2]}/png/{file_name}.png"
        
        # 📋 ФОРМИРУЕМ 3 ФАКТА
        fact_1 = f"📍 Центр снимка: <b>{round(coords['lat'], 2)}°, {round(coords['lon'], 2)}°</b>"
        fact_2 = f"📏 Дистанция до Земли: <b>~1,5 млн км</b>"
        fact_3 = f"⏰ Время съемки: <b>{latest_shot['date']}</b>"

        caption = (
            f"🌍 <b>ПЛАНЕТА ЗЕМЛЯ ИЗ КОСМОСА</b>\n"
            f"─────────────────────\n\n"
            f"🔹 {fact_1}\n\n"
            f"🔹 {fact_2}\n\n"
            f"🔹 {fact_3}\n\n"
            f"<i>Снимок сделан камерой EPIC со спутника DSCOVR, находящегося в точке Лагранжа L1.</i>\n\n"
            f"⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
            f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
        )
        return image_url, caption
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return None, None

def send_photo(photo_url, caption):
    """Отправляет готовый пост в Телеграм."""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    payload = {
        'chat_id': CHANNEL_NAME, 
        'photo': photo_url, 
        'caption': caption, 
        'parse_mode': 'HTML'
    }
    r = requests.post(url, data=payload)
    print(f"📡 Статус отправки: {r.status_code}")

if __name__ == '__main__':
    print("--- 🏁 Запуск Earth Bot ---")
    url, text = get_earth_data()
    if url: 
        send_photo(url, text)
    else:
        print("📭 Данные не получены.")
