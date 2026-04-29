import requests
import os
import random
# Импортируем нашу базу данных
from base_fact_star import CONSTELLATIONS

# ============================================================
# ⚙️ НАСТРОЙКИ
# ============================================================
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHANNEL_NAME   = '@vladislav_space' 
BOT_USERNAME   = 'MartyAstrobot' 

GITHUB_USER = "fomichd-del" 
REPO_NAME   = "my-space-bots"
FOLDER_NAME = "photo"

# Прямая ссылка для Telegram
GITHUB_PHOTO_BASE = f"https://raw.githubusercontent.com/{GITHUB_USER}/{REPO_NAME}/main/{FOLDER_NAME}/"

# ❗ ВАЖНО: На твоем скрине всего 2 фото. Поставь столько, сколько реально лежит в папке!
PHOTO_COUNT = 2 

def post_star_guide():
    print("🛰 [СИСТЕМА] Старт трансляции v2.4...")

    if not TELEGRAM_TOKEN:
        print("❌ [ОШИБКА] Токен не найден!")
        return

    item = random.choice(CONSTELLATIONS)
    bot_link = f"https://t.me/{BOT_USERNAME}?start=get_map"
    
    # 1. ЗАГОЛОВОК ДЛЯ ФОТО (Лаконичный)
    photo_caption = f"🚀 <b>КОСМИЧЕСКИЙ ПАТРУЛЬ: ОБЪЕКТ ОБНАРУЖЕН!</b> 🚀"

    # 2. ОСНОВНОЙ ТЕКСТ (С названием в самом начале)
    main_text = (
        f"🔭 <b>СЕГОДНЯ ИЗУЧАЕМ: {item['name_ru'].upper()} ({item['name_latin'].upper()})</b>\n"
        f"🌟✨🌟✨🌟✨🌟✨🌟✨🌟✨🌟\n\n"
        f"📖 <b>А ВЫ ЗНАЛИ?</b>\n"
        f"{item['fact']}\n\n"
        f"🎯 <b>МИССИЯ НА СЕГОДНЯ:</b>\n"
        f"Активируйте радар, получите координаты и найдите цель на небе!\n\n"
        f"⚠️ <i>Соблюдайте осторожность на балконах и у окон!</i>\n\n"
        f"🛰 <b><a href='{bot_link}'>[ 📡 АКТИВИРОВАТЬ ОРБИТАЛЬНЫЙ РАДАР ]</a></b>\n\n"
        f"🛸 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
    )

    # Случайное фото (теперь точно из тех, что есть)
    photo_num = random.randint(1, PHOTO_COUNT)
    photo_url = f"{GITHUB_PHOTO_BASE}{photo_num}.jpg"
    
    print(f"📸 [ИНФО] Пытаюсь отправить: {photo_url}")

    base_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
    
    try:
        # Отправка фото
        photo_payload = {'chat_id': CHANNEL_NAME, 'photo': photo_url, 'caption': photo_caption, 'parse_mode': 'HTML'}
        r_photo = requests.post(f"{base_url}/sendPhoto", json=photo_payload, timeout=25)
        
        if r_photo.status_code == 200:
            print(f"✅ Фото прошло.")
            # Отправка текста
            text_payload = {'chat_id': CHANNEL_NAME, 'text': main_text, 'parse_mode': 'HTML', 'link_preview_options': {'is_disabled': True}}
            requests.post(f"{base_url}/sendMessage", json=text_payload, timeout=25)
            print(f"✅ Текст с названием опубликован.")
        else:
            print(f"❌ Ошибка фото: {r_photo.text}")
            # Если фото упало — шлем текст с названием в начале
            requests.post(f"{base_url}/sendMessage", json={'chat_id': CHANNEL_NAME, 'text': main_text, 'parse_mode': 'HTML'})
            
    except Exception as e:
        print(f"💥 Сбой системы: {e}")

if __name__ == '__main__':
    post_star_guide()
