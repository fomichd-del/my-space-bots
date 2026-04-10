import requests
import os
import json
import random
from datetime import datetime, timezone
from deep_translator import GoogleTranslator

# --- ⚙️ НАСТРОЙКИ ---
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHANNEL_NAME = '@vladislav_space'
DB_FILE = "sent_radar_lives.txt"

translator = GoogleTranslator(source='auto', target='ru')

# Ключевые слова для фильтрации (никакой войны и политики)
FORBIDDEN_WORDS = [
    'military', 'defense', 'spy', 'reconnaissance', 'missile', 'combat', 
    'war', 'weapon', 'nuke', 'pentagon', 'securing', 'army', 'война', 'оборона'
]

def is_military(text):
    """Проверяет, нет ли в описании военной тематики"""
    if not text: return False
    return any(word in text.lower() for word in FORBIDDEN_WORDS)

def get_global_launches():
    """Запрашивает ближайшие запуски со всего мира"""
    # Запрашиваем 5 ближайших, чтобы выбрать подходящий не военный
    url = "https://ll.thespacedevs.com/2.2.0/launch/upcoming/?limit=5"
    
    try:
        print("📡 Сканирую космодромы мира...")
        response = requests.get(url, timeout=25)
        if response.status_code != 200:
            return None, None

        data = response.json()
        launches = data.get('results', [])
        
        for launch in launches:
            launch_id = launch['id']
            
            # 1. Проверка памяти
            if os.path.exists(DB_FILE):
                with open(DB_FILE, 'r', encoding='utf-8') as f:
                    if launch_id in f.read(): continue

            # 2. Получаем данные
            mission = launch.get('mission')
            mission_desc = mission.get('description', '') if mission else "Описание миссии готовится."
            
            # 3. ФИЛЬТР: Пропускаем военные и секретные запуски
            if is_military(mission_desc) or is_military(launch['name']):
                print(f"⏭ Пропускаю военный/политический запуск: {launch['name']}")
                continue

            # 4. Собираем информацию
            rocket_name = launch['rocket']['configuration']['name']
            agency_name = launch['launch_service_provider']['name']
            location = launch['pad']['location']['name']
            launch_time = datetime.fromisoformat(launch['net'].replace('Z', '+00:00'))
            img_url = launch.get('image')
            
            # Ищем видео-ссылку (YouTube приоритет для видео-бара)
            video_url = None
            vid_urls = launch.get('vidURLs', [])
            if vid_urls:
                video_url = vid_urls[0].get('url')

            # 5. Перевод
            print(f"📝 Перевожу данные миссии: {launch['name']}...")
            mission_ru = translator.translate(mission_desc)
            agency_ru = translator.translate(agency_name)

            # 6. ОФОРМЛЕНИЕ
            # Ставим видео-ссылку в самое начало или конец, чтобы ТГ создал видео-бар
            caption = (
                f"🚀 <b>МИРОВОЙ ЗАПУСК: {rocket_name.upper()}</b>\n"
                f"─────────────────────\n\n"
                f"🏢 <b>Организатор:</b> {agency_ru}\n"
                f"🎯 <b>Миссия:</b> {mission.get('name') if mission else 'Научная'}\n"
                f"📍 <b>Космодром:</b> {location}\n"
                f"📅 <b>Дата старта:</b> {launch_time.strftime('%d.%m.%Y %H:%M')} UTC\n\n"
                f"📖 <b>ЧТО И ДЛЯ ЧЕГО:</b>\n{mission_ru}\n\n"
                f"🍿 <a href='{video_url if video_url else 'https://t.me/vladislav_space'}'><b>ОТКРЫТЬ ВИДЕО-ТРАНСЛЯЦИЮ</b></a>\n\n"
                f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
            )
            
            return caption, launch_id, img_url, video_url

    except Exception as e:
        print(f"❌ Ошибка радара: {e}")
        return None, None, None, None
    return None, None, None, None

def send():
    text, launch_id, img_url, video_url = get_global_launches()
    
    if text:
        # Для видео-бара используем sendMessage с Link Preview
        payload = {
            "chat_id": CHANNEL_NAME,
            "text": text,
            "parse_mode": "HTML",
            "link_preview_options": {
                "url": video_url if video_url else img_url,
                "prefer_large_media": True,
                "show_above_text": False
            }
        }
        
        base_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        r = requests.post(base_url, json=payload)
        
        if r.status_code == 200:
            with open(DB_FILE, 'a', encoding='utf-8') as f:
                f.write(f"{launch_id}\n")
            print(f"✅ Запуск {launch_id} успешно добавлен в радар!")
        else:
            print(f"❌ Ошибка Telegram: {r.text}")

if __name__ == '__main__':
    send()
