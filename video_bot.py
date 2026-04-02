import os
import telebot
import yt_dlp
from googleapiclient.discovery import build
import random
import time

# Конфигурация из Secrets на GitHub
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
# Имя канала из Secrets или используем дефолт
CHANNEL_NAME = os.getenv('CHANNEL_NAME') or '@vladislav_space'

bot = telebot.TeleBot(TELEGRAM_TOKEN)

# Источники, где нам НЕ важен язык (NASA, SpaceX)
GLOBAL_SOURCES = {
    "SpaceX": "UCtI0Hodo5o5dUb67FeUjDeA",
    "NASA": "UCOV19_pU-Z58VdB1YfSkA3w"
}

# Каналы, которые уже на русском
RUSSIAN_SOURCES = {
    "Alpha Centauri": "UC6mD3sE6ZJ_W_7_xI0KxhSg", 
    "Космос Просто": "UC5pCHu36K7idvX_V5vVpAnA"
}

# Темы для общего поиска на русском
QUERIES = ["новости космоса за неделю", "запуск ракеты", "факты о планетах"]

def download_video(url):
    """Скачивает видео с ограничением по размеру для Telegram (50МБ)"""
    filename = 'video_to_send.mp4'
    ydl_opts = {
        # Пытаемся взять лучшее качество в mp4, но не тяжелее 50МБ
        'format': 'best[ext=mp4][filesize<50M]/worst[ext=mp4]',
        'outtmpl': filename,
        'quiet': True,
        'no_warnings': True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return filename
    except Exception as e:
        print(f"Ошибка скачивания: {e}")
        return None

def get_video_data():
    """Находит видео с учетом гибридной логики языка"""
    youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
    
    # 1. Выбираем режим: Глобальный канал, Русский канал или Общий поиск
    mode = random.choice(['global', 'russian', 'search'])
    
    if mode == 'global':
        source_name, channel_id = random.choice(list(GLOBAL_SOURCES.items()))
        print(f"Режим: Источник '{source_name}' (язык любой)")
        request = youtube.search().list(channelId=channel_id, part='snippet', maxResults=3, type='video', order='date')
    elif mode == 'russian':
        source_name, channel_id = random.choice(list(RUSSIAN_SOURCES.items()))
        print(f"Режим: Проверенный русский канал ({source_name})")
        request = youtube.search().list(channelId=channel_id, part='snippet', maxResults=3, type='video', order='date')
    else:
        query = random.choice(QUERIES)
        print(f"Режим: Общий поиск на русском по теме '{query}'")
        request = youtube.search().list(q=query, part='snippet', maxResults=1, type='video', relevanceLanguage='ru', order='relevance')

    response = request.execute()

    if response['items']:
        video = random.choice(response['items'])
        return {
            'url': f"https://www.youtube.com/watch?=watch?v={video['id']['videoId']}",
            'title': video['snippet']['title'],
            'desc': video['snippet']['description'][:250] + "..."
        }
    return None

def post_daily_video():
    """Публикует видео только файлом и без превью ссылки"""
    data = get_video_data()
    if not data:
        return

    print(f"Пытаюсь скачать: {data['title']}")
    video_file = download_video(data['url'])

    # Формируем подпись по твоему шаблону (HTML)
    caption = (
        f"🎬 <b>Тема: {data['title']}</b>\n\n"
        f"ℹ️ <b>Описание:</b> {data['desc']}\n\n"
        f"\n\n"
        f"<a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
    )

    if video_file and os.path.exists(video_file):
        print(f"Файл готов к отправке в {CHANNEL_NAME}...")
        # Устанавливаем supports_streaming=True для быстрого просмотра
        #disable_web_page_preview=True убирает бар превью
        with open(video_file, 'rb') as v:
            bot.send_video(
                CHANNEL_NAME, 
                v, 
                caption=caption, 
                parse_mode='HTML', 
                supports_streaming=True
            )
        
        # Удаляем файл после отправки
        os.remove(video_file)
        print("Видео успешно отправлено и файл удален.")
    else:
        # Критическое изменение: если не скачалось, мы НЕ шлем пост ссылкой.
        # Это предотвратит появление превью канала. Вместо этого — красная ошибка на GitHub Actions.
        print("Ошибка: Видео не скачалось. Пост не отправлен в канал.")
        # Поднимаем ошибку, чтобы Action на GitHub Actions упал
        raise Exception("Видео не скачалось (слишком тяжелое или ошибка API)") 

if __name__ == "__main__":
    post_daily_video()
