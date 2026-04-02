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

# Список только научных и официальных каналов
SOURCES = {
    "NASA": "UCOV19_pU-Z58VdB1YfSkA3w",
    "SpaceX": "UCtI0Hodo5o5dUb67FeUjDeA",
    "Alpha Centauri": "UC6mD3sE6ZJ_W_7_xI0KxhSg",
    "NASASpaceflight": "UCSUu1lih2nj6Z1qbd1E9Vag",
    "ESA": "UCdq0byZ-STP8_7GisA5T-sQ"
}

# ЧЕРНЫЙ СПИСОК (чтобы никакой политики)
BANNED_KEYWORDS = [
    'война', 'санкции', 'политика', 'conflict', 'war', 'sanctions', 
    'politics', 'украин', 'росс', 'армия', 'army', 'military'
]

def is_safe(text):
    """Проверяет текст на отсутствие политики"""
    t = text.lower()
    return not any(word in t for word in BANNED_KEYWORDS)

def translate_safe(text, length=350):
    """Перевод и краткое описание"""
    try:
        res = translator.translate(text)
        return res[:length] + "..." if len(res) > length else res
    except: return "Смотрите подробности в видео миссии."

def parse_mission(title, desc):
    """Парсинг деталей миссии"""
    t_ru = translator.translate(title)
    
    # Пытаемся найти место
    place = "Космический центр"
    for loc in ["Кеннеди", "Байконур", "Канаверал", "Бока-Чика", "Vandenberg", "Starbase"]:
        if loc.lower() in title.lower() or loc.lower() in desc.lower():
            place = loc
            break
            
    mission = "Научное исследование"
    if "Artemis" in title or "Артемида" in t_ru: mission = "Миссия Artemis (Луна)"
    elif "Starship" in title: mission = "Испытание Starship"
    elif "Crew" in title: mission = "Пилотируемый полет"
    
    return t_ru, mission, place

def get_video_data():
    youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
    
    # 1. Сначала ищем LIVE (Артемида и т.д.)
    print("Ищу живые трансляции...")
    for q in ['NASA Live', 'SpaceX Live', 'Space Launch Live']:
        req = youtube.search().list(q=q, part='snippet', type='video', eventType='live', maxResults=3)
        res = req.execute()
        for item in res.get('items', []):
            if is_safe(item['snippet']['title']):
                v = item
                t, m, p = parse_mission(v['snippet']['title'], v['snippet']['description'])
                return {'url': f"https://www.youtube.com/watch?v={v['id']['videoId']}", 
                        'title': t, 'mission': m, 'place': p, 
                        'desc': translate_safe(v['snippet']['description']), 'type': "🔴 LIVE"}

    # 2. Если LIVE нет — свежие видео за 3 дня
    print("Эфиров нет, ищу свежие видео...")
    c_id = random.choice(list(SOURCES.values()))
    req = youtube.search().list(channelId=c_id, part='snippet', type='video', order='date', maxResults=5)
    res = req.execute()
    for item in res.get('items', []):
        if is_safe(item['snippet']['title']):
            v = item
            t, m, p = parse_mission(v['snippet']['title'], v['snippet']['description'])
            return {'url': f"https://www.youtube.com/watch?v={v['id']['videoId']}", 
                    'title': t, 'mission': m, 'place': p, 
                    'desc': translate_safe(v['snippet']['description']), 'type': "🚀 НОВОСТИ"}
    return None

def post_daily_video():
    data = get_video_data()
    if not data: return

    # \u200b - невидимый символ, в который мы прячем ссылку на YouTube
    # Это заставит плеер появиться СВЕРХУ текста
    caption = (
        f"<a href='{data['url']}'>\u200b</a>"
        f"<b>{data['title']}</b>\n\n"
        f"🛰 <b>Миссия:</b> {data['mission']}\n"
        f"📍 <b>Место:</b> {data['place']}\n\n"
        f"📖 <b>О чем видео:</b>\n{data['desc']}\n\n"
        f"🔗 <a href='{data['url']}'>Открыть видео в YouTube</a>\n\n"
        f"🛰 <a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
    )

    # Важно: disable_web_page_preview=False, чтобы появилось окошко видео
    bot.send_message(CHANNEL_NAME, caption, parse_mode='HTML', disable_web_page_preview=False)
    print("Пост успешно опубликован!")

if __name__ == "__main__":
    post_daily_video()
