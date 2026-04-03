import requests
import os
import random
import json
from deep_translator import GoogleTranslator

# ============================================================
# ⚙️ НАСТРОЙКИ
# ============================================================
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHANNEL_NAME   = '@vladislav_space'

translator = GoogleTranslator(source='auto', target='ru')

# Список планет для "Планетарной рулетки"
PLANETS = [
    "Mercury planet", "Venus planet", "Mars planet", 
    "Jupiter planet", "Saturn planet", "Uranus planet", 
    "Neptune planet", "Pluto dwarf planet"
]

def get_planet_data():
    """Выбирает случайную планету и ищет её лучшее фото в NASA Image Library"""
    planet_query = random.choice(PLANETS)
    planet_name_simple = planet_query.split()[0] # Получаем чистое название
    
    # Поиск в официальной библиотеке NASA
    url = f"https://images-api.nasa.gov/search?q={planet_query}&media_type=image"
    
    try:
        print(f"📡 Ищу фото для планеты: {planet_name_simple}...")
        res = requests.get(url, timeout=20).json()
        items = res['collection']['items']
        
        # Берем случайное фото из первых 15 результатов (там самые качественные)
        item = random.choice(items[:15])
        
        img_url = item['links'][0]['href']
        title_en = item['data'][0]['title']
        desc_en = item['data'][0].get('description', '')

        # Перевод на русский
        print(f"📝 Перевожу описание...")
        title_ru = translator.translate(title_en)
        
        # Берем первые 2-3 предложения описания
        short_desc_en = '. '.join(desc_en.split('.')[:3]) + '.'
        desc_ru = translator.translate(short_desc_en)

        caption = (
            f"🪐 <b>ПЛАНЕТА ДНЯ: {title_ru.upper()}</b>\n"
            f"─────────────────────\n\n"
            f"📖 <b>Интересный факт:</b>\n{desc_ru}\n\n"
            f"🔭 <i>Этот снимок был сделан одной из межпланетных станций NASA во время исследования нашей системы.</i>\n\n"
            f"⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
            f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
        )
        
        return img_url, caption
        
    except Exception as e:
        print(f"❌ Ошибка поиска планеты: {e}")
        return None, None

def send_to_telegram():
    img_url, caption = get_planet_data()
    
    if not img_url:
        print("📭 Не удалось найти подходящее фото.")
        return

    base_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    payload = {
        'chat_id': CHANNEL_NAME,
        'photo': img_url,
        'caption': caption,
        'parse_mode': 'HTML'
    }
    
    r = requests.post(base_url, data=payload)
    if r.status_code == 200:
        print(f"✅ Пост про планету успешно отправлен!")
    else:
        print(f"❌ Ошибка Telegram: {r.text}")

if __name__ == '__main__':
    print("--- 🏁 Запуск Планетарного Бота ---")
    send_to_telegram()
