import requests
import os

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
NASA_API_KEY = os.getenv('NASA_API_KEY')
CHANNEL_NAME = '@vladislav_space'

def get_nasa_photo():
    url = f"https://api.nasa.gov/planetary/apod?api_key={NASA_API_KEY}"
    response = requests.get(url).json()
    
    title = response.get('title', 'Космическое фото')
    explanation = response.get('explanation', '')
    img_url = response.get('url', '')
    
    # Переводим заголовок на русский (примерный вариант)
    text = f"🌌 <b>ФОТО ДНЯ: {title}</b>\n\n"
    # Ограничим описание, чтобы оно не было слишком длинным
    text += (explanation[:300] + '...') if len(explanation) > 300 else explanation
    text += "\n\n"
    text += "🌌 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
    
    return img_url, text

def send_photo(photo_url, caption):
    api_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    requests.post(api_url, data={
        'chat_id': CHANNEL_NAME,
        'photo': photo_url,
        'caption': caption,
        'parse_mode': 'HTML'
        # У фото превью ссылки отключать не нужно, оно и так не появится
    })

if __name__ == '__main__':
    url, txt = get_nasa_photo()
    send_photo(url, txt)
