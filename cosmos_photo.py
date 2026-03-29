import requests
import os

NASA_API_KEY = os.getenv('NASA_API_KEY')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHANNEL_NAME = '@vladislav_space'

def get_cosmos_photo():
    url = f"https://api.nasa.gov/planetary/apod?api_key={NASA_API_KEY}"
    res = requests.get(url).json()
    
    title = res.get('title', 'Космическое фото')
    explanation = res.get('explanation', '')
    media_type = res.get('media_type') # Проверяем: фото или видео?
    url_media = res.get('url')
    hd_url = res.get('hdurl', url_media) # Ссылка на высокое качество
    
    short_text = (explanation[:500] + '...') if len(explanation) > 500 else explanation
    
    report = f"🌌 <b>{title}</b>\n\n{short_text}\n\n"
    if media_type == 'image':
        report += f"🖼 <a href='{hd_url}'>Открыть в HD качестве</a>\n\n"
    
    # --- ТВОЯ ПОДПИСЬ ---
    report += "--------------------------\n"
    report += "🚀 Больше космоса тут:\n"
    report += "👉 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
    
    return url_media, report, media_type

def send_to_tg():
    url, text, m_type = get_cosmos_photo()
    base_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/"
    
    if m_type == 'image':
        requests.post(base_url + "sendPhoto", data={'chat_id': CHANNEL_NAME, 'photo': url, 'caption': text, 'parse_mode': 'HTML'})
    else:
        # Если это видео (YouTube), отправляем просто текстом с ссылкой
        requests.post(base_url + "sendMessage", data={'chat_id': CHANNEL_NAME, 'text': text + f"\n\n📺 Видео дня: {url}", 'parse_mode': 'HTML'})

if __name__ == "__main__":
    send_to_tg()
