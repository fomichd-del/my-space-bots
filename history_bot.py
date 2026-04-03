import requests
import os
import random
import json
from datetime import datetime
from deep_translator import GoogleTranslator

# ============================================================
# ⚙️ НАСТРОЙКИ
# ============================================================
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHANNEL_NAME   = '@vladislav_space'

translator = GoogleTranslator(source='auto', target='ru')

def get_history_event():
    """Ищет историческое событие в архивах NASA на текущий день."""
    now = datetime.now()
    # Формат запроса: "April 3" или "October 12"
    month_name = now.strftime("%B")
    day = now.day
    query = f"{month_name} {day} history"
    
    url = f"https://images-api.nasa.gov/search?q={query}&media_type=image"
    
    try:
        print(f"🔍 Ищу в архивах событие на {day} {month_name}...")
        res = requests.get(url, timeout=20).json()
        items = res['collection']['items']
        
        if not items:
            # Если на конкретный день нет, ищем просто по месяцу
            print("📭 На этот день пусто, ищу события месяца...")
            url = f"https://images-api.nasa.gov/search?q={month_name} space history&media_type=image"
            res = requests.get(url, timeout=20).json()
            items = res['collection']['items']

        # Берем случайное историческое фото из топа выдачи
        item = random.choice(items[:10])
        
        img_url = item['links'][0]['href']
        title_en = item['data'][0]['title']
        desc_en = item['data'][0].get('description', '')
        year = item['data'][0].get('date_created', '')[:4]

        # Перевод
        title_ru = translator.translate(title_en)
        # Ограничиваем описание, чтобы не было скучно
        short_desc_en = '. '.join(desc_en.split('.')[:3]) + '.'
        desc_ru = translator.translate(short_desc_en)

        caption = (
            f"📜 <b>ЭТОТ ДЕНЬ В ИСТОРИИ КОСМОСА</b>\n"
            f"─────────────────────\n\n"
            f"📅 <b>Год: {year}</b>\n"
            f"🚀 <b>Событие:</b> {title_ru}\n\n"
            f"📖 <b>Как это было:</b>\n{desc_ru}\n\n"
            f"⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
            f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
        )
        
        return img_url, caption
        
    except Exception as e:
        print(f"❌ Ошибка в архивах истории: {e}")
        return None, None

def send_to_telegram():
    img_url, caption = get_history_event()
    
    if not img_url: return

    base_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    payload = {
        'chat_id': CHANNEL_NAME,
        'photo': img_url,
        'caption': caption,
        'parse_mode': 'HTML'
    }
    
    r = requests.post(base_url, data=payload)
    if r.status_code == 200:
        print("✅ Исторический пост отправлен!")
    else:
        print(f"❌ Ошибка: {r.text}")

if __name__ == '__main__':
    send_to_telegram()
