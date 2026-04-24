import requests
import os
import sys
import json
import re
from deep_translator import GoogleTranslator

# --- НАСТРОЙКИ ---
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
NASA_API_KEY   = os.getenv('NASA_API_KEY') or "DEMO_KEY"
CHANNEL_NAME   = '@vladislav_space'

def get_short_facts(text, icons):
    """Разбивает описание NASA на 3 интересных факта"""
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

def clean_video_url(url):
    """
    Превращает 'embed' ссылки NASA в обычные ссылки YouTube.
    Telegram гораздо лучше генерирует плеер из стандартных ссылок.
    """
    if 'youtube.com/embed/' in url:
        # Извлекаем ID видео из ссылки типа https://www.youtube.com/embed/XXXXX?rel=0
        video_id = url.split('/')[-1].split('?')[0]
        return f"https://www.youtube.com/watch?v={video_id}"
    return url

def get_cosmos_content(target_type):
    """Ищет свежий контент в NASA APOD (фото или видео)"""
    url = f"https://api.nasa.gov/planetary/apod?api_key={NASA_API_KEY}"
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
        except:
            continue
    return None

def send_to_telegram(target_type):
    """Основная логика отправки"""
    db_file = f"last_cosmo_{target_type}.txt"
    
    data = get_cosmos_content(target_type)
    if not data: 
        print(f"❌ Не удалось найти {target_type} от NASA")
        return

    current_id = data.get('date', data.get('title', ''))
    
    if os.path.exists(db_file):
        with open(db_file, 'r', encoding='utf-8') as f:
            if f.read().strip() == current_id:
                print(f"✋ Этот контент ({target_type}) за {current_id} уже был.")
                return

    try:
        translator = GoogleTranslator(source='en', target='ru')
        ru_title = translator.translate(data.get('title', 'Космос'))
        ru_desc = translator.translate(data.get('explanation', ''))
        
        icons = ["🎬", "🎥", "🌠"] if target_type == 'video' else ["🚀", "🪐", "🔭"]
        facts = get_short_facts(ru_desc, icons)
    except:
        ru_title = data.get('title', 'Космическое событие')
        facts = "Удивительный факт о космосе уже на подходе! 🛰️"

    # --- СБОРКА ПОСТА ---
    prefix = "🎬 <b>ВИДЕО:</b> " if target_type == 'video' else "🌌 "
    header = f"{prefix}<b>{ru_title.upper()}</b>\n─────────────────────\n\n"
    body = f"<b>ГЛАВНОЕ:</b>\n\n{facts}\n\n"
    footer = f"✨ <b>Больше космоса:</b>\n👉 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"

    payload = {
        'chat_id': CHANNEL_NAME,
        'parse_mode': 'HTML'
    }

    if target_type == 'image':
        payload['photo'] = data.get('url')
        payload['caption'] = header + body + footer
        api_method = "sendPhoto"
    else:
        # 1. Чистим ссылку (убираем /embed/)
        video_url = clean_video_url(data.get('url'))
        
        # 2. Используем невидимый пробел (\u200b) внутри тега ссылки.
        # Это заставляет Telegram видеть ссылку для превью, но она не видна в тексте.
        hidden_link = f"<a href='{video_url}'>\u200b</a>" 
        
        payload['text'] = hidden_link + header + body + footer
        
        # 3. Настройка превью: Обязательно указываем URL и позицию сверху
        payload['link_preview_options'] = {
            'is_disabled': False,
            'url': video_url,
            'show_above_text': True,
            'prefer_large_media': True
        }
        api_method = "sendMessage"

    # --- ОТПРАВКА ---
    # Важно: используем json=payload, чтобы Telegram правильно считал настройки превью
    r = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/{api_method}", json=payload)
    
    if r.status_code == 200:
        with open(db_file, 'w', encoding='utf-8') as f:
            f.write(current_id)
        print(f"✅ Пост успешно отправлен. Память сохранена в {db_file}")
    else:
        print(f"❌ Ошибка Telegram: {r.text}")

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else 'image'
    send_to_telegram(mode)
