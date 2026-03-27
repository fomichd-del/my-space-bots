import requests
import os
from datetime import datetime, timezone

# Загружаем секреты
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHANNEL_NAME = '@vladislav_space'

def check_and_notify():
    # 1. Получаем данные о ближайшем запуске
    url = "https://ll.thespacedevs.com/2.2.0/launch/upcoming/?limit=1"
    response = requests.get(url).json()
    launch = response['results'][0]
    
    new_id = launch['id']
    launch_time_str = launch['net'] # Время запуска в формате ISO
    launch_time = datetime.strptime(launch_time_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    
    # Считаем, сколько минут осталось до старта
    diff_minutes = (launch_time - now).total_seconds() / 60

    # 2. Читаем "память" из файла
    if os.path.exists('last_id.txt'):
        with open('last_id.txt', 'r') as f:
            last_id = f.read().strip()
    else:
        last_id = ""

    # 3. Условие: если запуск новый И до него осталось меньше 30 минут
    if new_id != last_id and 0 < diff_minutes <= 30:
        video_url = launch['vidURLs'][0]['url'] if launch['vidURLs'] else "Трансляция пока не найдена 🛰️"
        rocket = launch['rocket']['configuration']['name']
        
        text = f"🚀 <b>Внимание! Скоро старт!</b>\n\nРакета: <b>{rocket}</b>\nДо запуска осталось примерно {int(diff_minutes)} мин.\n\n📺 Ссылка на трансляцию: {video_url}"
        
        # Отправляем в Telegram
        api_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(api_url, data={'chat_id': CHANNEL_NAME, 'text': text, 'parse_mode': 'HTML'})
        
        # Запоминаем ID
        with open('last_id.txt', 'w') as f:
            f.write(new_id)

if __name__ == '__main__':
    check_and_notify()
