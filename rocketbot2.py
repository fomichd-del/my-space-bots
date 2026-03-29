import requests
import os
from datetime import datetime

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHANNEL_NAME = '@vladislav_space'

def check_launches():
    # Берем сразу 3 запуска (limit=3) 📑
    url = "https://ll.thespacedevs.com/2.2.0/launch/upcoming/?limit=3"
    response = requests.get(url).json()
    launches = response['results']
    
    report = "🚀 <b>График ближайших запусков</b>\n\n"
    
    for launch in launches:
        rocket = launch['rocket']['configuration']['name']
        company = launch['launch_service_provider']['name']
        mission = launch['mission']['name'] if launch['mission'] else "Исследование"
        
        # Красиво оформляем дату
        raw_time = launch['net']
        time_obj = datetime.strptime(raw_time, "%Y-%m-%dT%H:%M:%SZ")
        launch_date = time_obj.strftime("%d %b, %H:%M")
        
        report += f"🔹 <b>{rocket}</b> ({company})\n"
        report += f"🎯 {mission}\n"
        report += f"📅 Старт: {launch_date} UTC\n\n"
    
    # --- ТВОЯ ПОДПИСЬ ---
    report += "--------------------------\n"
    report += "🛰️ Следи за стартами в блоге:\n"
    report += "👉 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
    
    return report

def send_to_telegram(text):
    api_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(api_url, data={'chat_id': CHANNEL_NAME, 'text': text, 'parse_mode': 'HTML', 'disable_web_page_preview': 'True'})

if __name__ == '__main__':
    send_to_telegram(check_launches())
