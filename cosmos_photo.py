import requests
import os
from deep_translator import GoogleTranslator

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
NASA_API_KEY = os.getenv('NASA_API_KEY') 
CHANNEL_NAME = '@vladislav_space'

def get_cosmos_photo():
    # 1. Добавляем параметр &count=1 для случайного фото
    url = f"https://api.nasa.gov/planetary/apod?api_key={NASA_API_KEY}&count=1"
    response = requests.get(url).json()
    
    # 2. Так как пришел список, берем самый первый объект [0]
    data = response[0]
    
    photo_url = data.get('url')
    title_en = data.get('title')
    explanation_en = data.get('explanation')
    
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
