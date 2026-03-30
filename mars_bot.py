import requests
import os
import time

# Настройки доступа
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
NASA_API_KEY   = os.getenv('NASA_API_KEY') or "DEMO_KEY"
CHANNEL_NAME   = '@vladislav_space'

def get_mars_data():
    """Ищет самое свежее и красивое фото с Марса."""
    # Используем эндпоинт latest_photos, чтобы не угадывать дату
    url = f"https://api.nasa.gov/mars-photos/api/v1/rovers/curiosity/latest_photos?api_key={NASA_API_KEY}"
    
    try:
        response = requests.get(url, timeout=15).json()
        photos = response.get('latest_photos', [])
        if not photos: return None, None

        # Сначала ищем фото с цветной камеры MAST
        best_photo = next((p for p in photos if p['camera']['name'] == "MAST"), photos[0])
        
        image_url = best_photo['img_src'].replace("http://", "https://")
        caption = (
            f"🏜 <b>Марсианские будни</b>\n\n"
            f"Ровер: {best_photo['rover']['name']}\n"
            f"Камера: {best_photo['camera']['full_name']}\n"
            f"Сол (день на Марсе): {best_photo['sol']}"
        )
        return image_url, caption
    except Exception as e:
        print(f"Ошибка: {e}")
        return None, None

def send_photo(photo_url, caption):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    payload = {'chat_id': CHANNEL_NAME, 'photo': photo_url, 'caption': caption, 'parse_mode': 'HTML'}
    requests.post(url, data=payload)

if __name__ == '__main__':
    url, text = get_mars_data()
    if url:
        send_photo(url, text)
