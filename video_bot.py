import os
import telebot
import yt_dlp
from googleapiclient.discovery import build
import random
import time

# Конфигурация
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
CHANNEL_NAME = os.getenv('CHANNEL_NAME') or '@vladislav_space'

bot = telebot.TeleBot(TELEGRAM_TOKEN)

# Источники
GLOBAL_SOURCES = {
    "SpaceX": "UCtI0Hodo5o5dUb67FeUjDeA",
    "NASA": "UCOV19_pU-Z58VdB1YfSkA3w"
}
RUSSIAN_SOURCES = {
    "Alpha Centauri": "UC6mD3sE6ZJ_W_7_xI0KxhSg", 
    "Космос Просто": "UC5pCHu36K7idvX_V5vVpAnA"
}
QUERIES = ["новости космоса за неделю", "запуск ракеты", "факты о планетах"]

def download_video(url):
    """Скачивает видео до 50МБ"""
    filename = 'video_to_send.mp4'
    ydl_opts = {
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
    if not YOUTUBE_API_KEY:
        raise Exception("ОШИБКА: YOUTUBE_API_KEY не найден в Secrets!")
    
    youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
    mode = random.choice(['global', 'russian', 'search'])
    
    if mode == 'global':
        source_name, channel_id = random.choice(list(GLOBAL_SOURCES.items()))
        request = youtube.search().list(channelId=channel_id, part='snippet', maxResults=3, type='video', order='date')
    elif mode == 'russian':
        source_name, channel_id = random.choice(list(RUSSIAN_SOURCES.items()))
        request = youtube.search().list(channelId=channel_id, part='snippet', maxResults=3, type='video', order='date')
    else:
        query = random.choice(QUERIES)
        request = youtube.search().list(q=query, part='snippet', maxResults=1, type='video', relevanceLanguage='ru', order='relevance')

    response = request.execute()
    if response['items']:
        video = random.choice(response['items'])
        return {
            'url': f"https://www.youtube.com/watch?v={video['id']['videoId']}", # ОПЕЧАТКА ИСПРАВЛЕНА ТУТ
            'title': video['snippet']['title'],
            'desc': video['snippet']['description'][:250] + "..."
        }
    return None

def post_daily_video():
    print("Начинаю поиск видео...")
    data = get_video_data()
    if not data:
        print("Видео не найдено.")
        return

    print(f"Пытаюсь скачать: {data['title']} ({data['url']})")
    video_file = download_video(data['url'])

    caption = (
        f"🎬 <b>Тема: {data['title']}</b>\n\n"
        f"ℹ️ <b>Описание:</b> {data['desc']}\n\n"
        f"\n\n"
        f"<a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
    )

    if video_file and os.path.exists(video_file):
        print(f"Отправка файла в канал {CHANNEL_NAME}...")
        try:
            with open(video_file, 'rb') as v:
                bot.send_video(CHANNEL_NAME, v, caption=caption, parse_mode='HTML', supports_streaming=True)
            print("УСПЕХ: Видео в канале!")
        except Exception as e:
            print(f"ОШИБКА TELEGRAM: {e}")
            raise e
        finally:
            if os.path.exists(video_file):
                os.remove(video_file)
    else:
        print("Файл не скачался (возможно, ролик слишком тяжелый).")
        raise Exception("Видео недоступно для отправки файлом.")

if __name__ == "__main__":
    post_daily_video()
