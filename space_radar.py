import requests
import os
from datetime import datetime, timezone
from deep_translator import GoogleTranslator

# ============================================================
# ⚙️ НАСТРОЙКИ
# ============================================================
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHANNEL_NAME = '@vladislav_space'
DB_FILE = "sent_radar_lives.txt"

translator = GoogleTranslator(source='auto', target='ru')

# Заголовки для надежности (имитируем браузер)
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) SpaceRadar/1.0'}

# Список стоп-слов (мирный космос)
FORBIDDEN_WORDS = ['military', 'defense', 'spy', 'reconnaissance', 'missile', 'combat', 'war', 'weapon', 'nuke', 'army', 'война', 'оборона']

def is_military(text):
    if not text: return False
    return any(word in text.lower() for word in FORBIDDEN_WORDS)

def get_live_launch():
    """Сканирует ВСЕ источники трансляций (YouTube, X, Twitch, сайты агентств)"""
    url = "https://ll.thespacedevs.com/2.2.0/launch/upcoming/?limit=5"
    try:
        print("📡 Сканирую мировые частоты на наличие эфиров...")
        res = requests.get(url, headers=HEADERS, timeout=25).json()
        launches = res.get('results', [])
        
        sent_ids = []
        if os.path.exists(DB_FILE):
            with open(DB_FILE, 'r', encoding='utf-8') as f:
                sent_ids = f.read().splitlines()

        for launch in launches:
            l_id = str(launch['id'])
            if l_id in sent_ids: continue

            # 1. Фильтр на военную тематику
            mission_desc = launch.get('mission', {}).get('description', '')
            if is_military(mission_desc) or is_military(launch.get('name', '')):
                continue

            # 2. СОБИРАЕМ ВСЕ ССЫЛКИ НА ЭФИРЫ
            # База LL2 агрегирует ссылки со всех платформ (X, YT, Twitch, сайты)
            video_url = None
            vid_urls = launch.get('vidURLs', [])
            
            if vid_urls:
                # Приоритет 1: Ищем YouTube/Twitch (для видео-бара в ТГ)
                for v in vid_urls:
                    if any(x in v['url'] for x in ['youtube.com', 'youtu.be', 'twitch.tv', 'vimeo.com']):
                        video_url = v['url']
                        break
                
                # Приоритет 2: Если YouTube нет, берем ЛЮБУЮ первую ссылку (X, сайт агентства и т.д.)
                if not video_url:
                    video_url = vid_urls[0]['url']
            
            # 3. Если видео-ссылок нет совсем, проверяем infoURLs (официальные страницы миссий)
            if not video_url:
                info_urls = launch.get('infoURLs', [])
                if info_urls:
                    video_url = info_urls[0]['url']

            # Если видео/ссылки всё еще нет — пропускаем запуск до следующего раза
            if not video_url:
                print(f"⏳ Для {launch['name']} эфир пока не найден. Ждем...")
                continue

            # 4. ОФОРМЛЯЕМ ПОСТ
            rocket = launch['rocket']['configuration']['name']
            agency_name = launch['launch_service_provider']['name']
            agency_ru = translator.translate(agency_name)
            mission_ru = translator.translate(mission_desc) if mission_desc else "Научное исследование космоса."
            launch_time = datetime.fromisoformat(launch['net'].replace('Z', '+00:00'))

            caption = (
                f"🚀 <b>ПРЯМОЙ ЭФИР: {rocket.upper()}</b>\n"
                f"─────────────────────\n\n"
                f"🏢 <b>Организатор:</b> {agency_ru}\n"
                f"📍 <b>Космодром:</b> {launch['pad']['location']['name']}\n"
                f"📅 <b>Старт:</b> {launch_time.strftime('%d.%m.%Y %H:%M')} UTC\n\n"
                f"📖 <b>О МИССИИ:</b>\n{mission_ru}\n\n"
                f"🍿 <a href='{video_url}'><b>СМОТРЕТЬ ТРАНСЛЯЦИЮ</b></a>\n\n"
                f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
            )
            
            return caption, l_id, video_url, launch.get('image')

    except Exception as e:
        print(f"❌ Ошибка Радара: {e}")
    return None, None, None, None

def send():
    text, l_id, video_url, fallback_img = get_live_launch()
    if text:
        # Link Preview настроен так, чтобы показывать видео или большую картинку
        payload = {
            "chat_id": CHANNEL_NAME,
            "text": text,
            "parse_mode": "HTML",
            "link_preview_options": {
                "url": video_url,
                "prefer_large_media": True,
                "show_above_text": False
            }
        }
        
        r = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", json=payload)
        
        if r.status_code == 200:
            with open(DB_FILE, 'a', encoding='utf-8') as f:
                f.write(f"{l_id}\n")
            print(f"✅ Трансляция {l_id} успешно отправлена!")
        else:
            print(f"❌ Ошибка ТГ: {r.text}")

if __name__ == '__main__':
    send()
