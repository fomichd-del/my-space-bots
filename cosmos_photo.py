import requests
import os
from deep_translator import GoogleTranslator

# ⚙️ Настройки
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
NASA_API_KEY = os.getenv('NASA_API_KEY') or "DEMO_KEY"
CHANNEL_NAME = '@vladislav_space'

def get_short_facts(text):
    """Превращает текст в 3 кратких факта"""
    # Разделяем текст на предложения
    sentences = text.split('. ')
    # Берем первые 3 предложения
    top_facts = sentences[:3]
    
    # Список эмодзи для фактов
    icons = ["🚀", "🪐", "🔭"]
    formatted_list = []
    
    for i, fact in enumerate(top_facts):
        # Очищаем от лишних точек и пробелов
        clean_fact = fact.strip().replace('.', '')
        formatted_list.append(f"{icons[i]} {clean_fact}.")
    
    return "\n\n".join(formatted_list)

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
            # Переводим и сокращаем до 3 фактов
            raw_desc = translator.translate(explanation)
            ru_facts = get_short_facts(raw_desc)
            return url_photo, ru_title, ru_facts
        except:
            return url_photo, title, explanation
    return None, None, None

def send_to_telegram():
    img, title, facts = get_cosmos_content()
    if not img: return

    telegram_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    
    # 🎨 Формируем короткий и стильный пост
    caption_text = (
        f"🌌 <b>{title.upper()}</b>\n"
        f"─────────────────────\n\n"
        f"<b>ГЛАВНОЕ ЗА СЕГОДНЯ:</b>\n\n"
        f"{facts}\n\n"
        f"✨ <b>Больше космоса:</b>\n"
        f"👉 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
    )
    
    payload = {
        'chat_id': CHANNEL_NAME,
        'photo': img,
        'caption': caption_text,
        'parse_mode': 'HTML'
    }
    
    r = requests.post(telegram_url, data=payload)
    print(f"Статус отправки: {r.status_code}")

if __name__ == "__main__":
    send_to_telegram()
