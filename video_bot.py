import os
import telebot
from googleapiclient.discovery import build
import random
from datetime import datetime, timedelta
from deep_translator import GoogleTranslator
import re

# Настройки
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
CHANNEL_NAME = os.getenv('CHANNEL_NAME') or '@vladislav_space'

bot = telebot.TeleBot(TELEGRAM_TOKEN)
translator = GoogleTranslator(source='auto', target='ru')

SOURCES = {
    "NASA": "UCOV19_pU-Z58VdB1YfSkA3w",
    "SpaceX": "UCtI0Hodo5o5dUb67FeUjDeA",
    "Alpha Centauri": "UC6mD3sE6ZJ_W_7_xI0KxhSg",
    "ESA": "UCdq0byZ-STP8_7GisA5T-sQ"
}

# Фильтр политики
BANNED_KEYWORDS = ['война', 'санкции', 'политика', 'conflict', 'war', 'sanctions', 'politics', 'армия']

def is_safe(text):
    t = text.lower()
    return not any(word in t for word in BANNED_KEYWORDS)

def translate_safe(text, length=350):
    try:
        res = translator.translate(text)
        return res[:length] + "..." if len(res) > length else res
    except: return "Детали миссии доступны в прямом эфире."

def get_video_data():
    youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
    now_time = datetime.now().strftime("%H:%M")
    
    # 1. Поиск LIVE (Трансляции)
    print("Ищу активные эфиры...")
    search_queries = ['NASA Live', 'SpaceX Live', 'Space Mission Live']
    for q in search_queries:
        req = youtube.search().list(q=q, part='snippet', type='video', eventType='live', maxResults=2)
        res = req.execute()
        for item in res.get('items', []):
            if is_safe(item['snippet']['title']):
                title_ru = translator.translate(item['snippet']['title'])
                return {
                    'url': f"https://www.youtube.com/watch?v={item['id']['videoId']}",
                    'title': f"🔴 ПРЯМОЙ ЭФИР: {title_ru}",
                    'time_info': f"🕒 Идет сейчас (время замера: {now_time} МСК)",
                    'desc': translate_safe(item['snippet']['description']),
                    'is_live': True
                }

    # 2. Если LIVE нет — свежие новости
    print("Эфиров нет, ищу последние видео...")
    c_id = random.choice(list(SOURCES.values()))
    req = youtube.search().list(channelId=c_id, part='snippet', type='video', order='date', maxResults=5)
    res = req.execute()
    for item in res.get('items', []):
        if is_safe(item['snippet']['title']):
            title_ru = translator.translate(item['snippet']['title'])
            return {
                'url': f"https://www.youtube.com/watch?v={item['id']['videoId']}",
                'title': f"🚀 НОВОСТИ: {title_ru}",
                'time_info': "📅 Свежий выпуск",
                'desc': translate_safe(item['snippet']['description']),
                'is_live': False
            }
    return None

def post_daily_video():
    data = get_video_data()
    if not data: return

    # Плеер видео будет СВЕРХУ благодаря невидимой ссылке \u200b
    caption = (
        f"<a href='{data['url']}'>\u200b</a>"
        f"<b>{data['title']}</b>\n\n"
        f"🛰 <b>Статус:</b> {data['time_info']}\n\n"
        f"📖 <b>О миссии:</b>\n{data['desc']}\n\n"
        f"🔗 <a href='{data['url']}'>Смотреть трансляцию</a>\n\n"
        f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
    )

    # Отправляем сообщение с предпросмотром (окошком)
    bot.send_message(CHANNEL_NAME, caption, parse_mode='HTML', disable_web_page_preview=False)
    print("Пост опубликован!")

if __name__ == "__main__":
    post_daily_video()
