import os
import telebot
import yt_dlp
from googleapiclient.discovery import build
import random
from datetime import datetime, timedelta
from deep_translator import GoogleTranslator

# Конфигурация
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
CHANNEL_NAME = os.getenv('CHANNEL_NAME') or '@vladislav_space'

bot = telebot.TeleBot(TELEGRAM_TOKEN)
translator = GoogleTranslator(source='auto', target='ru')

SOURCES = {
    "NASA": "UCOV19_pU-Z58VdB1YfSkA3w",
    "SpaceX": "UCtI0Hodo5o5dUb67FeUjDeA",
    "Alpha Centauri": "UC6mD3sE6ZJ_W_7_xI0KxhSg",
    "NASASpaceflight": "UCSUu1lih2nj6Z1qbd1E9Vag"
}

def translate_and_summarize(text, max_len=400):
    try:
        translated = translator.translate(text)
        return translated[:max_len] + "..." if len(translated) > max_len else translated
    except: return text[:max_len]

def get_video_data():
    youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
    
    # ПЛАН А: Глобальный поиск по ключевым словам (самый надежный для Live)
    print("Ищу активные трансляции по ключевым словам...")
    search_queries = ['NASA Live', 'SpaceX Live Launch', 'Rocket Launch Live', 'ISS Live Stream']
    
    for q in search_queries:
        # Ищем по всему YouTube активный Live про космос
        req = youtube.search().list(
            q=q, 
            part='snippet', 
            type='video', 
            eventType='live', 
            maxResults=3,
            relevanceLanguage='en'
        )
        res = req.execute()
        if res.get('items'):
            v = res['items'][0]
            print(f"НАЙДЕНО ЧЕРЕЗ ГЛОБАЛЬНЫЙ ПОИСК: {v['snippet']['title']}")
            return {
                'url': f"https://www.youtube.com/watch?v={v['id']['videoId']}",
                'title': "🔴 В ПРЯМОМ ЭФИРЕ: " + translator.translate(v['snippet']['title']),
                'desc': translate_and_summarize(v['snippet']['description']),
                'is_live': True
            }

    # ПЛАН Б: Если глобальный поиск ничего не дал, проверяем наши каналы
    print("Глобальный поиск не дал результатов. Проверяю список каналов...")
    for name, c_id in SOURCES.items():
        req = youtube.search().list(channelId=c_id, part='snippet', type='video', eventType='live')
        res = req.execute()
        if res.get('items'):
            v = res['items'][0]
            return {
                'url': f"https://www.youtube.com/watch?v={v['id']['videoId']}",
                'title': f"🛰 {name} В ЭФИРЕ: " + translator.translate(v['snippet']['title']),
                'desc': translate_and_summarize(v['snippet']['description']),
                'is_live': True
            }

    # ПЛАН В: Если стримов НЕТ вообще, ищем свежее короткое видео за сегодня
    print("Эфиров нет. Ищем свежее короткое видео...")
    three_days_ago = (datetime.utcnow() - timedelta(days=3)).isoformat() + "Z"
    for name, c_id in SOURCES.items():
        req = youtube.search().list(channelId=c_id, part='snippet', type='video', 
                                    publishedAfter=three_days_ago, order='date', maxResults=1)
        res = req.execute()
        if res.get('items'):
            v = res['items'][0]
            return {
                'url': f"https://www.youtube.com/watch?v={v['id']['videoId']}",
                'title': "🚀 СОБЫТИЕ: " + translator.translate(v['snippet']['title']),
                'desc': translate_and_summarize(v['snippet']['description']),
                'is_live': True
            }
    return None

def post_daily_video():
    data = get_video_data()
    if not data:
        print("Ничего не найдено.")
        return

    # Невидимый символ для превью НАВЕРХУ
    hidden_link = f"<a href='{data['url']}'>\u200b</a>"
    
    caption = (
        f"{hidden_link}<b>{data['title']}</b>\n\n"
        f"ℹ️ {data['desc']}\n\n"
        f"\n\n"
        f"<a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
    )

    # Всегда шлем через превью (окошко), чтобы видео было над текстом
    bot.send_message(CHANNEL_NAME, caption, parse_mode='HTML', disable_web_page_preview=False)
    print(f"Успешно опубликовано: {data['title']}")

if __name__ == "__main__":
    post_daily_video()
