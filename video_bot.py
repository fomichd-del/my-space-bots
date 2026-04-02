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

# Каналы для поиска
SOURCES = {
    "NASA": "UCOV19_pU-Z58VdB1YfSkA3w",
    "SpaceX": "UCtI0Hodo5o5dUb67FeUjDeA",
    "Alpha Centauri": "UC6mD3sE6ZJ_W_7_xI0KxhSg",
    "Космос Просто": "UC5pCHu36K7idvX_V5vVpAnA"
}

QUERIES = ["космос новости за неделю", "запуск ракеты", "факты о планетах", "черные дыры"]

def download_video(url):
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
        raise Exception("YOUTUBE_API_KEY не найден!")
    
    youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
    
    # Пытаемся найти видео в три этапа
    # ЭТАП 1: Случайный канал из списка
    source_name = random.choice(list(SOURCES.keys()))
    channel_id = SOURCES[source_name]
    print(f"Попытка 1: Ищем на канале {source_name}...")
    
    request = youtube.search().list(
        channelId=channel_id, part='snippet', maxResults=5, type='video', order='date'
    )
    res = request.execute()
    
    # ЭТАП 2: Если на канале пусто, делаем общий поиск на русском
    if not res.get('items'):
        query = random.choice(QUERIES)
        print(f"Попытка 2: На канале пусто. Общий поиск по теме: {query}...")
        request = youtube.search().list(
            q=query, part='snippet', maxResults=5, type='video', relevanceLanguage='ru'
        )
        res = request.execute()

    # Если нашли хоть что-то
    if res.get('items'):
        video = random.choice(res['items'])
        v_id = video['id'].get('videoId') or video['id'].get('playlistId')
        return {
            'url': f"https://www.youtube.com/watch?v={v_id}",
            'title': video['snippet']['title'],
            'desc': video['snippet']['description'][:250] + "..."
        }
    
    return None

def post_daily_video():
    print("--- ЗАПУСК ПОИСКА ---")
    data = get_video_data()
    
    if not data:
        print("Критическая ошибка: Видео не найдено даже в общем поиске.")
        return

    print(f"Выбрано видео: {data['title']}")
    video_file = download_video(data['url'])

    # Тот самый формат без лишних баров
    caption = (
        f"🎬 <b>Тема: {data['title']}</b>\n\n"
        f"ℹ️ <b>Описание:</b> {data['desc']}\n\n"
        f"\n\n"
        f"<a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
    )

    if video_file and os.path.exists(video_file):
        print("Отправка видео в канал...")
        with open(video_file, 'rb') as v:
            bot.send_video(
                CHANNEL_NAME, 
                v, 
                caption=caption, 
                parse_mode='HTML', 
                supports_streaming=True
            )
        os.remove(video_file)
        print("Успешно отправлено!")
    else:
        # Если скачивание не удалось, шлем просто текстом, НО без превью
        print("Файл не скачался, отправляю текст без превью...")
        bot.send_message(
            CHANNEL_NAME, 
            caption, 
            parse_mode='HTML', 
            disable_web_page_preview=True # Убирает тот самый большой бар
        )

if __name__ == "__main__":
    post_daily_video()
