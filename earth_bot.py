import requests
import os

# Настройки
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
NASA_API_KEY   = os.getenv('NASA_API_KEY') or "DEMO_KEY"
CHANNEL_NAME   = '@vladislav_space'

def get_earth_data():
    avail_url = f"https://api.nasa.gov/epic/api/natural/available?api_key={NASA_API_KEY}"
    try:
        dates = requests.get(avail_url).json()
        last_date = dates[-1]
        data_url = f"https://api.nasa.gov/epic/api/natural/date/{last_date}?api_key={NASA_API_KEY}"
        latest_shot = requests.get(data_url).json()[-1]
        
        file_name = latest_shot['image']
        p = last_date.split("-")
        image_url = f"https://epic.gsfc.nasa.gov/archive/natural/{p[0]}/{p[1]}/{p[2]}/png/{file_name}.png"
        
        # Обновленная подпись
        caption = (
            "🌍 <b>Планета Земля сегодня</b>\n\n"
            "Вид с камеры EPIC (NASA) 🛰️\n\n"
            "🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
        )
        return image_url, caption
    except:
        return None, None

def send_photo(photo_url, caption):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    requests.post(url, data={'chat_id': CHANNEL_NAME, 'photo': photo_url, 'caption': caption, 'parse_mode': 'HTML'})

if __name__ == '__main__':
    url, text = get_earth_data()
    if url: send_photo(url, text)
