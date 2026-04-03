import requests
import os
import json
from datetime import datetime, timedelta
from deep_translator import GoogleTranslator

# ============================================================
# ⚙️ НАСТРОЙКИ
# ============================================================
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
NASA_API_KEY   = os.getenv('NASA_API_KEY') or "DEMO_KEY"
CHANNEL_NAME   = '@vladislav_space'

translator = GoogleTranslator(source='auto', target='ru')

def should_be_silent():
    """Проверяет, нужно ли присылать без звука (с 22:00 до 07:00 по МСК)"""
    # GitHub работает по UTC. Москва — это UTC + 3.
    msk_now = datetime.utcnow() + timedelta(hours=3)
    return 22 <= msk_now.hour or msk_now.hour < 7

def get_video_data():
    """Получает видео дня от NASA (APOD)"""
    url = f"https://api.nasa.gov/planetary/apod?api_key={NASA_API_KEY}"
    
    try:
        print("📡 Запрашиваю данные у NASA...")
        res = requests.get(url, timeout=20).json()
        
        if res.get('media_type') != 'video':
            print("ℹ️ Сегодня у NASA не видео, а фото. Пропускаю запуск видео-бота.")
            return None, None, None

        url_video = res.get('url')
        title_en = res.get('title', 'Космическое видео')
        desc_en = res.get('explanation', '')

        print(f"📝 Перевожу заголовок: {title_en}")
        title_ru = translator.translate(title_en)
        
        # Берем первые 4 предложения описания для краткости
        sentences = desc_en.split('.')
        short_desc_en = '. '.join(sentences[:4]) + '.'
        desc_ru = translator.translate(short_desc_en)

        return url_video, title_ru, desc_ru
        
    except Exception as e:
        print(f"❌ Ошибка получения видео: {e}")
        return None, None, None

def send_to_telegram():
    url_video, title_ru, desc_ru = get_video_data()
    
    if not url_video:
        return

    # МАГИЯ: Прячем ссылку в невидимый символ \u200b
    # Это оставит видео-плеер внизу, но уберет длинную ссылку из текста
    invisible_link = f'<a href="{url_video}">\u200b</a>'

    caption = (
        f"{invisible_link}🎬 <b>ВИДЕО: {title_ru.upper()}</b>\n"
        f"─────────────────────\n\n"
        f"<b>О ЧЕМ РОЛИК:</b>\n"
        f"{desc_ru}\n\n"
        f"⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
        f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
    )

    print("📤 Отправляю чистое сообщение в Telegram...")
    base_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    
    payload = {
        'chat_id': CHANNEL_NAME,
        'text': caption,
        'parse_mode': 'HTML',
        'disable_web_page_preview': False, # Оставляем False, чтобы видео-плеер появился
        'disable_notification': should_be_silent()
    }
    
    r = requests.post(base_url, data=payload)
    if r.status_code == 200:
        print("✅ Видео успешно опубликовано без лишних ссылок!")
    else:
        print(f"❌ Ошибка Telegram: {r.text}")

if __name__ == '__main__':
    print("--- 🎬 Запуск Video Bot ---")
    send_to_telegram()
