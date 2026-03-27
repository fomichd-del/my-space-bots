import requests

TOKEN = '8745137839:AAFtVLdh4csqLcxC0YnH7nXdckN64vkZhBM'
CHANNEL = '@vladislav_space'
API_KEY = 'DEMO_KEY'

def get_asteroids():
    url = f"https://api.nasa.gov/neo/rest/v1/feed/today?detailed=true&api_key={API_KEY}"
    data = requests.get(url).json()
    count = data['element_count']
    return f"☄️ Сегодня мимо Земли пролетает {count} астероидов!"

def send_msg(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={'chat_id': CHANNEL, 'text': text})

if __name__ == '__main__':
    send_msg(get_asteroids())
