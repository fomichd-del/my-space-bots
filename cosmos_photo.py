import requests
import os
import sys
from deep_translator import GoogleTranslator

# --- НАСТРОЙКИ ---
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
NASA_API_KEY   = os.getenv('NASA_API_KEY') or "DEMO_KEY"
CHANNEL_NAME   = '@vladislav_space'
DB_FILE        = "last_cosmo_post.txt"

def get_short_facts(text, icons):
    """Разбивает описание на 3 интересных факта"""
    if not text: return "Детали скоро появятся! 🔭"
    # Очищаем текст и разбиваем на предложения
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
    """Ищет свежий контент в NASA APOD"""
    url = f"https://api.nasa.gov/planetary/apod?api_key={NASA_API_KEY}"
    # Пробуем получить сегодняшний пост, если не тот тип — берем случайные
    for attempt in range(5):
        fetch_url = url if attempt == 0 else f"{url}&count=10"
        try:
            response = requests.get(fetch_url, timeout=20)
            if response.status_code == 200:
                items = response.json()
                if not isinstance(items, list): items = [items]
                for item in items:
                    if item.get('media_type') == target_type:
                        return item
        except Exception as e:
            print(f"Ошибка сети: {e}")
    return None

def send_to_telegram(target_type):
    """Формирует и отправляет пост"""
    data = get_cosmos_content(target_type)
    if not data: 
        print(f"❌ Не удалось найти контент типа {target_type}")
        return

    # --- ПРОВЕРКА НА ПОВТОРЫ (Используем дату, она надежнее заголовка) ---
    current_id = data.get('date', 'no_date')
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            if f.read().strip() == current_id:
                print(f"✋ Пост за {current_id} уже был опубликован. Пропускаю.")
                return

    # --- ПЕРЕВОД ---
    try:
        translator = GoogleTranslator(source='en', target='ru')
        ru_title = translator.translate(data.get('title', 'Космическое фото'))
        ru_desc = translator.translate(data.get('explanation', ''))
        
        icons = ["🎬", "🎥", "🌠"] if target_type == 'video' else ["🚀", "🪐", "🔭"]
        facts = get_short_facts(ru_desc, icons)
    except Exception as e:
        print(f"Ошибка перевода: {e}")
        ru_title, facts = data.get('title'), "Космос прекрасен даже без перевода! 🛰️"

    # --- ОФОРМЛЕНИЕ ---
    prefix = "🎬 <b>ВИДЕО:</b> " if target_type == 'video' else "🌌 "
    header = f"{prefix}<b>{ru_title.upper()}</b>\n─────────────────────\n\n"
    body = f"<b>ГЛАВНОЕ:</b>\n\n{facts}\n\n"
    footer = f"✨ <b>Больше космоса:</b>\n👉 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"

    payload = {
        'chat_id': CHANNEL_NAME,
        'parse_mode': 'HTML',
        'disable_web_page_preview': False 
    }

    if target_type == 'image':
        payload['photo'] = data.get('url')
        payload['caption'] = header + body + footer
        api_method = "sendPhoto"
    else:
        video_url = data.get('url')
        video_note = f"🎞 <b>Ссылка на ролик:</b> {video_url}\n\n"
        payload['text'] = header + video_note + body + footer
        api_method = "sendMessage"

    # --- ОТПРАВКА ---
    r = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/{api_method}", data=payload)
    
    if r.status_code == 200:
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            f.write(current_id)
        print(f"✅ Успешно! Дата {current_id} сохранена в {DB_FILE}")
    else:
        print(f"❌ Ошибка Telegram: {r.text}")

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else 'image'
    send_to_telegram(mode)
