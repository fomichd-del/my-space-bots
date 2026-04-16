import requests
import os
import json
import random
from datetime import datetime, timezone
from deep_translator import GoogleTranslator

# ============================================================
# ⚙️ НАСТРОЙКИ
# ============================================================
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
NASA_API_KEY = os.getenv('NASA_API_KEY')
CHANNEL_NAME   = '@vladislav_space'
DB_FILE        = "db_launch.txt"

translator = GoogleTranslator(source='auto', target='ru')

# Список фактов (сокращено для примера, используй свой полный список из 51 факта)
MARTI_FACTS = [
    "В космосе абсолютная тишина, потому что там нет воздуха.",
    "На Венере солнце встает на западе.",
    "Закат на Марсе — синего цвета.",
    "Космос пахнет жареным стейком и горячим металлом."
]

def get_launch_data():
    print("🛰 Запрос данных из Space Devs API...")
    url = "https://ll.thespacedevs.com/2.2.0/launch/upcoming/?limit=5"
    try:
        res = requests.get(url, timeout=30)
        res.raise_for_status()
        return res.json().get('results', [])
    except Exception as e:
        print(f"❌ Ошибка API: {e}")
        return None

def main():
    if not TELEGRAM_TOKEN:
        print("❌ Ошибка: TELEGRAM_TOKEN не найден в Secrets!")
        return

    launches = get_launch_data()
    if not launches:
        print("📭 Новых запусков не найдено.")
        return

    now = datetime.now(timezone.utc)
    
    # Загружаем историю отправок
    sent_ids = []
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r') as f:
            sent_ids = [line.strip() for line in f.readlines()]

    for launch in launches:
        l_id = launch['id']
        name = launch['name']
        provider = launch['launch_service_provider']['name']
        net_str = launch['net']
        
        # Парсим дату запуска
        net = datetime.fromisoformat(net_str.replace('Z', '+00:00'))
        diff_minutes = (net - now).total_seconds() / 60
        
        print(f"🔎 Проверка: {name} (через {int(diff_minutes)} мин)")

        # Логика: отправляем, если до запуска меньше 24 часов и мы его еще не постили
        if 0 < diff_minutes < 1440:
            memory_key = f"{l_id}_24h"
            
            if memory_key in sent_ids:
                print(f"✅ Уведомление для {l_id} уже было отправлено ранее.")
                continue

            print(f"🚀 Готовим пост для: {name}")
            
            # Перевод описания
            mission_desc = launch.get('mission', {}).get('description', 'Научная миссия.')
            try:
                desc_ru = translator.translate(mission_desc)
                provider_ru = translator.translate(provider)
            except:
                desc_ru, provider_ru = mission_desc, provider

            # Ссылка на видео
            video_url = launch['vidURLs'][0]['url'] if launch.get('vidURLs') else f"https://www.youtube.com/results?search_query={provider}+launch+live"
            
            caption = (
                f"🚀 <b>ГОТОВНОСТЬ 24 ЧАСА: {name.upper()}</b>\n"
                f"─────────────────────\n\n"
                f"🏢 <b>Организатор:</b> {provider_ru}\n"
                f"⏰ <b>Старт:</b> {net.strftime('%d.%m %H:%M')} UTC\n"
                f"📍 <b>Космодром:</b> {launch['pad']['location']['name']}\n\n"
                f"📖 <b>О МИССИИ:</b>\n{desc_ru}\n\n"
                f"🍿 <b>ТРАНСЛЯЦИЯ:</b> <a href='{video_url}'>СМОТРЕТЬ</a>\n\n"
                f"🐩 <b>СЕКРЕТ ОТ МАРТИ:</b>\n<i>{random.choice(MARTI_FACTS)}</i>\n\n"
                f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
            )

            payload = {
                "chat_id": CHANNEL_NAME,
                "text": caption,
                "parse_mode": "HTML",
                "disable_web_page_preview": False
            }
            
            tg_res = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", json=payload)
            
            if tg_res.status_code == 200:
                print("📩 Сообщение успешно отправлено в Telegram!")
                with open(DB_FILE, 'a') as f:
                    f.write(f"{memory_key}\n")
            else:
                print(f"❌ Ошибка Telegram: {tg_res.text}")
            
            break # Отправляем один пост за один прогон

if __name__ == '__main__':
    main()
