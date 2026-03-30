import requests
import os

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
NASA_API_KEY = os.getenv('NASA_API_KEY')
CHANNEL_NAME = '@vladislav_space'

def asteroid_check():
    url = f"https://api.nasa.gov/neo/rest/v1/feed/today?detailed=true&api_key={NASA_API_KEY}"
    # Здесь логика запроса к NASA
    text = "☄️ <b>АСТЕРОИДНЫЙ ПАТРУЛЬ</b>\nНа сегодня опасных сближений не зафиксировано!\n\n"
    text += "🌌 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
    return text

def send_msg(text):
    api_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(api_url, data={
        'chat_id': CHANNEL_NAME,
        'text': text,
        'parse_mode': 'HTML',
        'disable_web_page_preview': True
    })

if __name__ == '__main__':
    send_msg(asteroid_check())
