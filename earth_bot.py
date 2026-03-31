import requests
import os

# ============================================================
# ⚙️ НАСТРОЙКИ
# ============================================================
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
NASA_API_KEY   = os.getenv('NASA_API_KEY', 'DEMO_KEY')
CHANNEL_NAME   = '@vladislav_space'

def get_earth_data():
    """Получает данные о свежих снимках Земли."""
    avail_url = f"https://api.nasa.gov/epic/api/natural/available?api_key={NASA_API_KEY}"
    
    try:
        print(f"📡 Проверка доступности данных EPIC...")
        resp = requests.get(avail_url, timeout=15)
        
        if resp.status_code != 200:
            print(f"❌ Ошибка API: Статус {resp.status_code}. Проверь NASA_API_KEY.")
            return None, None # Исправлено: возвращаем пару
            
        dates = resp.json()
        if not dates:
            print("📭 Список дат пуст.")
            return None, None
            
        last_date = dates[-1]
        print(f"✅ Найдена дата: {last_date}")
        
        data_url = f"https://api.nasa.gov/epic/api/natural/date/{last_date}?api_key={NASA_API_KEY}"
        shots = requests.get(data_url, timeout=15).json()
        
        if not shots:
            return None, None
            
        latest_shot = shots[-1]
        file_name = latest_shot['image']
        coords = latest_shot['centroid_coordinates']
        
        # Ссылка на изображение
        p = last_date.split("-")
        image_url = f"https://epic.gsfc.nasa.gov/archive/natural/{p[0]}/{p[1]}/{p[2]}/png/{file_name}.png"
        
        caption = (
            f"🌍 <b>ПЛАНЕТА ЗЕМЛЯ ИЗ КОСМОСА</b>\n"
            f"─────────────────────\n\n"
            f"📍 Координаты центра: <b>{round(coords['lat'], 2)}°, {round(coords['lon'], 2)}°</b>\n"
            f"⏰ Время съемки: <b>{latest_shot['date']}</b>\n\n"
            f"<i>Снимок сделан камерой EPIC с расстояния 1.5 млн км!</i>\n\n"
            f"⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
            f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
        )
        return image_url, caption
        
    except Exception as e:
        print(f"⚠️ Произошла ошибка: {e}")
        return None, None

def send_photo(photo_url, caption):
    """Отправляет пост в Telegram."""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    payload = {'chat_id': CHANNEL_NAME, 'photo': photo_url, 'caption': caption, 'parse_mode': 'HTML'}
    r = requests.post(url, data=payload)
    print(f"📡 Статус Telegram: {r.status_code}")

if __name__ == '__main__':
    print("--- 🏁 Запуск Earth Bot ---")
    url, text = get_earth_data()
    if url and text:
        send_photo(url, text)
    else:
        print("📭 Сегодня данных от EPIC пока нет. Попробуем позже!")
