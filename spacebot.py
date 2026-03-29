import requests
import os
from datetime import datetime

# Секреты
NASA_API_KEY = os.getenv('NASA_API_KEY')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHANNEL_NAME = '@vladislav_space'

# Ссылка на заставку
COVER_IMAGE_URL = "https://images-assets.nasa.gov/image/PIA00271/PIA00271~medium.jpg"

def get_emoji(diameter):
    """Выбираем иконку по размеру астероида"""
    if diameter < 50: return "🪨"
    elif diameter < 150: return "🌑"
    elif diameter < 300: return "☄️"
    else: return "🪐"

def get_asteroids():
    today = datetime.now().strftime('%Y-%m-%d')
    url = f"https://api.nasa.gov/neo/rest/v1/feed?start_date={today}&end_date={today}&api_key={NASA_API_KEY}"
    
    response = requests.get(url).json()
    asteroids = response['near_earth_objects'][today]
    asteroids.sort(key=lambda x: float(x['close_approach_data'][0]['miss_distance']['kilometers']))
    
    # --- ЛОГИКА ПРОВЕРКИ ОПАСНОСТИ ---
    danger_found = False
    for ast in asteroids:
        if ast['is_potentially_hazardous_asteroid']:
            danger_found = True
            break # Нашли хотя бы одного — дальше можно не искать
            
    if danger_found:
        report = "⚠️ <b>ВНИМАНИЕ: Потенциальная угроза!</b> ⚠️\n\n"
    else:
        report = f"☄️ <b>Астероидный патруль на {today}</b>\n\n"
    # --------------------------------
    
    for n, ast in enumerate(asteroids[:5], 1):
        name = ast['name']
        dist = int(float(ast['close_approach_data'][0]['miss_distance']['kilometers']))
        diam = int(ast['estimated_diameter']['meters']['estimated_diameter_max'])
        
        # Пометка для опасных внутри списка
        is_hazard = ast['is_potentially_hazardous_asteroid']
        danger_label = "⚠️ ОПАСЕН!" if is_hazard else "✅ Безопасен"
        
        icon = get_emoji(diam)
        
        report += f"{n}. {icon} <b>{name}</b>\n"
        report += f"   📏 Диаметр: ~{diam} м\n"
        report += f"   🛣️ Дистанция: {dist:,} км\n"
        report += f"   🛡️ Статус: {danger_label}\n\n"
    
    return report

def send_to_tg():
    text = get_asteroids()
    api_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    payload = {
        'chat_id': CHANNEL_NAME,
        'photo': COVER_IMAGE_URL,
        'caption': text,
        'parse_mode': 'HTML'
    }
    requests.post(api_url, data=payload)

if __name__ == "__main__":
    send_to_tg()
