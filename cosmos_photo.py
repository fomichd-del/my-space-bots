import requests
import os
from deep_translator import GoogleTranslator

# Настройки
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
NASA_API_KEY = os.getenv('NASA_API_KEY') or "DEMO_KEY"
CHANNEL_NAME = '@vladislav_space'

def get_cosmos_content():
    url = f"https://api.nasa.gov/planetary/apod?api_key={NASA_API_KEY}&count=1"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()[0]
        url_photo = data.get('url')
        title = data.get('title')
        explanation = data.get('explanation')
        
        try:
            translator = GoogleTranslator(source='en', target='ru')
            ru_title = translator.translate(title)
            # Принудительно разбиваем текст на абзацы после каждой точки с пробелом
            ru_desc = translator.translate(explanation).replace('. ', '.\n\n')
            return url_photo, ru_title, ru_desc
        except:
            return url_photo, title, explanation
    return None, None, None

def send_to_telegram():
    img, title, desc = get_cosmos_content()
    if not img: return

    telegram_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    
    # Формируем структуру поста
    # \n\n — это пустая строка между блоками
    text = (
        f"🌌 <b>{title.upper()}</b>\n"
        f"─────────────────────\n\n"
        f"🛰 <b>ИССЛЕДОВАНИЕ:</b>\n\n"
        f"{desc[:700]}...\n\n" # Описание теперь с абзацами
        f"☄️ <b>Присоединяйся к нам:</b>\n"
        f"👉 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
    )
    
    payload = {
        'chat_id': CHANNEL_NAME,
        'photo': img,
        'caption': text,
        'parse_mode': 'HTML'
    }
    
    r = requests.post(telegram_url, data=payload)
    print(f"Статус отправки: {r.status_code}")

if __name__ == "__main__":
    send_to_telegram()
