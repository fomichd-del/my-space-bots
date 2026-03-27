import requests
import os
from datetime import datetime

# Секреты
NASA_API_KEY = os.getenv('NASA_API_KEY')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHANNEL_NAME = '@vladislav_space'

# Ссылка на красивую заставку с астероидом
COVER_IMAGE_URL = "https://images-assets.nasa.gov/image/PIA00271/PIA00271~medium.jpg"

def get_emoji(diameter):
    """Выбираем иконку в зависимости от размера астероида 📏"""
    if diameter < 50:
        return "🪨" # Совсем маленький
    elif diameter < 150:
        return "🌑" # Средний
    elif diameter < 300:
        return "☄️" # Большой
    else:
        return "🪐" # Гигант

def get_asteroids():
    today = datetime.now().strftime('%Y-%m-%d')
    url = f"https://api.nasa.gov/neo/rest/v1/feed?start_date={today}&end_date={today}&api_key={NASA_API_KEY}"
    
    response = requests.get(url).json()
    asteroids = response['near_earth_objects'][today]
    
    # Сортируем по близости к Земле
    asteroids.sort(key=lambda x: float(x['close_approach_data'][0]['miss_distance']['kilometers']))
    
    report = f"☄️ <b>Астероидный патруль на {today}</b>\n\n"
    
    for n, ast in enumerate(asteroids[:3], 1):
        name = ast['name']
        dist = int(float(ast['close_approach_data'][0]['miss_distance']['kilometers']))
        diam = int(ast['estimated_diameter']['meters']['estimated_diameter_max'])
        danger = "⚠️ Опасен!" if ast['is_potentially_hazardous_asteroid'] else "✅ Безопасен"
        
        icon = get_emoji(diam) # Получаем наш «визуальный» размер
        
        report += f"{n}. {icon} <b>{name}</b>\n"
        report += f"   📏 Диаметр: ~{diam} м\n"
        report += f"   🛣️ Дистанция: {dist:,} км\n"
        report += f"   🛡️ Статус: {danger}\n\n"
    
    return report

def send_to_tg():
    text = get_asteroids()
    # Используем sendPhoto вместо sendMessage 📸
    api_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    payload = {
        'chat_id': CHANNEL_NAME,
        'photo': COVER_IMAGE_URL,
        'caption': text, # Весь наш текст теперь идет как подпись к фото
        'parse_mode': 'HTML'
    }
    requests.post(api_url, data=payload)

if __name__ == "__main__":
    send_to_tg()
