import requests
import os
from datetime import datetime, timezone

# Секреты
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHANNEL_NAME = '@vladislav_space'

def check_launches():
    url = "https://ll.thespacedevs.com/2.2.0/launch/upcoming/?limit=1"
    response = requests.get(url).json()
    launch = response['results'][0]
    
    # 1. Собираем данные
    rocket = launch['rocket']['configuration']['name']
    company = launch['launch_service_provider']['name']
    location = launch['pad']['location']['name']
    country = launch['pad']['location']['country_code'] # Код страны (например, USA или RUS)
    mission = launch['mission']['name'] if launch['mission'] else "Исследование космоса"
    
    # 2. Работаем со временем ⏱️
    raw_time = launch['net']
    # Превращаем строку в объект времени (UTC)
    launch_time = datetime.strptime(raw_time, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    
    # Считаем разницу (обратный отсчет)
    diff = launch_time - now
    days = diff.days
    hours = diff.seconds // 3600
    
    if diff.total_seconds() > 0:
        countdown = f"⏳ Осталось: <b>{days} д. и {hours} ч.</b>"
    else:
        countdown = "🚀 <b>Запуск уже состоялся или идет прямо сейчас!</b>"

    # 3. Формируем текст с акцентами ✨
    report = f"🚀 <b>НОВЫЙ ЗАПУСК: {rocket.upper()}</b>\n"
    report += f"--------------------------\n\n"
    report += f"🏢 <b>Компания:</b> <code>{company}</code>\n"
    report += f"🏳️ <b>Страна:</b> {country}\n"
    report += f"🎯 <b>Миссия:</b> <i>{mission}</i>\n"
    report += f"📍 <b>Место:</b> {location}\n\n"
    report += f"{countdown}\n\n"

    # Ссылки на трансляцию
    videos = launch.get('vidURLs', [])
    if videos:
        stream_url = videos[0]['url']
        report += f"🎬 <b>ТРАНСЛЯЦИЯ:</b>\n👉 <a href='{stream_url}'>СМОТРЕТЬ В ПРЯМОМ ЭФИРЕ</a>\n\n"
    else:
        report += "📺 Ссылка на эфир появится позже.\n\n"

    # Подпись
    report += "--------------------------\n"
    report += "🌌 Читайте мой блог:\n"
    report += "👉 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
    
    return report

def send_to_telegram(text):
    api_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(api_url, data={
        'chat_id': CHANNEL_NAME, 
        'text': text, 
        'parse_mode': 'HTML',
        'disable_web_page_preview': False 
    })

if __name__ == '__main__':
    send_to_telegram(check_launches())
