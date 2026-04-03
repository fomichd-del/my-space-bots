import requests
import os
import random
from datetime import datetime, timedelta
from deep_translator import GoogleTranslator

# ============================================================
# ⚙️ НАСТРОЙКИ
# ============================================================
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
NASA_API_KEY   = os.getenv('NASA_API_KEY') or "DEMO_KEY"
CHANNEL_NAME   = '@vladislav_space'

translator = GoogleTranslator(source='auto', target='ru')

def translate_cam(cam_name):
    """Переводит технические названия камер на понятный язык"""
    cams = {
        "Mast Camera": "Основная панорамная камера (Mastcam)",
        "Front Hazard Avoidance Camera": "Передняя камера избегания препятствий (Hazcam)",
        "Rear Hazard Avoidance Camera": "Задняя камера избегания препятствий (Hazcam)",
        "Navigation Camera": "Навигационная камера (Navcam)",
        "Chemistry and Camera Complex": "Химический анализатор (ChemCam)",
        "Mars Hand Lens Imager": "Микроскоп для камней (MAHLI)",
        "Mars Descent Imager": "Камера для съемки при посадке (MARDI)"
    }
    return cams.get(cam_name, cam_name)

def get_mars_data():
    """Получает фото: либо свежее, либо крутое из архива."""
    # Список роверов и их максимальные Солы (примерно)
    rovers = {
        'perseverance': {'status': 'active', 'max_sol': 1100},
        'curiosity': {'status': 'active', 'max_sol': 4100},
        'opportunity': {'status': 'completed', 'max_sol': 5111},
        'spirit': {'status': 'completed', 'max_sol': 2200}
    }
    
    selected_rover = random.choice(list(rovers.keys()))
    print(f"🤖 Выбран ровер: {selected_rover}")
    
    # План А: Пытаемся найти СВЕЖЕЕ (только для активных)
    if rovers[selected_rover]['status'] == 'active':
        for day_offset in range(1, 10):
            date = (datetime.now() - timedelta(days=day_offset)).strftime('%Y-%m-%d')
            url = f"https://api.nasa.gov/mars-photos/api/v1/rovers/{selected_rover}/photos?earth_date={date}&api_key={NASA_API_KEY}"
            try:
                res = requests.get(url, timeout=15).json()
                if res.get('photos'):
                    photo = random.choice(res['photos'])
                    return photo, "🆕 СВЕЖИЙ КАДР С МАРСА"
            except: continue

    # План Б: СЛУЧАЙНЫЙ СОЛ (для всех, включая легендарные миссии)
    print(f"📂 Ищу крутой кадр в архиве {selected_rover}...")
    max_sol = rovers[selected_rover]['max_sol']
    random_sol = random.randint(1, max_sol)
    url = f"https://api.nasa.gov/mars-photos/api/v1/rovers/{selected_rover}/photos?sol={random_sol}&api_key={NASA_API_KEY}"
    
    try:
        res = requests.get(url, timeout=15).json()
        if res.get('photos'):
            photo = random.choice(res['photos'])
            return photo, "📜 ЛЕГЕНДАРНЫЕ МИССИИ"
    except: pass
    
    return None, None

def send_mars_post():
    photo, tag = get_mars_data()
    if not photo:
        print("❌ Не удалось получить фото Марса")
        return

    # Данные
    rover_name = photo['rover']['name']
    cam_name = translate_cam(photo['camera']['full_name'])
    earth_date = photo['earth_date']
    sol = photo['sol']
    img_url = photo['img_src'].replace("http://", "https://")

    # Текст как в боте Земли
    caption = (
        f"🪐 <b>{tag}</b>\n"
        f"─────────────────────\n\n"
        f"🤖 Ровер: <b>{rover_name}</b>\n"
        f"📸 Камера: <b>{cam_name}</b>\n"
        f"📅 Дата: <b>{earth_date}</b> (Sol {sol})\n\n"
        f"Марсианские сутки (Сол) длятся на 40 минут дольше земных. "
        f"Этот снимок был передан на Землю через сеть дальней космической связи NASA. 📡\n\n"
        f"⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
        f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
    )

    # Отправка
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    payload = {'chat_id': CHANNEL_NAME, 'photo': img_url, 'caption': caption, 'parse_mode': 'HTML'}
    
    r = requests.post(url, data=payload)
    if r.status_code == 200:
        print(f"✅ Пост про Марс ({rover_name}) отправлен!")
    else:
        print(f"❌ Ошибка: {r.text}")

if __name__ == '__main__':
    print("--- 🏁 Старт Mars Bot ---")
    send_mars_post()
