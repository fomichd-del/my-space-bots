import requests
import os
import random
import sys
# Импортируем нашу базу данных
from base_fact_star import CONSTELLATIONS

# ============================================================
# ⚙️ НАСТРОЙКИ (ПОЛНЫЕ КООРДИНАТЫ)
# ============================================================
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHANNEL_NAME   = '@vladislav_space' 
BOT_USERNAME   = 'MartyAstrobot' 

# Твои данные GitHub
GITHUB_USER = "fomichd-del" 
REPO_NAME   = "my-space-bots"
FOLDER_NAME = "photo"

# Формируем ПРЯМУЮ ссылку для серверов Telegram
GITHUB_PHOTO_BASE = f"https://raw.githubusercontent.com/{GITHUB_USER}/{REPO_NAME}/main/{FOLDER_NAME}/"

# Укажи здесь количество фото, которые ты реально загрузил в папку
PHOTO_COUNT = 4 

def post_star_guide():
    print("🛰 [СИСТЕМА] Запуск раздельной трансляции...")

    if not TELEGRAM_TOKEN:
        print("❌ [ОШИБКА] TELEGRAM_TOKEN не найден в секретах GitHub!")
        return

    # Выбираем случайную цель из базы
    item = random.choice(CONSTELLATIONS)
    bot_link = f"https://t.me/{BOT_USERNAME}?start=get_map"
    
    # 1. ЗАГОЛОВОК ДЛЯ ФОТО (не более 1024 символов)
    photo_caption = (
        f"🚀 <b>ВНИМАНИЕ! КОСМИЧЕСКИЙ ПАТРУЛЬ!</b> 🚀\n"
        f"🌟✨🌟✨🌟✨🌟✨🌟✨🌟✨🌟\n\n"
        f"🛰 <i>Прием, юные штурманы! Обнаружена новая цель:</i> <b>{item['name_ru']} ({item['name_latin']})</b>"
    )

    # 2. ОСНОВНОЙ ТЕКСТ (не более 4096 символов)
    main_text = (
        f"📖 <b>А ВЫ ЗНАЛИ?</b>\n"
        f"{item['fact']}\n\n"
        f"🎯 <b>МИССИЯ НА СЕГОДНЯ:</b>\n"
        f"Ваша задача — активировать радар, получить координаты и попытаться найти цель на небе! Кто справится?\n\n"
        f"Выходите на улицу или балкон (⚠️ <b>ВНИМАНИЕ: соблюдаем предельную осторожность!</b>), "
        f"делайте фото и присылайте в комментарии! 🔭\n\n"
        f"<b>НАВИГАЦИЯ ШТУРМАНА:</b>\n"
        f"🛰 <b><a href='{bot_link}'>[ 📡 АКТИВИРОВАТЬ ОРБИТАЛЬНЫЙ РАДАР ]</a></b>\n"
        f"─────────────────────\n"
        f"🛸 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
    )

    # Выбираем случайное фото
    photo_num = random.randint(1, PHOTO_COUNT)
    photo_url = f"{GITHUB_PHOTO_BASE}{photo_num}.jpg"
    
    print(f"📸 [ИНФО] Пытаюсь отправить фото: {photo_url}")

    base_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
    
    try:
        # ШАГ 1: Отправляем фото
        photo_payload = {
            'chat_id': CHANNEL_NAME,
            'photo': photo_url,
            'caption': photo_caption,
            'parse_mode': 'HTML'
        }
        r_photo = requests.post(f"{base_url}/sendPhoto", json=photo_payload, timeout=25)
        
        if r_photo.status_code == 200:
            print(f"✅ [1/2] Фото успешно передано в канал.")
            
            # ШАГ 2: Отправляем текст вторым сообщением
            text_payload = {
                'chat_id': CHANNEL_NAME,
                'text': main_text,
                'parse_mode': 'HTML',
                'link_preview_options': {'is_disabled': True}
            }
            r_text = requests.post(f"{base_url}/sendMessage", json=text_payload, timeout=25)
            
            if r_text.status_code == 200:
                print(f"✅ [2/2] Текст с фактами опубликован!")
            else:
                print(f"❌ [ОШИБКА ТЕКСТА] {r_text.text}")
        else:
            print(f"❌ [ОШИБКА ФОТО] {r_photo.text}")
            print("🔄 Пробую отправить только текст без фото...")
            requests.post(f"{base_url}/sendMessage", json={'chat_id': CHANNEL_NAME, 'text': main_text, 'parse_mode': 'HTML'})
            
    except Exception as e:
        print(f"💥 Критический сбой: {e}")

if __name__ == '__main__':
    post_star_guide()
