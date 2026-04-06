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

def get_video_data():
    """Получает видео дня и превращает его в формат, который понимает Telegram"""
    url = f"https://api.nasa.gov/planetary/apod?api_key={NASA_API_KEY}"
    
    try:
        print("📡 Запрашиваю данные у NASA...")
        res = requests.get(url, timeout=20).json()
        
        if res.get('media_type') != 'video':
            print("ℹ️ Сегодня не видео. Пропускаю.")
            return None, None, None

        raw_url = res.get('url')
        
        # КРИТИЧЕСКИЙ МОМЕНТ: Превращаем embed-ссылку в полноценную ссылку YouTube.
        # Без этого "окно" (бар) видео часто не появляется.
        video_id = ""
        if 'youtube.com/embed/' in raw_url:
            video_id = raw_url.split('/embed/')[1].split('?')[0]
        elif 'youtu.be/' in raw_url:
            video_id = raw_url.split('youtu.be/')[1].split('?')[0]
        elif 'v=' in raw_url:
            video_id = raw_url.split('v=')[1].split('&')[0]
        
        url_video = f"https://www.youtube.com/watch?v={video_id}" if video_id else raw_url

        title_ru = translator.translate(res.get('title', 'Космическое видео'))
        
        # Сокращаем описание, чтобы пост не был слишком длинным
        desc_en = res.get('explanation', '')
        short_desc_en = '. '.join(desc_en.split('.')[:4]) + '.'
        desc_ru = translator.translate(short_desc_en)

        return url_video, title_ru, desc_ru
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return None, None, None

def send_to_telegram():
    url_video, title_ru, desc_ru = get_video_data()
    
    if not url_video:
        return

    # Мы ставим невидимый символ в начало, чтобы Telegram зацепился за ссылку.
    # Но в самом тексте НИКАКИХ лишних ссылок не будет.
    invisible_link = f'<a href="{url_video}">&#8203;</a>'

    caption = (
        f"{invisible_link}🎬 <b>ВИДЕО: {title_ru.upper()}</b>\n"
        f"─────────────────────\n\n"
        f"<b>О ЧЕМ РОЛИК:</b>\n"
        f"{desc_ru}\n\n"
        f"⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
        f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
    )

    print(f"📤 Отправляю пост с принудительным плеером видео...")
    base_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    
    # link_preview_options — это секретное оружие.
    # Оно говорит: "Бери только ссылку на видео, игнорируй ссылку на канал!"
    payload = {
        'chat_id': CHANNEL_NAME,
        'text': caption,
        'parse_mode': 'HTML',
        'link_preview_options': json.dumps({
            'url': url_video,             # Ссылка на видео для превью
            'prefer_large_media': True,   # Делаем окно видео БОЛЬШИМ (как на твоем фото)
            'show_above_text': False      # Плеер будет ПОД текстом
        })
    }
    
    r = requests.post(base_url, data=payload)
    if r.status_code == 200:
        print("✅ Готово! Теперь видео внизу в окошке.")
    else:
        # Если Telegram-бот старый и не знает link_preview_options, шлем по-старинке
        payload_old = {
            'chat_id': CHANNEL_NAME,
            'text': caption,
            'parse_mode': 'HTML',
            'disable_web_page_preview': False
        }
        requests.post(base_url, data=payload_old)

if __name__ == '__main__':
    send_to_telegram()
