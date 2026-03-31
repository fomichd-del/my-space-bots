import requests
import os
import sys
import json
from deep_translator import GoogleTranslator

# ============================================================
# ⚙️ НАСТРОЙКИ
# ============================================================
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
NASA_API_KEY   = os.getenv('NASA_API_KEY') or "DEMO_KEY"
CHANNEL_NAME   = '@vladislav_space'

def get_short_facts(text):
    """Превращает длинный текст в 3 кратких факта."""
    if not text: return "Детали миссии скоро появятся! 🛰️"
    
    # Разделяем на предложения и берем первые 3
    sentences = [s.strip() for s in text.split('. ') if s.strip()]
    top_facts = sentences[:3]
    
    icons = ["🚀", "🪐", "🔭"]
    formatted_list = []
    
    for i, fact in enumerate(top_facts):
        clean_fact = fact.rstrip('.')
        formatted_list.append(f"{icons[i]} {clean_fact}.")
    
    return "\n\n".join(formatted_list)

def get_cosmos_content(target_type):
    """
    Ищет контент нужного типа (image или video).
    Если сегодня тип не совпадает, берет случайный объект того же типа.
    """
    # Сначала проверяем сегодняшний пост
    url = f"https://api.nasa.gov/planetary/apod?api_key={NASA_API_KEY}"
    
    # Если нам нужно видео, а сегодня фото (или наоборот) — берем случайную подборку
    # и ищем там подходящий тип.
    max_attempts = 5
    for attempt in range(max_attempts):
        fetch_url = url if attempt == 0 else f"{url}&count=10"
        response = requests.get(fetch_url)
        
        if response.status_code == 200:
            results = response.json()
            # Превращаем в список, если это один объект (сегодняшний)
            items = results if isinstance(results, list) else [results]
            
            for item in items:
                if item.get('media_type') == target_type:
                    return item
    return None

def send_to_telegram(target_type):
    """Формирует и отправляет пост в зависимости от типа медиа."""
    data = get_cosmos_content(target_type)
    
    if not data:
        print(f"❌ Не удалось найти контент типа: {target_type}")
        return

    media_url = data.get('url')
    title = data.get('title', 'Космическое событие')
    explanation = data.get('explanation', '')

    # Перевод
    try:
        translator = GoogleTranslator(source='en', target='ru')
        ru_title = translator.translate(title)
        ru_desc = translator.translate(explanation)
        facts = get_short_facts(ru_desc)
    except:
        ru_title, facts = title, get_short_facts(explanation)

    # Оформление текста
    caption_text = (
        f"🌌 <b>{ru_title.upper()}</b>\n"
        f"─────────────────────\n\n"
        f"<b>ГЛАВНОЕ:</b>\n\n"
        f"{facts}\n\n"
        f"✨ <b>Больше космоса:</b>\n"
        f"👉 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
    )

    # Выбор метода отправки
    if target_type == 'image':
        api_method = "sendPhoto"
        payload = {'chat_id': CHANNEL_NAME, 'photo': media_url, 'caption': caption_text, 'parse_mode': 'HTML'}
    else:
        # Для видео (YouTube ссылки) используем sendMessage, чтобы Telegram сам сделал предпросмотр
        api_method = "sendMessage"
        video_text = f"{caption_text}\n\n🎬 <b>Смотреть видео:</b> {media_url}"
        payload = {'chat_id': CHANNEL_NAME, 'text': video_text, 'parse_mode': 'HTML'}

    r = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/{api_method}", data=payload)
    print(f"📡 Статус отправки ({target_type}): {r.status_code}")

if __name__ == "__main__":
    # Читаем аргумент из командной строки (image или video)
    # Если аргумента нет, по умолчанию берем image
    mode = sys.argv[1] if len(sys.argv) > 1 else 'image'
    send_to_telegram(mode)
