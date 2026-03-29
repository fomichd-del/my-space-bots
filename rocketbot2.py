import requests
import os

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHANNEL_NAME = '@vladislav_space'

def get_launch_report():
    url = "https://ll.thespacedevs.com/2.2.0/launch/upcoming/?limit=1"
    res = requests.get(url).json()['results'][0]
    
    name = res['name']
    video = res['vidURLs'][0]['url'] if res['vidURLs'] else "Трансляция скоро появится"
    
    text = "📢 <b>РЕПОРТАЖ ИЗ ЦУПА</b>\n\n"
    text += f"🚀 Готовится взлет: {name}\n"
    text += f"📺 Трансляция: {video}\n\n"
    text += "🌌 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
    return text

def send_to_tg(text):
    api_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(api_url, data={
        'chat_id': CHANNEL_NAME,
        'text': text,
        'parse_mode': 'HTML',
        'disable_web_page_preview': True
    })

if __name__ == '__main__':
    send_to_tg(get_launch_report())
