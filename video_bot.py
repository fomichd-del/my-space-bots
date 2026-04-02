import os
import telebot
from googleapiclient.discovery import build
import random
from datetime import datetime
from deep_translator import GoogleTranslator
import re

# Настройки
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
CHANNEL_NAME = os.getenv('CHANNEL_NAME') or '@vladislav_space'

bot = telebot.TeleBot(TELEGRAM_TOKEN)
translator = GoogleTranslator(source='auto', target='ru')

# ГЛОБАЛЬНЫЕ ИСТОЧНИКИ (Весь мир)
SOURCES = {
    "NASA": "UCOV19_pU-Z58VdB1YfSkA3w",
    "SpaceX": "UCtI0Hodo5o5dUb67FeUjDeA",
    "Роскосмос": "UCOS_m87vNfS6E_5An_Ym2pA",
    "ESA (Европа)": "UCdq0byZ-STP8_7GisA5T-sQ",
    "ISRO (Индия)": "UC9fD-XU0sQG_uQZ7YtqO8pA",
    "JAXA (Япония)": "UCY8YJ_R6O7oXf0O88SSTK1w",
    "Alpha Centauri": "UC6mD3sE6ZJ_W_7_xI0KxhSg",
    "NASASpaceflight": "UCSUu1lih2nj6Z1qbd1E9Vag"
}

# Политический фильтр остается жестким
BANNED_KEYWORDS = ['война', 'санкции', 'политика', 'conflict', 'war', 'politics', 'армия', 'military']

THEMATIC_QUERIES = [
    "планеты солнечной системы", "черные дыры", "как устроена вселенная",
    "жизнь на мкс", "будущее колонизации марса", "история полета гагарина",
    "телескоп джеймс уэбб", "лунная база будущего"
]

def is_safe(text):
    t = text.lower()
    return not any(word in t for word in BANNED_KEYWORDS)

def format_description(text):
    try:
        text = re.sub(r'http\S+', '', text)
        text = re.sub(r'#\S+', '', text)
        translated = translator.translate(text)
        sentences = translated.split('. ')
        return '. '.join(sentences[:3]).strip() + "."
    except:
        return "Детали миссии доступны в прямом эфире."

def parse_mission_details(title, desc):
    """Распознает международные миссии и космодромы"""
    title_ru = translator.translate(title)
    
    # География запусков (Весь мир)
    locations = {
        "Байконур": ["Baikonur", "Байконур"],
        "Восточный": ["Vostochny", "Восточный"],
        "Кеннеди (США)": ["Kennedy", "KSC"],
        "Канаверал (США)": ["Canaveral"],
        "Куру (Французская Гвиана)": ["Kourou", "Guiana"],
        "Шрихарикота (Индия)": ["Sriharikota", "Satish Dhawan"],
        "Танегасима (Япония)": ["Tanegashima"],
        "Бока-Чика (Starbase)": ["Boca Chica", "Starbase"],
        "Плесецк": ["Plesetsk", "Плесецк"]
    }
    
    place = "Международный космодром"
    for p_name, keys in locations.items():
        if any(k.lower() in title.lower() or k.lower() in desc.lower() for k in keys):
            place = p_name
            break
            
    # Тип миссии
    mission = "Космическая миссия"
    if "Artemis" in title or "Артемида" in title_ru: mission = "Артемида (Луна)"
    elif "Soyuz" in title or "Союз" in title_ru: mission = "Полет корабля Союз"
    elif "Starship" in title: mission = "Испытание Starship"
    elif "Progress" in title or "Прогресс" in title_ru: mission = "Грузовой корабль"
    elif "Chandrayaan" in title: mission = "Индийская лунная миссия"
    
    return title_ru, mission, place

def get_video_data():
    youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
    now = datetime.utcnow()
    is_evening_slot = (now.hour == 16 and now.minute < 15) # 19:00 по Киеву/МСК
    
    # 1. МЕЖДУНАРОДНЫЙ РАДАР (Live прямо сейчас)
    print("Глобальный радар: ищу трансляции по всему миру...")
    # Ищем на английском и русском для максимального охвата
    search_queries = ['Space Launch Live', 'Запуск ракеты прямой эфир', 'NASA Live', 'Roscosmos Live']
    
    for q in search_queries:
        req = youtube.search().list(q=q, part='snippet', type='video', eventType='live', maxResults=2)
        res = req.execute()
        for item in res.get('items', []):
            if is_safe(item['snippet']['title']):
                title_ru, mission, place = parse_mission_details(item['snippet']['title'], item['snippet']['description'])
                return {
                    'url': f"https://www.youtube.com/watch?v={item['id']['videoId']}",
                    'title': f"🔴 ПРЯМОЙ ЭФИР: {title_ru}",
                    'status': f"🕒 Идет сейчас (время: {now.strftime('%H:%M')})",
                    'mission': mission,
                    'place': place,
                    'desc': format_description(item['snippet']['description']),
                    'label': "Глобальный мониторинг космических запусков."
                }

    # 2. ВЕЧЕРНИЙ ПОСТ (в 19:00, если нет эфира)
    if is_evening_slot:
        print("Вечерний слот: тематическое видео...")
        query = random.choice(THEMATIC_QUERIES)
        req = youtube.search().list(q=query, part='snippet', type='video', maxResults=5, relevanceLanguage='ru')
        res = req.execute()
        if res.get('items'):
            item = random.choice(res['items'])
            if is_safe(item['snippet']['title']):
                return {
                    'url': f"https://www.youtube.com/watch?v={item['id']['videoId']}",
                    'title': f"🌌 ВЕЧЕРНИЙ КОСМОС: {translator.translate(item['snippet']['title'])}",
                    'status': "📅 Ежедневный познавательный выпуск",
                    'mission': "Образование и наука",
                    'place': "Вся Вселенная",
                    'desc': format_description(item['snippet']['description']),
                    'label': "Расширяем горизонты знаний о космосе."
                }
    return None

def post_video():
    data = get_video_data()
    if not data: return

    hidden_link = f"<a href='{data['url']}'>\u200b</a>"
    caption = (
        f"{hidden_link}<b>{data['title']}</b>\n\n"
        f"🛰 <b>Статус:</b> {data['status']}\n"
        f"🚀 <b>Миссия:</b> {data['mission']}\n"
        f"📍 <b>Место:</b> {data['place']}\n\n"
        f"📖 <b>Что происходит:</b>\n{data['desc']}\n\n"
        f"🎯 <b>{data['label']}</b>\n\n"
        f"🔗 <a href='{data['url']}'>Смотреть на YouTube</a>\n\n"
        f"🛰 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
    )

    bot.send_message(CHANNEL_NAME, caption, parse_mode='HTML', disable_web_page_preview=False)
    print(f"Опубликовано: {data['title']}")

if __name__ == "__main__":
    post_video()
