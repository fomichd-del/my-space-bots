import requests
import os
import sys
from deep_translator import GoogleTranslator

# --- НАСТРОЙКИ ---
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
NASA_API_KEY   = os.getenv('NASA_API_KEY') or "DEMO_KEY"
CHANNEL_NAME   = '@vladislav_space'

def get_short_facts(text, icons):
    """Разбивает текст на 3 интересных факта"""
    if not text: return "Детали скоро появятся! 🔭"
    sentences = [s.strip() for s in text.split('. ') if s.strip()]
    top_facts = sentences[:3]
    
    formatted_list = []
    for i, fact in enumerate(top_facts):
        clean_fact = fact.rstrip('.')
        icon = icons[i] if i < len(icons) else "✨"
        if ':' in clean_fact:
            header, desc = clean_fact.split(':', 1)
            formatted_list.append(f"{icon} <b>{header}:</b>{desc}.")
        else:
            formatted_list.append(f"{icon} {clean_fact}.")
    return "\n\n".join(formatted_list)

def get_cosmos_content(target_type):
    """Ищет свежий контент нужного типа (image или video)"""
    url = f"https://api.nasa.gov/planetary/apod?api_key={NASA_API_KEY}"
    for attempt in range(5):
        # При первой попытке берем за сегодня, при неудаче — случайные 10
        fetch_url = url if attempt == 0 else f"{url}&count=10"
        try:
            response = requests.get(fetch_url, timeout=20)
            if response.status_code == 200:
                items = response.json()
                if not isinstance(items, list): items = [items]
                for item in items:
                    if item.get('media_type') == target_type:
                        return item
        except:
            continue
    return None

def send_to_telegram(target_type):
    """Формирует и отправляет пост в канал"""
    # Выбираем файл памяти в зависимости от режима
    db_file = f"last_cosmo_{target_type}.txt"
    
    data = get_cosmos_content(target_type)
    if not data: 
        print(f"❌ Не удалось найти контент типа {target_type}")
        return

    # Используем дату в качестве уникального ID (надёжнее заголовка)
    current_id = data.get('date', data.get('title', ''))
    
    # --- ПРОВЕРКА НА ПОВТОРЫ ---
    if os.path.exists(db_file):
        with open(db_file, 'r', encoding='utf-8') as f:
            if f.read().strip() == current_id:
                print(f"✋ Контент '{current_id}' ({target_type}) уже был опубликован.")
                return

    # --- ПЕРЕВОД И ОФОРМЛЕНИЕ ---
    try:
        translator = GoogleTranslator(source='en', target='ru')
        ru_title = translator.translate(data.get('title', 'Космос'))
        ru_desc = translator.translate(data.get('explanation', ''))
        
        # Выбираем иконки для фактов
        icons = ["🎬", "🎥", "🌠"] if target_type == 'video' else ["🚀", "🪐", "🔭"]
        facts = get_short_facts(ru_desc, icons)
    except:
        ru_title = data.get('title', 'Космос')
        facts = "Интересные факты о сегодняшнем событии уже в пути! 🛰️"

    # --- ЛОГИКА ОФОРМЛЕНИЯ ---
    prefix = "🎬 <b>ВИДЕО:</b> " if target_type == 'video' else "🌌 "
    header = f"{prefix}<b>{ru_title.upper()}</b>\n─────────────────────\n\n"
    
    body = f"<b>ГЛАВНОЕ:</b>\n\n{facts}\n\n"
    footer = f"✨ <b>Больше космоса:</b>\n👉 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"

    payload = {
        'chat_id': CHANNEL_NAME,
        'parse_mode': 'HTML',
        'disable_web_page_preview': False 
    }

    # --- ОТПРАВКА ---
    if target_type == 'image':
        payload['photo'] = data.get('url')
        payload['caption'] = header + body + footer
        api_method = "sendPhoto"
    else:
        video_url = data.get('url')
        video_note = f"🎞 <b>Ссылка на ролик:</b> {video_url}\n\n"
        payload['text'] = header + video_note + body + footer
        api_method = "sendMessage"

    r = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/{api_method}", data=payload)
    
    if r.status_code == 200:
        with open(db_file, 'w', encoding='utf-8') as f:
            f.write(current_id)
        print(f"✅ Пост '{current_id}' успешно отправлен!")
    else:
        print(f"❌ Ошибка Telegram: {r.text}")

if __name__ == "__main__":
    # Читаем режим из аргументов (image или video)
    mode = sys.argv[1] if len(sys.argv) > 1 else 'image'
    send_to_telegram(mode)
