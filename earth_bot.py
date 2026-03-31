import requests
import os

# ============================================================
# ⚙️ НАСТРОЙКИ (УМНЫЙ ВЫБОР КЛЮЧА)
# ============================================================
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHANNEL_NAME   = '@vladislav_space'

# Получаем то, что лежит в секретах GitHub
raw_key = os.getenv('NASA_API_KEY')

# Проверяем ключ на "профпригодность"
if not raw_key or len(str(raw_key)) < 10 or raw_key.startswith('$'):
    # Если ключа нет, он слишком короткий или это техническая строка ${{...}}
    print("🔓 Личный ключ не найден или некорректен. Используем: DEMO_KEY")
    NASA_API_KEY = 'DEMO_KEY'
else:
    print("✅ Используем ваш личный ключ NASA из секретов.")
    NASA_API_KEY = raw_key

def get_earth_data():
    """Получает данные о свежих снимках Земли."""
    avail_url = f"https://api.nasa.gov/epic/api/natural/available?api_key={NASA_API_KEY}"
    
    try:
        print(f"📡 Запрос к API EPIC (Ключ: {NASA_API_KEY})...")
        resp = requests.get(avail_url, timeout=15)
        
        if resp.status_code != 200:
            print(f"❌ Ошибка API: {resp.status_code}. Возможно, DEMO_KEY исчерпан.")
            return None, None
            
        dates = resp.json()
        if not dates:
            return None, None
            
        last_date = dates[-1] 
        print(f"📅 Найдена свежая дата: {last_date}")
        
        data_url = f"https://api.nasa.gov/epic/api/natural/date/{last_date}?api_key={NASA_API_KEY}"
        shots = requests.get(data_url, timeout=15).json()
        
        if not shots:
            return None, None
            
        # Берем самый свежий кадр за этот день
        latest_shot = shots[-1]
        file_name = latest_shot['image']
        coords = latest_shot['centroid_coordinates']
        
        # Ссылка на качественный PNG (EPIC хранит их в папке png)
        p = last_date.split("-")
        image_url = f"https://epic.gsfc.nasa.gov/archive/natural/{p[0]}/{p[1]}/{p[2]}/png/{file_name}.png"
        
        caption = (
            f"🌍 <b>ПЛАНЕТА ЗЕМЛЯ ИЗ КОСМОСА</b>\n"
            f"─────────────────────\n\n"
            f"📍 Координаты центра: <b>{round(coords['lat'], 2)}°, {round(coords['lon'], 2)}°</b>\n\n"
            f"⏰ Время съемки: <b>{latest_shot['date']}</b>\n\n"
            f"🛰️ Камера: <b>EPIC (спутник DSCOVR)</b>\n\n"
            f"⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
            f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
        )
        return image_url, caption
        
    except Exception as e:
        print(f"⚠️ Ошибка при получении данных: {e}")
        return None, None

def send_photo(photo_url, caption):
    """Отправляет готовый пост в канал."""
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
        print("📭 Данных от NASA пока нет (они обновляются с задержкой 1-3 дня).")
    print("--- 🏁 Работа завершена ---")
