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
LOG_CHAT_ID = "-1003756164148"

GITHUB_USER = "fomichd-del" 
REPO_NAME   = "my-space-bots"
FOLDER_NAME = "photo"

# Прямая ссылка для серверов Telegram
GITHUB_PHOTO_BASE = f"https://raw.githubusercontent.com/{GITHUB_USER}/{REPO_NAME}/main/{FOLDER_NAME}/"

# ❗ ВАЖНО: На скрине было 2 фото. Если добавишь еще — поменяй цифру.
PHOTO_COUNT = 2 

def post_star_guide():
    print("🛰 [СИСТЕМА] Запуск звёздной охоты v2.5...")

    if not TELEGRAM_TOKEN:
        print("❌ [ОШИБКА] Токен не найден в секретах!")
        return

    # Выбираем случайное созвездие из базы
    item = random.choice(CONSTELLATIONS)
    bot_link = f"https://t.me/{BOT_USERNAME}?start=get_map"
    
    # 1. ЗАГОЛОВОК ДЛЯ ФОТО
    photo_caption = f"🛰 <b><a href='{bot_link}'>[ 📡 КОСМИЧЕСКИЙ ПАТРУЛЬ: ОБЪЕКТ ОБНАРУЖЕН!]</a></b>\n\n"

    # 2. ОСНОВНОЙ ТЕКСТ (Вариант 2: Звёздная охота)
    main_text = (
        f"🔭 <b>СЕГОДНЯ ИЗУЧАЕМ: {item['name_ru'].upper()} ({item['name_latin'].upper()})</b>\n"
        f"🌟✨🌟✨🌟✨🌟✨🌟✨🌟✨🌟\n\n"
        f"🐾 <b>МАРТИ ОБЪЯВЛЯЕТ ЗВЕЗДНУЮ ОХОТУ!</b>\n\n"
        f"📖 <b>А ВЫ ЗНАЛИ?</b>\n"
        f"{item['fact']}\n\n"
        f"🔭 <b>ВАШ ПЛАН ДЕЙСТВИЙ:</b>\n"
        f"Жмите на кнопку радара ниже, берите смартфоны и выходите на охоту! Как только поймаете нашу цель в кадр — сразу выкладывайте фото в комментарии. 📸\n\n"
        f"Ждем ваши личные снимки неба! Давайте соберём свою карту созвездий прямо здесь в комментариях! 👇\n\n"
        f"⚠️ <b>ВАЖНОЕ НАПОМИНАНИЕ:</b>\n"
        f"Друзья, космос огромен, но балкон — нет. Держитесь крепче и не перегибайтесь через перила. Безопасность превыше всего! 🛡\n\n"
        f"🛰 <b><a href='{bot_link}'>[ 📡 АКТИВИРОВАТЬ ОРБИТАЛЬНЫЙ РАДАР ]</a></b>\n\n"
        f"🛸 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
    )

    # Случайное фото
    photo_num = random.randint(1, PHOTO_COUNT)
    photo_url = f"{GITHUB_PHOTO_BASE}{photo_num}.jpg"
    
    print(f"📸 [ИНФО] Пытаюсь отправить цель: {item['name_ru']} (Фото: {photo_num}.jpg)")

    base_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
    
    try:
        # Отправка фото
        photo_payload = {
            'chat_id': CHANNEL_NAME, 
            'photo': photo_url, 
            'caption': photo_caption, 
            'parse_mode': 'HTML'
        }
        r_photo = requests.post(f"{base_url}/sendPhoto", json=photo_payload, timeout=25)
        
        if r_photo.status_code == 200:
            print(f"✅ Фото отправлено успешно.")
            # Отправка подробного текста
            text_payload = {
                'chat_id': CHANNEL_NAME, 
                'text': main_text, 
                'parse_mode': 'HTML', 
                'link_preview_options': {'is_disabled': True}
            }
            requests.post(f"{base_url}/sendMessage", json=text_payload, timeout=25)
            print(f"✅ Текст квеста опубликован.")
        else:
            print(f"❌ Ошибка фото: {r_photo.text}")
            # Резервная отправка только текста, если фото подвело
            requests.post(f"{base_url}/sendMessage", json={'chat_id': CHANNEL_NAME, 'text': main_text, 'parse_mode': 'HTML'})
            
    except Exception as e:
        print(f"💥 Критический сбой: {e}")

if __name__ == '__main__':
    post_star_guide()
