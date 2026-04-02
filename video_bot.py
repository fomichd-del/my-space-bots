import os
import telebot
from googleapiclient.discovery import build
import random

# Конфигурация из переменных окружения
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
NASA_API_KEY   = os.getenv('NASA_API_KEY') or "DEMO_KEY"
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
CHANNEL_NAME   = '@vladislav_space'

bot = telebot.TeleBot(TELEGRAM_TOKEN)

# Список поисковых запросов для разнообразия
QUERIES = [
    "космос новости за неделю",
    "запуски ракет сегодня",
    "научные факты о вселенной",
    "новые открытия в астрономии",
    "жизнь на мкс видео",
    "космические миссии 2026"
]

def get_latest_video():
    """Находит видео, его название и описание через YouTube API"""
    if not YOUTUBE_API_KEY:
        return None, None, "Ошибка: Не задан YOUTUBE_API_KEY"

    try:
        youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
        query = random.choice(QUERIES)
        
        request = youtube.search().list(
            q=query,
            part='snippet',
            maxResults=1,
            type='video',
            relevanceLanguage='ru',
            order='date' 
        )
        response = request.execute()

        if response['items']:
            video = response['items'][0]
            video_id = video['id']['videoId']
            title = video['snippet']['title']
            # Берем описание и обрезаем его для компактности
            description = video['snippet']['description']
            if len(description) > 300:
                description = description[:297] + "..."
                
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            return video_url, title, description
        return None, None, "Видео не найдены."
    except Exception as e:
        return None, None, f"Ошибка API: {e}"

def post_daily_video():
    """Публикует видео с заданным форматированием"""
    url, title, desc = get_latest_video()
    
    if url:
        # Формируем текст поста
        # \n\n — это перенос строки. Два раза дает пустую строку.
        caption = (
            f"🎬 <b>Тема: {title}</b>\n\n"
            f"ℹ️ <b>Описание:</b> {desc}\n\n"
            f"🔗 <b>Смотреть тут:</b> {url}\n\n"
            f"\n\n" # Две пустые строки перед подписью
            f"<a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
        )
        
        # Используем parse_mode='HTML' для поддержки тега <a>
        bot.send_message(CHANNEL_NAME, caption, parse_mode='HTML', disable_web_page_preview=False)
        print(f"Пост '{title}' опубликован.")
    else:
        print(f"Ошибка: {desc}")

if __name__ == "__main__":
    post_daily_video()
