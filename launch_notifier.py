import requests
import os

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHANNEL_NAME = '@vladislav_space'

def get_launches():
    # Используем бесплатное API для запусков
    url = "https://ll.thespacedevs.com/2.2.0/launch/upcoming/?limit=1"
    response = requests.get(url).json()
    launch = response['results'][0]
    
    name = launch['name']
    date = launch['window_start']
    pad = launch['pad']['name']
    
    report = f"🚀 <b>Ближайший запуск:</b>\n\n"
    report += f"🔹 Миссия: {name}\n"
    report += f"📅 Когда: {date}\n"
    report += f"📍 Площадка: {pad}\n\n"
    
    # --- НАША ПОДПИСЬ ---
    report += "--------------------------\n"
    report += "🛰️ Следите за космосом вместе со мной:\n"
    report += "👉 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
    
    return report

def send_to_tg():
    text = get_launches()
    api_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        'chat_id': CHANNEL_NAME,
        'text': text,
        'parse_mode': 'HTML'
    }
    requests.post(api_url, data=payload)

if __name__ == "__main__":
    send_to_tg()
