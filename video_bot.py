import os
import telebot
import yt_dlp
from googleapiclient.discovery import build
import random

# Конфигурация
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
NASA_API_KEY   = os.getenv('NASA_API_KEY') or "DEMO_KEY"
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
CHANNEL_NAME   = '@vladislav_space'

bot = telebot.TeleBot(TELEGRAM_TOKEN)

QUERIES = [
    "космос коротко факты",
    "запуски ракет видео",
    "планеты солнечной системы обзор",
    "наука космос интересное"
]

def download_video(url):
    """Скачивает видео в минимальном качестве, чтобы влезло в лимит Telegram (50МБ)"""
    ydl_opts = {
        'format': 'best[ext=mp4][filesize<50M]/worst[ext=mp4]', # Ограничение по весу
        'outtmpl': 'video_to_send.mp4',
        'quiet': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            ydl.download([url])
            return 'video_to_send.mp4'
        except:
            return None

def get_video_data():
    """Ищет видео через YouTube API"""
    youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
    query = random.choice(QUERIES)
    
    request = youtube.search().list(
        q=query, part='snippet', maxResults=1, type='video', relevanceLanguage='ru', order='date'
    )
    response = request.execute()

    if response['items']:
        item = response['items'][0]
        return {
            'url': f"https://www.youtube.com/watch?v={item['id']['videoId']}",
            'title': item['snippet']['title'],
            'desc': item['snippet']['description'][:250] + "..."
        }
    return None

def post_daily_video():
    data = get_video_data()
    if not data: return

    print(f"Начинаю загрузку: {data['title']}")
    video_file = download_video(data['url'])

    if video_file and os.path.exists(video_file):
        caption = (
            f"🎬 <b>Тема: {data['title']}</b>\n\n"
            f"ℹ️ <b>Описание:</b> {data['desc']}\n\n"
            f"\n\n"
            f"<a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
        )

        with open(video_file, 'rb') as v:
            bot.send_video(
                CHANNEL_NAME, 
                v, 
                caption=caption, 
                parse_mode='HTML',
                supports_streaming=True # Позволяет смотреть видео, пока оно качается
            )
        
        os.remove(video_file) # Удаляем файл после отправки
        print("Видео успешно загружено в канал!")
    else:
        # Если видео слишком большое или ошибка — шлем просто ссылку
        caption = f"🎬 <b>Тема: {data['title']}</b>\n\n{data['url']}\n\n\n\n<a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
        bot.send_message(CHANNEL_NAME, caption, parse_mode='HTML')

if __name__ == "__main__":
    post_daily_video()
