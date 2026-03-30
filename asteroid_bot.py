import requests
import os
from datetime import datetime

# ============================================================
# ⚙️ НАСТРОЙКИ
# ============================================================
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
NASA_API_KEY   = os.getenv('NASA_API_KEY') or "DEMO_KEY"
CHANNEL_NAME   = '@vladislav_space'

# ============================================================
# 🔍 ЛОГИКА ПОИСКА АСТЕРОИДОВ
# ============================================================

def get_asteroid_report():
    """Связывается с NASA и анализирует угрозы на сегодня."""
    url = f"https://api.nasa.gov/neo/rest/v1/feed/today?detailed=true&api_key={NASA_API_KEY}"
    
    try:
        response = requests.get(url).json()
        today = datetime.now().strftime('%Y-%m-%d')
        asteroids = response['near_earth_objects'].get(today, [])
        
        if not asteroids:
            return "☄️ <b>АСТЕРОИДНЫЙ ПАТРУЛЬ</b>\nСегодня в окрестностях Земли пусто и спокойно. ✨"

        # Сбор статистики
        total_count = len(asteroids)
        hazards = []
        
        # Ищем самый крупный и самый близкий
        biggest = max(asteroids, key=lambda x: x['estimated_diameter']['meters']['estimated_diameter_max'])
        closest = min(asteroids, key=lambda x: float(x['close_approach_data'][0]['miss_distance']['kilometers']))
        
        # Проверка на опасность
        for obj in asteroids:
            if obj['is_potentially_hazardous_asteroid']:
                name = obj['name']
                # Извлекаем время сближения
                full_time = obj['close_approach_data'][0]['close_approach_date_full']
                time_only = full_time.split()[1] if full_time else "??:??"
                hazards.append(f"🚨 <b>{name}</b> — пик сближения в {time_only}")

        # Подготовка данных для текста
        dist_km = float(closest['close_approach_data'][0]['miss_distance']['kilometers'])
        dist_pretty = f"{round(dist_km):,}".replace(",", " ")
        size_m = round(biggest['estimated_diameter']['meters']['estimated_diameter_max'])

        # Сборка сообщения
        report = [
            "☄️ <b>АСТЕРОИДНЫЙ ПАТРУЛЬ</b>",
            f"\n✅ Обнаружено «гостей»: <b>{total_count}</b>",
            f"📏 Самый близкий пролетит в <b>{dist_pretty} км</b>",
            f"⚠ Максимальный размер сегодня: <b>≈{size_m} м</b>\n"
        ]

        if hazards:
            report.append("❗ <b>ПОТЕНЦИАЛЬНО ОПАСНЫЕ ОБЪЕКТЫ:</b>")
            report.extend(hazards)
            report.append("\n<i>*Эти объекты требуют особого внимания астрономов!</i>")
        else:
            report.append("🍀 Сегодня серьезных угроз не зафиксировано.")

        report.append("\n⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯")
        report.append("🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>")
        
        return "\n".join(report)

    except Exception as e:
        print(f"Ошибка: {e}")
        return "⚠️ Не удалось связаться с радарами NASA. Проверьте соединение."

def send_to_telegram(text):
    """Отправляет готовый отчет в канал."""
    api_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(api_url, data={
        'chat_id': CHANNEL_NAME,
        'text': text,
        'parse_mode': 'HTML',
        'disable_web_page_preview': True
    })

# ============================================================
# 🚀 ЗАПУСК
# ============================================================

if __name__ == '__main__':
    final_text = get_asteroid_report()
    send_to_telegram(final_text)
