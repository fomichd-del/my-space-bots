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
            ru_desc = translator.translate(explanation)
            return url_photo, ru_title, ru_desc
        except:
            return url_photo, title, explanation
    return None, None, None

def send_to_telegram():
    img, title, desc = get_cosmos_content()
    if not img: return

    telegram_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    
    # --- КРАСИВОЕ ФОРМАТИРОВАНИЕ ---
    # \n - перенос строки, <b> - жирный текст
    text = (
        f"🌟 <b>{title}</b>\n\n"        # Заголовок и двойной отступ
        f"📖 <b>Описание:</b>\n"        # Подзаголовок
        f"<i>{desc[:500]}...</i>\n\n"  # Текст курсивом (ограничен до 500 символов)
        f"🛰 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
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
