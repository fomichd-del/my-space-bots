import requests
import os # 1. Добавляем модуль для связи с системой

# 2. Вместо текста в кавычках просим систему выдать секрет
TOKEN = os.getenv('TELEGRAM_TOKEN')
CHANNEL = '@vladislav_space'
API_KEY = os.getenv('NASA_API_KEY')

def get_asteroids():
    # Если API_KEY не найден, программа выдаст ошибку, поэтому используем f-строку как обычно
    url = f"https://api.nasa.gov/neo/rest/v1/feed/today?detailed=true&api_key={API_KEY}"
    data = requests.get(url).json()
    count = data['element_count']
    return f"☄️ Сегодня мимо Земли пролетает {count} астероидов!"

def send_msg(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={'chat_id': CHANNEL, 'text': text})

if __name__ == '__main__':
    send_msg(get_asteroids())
