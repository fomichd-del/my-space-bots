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

# Чистые научные источники
SOURCES = {
    "NASA": "UCOV19_pU-Z58VdB1YfSkA3w",
    "SpaceX": "UCtI0Hodo5o5dUb67FeUjDeA",
    "Alpha Centauri": "UC6mD3sE6ZJ_W_7_xI0KxhSg",
    "ESA": "UCdq0byZ-STP8_7GisA5T-sQ"
}

# Фильтр политики
BANNED_KEYWORDS = ['война', 'санкции', 'политика', 'conflict', 'war', 'sanctions', 'politics', 'армия', 'military']

def is_safe(text):
    t = text.lower()
    return not any(word in t for word in BANNED_KEYWORDS)

def format_description(text):
    """Делает описание коротким, понятным и структурированным"""
    try:
        # 1. Очистка от ссылок, хештегов и мусора
        text = re.sub(r'http\S+', '', text)
        text = re.sub(r'#\S+', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        
        # 2. Перевод
        translated = translator.translate(text)
        
        # 3. Берем первые 3-4 предложения (самая суть)
        sentences = translated.split('. ')
        summary = '. '.join(sentences[:3])
        if len(summary) < 50 and len(sentences) > 3:
            summary = '. '.join(sentences[:5])
            
        return summary + "." if not summary.endswith('.') else summary
    except:
        return "Следим за ходом ключевых событий в космосе в реальном времени."

def get_video_data():
    youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
    now_time = datetime.now().strftime("%H:%M")
    
    # 1. Поиск LIVE (Трансляции)
    search_queries = ['NASA Live', 'SpaceX Starship Live', 'Space Launch Live']
    for q in search_queries:
        req = youtube.search().list(q=q, part='snippet', type='video', eventType='live', maxResults=2)
        res = req.execute()
        for item in res.get('items', []):
            if is_safe(item['snippet']['title']):
                title_ru = translator.translate(item['snippet']['title'])
                return {
                    'url': f"https://www.youtube.com/watch?v={item['id']['videoId']}",
                    'title': f"🔴 ПРЯМОЙ ЭФИР: {title_ru}",
                    'status': f"🕒 Идет сейчас (время: {now_time})",
                    'desc': format_description(item['snippet']['description']),
                    'is_live': True
                }

    # 2. Если LIVE нет — свежие новости
    c_id = random.choice(list(SOURCES.values()))
    req = youtube.search().list(channelId=c_id, part='snippet', type='video', order='date', maxResults=5)
    res = req.execute()
    for item in res.get('items', []):
        if is_safe(item['snippet']['title']):
            title_ru = translator.translate(item['snippet']['title'])
            return {
                'url': f"https://www.youtube.com/watch?v={item['id']['videoId']}",
                'title': f"🚀 НОВОСТИ: {title_ru}",
                'status': "📅 Свежий выпуск",
                'desc': format_description(item['snippet']['description']),
                'is_live': False
            }
    return None

def post_daily_video():
    data = get_video_data()
    if not data: return

    # Невидимая ссылка для плеера НАВЕРХУ
    hidden_link = f"<a href='{data['url']}'>\u200b</a>"
    
    # Формируем информативный текст
    caption = (
        f"{hidden_link}<b>{data['title']}</b>\n\n"
        f"🛰 <b>Статус:</b> {data['status']}\n\n"
        f"🔹 <b>Что происходит:</b>\n{data['desc']}\n\n"
        f"🎯 <b>Цель:</b> Исследование космоса и развитие технологий.\n\n"
        f"🔗 <a href='{data['url']}'>Перейти к просмотру на YouTube</a>\n\n"
        f"🚀 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
    )

    bot.send_message(CHANNEL_NAME, caption, parse_mode='HTML', disable_web_page_preview=False)
    print(f"Готово: {data['title']}")

if __name__ == "__main__":
    post_daily_video()
