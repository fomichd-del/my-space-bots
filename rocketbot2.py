import requests
import os
from datetime import datetime, timezone

# Секреты из настроек GitHub
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHANNEL_NAME = '@vladislav_space'

def check_launches():
    # Запрашиваем данные о ближайшем запуске
    url = "https://ll.thespacedevs.com/2.2.0/launch/upcoming/?limit=1"
    response = requests.get(url).json()
    launch = response['results'][0]
    
    # 1. Собираем информацию о ракете и миссии
    rocket = launch['rocket']['configuration']['name']
    company = launch['launch_service_provider']['name']
    location = launch['pad']['location']['name']
    country = launch['pad']['location']['country_code']
    mission = launch['mission']['name'] if launch['mission'] else "Исследование космоса"
    
    # 2. Магия времени и обратный отсчет ⏱️
    raw_time = launch['net']
    launch_time = datetime.strptime(raw_time, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    
    diff = launch_time - now
    total_sec = diff.total_seconds()
    days = diff.days
    hours = diff.seconds // 3600

    # 3. ЛОГИКА ЦУП: Выбор заголовка и текста в зависимости от времени
    if 0 < total_sec < 3600:
        # 🚨 СРОЧНО (меньше 1 часа)
        header = f"🔴 <b>ВНИМАНИЕ: СКОРО СТАРТ {rocket.upper()}!</b>\n"
        countdown = f"🚨 СРОЧНО: КЛЮЧ НА СТАРТ! 🚀\n{rocket} взлетит меньше чем через час! 📺"
    elif total_sec > 0:
        # 📡 ОБЫЧНЫЙ РЕЖИМ (подготовка)
        header = f"📡 <b>ЦУП СООБЩАЕТ: ПОДГОТОВКА {rocket.upper()}</b>\n"
        countdown = f"⏳ Осталось: <b>{days} д. и {hours} ч.</b>"
    else:
        # ✅ ЗАВЕРШЕНО
        header = f"✅ <b>СТАТУС: МИССИЯ {rocket.upper()} УСПЕШНА</b>\n"
        countdown = "🚀 <b>Ракета уже в пути или успешно выведена на орбиту!</b>"

    # 4. Формируем итоговый отчет ✨
    report = header
    report += f"--------------------------\n\n"
    report += f"🏢 <b>Компания:</b> <code>{company}</code>\n"
    report += f"🏳️ <b>Страна:</b> {country}\n"
    report += f"🎯 <b>Миссия:</b> <i>{mission}</i>\n"
    report += f"📍 <b>Место:</b> {location}\n\n"
    report += f"{countdown}\n\n"

    # Ищем трансляцию 🎬
    videos = launch.get('vidURLs', [])
    if videos:
        stream_url = videos[0]['url']
        report += f"🎬 <b>ТРАНСЛЯЦИЯ:</b>\n👉 <a href='{stream_url}'>СМОТРЕТЬ В ПРЯМОМ ЭФИРЕ</a>\n\n"
    else:
        report += "📺 Ссылка на эфир появится ближе к старту.\n\n"

    # Твоя фирменная подпись 🔗
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
        'disable_web_page_preview': False # Включаем плеер YouTube
    })

if __name__ == '__main__':
    send_to_telegram(check_launches())
