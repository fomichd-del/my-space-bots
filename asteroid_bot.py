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
    """Получает данные и формирует 3 ключевых факта."""
    url = f"https://api.nasa.gov/neo/rest/v1/feed/today?detailed=true&api_key={NASA_API_KEY}"
    
    for attempt in range(3):
        try:
            print(f"Попытка {attempt + 1}: Запрос данных от NASA...")
            response = requests.get(url, timeout=15)
            
            if response.status_code != 200:
                print(f"❌ Сервер NASA ответил статусом: {response.status_code}")
                if attempt < 2:
                    time.sleep(60)
                    continue
                return None, None

            data = response.json()
            today = datetime.now().strftime('%Y-%m-%d')
            asteroids = data['near_earth_objects'].get(today, [])
            
            print(f"✅ Данные получены успешно. Обнаружено объектов: {len(asteroids)}")
            
            if not asteroids:
                return "☄️ <b>АСТЕРОИДНЫЙ ПАТРУЛЬ</b>\n\nСегодня в окрестностях Земли спокойно. ✨", None

            # Выбор самого интересного объекта
            hazardous = [a for a in asteroids if a['is_potentially_hazardous_asteroid']]
            if hazardous:
                hero = max(hazardous, key=lambda x: x['estimated_diameter']['meters']['estimated_diameter_max'])
                is_danger = True
            else:
                hero = max(asteroids, key=lambda x: x['estimated_diameter']['meters']['estimated_diameter_max'])
                is_danger = False

            # Данные объекта
            dist = float(hero['close_approach_data'][0]['miss_distance']['kilometers'])
            size = round(hero['estimated_diameter']['meters']['estimated_diameter_max'])
            name = hero['name'].replace("(", "").replace(")", "")

            # 📋 ФОРМИРУЕМ 3 ФАКТА
            status_icon = "⚠️" if is_danger else "✅"
            
            fact_1 = f"📊 Всего обнаружено объектов: <b>{len(asteroids)}</b>"
            fact_2 = f"🎯 Главный гость: <b>{name}</b> (≈<b>{size} м</b>)"
            fact_3 = f"🛣 Дистанция пролета: <b>{round(dist):,} км</b>".replace(",", " ")

            text = (
                f"☄️ <b>АСТЕРОИДНЫЙ ПАТРУЛЬ</b>\n"
                f"─────────────────────\n\n"
                f"<b>ГЛАВНЫЕ ФАКТЫ:</b>\n\n"
                f"{fact_1}\n\n"
                f"{fact_2}\n\n"
                f"{fact_3}\n\n"
                f"{status_icon} <b>Статус: " + ("ОПАСЕН" if is_danger else "БЕЗОПАСЕН") + "</b>\n\n"
                f"⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
                f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
            )

            # Исправленная кнопка: используем "url" вместо "web_app"
            keyboard = {
                "inline_keyboard": [[{
                    "text": "🛰 Исследовать орбиту в 3D",
                    "url": f"https://ssd.jpl.nasa.gov/tools/sbdb_lookup.html#/?sstr={hero['neo_reference_id']}"
                }]]
            }

            return text, keyboard

        except Exception as e:
            print(f"⚠️ Ошибка: {e}")
            if attempt < 2: time.sleep(60)
            else: return None, None

def send_message(text, keyboard):
    """Отправка сообщения с проверкой результата."""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        'chat_id': CHANNEL_NAME,
        'text': text,
        'parse_mode': 'HTML',
        'reply_markup': json.dumps(keyboard) if keyboard else None,
        'disable_web_page_preview': True
    }
    r = requests.post(url, data=payload)
    
    print(f"📡 Статус отправки в Telegram: {r.status_code}")
    if r.status_code != 200:
        print(f"📋 Ответ сервера: {r.text}")

if __name__ == '__main__':
    msg_text, msg_key = get_asteroid_data()
    if msg_text:
        send_message(msg_text, msg_key)
