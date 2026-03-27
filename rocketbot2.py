import requests
from datetime import datetime

TELEGRAM_TOKEN = '8745137839:AAFtVLdh4csqLcxC0YnH7nXdckN64vkZhBM'
CHANNEL_NAME = '@vladislav_space'

def check_launches():
    url = "https://ll.thespacedevs.com/2.2.0/launch/upcoming/?limit=1"
    response = requests.get(url).json()
    launch = response['results'][0]
    
    rocket = launch['rocket']['configuration']['name']
    company = launch['launch_service_provider']['name']
    location = launch['pad']['location']['name']
    mission = launch['mission']['name'] if launch['mission'] else "Секретная миссия! 🕵️‍♂️"
    
    raw_time = launch['net']
    time_obj = datetime.strptime(raw_time, "%Y-%m-%dT%H:%M:%SZ")
    launch_time = time_obj.strftime("%d.%m.%Y в %H:%M")
    
    return f"🚀 <b>Новый запуск!</b>\n\nКомпания <b>{company}</b> готовит <b>{rocket}</b>.\n\n🌍 <b>Откуда:</b> {location}\n🎯 <b>Миссия:</b> {mission}\n⏱️ <b>Старт:</b> {launch_time}"

def send_to_telegram(text):
    api_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(api_url, data={'chat_id': CHANNEL_NAME, 'text': text, 'parse_mode': 'HTML'})

if __name__ == '__main__':
    send_to_telegram(check_launches())
