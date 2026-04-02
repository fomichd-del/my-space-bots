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

# Источники, где нам НЕ важен язык (NASA, SpaceX и др.)
GLOBAL_SOURCES = {
    "SpaceX (Official)": "UCtI0Hodo5o5dUb67FeUjDeA",
    "NASA (Official)": "UCOV19_pU-Z58VdB1YfSkA3w",
    "ESA (European Space Agency)": "UCdq0byZ-STP8_7GisA5T-sQ",
    "James Webb Telescope Updates": "UCP2I6M6O_W5lA4G27Sscs3A"
}

# Каналы, которые уже на русском
RUSSIAN_SOURCES = {
    "Alpha Centauri": "UC6mD3sE6ZJ_W_7_xI0KxhSg", 
    "Космос Просто": "UC5pCHu36K7idvX_V5vVpAnA",
    "Роскосмос ТВ": "UCOS_m87vNfS6E_5An_Ym2pA"
}

QUERIES = ["новости космоса", "черные дыры", "запуск ракеты", "планеты"]

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
    except:
        return None

def get_video_data():
    youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
    
    # 1. Выбираем тип поиска: Глобальный канал, Русский канал или Общий поиск
    mode = random.choice(['global', 'russian', 'search'])
    
    if mode == 'global':
        # Ищем по мировым каналам БЕЗ фильтра языка
        source_name, channel_id = random.choice(list(GLOBAL_SOURCES.items()))
        print(f"Режим: Глобальный источник ({source_name})")
        request = youtube.search().list(
            channelId=channel_id, part='snippet', maxResults=3, type='video', order='date'
        )
    elif mode == 'russian':
        # Ищем по русскоязычным каналам
        source_name, channel_id = random.choice(list(RUSSIAN_SOURCES.items()))
        print(f"Режим: Проверенный русский канал ({source_name})")
        request = youtube.search().list(
            channelId=channel_id, part='snippet', maxResults=3, type='video', order='date'
        )
    else:
        # Общий поиск ПО ВСЕМУ ЮТУБУ только на РУССКОМ
        query = random.choice(QUERIES)
        print(f"Режим: Общий поиск на русском по теме '{query}'")
        request = youtube.search().list(
            q=query, part='snippet', maxResults=1, type='video', 
            relevanceLanguage='ru', order='relevance' # Здесь фильтр языка включен
        )

    response = request.execute()

    if response['items']:
        video = random.choice(response['items'])
        return {
            'url': f"https://www.youtube.com/watch?v={video['id']['videoId']}",
            'title': video['snippet']['title'],
            'desc': video['snippet']['description'][:300] + "..."
        }
    return None

def post_daily_video():
    data = get_video_data()
    if not data: return

    print(f"Обработка: {data['title']}")
    video_file = download_video(data['url'])

    # Формируем подпись по твоему шаблону
    caption = (
        f"🎬 <b>Тема: {data['title']}</b>\n\n"
        f"ℹ️ <b>Описание:</b> {data['desc']}\n\n"
        f"\n\n"
        f"<a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
    )

    if video_file and os.path.exists(video_file):
        with open(video_file, 'rb') as v:
            bot.send_video(CHANNEL_NAME, v, caption=caption, parse_mode='HTML', supports_streaming=True)
        os.remove(video_file)
    else:
        # Если файл не скачался (тяжелый), шлем ссылкой с превью
        bot.send_message(CHANNEL_NAME, caption, parse_mode='HTML')

if __name__ == "__main__":
    post_daily_video()
