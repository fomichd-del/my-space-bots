import requests
import os
import random
import sys
# Импортируем нашу огромную базу данных
from base_fact_star import CONSTELLATIONS

# ============================================================
# ⚙️ НАСТРОЙКИ
# ============================================================
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHANNEL_NAME   = '@vladislav_space' 
BOT_USERNAME   = 'MartyAstrobot' 

# Ссылки на твои фото в GitHub (замени 'USER' и 'REPO' на свои данные)
# Или просто укажи прямые ссылки на фото, если они уже где-то лежат
GITHUB_PHOTO_BASE = "https://raw.githubusercontent.com/USER/REPO/main/photos/"
PHOTO_COUNT = 5 # Укажи, сколько фото у тебя в папке

def post_star_guide():
    print("🛰 [СИСТЕМА] Запуск орбитальной публикации...")

    if not TELEGRAM_TOKEN:
        print("❌ [ОШИБКА] Токен не найден!")
        return

    # Выбираем случайное созвездие из нашей новой базы
    item = random.choice(CONSTELLATIONS)
    bot_link = f"https://t.me/{BOT_USERNAME}?start=get_map"
    
    # Собираем текст поста
    header = (
        f"🚨 <b>ВНИМАНИЕ! КОСМИЧЕСКИЙ ПАТРУЛЬ!</b> 🚨\n"
        f"🌟✨🌟✨🌟✨🌟✨🌟✨🌟✨🌟\n\n"
        f"🛰 <i>Прием, юные штурманы! Ночное небо зажгло свои огни. Радары фиксируют повышенную звездную активность!</i>\n\n"
    )
    
    fact_block = (
        f"📖 <b>А ВЫ ЗНАЛИ? ({item['name_ru']} / {item['name_latin']})</b>\n"
        f"{item['fact']}\n\n"
    )

    mission = (
        f"🎯 <b>МИССИЯ НА СЕГОДНЯ:</b>\n"
        f"Ваша задача — активировать радар, получить координаты и попытаться найти свою цель на ночном небе! Кто справится?\n\n"
        f"Выходите во двор или на балкон (⚠️ <b>ВНИМАНИЕ: на балконе и у окон соблюдаем предельную осторожность! Без глупостей!</b>), "
        f"делайте фото неба и присылайте в комментарии! Посмотрим, кто сегодня первый захватит цель! 🔭\n\n"
    )

    navigation = (
        f"<b>НАВИГАЦИЯ ШТУРМАНА:</b>\n"
        f"🛰 <b><a href='{bot_link}'>[ 📡 АКТИВИРОВАТЬ ОРБИТАЛЬНЫЙ РАДАР ]</a></b>\n"
        f"─────────────────────\n\n"
    )

    footer = f"🛸 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
    
    full_caption = header + fact_block + mission + navigation + footer

    # Выбираем случайное фото из папки на GitHub
    photo_num = random.randint(1, PHOTO_COUNT)
    photo_url = f"{GITHUB_PHOTO_BASE}{photo_num}.jpg"

    payload = {
        'chat_id': CHANNEL_NAME,
        'photo': photo_url,
        'caption': full_caption,
        'parse_mode': 'HTML',
        'link_preview_options': {'is_disabled': True} 
    }

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    
    try:
        r = requests.post(url, json=payload, timeout=25)
        if r.status_code == 200:
            print(f"✅ [УСПЕХ] Пост про {item['name_ru']} отправлен!")
        else:
            print(f"❌ [ОШИБКА] {r.text}")
            # Запасной вариант без фото
            requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                          json={'chat_id': CHANNEL_NAME, 'text': full_caption, 'parse_mode': 'HTML'})
    except Exception as e:
        print(f"💥 Ошибка связи: {e}")

if __name__ == '__main__':
    post_star_guide()
