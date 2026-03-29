import requests
import os

NASA_API_KEY = os.getenv('NASA_API_KEY')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHANNEL_NAME = '@vladislav_space'

def get_cosmos_photo():
    url = f"https://api.nasa.gov/planetary/apod?api_key={NASA_API_KEY}"
    response = requests.get(url).json()
    
    title = response.get('title', 'Космическое фото')
    explanation = response.get('explanation', '')
    photo_url = response.get('url')
    
    # Ограничим описание, чтобы оно влезло в лимит Telegram (1024 символа для фото)
    short_explanation = (explanation[:600] + '...') if len(explanation) > 600 else explanation
    
    caption = f"🌌 <b>{title}</b>\n\n{short_explanation}\n\n"
    
    # --- НАША ПОДПИСЬ ---
    caption += "--------------------------\n"
    caption += "🚀 Читайте больше в моем блоге:\n"
    caption += "👉 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
    
    return photo_url, caption

def send_to_tg():
    photo, text = get_cosmos_photo()
    api_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    payload = {
        'chat_id': CHANNEL_NAME,
        'photo': photo,
        'caption': text,
        'parse_mode': 'HTML'
    }
    requests.post(api_url, data=payload)

if __name__ == "__main__":
    send_to_tg()
