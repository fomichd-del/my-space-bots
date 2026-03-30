import requests
import os
import json
import time
from datetime import datetime

# ============================================================
# ⚙️ НАСТРОЙКИ
# ============================================================
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
NASA_API_KEY   = os.getenv('NASA_API_KEY') or "DEMO_KEY"
CHANNEL_NAME   = '@vladislav_space'

def get_asteroid_data():
    """Получает данные с защитой от сбоев и повторными попытками."""
    url = f"https://api.nasa.gov/neo/rest/v1/feed/today?detailed=true&api_key={NASA_API_KEY}"
    
    for attempt in range(3):
        try:
            print(f"Попытка {attempt + 1}: Запрос данных от NASA...")
            response = requests.get(url, timeout=15)
            
            # Проверка статуса (Вариант 3)
            if response.status_code != 200:
                print(f"❌ Сервер NASA ответил статусом: {response.status_code}")
                if attempt < 2:
                    time.sleep(60)
                    continue
                return f"⚠️ NASA API недоступно (Ошибка {response.status_code})", None

            data = response.json()
            today = datetime.now().strftime('%Y-%m-%d')
            asteroids = data['near_earth_objects'].get(today, [])
            
            print(f"✅ Данные получены успешно. Обнаружено объектов: {len(asteroids)}")
            
            if not asteroids:
                return "☄️ <b>АСТЕРОИДНЫЙ ПАТРУЛЬ</b>\nСегодня в окрестностях Земли спокойно. ✨", None

            # Выбор главного героя (Опасность -> Размер)
            hazardous = [a for a in asteroids if a['is_potentially_hazardous_asteroid']]
            if hazardous:
                hero = max(hazardous, key=lambda x: x['estimated_diameter']['meters']['estimated_diameter_max'])
                is_danger = True
            else:
                hero = max(asteroids, key=lambda x: x['estimated_diameter']['meters']['estimated_diameter_max'])
                is_danger = False

            # Формирование текста
            dist = float(hero['close_approach_data'][0]['miss_distance']['kilometers'])
            size = round(hero['estimated_diameter']['meters']['estimated_diameter_max'])
            
            text = (
                f"☄️ <b>АСТЕРОИДНЫЙ ПАТРУЛЬ</b>\n\n"
                f"✅ Сегодня замечено объектов: <b>{len(asteroids)}</b>\n"
                f"🎯 В фокусе: <b>{hero['name']}</b>\n"
                f"📏 Размер: <b>≈{size} м</b>\n"
                f"🛣 Дистанция: <b>{round(dist):,} км</b>".replace(",", " ") + "\n\n"
            )
            
            if is_danger:
                text += "❗ <b>ВНИМАНИЕ: Объект потенциально опасен!</b>\n\n"
            
            text += "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
            text += "🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"

            # Кнопка Web App
            keyboard = {
                "inline_keyboard": [[{
                    "text": "🛰 Исследовать орбиту в 3D",
                    "web_app": {"url": f"https://ssd.jpl.nasa.gov/tools/sbdb_lookup.html#/?sstr={hero['neo_reference_id']}"}
                }]]
            }

            return text, keyboard

        except Exception as e:
            print(f"⚠️ Ошибка при попытке {attempt + 1}: {e}")
            if attempt < 2:
                time.sleep(60)
            else:
                return f"❌ Критическая ошибка после 3 попыток: {e}", None

def send_message(text, keyboard):
    """Отправка сообщения."""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        'chat_id': CHANNEL_NAME,
        'text': text,
        'parse_mode': 'HTML',
        'reply_markup': json.dumps(keyboard) if keyboard else None,
        'disable_web_page_preview': True
    }
    requests.post(url, data=payload)

if __name__ == '__main__':
    msg_text, msg_key = get_asteroid_data()
    if msg_text:
        send_message(msg_text, msg_key)
