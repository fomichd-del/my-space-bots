import os
import telebot
import yt_dlp
from googleapiclient.discovery import build
import random

# Конфигурация
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
CHANNEL_NAME   = '@vladislav_space'

bot = telebot.TeleBot(TELEGRAM_TOKEN)

QUERIES = [
    "космос короткие факты",
    "запуски ракет обзор",
    "новости астрономии",
    "космонавтика интересное"
]

def download_video(url):
    """Скачивает видео с ограничением по размеру для Telegram"""
    filename = 'video_to_send.mp4'
    ydl_opts = {
        # Выбираем лучшее качество, но чтобы файл был до 50МБ
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
    youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
    query = random.choice(QUERIES)
    
    request = youtube.search().list(
        q=query, part='snippet', maxResults=1, type='video', relevanceLanguage='ru', order='date'
    )
    response = request.execute()

    if response['items']:
        video = response['items'][0]
        return {
            'url': f"https://www.youtube.com/watch?v={video['id']['videoId']}",
            'title': video['snippet']['title'],
            'desc': video['snippet']['description'][:300] + "..."
        }
    return None

def post_daily_video():
    data = get_video_data()
    if not data:
        return

    print(f"Пытаюсь скачать: {data['title']}")
    video_file = download_video(data['url'])

    caption = (
        f"🎬 <b>Тема: {data['title']}</b>\n\n"
        f"ℹ️ <b>Описание:</b> {data['desc']}\n\n"
        f"\n\n"
        f"<a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
    )

    if video_file and os.path.exists(video_file):
        with open(video_file, 'rb') as v:
            bot.send_video(
                CHANNEL_NAME, 
                v, 
                caption=caption, 
                parse_mode='HTML',
                supports_streaming=True
            )
        os.remove(video_file) # Удаляем файл после отправки
    else:
        # Если не скачалось, шлем просто ссылкой (запасной вариант)
        bot.send_message(CHANNEL_NAME, caption, parse_mode='HTML')

if __name__ == "__main__":
    post_daily_video()
