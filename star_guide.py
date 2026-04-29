import requests
import os
import random
import sys
# Импортируем нашу базу данных
from base_fact_star import CONSTELLATIONS

# ============================================================
# ⚙️ НАСТРОЙКИ
# ============================================================
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHANNEL_NAME   = '@vladislav_space' 
BOT_USERNAME   = 'MartyAstrobot' 

# Ссылки на твои фото в GitHub
GITHUB_PHOTO_BASE = "https://raw.githubusercontent.com/USER/REPO/main/photos/"
PHOTO_COUNT = 5 

def post_star_guide():
    print("🛰 [СИСТЕМА] Подготовка раздельного пакета данных...")

    if not TELEGRAM_TOKEN:
        print("❌ [ОШИБКА] Токен не найден!")
        return

    item = random.choice(CONSTELLATIONS)
    bot_link = f"https://t.me/{BOT_USERNAME}?start=get_map"
    
    # 1. Короткий заголовок для фото (до 1024 знаков)
    photo_caption = (
        f"🚀 <b>ВНИМАНИЕ! КОСМИЧЕСКИЙ ПАТРУЛЬ!</b> 🚀\n"
        f"🌟✨🌟✨🌟✨🌟✨🌟✨🌟✨🌟\n\n"
        f"🛰 <i>Прием, юные штурманы! Обнаружена новая цель:</i> <b>{item['name_ru']} ({item['name_latin']})</b>"
    )

    # 2. Основной массив данных (до 4096 знаков)
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

    # Выбираем фото
    photo_num = random.randint(1, PHOTO_COUNT)
    photo_url = f"{GITHUB_PHOTO_BASE}{photo_num}.jpg"

    # --- ОТПРАВКА ---
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
            print(f"✅ [1/2] Фото цели {item['name_ru']} отправлено.")
            
            # ШАГ 2: Отправляем подробный текст вторым сообщением
            text_payload = {
                'chat_id': CHANNEL_NAME,
                'text': main_text,
                'parse_mode': 'HTML',
                'link_preview_options': {'is_disabled': True}
            }
            r_text = requests.post(f"{base_url}/sendMessage", json=text_payload, timeout=25)
            
            if r_text.status_code == 200:
                print(f"✅ [2/2] Подробные данные переданы в эфир!")
            else:
                print(f"❌ [ОШИБКА ТЕКСТА] {r_text.text}")
        else:
            print(f"❌ [ОШИБКА ФОТО] {r_photo.text}")
            
    except Exception as e:
        print(f"💥 Критическая ошибка связи: {e}")

if __name__ == '__main__':
    post_star_guide()
