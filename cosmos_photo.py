import requests
import os
import sys
import re
from deep_translator import GoogleTranslator

# ============================================================
# ⚙️ НАСТРОЙКИ
# ============================================================
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHANNEL_NAME   = '@vladislav_space' 
NASA_API_KEY   = "DEMO_KEY" 

# ============================================================
# 🛠️ ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================

def translate_to_russian(text):
    """Перевод текста на русский."""
    try:
        if not text: return ""
        return GoogleTranslator(source='auto', target='ru').translate(text)
    except Exception as e:
        print(f"❌ Ошибка перевода: {e}")
        return text

def format_description(text):
    """Разбивает сплошной текст на абзацы по 2 предложения."""
    # Разделяем текст на предложения
    sentences = re.split(r'(?<=[.!?])\s+', text)
    formatted = ""
    
    # Группируем предложения и добавляем пустые строки
    for i in range(0, len(sentences), 2):
        group = " ".join(sentences[i:i+2])
        formatted += group + "\n\n"
    
    return formatted.strip()

def fix_video_link(url):
    """Адаптация ссылок для плеера Telegram."""
    base_url = url.split("?")[0]
    if "youtube.com/embed/" in base_url:
        return base_url.replace("youtube.com/embed/", "youtube.com/watch?v=")
    elif "player.vimeo.com/video/" in base_url:
        return base_url.replace("player.vimeo.com/video/", "vimeo.com/")
    return url

# ============================================================
# 🌌 ЛОГИКА NASA И ОТПРАВКА
# ============================================================

def get_nasa_data():
    """Получает 10 случайных постов от NASA."""
    url = f"https://api.nasa.gov/planetary/apod?api_key={NASA_API_KEY}&count=10"
    try:
        return requests.get(url).json()
    except Exception as e:
        print(f"❌ Ошибка API: {e}")
        return []

def send_telegram(text, media_url, media_type):
    """Отправляет пост в канал."""
    if media_type == "image":
        api_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
        payload = {'chat_id': CHANNEL_NAME, 'photo': media_url, 'caption': text, 'parse_mode': 'HTML'}
    else:
        fixed_url = fix_video_link(media_url)
        api_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {'chat_id': CHANNEL_NAME, 'text': f"{text}\n\n📺 <b>Видео:</b> {fixed_url}", 'parse_mode': 'HTML'}
    
    res = requests.post(api_url, data=payload)
    print(f"📤 Статус: {res.status_code}")

# ============================================================
# 🚀 ЗАПУСК
# ============================================================

if __name__ == '__main__':
    target = sys.argv[1] if len(sys.argv) > 1 else "image"
    posts = get_nasa_data()
    
    selected = next((p for p in posts if p.get('media_type') == target), None)

    if selected:
        title = translate_to_russian(selected.get('title', 'Космос'))
        # Используем новую функцию для форматирования текста
        desc = format_description(translate_to_russian(selected.get('explanation', '')))
        
        message = (
            f"<b>🌌 {title.upper()}</b>\n\n"
            f"<b>📖 ОПИСАНИЕ:</b>\n"
            f"{desc}\n\n"
            f"⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
            f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
        )
        send_telegram(message, selected.get('url', ''), target)
