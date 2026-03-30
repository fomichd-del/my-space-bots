import requests
import os
import sys
from deep_translator import GoogleTranslator

# ==========================================
# ⚙️ НАСТРОЙКИ БОТА И КАНАЛА
# ==========================================
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHANNEL_NAME = '@vladislav_space' 
NASA_API_KEY = "DEMO_KEY" 


# ==========================================
# 🌐 ФУНКЦИИ ПЕРЕВОДА И ОБРАБОТКИ ССЫЛОК
# ==========================================
def translate_to_russian(text):
    """Переводит английский текст от NASA на русский."""
    try:
        if not text: 
            return ""
        return GoogleTranslator(source='auto', target='ru').translate(text)
    except Exception as e:
        print(f"❌ Ошибка перевода: {e}")
        return text


def fix_video_link(url):
    """Превращает ссылки в формат, который открывается в плеере Telegram."""
    base_url = url.split("?")[0]
    
    if "youtube.com/embed/" in base_url:
        return base_url.replace("youtube.com/embed/", "youtube.com/watch?v=")
        
    elif "player.vimeo.com/video/" in base_url:
        return base_url.replace("player.vimeo.com/video/", "vimeo.com/")
        
    return url


# ==========================================
# 🌌 РАБОТА С API NASA И ОТПРАВКА
# ==========================================
def get_random_apod():
    """Запрашивает у NASA 10 случайных постов."""
    url = f"https://api.nasa.gov/planetary/apod?api_key={NASA_API_KEY}&count=10"
    
    try:
        response = requests.get(url)
        return response.json()
    except Exception as e:
        print(f"❌ Ошибка API NASA: {e}")
        return []


def send_to_telegram(text, media_url, media_type):
    """Отправляет готовый пост в Telegram-канал."""
    if media_type == "image":
        api_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
        payload = {
            'chat_id': CHANNEL_NAME, 
            'photo': media_url, 
            'caption': text, 
            'parse_mode': 'HTML'
        }
    else:
        fixed_url = fix_video_link(media_url)
        api_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        full_text = f"{text}\n\n📺 <b>Смотреть видео:</b> {fixed_url}"
        payload = {
            'chat_id': CHANNEL_NAME, 
            'text': full_text, 
            'parse_mode': 'HTML'
        }
        
    res = requests.post(api_url, data=payload)
    print(f"Статус отправки: {res.status_code}")


# ==========================================
# 🚀 ЗАПУСК ОСНОВНОЙ ЛОГИКИ
# ==========================================
if __name__ == '__main__':
    # Определяем, что ищем сегодня: фото или видео
    target_type = sys.argv[1] if len(sys.argv) > 1 else "image"
    
    posts = get_random_apod()
    selected_post = None

    # Ищем в списке первый пост нужного формата
    for post in posts:
        if post.get('media_type') == target_type:
            selected_post = post
            break

    if selected_post:
        # Переводим заголовок и описание
        title_ru = translate_to_russian(selected_post.get('title', 'Космос'))
        desc_ru = translate_to_russian(selected_post.get('explanation', ''))
        url = selected_post.get('url', '')

        # Собираем красивый текст сообщения
        message = (
            f"<b>🌌 {title_ru.upper()}</b>\n\n"
            f"<b>📖 Описание:</b>\n"
            f"{desc_ru}\n\n"
            f"⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
            f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
        )
        
        send_to_telegram(message, url, target_type)
    else:
        print(f"Не удалось найти {target_type} в этой подборке.")
