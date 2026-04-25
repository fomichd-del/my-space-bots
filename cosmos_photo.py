import requests
import os
import sys
import json
import re
import time
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
    """Превращает 'embed' ссылки NASA в обычные ссылки YouTube для Telegram"""
    if 'youtube.com/embed/' in url:
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
    """Основная логика отправки с фиксом комментариев и видео сверху"""
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

    # --- СБОРКА ТЕКСТА ---
    prefix = "🎬 <b>ВИДЕО:</b> " if target_type == 'video' else "🌌 "
    header = f"{prefix}<b>{ru_title.upper()}</b>\n─────────────────────\n\n"
    body = f"<b>ГЛАВНОЕ:</b>\n\n{facts}\n\n"
    footer = f"✨ <b>Больше космоса:</b>\n👉 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
    full_text = header + body + footer

    # --- ЛОГИКА ОТПРАВКИ ---
    if target_type == 'image':
        # Для фото используем обычный метод (комментарии обычно работают без 2-х шагов, если нет кнопок)
        payload = {
            'chat_id': CHANNEL_NAME,
            'photo': data.get('url'),
            'caption': full_text,
            'parse_mode': 'HTML'
        }
        r = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto", json=payload)
    else:
        # --- РЕЖИМ ВИДЕО (ДВУХЭТАПНЫЙ ФИКС ДЛЯ КОММЕНТАРИЕВ) ---
        video_url = clean_video_url(data.get('url'))
        
        # Шаг 1: Отправляем базовый текст БЕЗ превью и ссылок (Активируем комментарии)
        payload_init = {
            'chat_id': CHANNEL_NAME,
            'text': full_text,
            'parse_mode': 'HTML',
            'link_preview_options': {'is_disabled': True}
        }
        r_init = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", json=payload_init)
        
        if r_init.status_code == 200:
            msg_id = r_init.json()['result']['message_id']
            time.sleep(1) # Короткая пауза для системной связи
            
            # Шаг 2: Редактируем, добавляя невидимую ссылку и плеер СВЕРХУ
            hidden_link = f"<a href='{video_url}'>\u200b</a>"
            payload_edit = {
                'chat_id': CHANNEL_NAME,
                'message_id': msg_id,
                'text': hidden_link + full_text,
                'parse_mode': 'HTML',
                'link_preview_options': {
                    'is_disabled': False,
                    'url': video_url,
                    'show_above_text': True,
                    'prefer_large_media': True
                }
            }
            r = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/editMessageText", json=payload_edit)
        else:
            r = r_init

    # --- ЗАВЕРШЕНИЕ ---
    if r.status_code == 200:
        with open(db_file, 'w', encoding='utf-8') as f:
            f.write(current_id)
        print(f"✅ Пост успешно отправлен через ЦУП. Комментарии активированы.")
    else:
        print(f"❌ Ошибка Telegram: {r.text}")

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else 'image'
    send_to_telegram(mode)
