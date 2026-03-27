import requests
import os # 1. Подключаем работу с секретами
from deep_translator import GoogleTranslator

# 2. Достаем оба ключа из "сейфа" GitHub
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
NASA_API_KEY = os.getenv('NASA_API_KEY') 
CHANNEL_NAME = '@vladislav_space'

def get_cosmos_photo():
    # Используем переменную NASA_API_KEY в ссылке
    url = f"https://api.nasa.gov/planetary/apod?api_key={NASA_API_KEY}"
    response = requests.get(url).json()
    
    photo_url = response.get('url')
    title_en = response.get('title')
    explanation_en = response.get('explanation')
    
    # Переводчик работает как обычно
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
