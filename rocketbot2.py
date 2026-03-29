import requests
import os
from datetime import datetime

# Берем данные из нашего защищенного хранилища
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHANNEL_NAME = '@vladislav_space'

def check_launches():
    # Запрашиваем данные о 1 ближайшем запуске
    url = "https://ll.thespacedevs.com/2.2.0/launch/upcoming/?limit=1"
    response = requests.get(url).json()
    launch = response['results'][0]
    
    # Собираем детали миссии
    rocket = launch['rocket']['configuration']['name']
    company = launch['launch_service_provider']['name']
    location = launch['pad']['location']['name']
    mission = launch['mission']['name'] if launch['mission'] else "Секретная миссия! 🕵️‍♂️"
    
    # Работаем со временем старта ⏱️
    raw_time = launch['net']
    time_obj = datetime.strptime(raw_time, "%Y-%m-%dT%H:%M:%SZ")
    launch_time = time_obj.strftime("%d.%m.%Y в %H:%M")
    
    # Формируем основной текст доклада
    report = f"🚀 <b>Новый запуск!</b>\n\n"
    report += f"Компания <b>{company}</b> готовит <b>{rocket}</b>.\n\n"
    report += f"🌍 <b>Откуда:</b> {location}\n"
    report += f"🎯 <b>Миссия:</b> {mission}\n"
    report += f"⏱️ <b>Старт:</b> {launch_time}\n\n"
    
    # --- ДОБАВЛЯЕМ ТВОЮ ФИРМЕННУЮ ПОДПИСЬ ---
    report += "--------------------------\n"
    report += "🛰️ Следите за космосом вместе со мной:\n"
    report += "👉 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
    # ---------------------------------------
    
    return report

def send_to_telegram(text):
    api_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(api_url, data={
        'chat_id': CHANNEL_NAME, 
        'text': text, 
        'parse_mode': 'HTML',
        'disable_web_page_preview': 'false' # Чтобы ссылка красиво подгружалась
    })

if __name__ == '__main__':
    send_to_telegram(check_launches())
