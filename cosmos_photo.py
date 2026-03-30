import requests
import os
import sys
from deep_translator import GoogleTranslator

# --- ⚙️ НАСТРОЙКИ ---
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHANNEL_NAME = '@vladislav_space' 
NASA_API_KEY = "DEMO_KEY" 

# --- 🌐 ФУНКЦИЯ ПЕРЕВОДА ---
def translate_to_russian(text):
    try:
        if not text: return ""
        return GoogleTranslator(source='auto', target='ru').translate(text)
    except Exception as e:
        print(f"❌ Ошибка перевода: {e}")
        return text

# --- 🔧 ИСПРАВЛЕНИЕ ССЫЛОК ДЛЯ ТЕЛЕГРАМ-ПЛЕЕРА ---
def fix_video_link(url):
    base_url = url.split("?")[0]
    if "youtube.com/embed/" in base_url:
        return base_url.replace("youtube.com/embed/", "youtube.com/watch?v=")
    elif "player.vimeo.com/video/" in base_url:
        return base_url.replace("player.vimeo.com/video/", "vimeo.com/")
    return url

# --- 🌌 ПОЛУЧЕНИЕ 10 СЛУЧАЙНЫХ ПОСТОВ ОТ NASA ---
def get_random_apod():
    url = f"https://api.nasa.gov/planetary/apod?api_key={NASA_API_KEY}&count=10"
    try:
        response = requests.get(url).json()
        return response
    except Exception as e:
        print(f"❌ Ошибка API NASA: {e}")
        return []

# --- 🚀 ОТПРАВКА В TELEGRAM ---
def send_to_telegram(text, media_url, media_type):
    if media_type == "image":
        api_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
        payload = {'chat_id': CHANNEL_NAME, 'photo': media_url, 'caption': text, 'parse_mode': 'HTML'}
    else:
        fixed_url = fix_video_link(media_url)
        api_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        full_text = f"{text}\n\n📺 <b>Смотреть видео:</b> {fixed_url}"
        payload = {'chat_id': CHANNEL_NAME, 'text': full_text, 'parse_mode': 'HTML', 'disable_web_page_preview': False}
        
    response = requests.post(api_url, data=payload)
    if response.status_code == 200:
        print("✅ Материал успешно отправлен!")
    else:
        print(f"❌ Ошибка отправки: {response.text}")

# --- ⚙️ ОСНОВНОЙ ЦИКЛ ---
if __name__ == '__main__':
    # Читаем команду от сервера (image или video). По умолчанию ищем image.
    target_type = "image" 
    if len(sys.argv) > 1:
        target_type = sys.argv[1].lower() 

    print(f"--- 🔭 Поиск материала (Цель: {target_type}) ---")
    
    posts = get_random_apod()
    selected_post = None

    for post in posts:
        if post.get('media_type') == target_type:
            selected_post = post
            break

    if selected_post:
        title_en = selected_post.get('title', 'Без названия')
        desc_en = selected_post.get('explanation', '')
        media_url = selected_post.get('url', '')

        title_ru = translate_to_russian(title_en)
        desc_ru = translate_to_russian(desc_en)

        message = (
            f"🌌 <b>{title_ru}</b>\n\n"
            f"📝 {desc_ru}\n\n"
            f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
        )

        send_to_telegram(message, media_url, target_type)
    else:
        print(f"⚠️ Формат {target_type} не найден в этой выборке. Попробуем в следующий раз.")
