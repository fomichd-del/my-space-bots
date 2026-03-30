import requests
import os
from deep_translator import GoogleTranslator

# --- ⚙️ НАСТРОЙКИ ---
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHANNEL_NAME = '@vladislav_space' 
# Если у тебя есть свой ключ NASA, вставь его сюда вместо DEMO_KEY
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
    # Убираем лишние параметры в конце ссылки (всё, что после знака вопроса)
    base_url = url.split("?")[0]
    
    # Превращаем технические embed-ссылки в обычные
    if "youtube.com/embed/" in base_url:
        return base_url.replace("youtube.com/embed/", "youtube.com/watch?v=")
    elif "player.vimeo.com/video/" in base_url:
        return base_url.replace("player.vimeo.com/video/", "vimeo.com/")
    
    return url

# --- 🌌 ПОЛУЧЕНИЕ ДАННЫХ ОТ NASA ---
def get_apod():
    url = f"https://api.nasa.gov/planetary/apod?api_key={NASA_API_KEY}"
    try:
        response = requests.get(url).json()
        return response
    except Exception as e:
        print(f"❌ Ошибка API NASA: {e}")
        return None

# --- 🚀 ОТПРАВКА В TELEGRAM ---
def send_to_telegram(text, media_url, media_type):
    if media_type == "image":
        api_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
        payload = {
            'chat_id': CHANNEL_NAME, 
            'photo': media_url, 
            'caption': text, 
            'parse_mode': 'HTML'
        }
    else:
        # 📺 Для видео исправляем ссылку и отправляем как текст
        fixed_url = fix_video_link(media_url)
        api_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        full_text = f"{text}\n\n📺 <b>Смотреть видео:</b> {fixed_url}"
        payload = {
            'chat_id': CHANNEL_NAME, 
            'text': full_text, 
            'parse_mode': 'HTML'
        }
        
    response = requests.post(api_url, data=payload)
    if response.status_code == 200:
        print("✅ Материал дня успешно отправлен!")
    else:
        print(f"❌ Ошибка отправки: {response.text}")

# --- ⚙️ ОСНОВНОЙ ЦИКЛ ---
if __name__ == '__main__':
    print("--- 🔭 Запуск поиска NASA ---")
    data = get_apod()
    
    if data:
        # Извлекаем данные
        title_en = data.get('title', 'Без названия')
        desc_en = data.get('explanation', '')
        media_url = data.get('url', '')
        media_type = data.get('media_type', 'image') 

        # Переводим текст
        title_ru = translate_to_russian(title_en)
        desc_ru = translate_to_russian(desc_en)

        # Собираем сообщение
        message = (
            f"🌌 <b>{title_ru}</b>\n\n"
            f"📝 {desc_ru}\n\n"
            f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
        )

        # Отправляем
        send_to_telegram(message, media_url, media_type)
