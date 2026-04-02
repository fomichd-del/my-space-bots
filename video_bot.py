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

# Источники и фильтры
SOURCES = {
    "NASA": "UCOV19_pU-Z58VdB1YfSkA3w",
    "SpaceX": "UCtI0Hodo5o5dUb67FeUjDeA",
    "Alpha Centauri": "UC6mD3sE6ZJ_W_7_xI0KxhSg",
    "ESA": "UCdq0byZ-STP8_7GisA5T-sQ"
}

BANNED_KEYWORDS = ['война', 'санкции', 'политика', 'conflict', 'war', 'sanctions', 'politics', 'армия']

# Список тем для ежедневного видео в 19:00
THEMATIC_QUERIES = [
    "планеты солнечной системы документальный",
    "черные дыры простыми словами",
    "как устроена вселенная",
    "жизнь на мкс интересные факты",
    "будущее колонизации марса",
    "самые красивые туманности в космосе",
    "история полета гагарина",
    "телескоп джеймс уэбб открытия"
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
        summary = '. '.join(sentences[:3]).strip()
        return summary + "." if not summary.endswith('.') else summary
    except:
        return "Детали этого космического события смотрите в видео."

def get_video_data():
    youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
    now = datetime.utcnow()
    
    # 19:00 по Москве (UTC+3) — это 16:00 UTC на сервере GitHub
    # Если запуск попал в окно с 16:00 до 16:15
    is_evening_slot = (now.hour == 16 and now.minute < 15)
    now_time_str = now.strftime("%H:%M")

    # --- ПРИОРИТЕТ 1: РАДАР (Поиск LIVE прямо сейчас) ---
    print("Радар: ищу активные трансляции...")
    search_queries = ['NASA Live', 'SpaceX Live', 'Space Launch Live']
    for q in search_queries:
        req = youtube.search().list(q=q, part='snippet', type='video', eventType='live', maxResults=1)
        res = req.execute()
        if res.get('items'):
            item = res['items'][0]
            if is_safe(item['snippet']['title']):
                return {
                    'url': f"https://www.youtube.com/watch?v={item['id']['videoId']}",
                    'title': f"🔴 ПРЯМОЙ ЭФИР: {translator.translate(item['snippet']['title'])}",
                    'status': f"🕒 Идет сейчас (время: {now_time_str})",
                    'desc': format_description(item['snippet']['description']),
                    'label': "Цель: Прямое наблюдение за событием."
                }

    # --- ПРИОРИТЕТ 2: ВЕЧЕРНИЙ ПОСТ (В 19:00, если нет эфира) ---
    if is_evening_slot:
        print("Вечерний слот: ищу тематическое видео...")
        query = random.choice(THEMATIC_QUERIES)
        req = youtube.search().list(q=query, part='snippet', type='video', maxResults=5, relevanceLanguage='ru')
        res = req.execute()
        if res.get('items'):
            item = random.choice(res['items'])
            if is_safe(item['snippet']['title']):
                return {
                    'url': f"https://www.youtube.com/watch?v={item['id']['videoId']}",
                    'title': f"🌌 ВЕЧЕРНИЙ КОСМОС: {translator.translate(item['snippet']['title'])}",
                    'status': "🕒 Ежедневный тематический выпуск",
                    'desc': format_description(item['snippet']['description']),
                    'label': "Зачем: Узнаем больше о тайнах Вселенной."
                }

    return None

def post_video():
    data = get_video_data()
    if not data:
        print("Активных трансляций нет, и сейчас не время для вечернего поста.")
        return

    # Невидимая ссылка для плеера сверху
    hidden_link = f"<a href='{data['url']}'>\u200b</a>"
    
    caption = (
        f"{hidden_link}<b>{data['title']}</b>\n\n"
        f"🛰 <b>Статус:</b> {data['status']}\n\n"
        f"🔹 <b>Что происходит:</b>\n{data['desc']}\n\n"
        f"🎯 <b>{data['label']}</b>\n\n"
        f"🔗 <a href='{data['url']}'>Смотреть на YouTube</a>\n\n"
        f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
    )

    bot.send_message(CHANNEL_NAME, caption, parse_mode='HTML', disable_web_page_preview=False)
    print(f"Пост опубликован: {data['title']}")

if __name__ == "__main__":
    post_video()
