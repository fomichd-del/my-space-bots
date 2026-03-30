import requests
import os
import sys
from deep_translator import GoogleTranslator

# ============================================================
# ⚙️ БЛОК НАСТРОЕК (Константы)
# ============================================================
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHANNEL_NAME   = '@vladislav_space' 
NASA_API_KEY   = "DEMO_KEY" 


# ============================================================
# 🌐 ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ (Перевод и ссылки)
# ============================================================

def translate_to_russian(text):
    """Переводит текст NASA на русский язык."""
    try:
        if not text: 
            return ""
        return GoogleTranslator(source='auto', target='ru').translate(text)
    except Exception as e:
        print(f"❌ Ошибка перевода: {e}")
        return text


def fix_video_link(url):
    """Адаптирует ссылки для видеоплеера Telegram."""
    base_url = url.split("?")[0]
    
    if "youtube.com/embed/" in base_url:
        return base_url.replace("youtube.com/embed/", "youtube.com/watch?v=")
        
    if "player.vimeo.com/video/" in base_url:
        return base_url.replace("player.vimeo.com/video/", "vimeo.com/")
        
    return url


# ============================================================
# 🌌 ОСНОВНАЯ ЛОГИКА (NASA и Telegram)
# ============================================================

def get_random_posts():
    """Запрашивает список из 10 случайных объектов у NASA."""
    url = f"https://api.nasa.gov/planetary/apod?api_key={NASA_API_KEY}&count=10"
    
    try:
        response = requests.get(url)
        return response.json()
    except Exception as e:
        print(f"❌ Ошибка при запросе к NASA: {e}")
        return []


def send_post(text, media_url, media_type):
    """Отправляет готовое сообщение в твой канал."""
    if media_type == "image":
        method = "sendPhoto"
        payload = {
            'chat_id': CHANNEL_NAME, 
            'photo': media_url, 
            'caption': text, 
            'parse_mode': 'HTML'
        }
    else:
        method = "sendMessage"
        video_url = fix_video_link(media_url)
        payload = {
            'chat_id': CHANNEL_NAME, 
            'text': f"{text}\n\n📺 <b>Видео:</b> {video_url}", 
            'parse_mode': 'HTML'
        }
        
    api_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/{method}"
    res = requests.post(api_url, data=payload)
    print(f"📤 Статус отправки: {res.status_code}")


# ============================================================
# 🚀 ТОЧКА ЗАПУСКА СКРИПТА
# ============================================================

if __name__ == '__main__':
    # 1. Определяем цель: "image" или "video" (берем из команды запуска)
    target = sys.argv[1] if len(sys.argv) > 1 else "image"
    
    # 2. Получаем данные от NASA
    all_posts = get_random_posts()
    found_post = None

    # 3. Ищем первый подходящий пост
    for p in all_posts:
        if p.get('media_type') == target:
            found_post = p
            break

    # 4. Если нашли — оформляем и отправляем
    if found_post:
        title_ru = translate_to_russian(found_post.get('title', 'Космос'))
        desc_ru  = translate_to_russian(found_post.get('explanation', ''))
        
        content = (
            f"<b>🌌 {title_ru.upper()}</b>\n\n"
            f"<b>📖 Описание:</b>\n{desc_ru}\n\n"
            f"⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
            f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
        )
        
        send_post(content, found_post.get('url', ''), target)
    else:
        print(f"⚠️ Не удалось найти подходящий тип: {target}")
