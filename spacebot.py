import requests
import os
from datetime import datetime

# Секреты
NASA_API_KEY = os.getenv('NASA_API_KEY')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHANNEL_NAME = '@vladislav_space'

def get_asteroids():
    today = datetime.now().strftime('%Y-%m-%d')
    url = f"https://api.nasa.gov/neo/rest/v1/feed?start_date={today}&end_date={today}&api_key={NASA_API_KEY}"
    
    response = requests.get(url).json()
    asteroids = response['near_earth_objects'][today]
    
    # Сортируем по близости к Земле (miss_distance в километрах)
    asteroids.sort(key=lambda x: float(x['close_approach_data'][0]['miss_distance']['kilometers']))
    
    report = f"☄️ <b>Астероидный патруль на {today}</b>\n\n"
    
    # Берем топ-3 самых близких
    for n, ast in enumerate(asteroids[:3], 1):
        name = ast['name']
        dist = int(float(ast['close_approach_data'][0]['miss_distance']['kilometers']))
        diam = int(ast['estimated_diameter']['meters']['estimated_diameter_max'])
        danger = "⚠️ Опасен!" if ast['is_potentially_hazardous_asteroid'] else "✅ Безопасен"
        
        report += f"{n}. <b>{name}</b>\n"
        report += f"   📏 Диаметр: ~{diam} м\n"
        report += f"   🛣️ Расстояние: {dist:,} км\n"
        report += f"   🛡️ Статус: {danger}\n\n"
    
    return report

def send_to_tg():
    text = get_asteroids()
    api_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(api_url, data={'chat_id': CHANNEL_NAME, 'text': text, 'parse_mode': 'HTML'})

if __name__ == "__main__":
    send_to_tg()
