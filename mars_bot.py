import requests
import os
import json
from deep_translator import GoogleTranslator

# ============================================================
# ⚙️ НАСТРОЙКИ
# ============================================================
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
NASA_API_KEY   = os.getenv('NASA_API_KEY') or "DEMO_KEY"
CHANNEL_NAME   = '@vladislav_space'

translator = GoogleTranslator(source='auto', target='ru')

def get_space_data():
    """Получает самое свежее и важное фото Вселенной от NASA"""
    url = f"https://api.nasa.gov/planetary/apod?api_key={NASA_API_KEY}"
    
    try:
        print("📡 Связываюсь с архивом глубокого космоса...")
        res = requests.get(url, timeout=20).json()
        
        # Данные от NASA
        media_type = res.get('media_type') # image или video
        url_media = res.get('hdurl') or res.get('url')
        title_en = res.get('title', 'Космический объект')
        desc_en = res.get('explanation', '')

        print(f"📝 Перевожу данные об объекте: {title_en}")
        title_ru = translator.translate(title_en)
        
        # Сокращаем описание до 3-4 предложений для удобства чтения в Telegram
        sentences = desc_en.split('.')
        short_desc_en = '. '.join(sentences[:4]) + '.'
        desc_ru = translator.translate(short_desc_en)

        # Формируем текст
        caption = (
            f"🌌 <b>ГЛУБОКИЙ КОСМОС: ГЛАВНОЕ СЕГОДНЯ</b>\n"
            f"─────────────────────\n\n"
            f"🔭 <b>Объект:</b> {title_ru}\n\n"
            f"📖 <b>Что мы видим:</b>\n{desc_ru}\n\n"
            f"⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
            f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
        )
        
        return url_media, caption, media_type
        
    except Exception as e:
        print(f"❌ Ошибка получения данных: {e}")
        return None, None, None

def send_to_telegram():
    url_media, caption, media_type = get_space_data()
    
    if not url_media:
        print("📭 Не удалось получить контент.")
        return

    base_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
    
    if media_type == 'video':
        # Если сегодня пришло видео (например, таймлапс вращения Юпитера)
        print("📹 Обнаружено видео, отправляю ссылкой...")
        payload = {
            'chat_id': CHANNEL_NAME,
            'text': f"{caption}\n\n🎬 <b>Смотреть в движении:</b> {url_media}",
            'parse_mode': 'HTML'
        }
        requests.post(f"{base_url}/sendMessage", data=payload)
    else:
        # Если фото (как обычно)
        print("📸 Отправляю фото в высоком разрешении...")
        payload = {
            'chat_id': CHANNEL_NAME,
            'photo': url_media,
            'caption': caption,
            'parse_mode': 'HTML'
        }
        r = requests.post(f"{base_url}/sendPhoto", data=payload)
        if r.status_code != 200:
            print(f"❌ Ошибка Telegram: {r.text}")

if __name__ == '__main__':
    print("--- 🏁 Запуск Универсального Mars Bot ---")
    send_to_telegram()
    print("--- ✅ Завершено ---")
