import requests
import os

# Настройки
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
NASA_API_KEY   = os.getenv('NASA_API_KEY') or "DEMO_KEY"
CHANNEL_NAME   = '@vladislav_space'

def get_mars_data():
    url = f"https://api.nasa.gov/mars-photos/api/v1/rovers/curiosity/latest_photos?api_key={NASA_API_KEY}"
    try:
        photos = requests.get(url).json().get('latest_photos', [])
        if not photos: return None, None

        best_photo = next((p for p in photos if p['camera']['name'] == "MAST"), photos[0])
        image_url = best_photo['img_src'].replace("http://", "https://")
        
        # Обновленная подпись
        caption = (
            f"🏜 <b>Марсианские будни</b>\n\n"
            f"Снимок ровера Curiosity, {best_photo['sol']}-й марсианский день.\n"
            f"📸 Камера: {best_photo['camera']['full_name']}\n\n"
            f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
        )
        return image_url, caption
    except:
        return None, None

def send_photo(photo_url, caption):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    requests.post(url, data={'chat_id': CHANNEL_NAME, 'photo': photo_url, 'caption': caption, 'parse_mode': 'HTML'})

if __name__ == '__main__':
    url, text = get_mars_data()
    if url: send_photo(url, text)
