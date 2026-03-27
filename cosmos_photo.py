import requests
from deep_translator import GoogleTranslator

TELEGRAM_TOKEN = '8745137839:AAFtVLdh4csqLcxC0YnH7nXdckN64vkZhBM'
CHANNEL_NAME = '@vladislav_space'
NASA_API_KEY = 'DEMO_KEY' 

def get_cosmos_photo():
    url = f"https://api.nasa.gov/planetary/apod?api_key={NASA_API_KEY}"
    response = requests.get(url).json()
    
    photo_url = response.get('url')
    title_en = response.get('title')
    explanation_en = response.get('explanation')
    
    translator = GoogleTranslator(source='auto', target='ru')
    title_ru = translator.translate(title_en)
    explanation_ru = translator.translate(explanation_en)
    
    caption = f"🌌 <b>{title_ru}</b>\n\n{explanation_ru}"
    return photo_url, caption

def send_photo(photo_url, caption):
    api_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    requests.post(api_url, data={'chat_id': CHANNEL_NAME, 'photo': photo_url, 'caption': caption[:1024], 'parse_mode': 'HTML'})

if __name__ == '__main__':
    img, txt = get_cosmos_photo()
    send_photo(img, txt)
