import os
import telebot
import requests
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
    "NASASpaceflight": "UCSUu1lih2nj6Z1qbd1E9Vag"
}

def clean_and_translate(text, length=450):
    """Качественный перевод и очистка описания"""
    try:
        # Убираем ссылки и лишние теги из описания YouTube
        text = re.sub(r'http\S+', '', text)
        translated = translator.translate(text)
        if len(translated) > length:
            translated = translated[:length].rsplit('.', 1)[0] + "."
        return translated
    except:
        return "Детали миссии доступны в видеообзоре."

def parse_mission_info(title, description):
    """Пытается вытащить данные о миссии, времени и месте"""
    title_ru = translator.translate(title)
    
    # Ищем место (примерные ключевые слова)
    locations = ["Кеннеди", "Байконур", "Канаверал", "Бока-Чика", "Куру", "Ванденберг", "Starbase"]
    place = "Космический центр (уточняется)"
    for loc in locations:
        if loc.lower() in title.lower() or loc.lower() in description.lower():
            place = loc
            break
            
    # Ищем миссию
    mission = "Исследовательская миссия"
    if "Artemis" in title or "Артемида" in title_ru: mission = "Artemis (Лунная программа)"
    elif "Starship" in title: mission = "Starship Flight Test"
    elif "Crew" in title: mission = "Пилотируемый полет"
    elif "Starlink" in title: mission = "Вывод спутников Starlink"

    # Время (из даты публикации или текста)
    time_str = datetime.now().strftime("%H:%M") + " (МСК)" # По умолчанию

    return title_ru, mission, time_str, place

def get_video_data():
    youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
    
    # 1. Поиск активных трансляций (самый приоритет)
    search_queries = ['NASA Live', 'SpaceX Starship Live', 'Artemis Live']
    for q in search_queries:
        req = youtube.search().list(q=q, part='snippet', type='video', eventType='live', maxResults=1)
        res = req.execute()
        if res.get('items'):
            v = res['items'][0]
            t, m, tm, p = parse_mission_info(v['snippet']['title'], v['snippet']['description'])
            return {
                'url': f"https://www.youtube.com/watch?v={v['id']['videoId']}",
                'img': v['snippet']['thumbnails']['high']['url'],
                'title': t, 'mission': m, 'time': tm, 'place': p,
                'desc': clean_and_translate(v['snippet']['description']),
                'type': "🔴 ПРЯМОЙ ЭФИР"
            }

    # 2. Если эфиров нет — свежие новости
    source_name = random.choice(list(SOURCES.keys()))
    req = youtube.search().list(channelId=SOURCES[source_name], part='snippet', type='video', order='date', maxResults=1)
    res = req.execute()
    if res.get('items'):
        v = res['items'][0]
        t, m, tm, p = parse_mission_info(v['snippet']['title'], v['snippet']['description'])
        return {
            'url': f"https://www.youtube.com/watch?v={v['id']['videoId']}",
            'img': v['snippet']['thumbnails']['high']['url'],
            'title': t, 'mission': m, 'time': "Опубликовано недавно", 'place': p,
            'desc': clean_and_translate(v['snippet']['description']),
            'type': "🚀 НОВОСТИ КОСМОСА"
        }
    return None

def post_daily_video():
    data = get_video_data()
    if not data: return

    # Формируем красивый текст
    caption = (
        f"{data['type']}\n"
        f"<b>{data['title']}</b>\n\n"
        f"🛰 <b>Миссия:</b> {data['mission']}\n"
        f"⏰ <b>Время старта:</b> {data['time']}\n"
        f"📍 <b>Место отправления:</b> {data['place']}\n\n"
        f"📖 <b>Описание:</b>\n{data['desc']}\n\n"
        f"🔗 <a href='{data['url']}'>Смотреть видео полностью</a>\n\n"
        f"\n"
        f"<a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
    )

    try:
        # Отправляем ФОТО с текстом в подписи (так оформление самое красивое)
        bot.send_photo(
            CHANNEL_NAME, 
            data['img'], 
            caption=caption, 
            parse_mode='HTML'
        )
        print(f"Пост '{data['title']}' успешно опубликован.")
    except Exception as e:
        print(f"Ошибка при отправке: {e}")

if __name__ == "__main__":
    post_daily_video()
