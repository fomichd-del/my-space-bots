import requests
import os
from deep_translator import GoogleTranslator

# ⚙️ Настройки
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
NASA_API_KEY = os.getenv('NASA_API_KEY') or "DEMO_KEY"
CHANNEL_NAME = '@vladislav_space'

def format_description(text):
    """Разбивает сплошной текст на красивые абзацы"""
    sentences = text.split('. ')
    paragraphs = []
    # Группируем по 2 предложения в абзац для легкости чтения
    for i in range(0, len(sentences), 2):
        chunk = ". ".join(sentences[i:i+2])
        if not chunk.endswith('.'):
            chunk += '.'
        paragraphs.append(chunk)
    return "\n\n".join(paragraphs)

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
            # Переводим и структурируем
            raw_desc = translator.translate(explanation)
            ru_desc = format_description(raw_desc)
            return url_photo, ru_title, ru_desc
        except:
            return url_photo, title, explanation
    return None, None, None

def send_to_telegram():
    img, title, desc = get_cosmos_content()
    if not img: return

    telegram_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    
    # 🎨 Формируем пост с эмодзи и структурой
    # Мы ограничиваем текст, чтобы он точно влез в лимит Telegram (1024 символа для фото)
    clean_desc = desc[:800] + "..." if len(desc) > 800 else desc

    caption_text = (
        f"🌌 <b>{title.upper()}</b>\n"
        f"─────────────────────\n\n"
        f"🔭 <b>ОБЪЕКТ ИССЛЕДОВАНИЯ:</b>\n\n"
        f"{clean_desc}\n\n"
        f"✨ <b>Больше космоса здесь:</b>\n"
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
