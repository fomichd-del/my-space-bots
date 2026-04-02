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

# Основные источники запусков и новостей
SOURCES = {
    "SpaceX": "UCtI0Hodo5o5dUb67FeUjDeA",
    "NASA": "UCOV19_pU-Z58VdB1YfSkA3w",
    "Alpha Centauri": "UC6mD3sE6ZJ_W_7_xI0KxhSg",
    "Roscosmos": "UCOS_m87vNfS6E_5An_Ym2pA",
    "NASASpaceflight (L2)": "UCSUu1lih2nj6Z1qbd1E9Vag"
}

def translate_text(text):
    try: return translator.translate(text)
    except: return text

def download_video(url):
    filename = 'video_to_send.mp4'
    ydl_opts = {
        'format': 'best[ext=mp4][filesize<50M]/worst[ext=mp4]',
        'outtmpl': filename, 'quiet': True, 'no_warnings': True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return filename
    except: return None

def get_video_data():
    youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
    
    # Считаем дату 3 дня назад для фильтра
    three_days_ago = (datetime.utcnow() - timedelta(days=3)).isoformat() + "Z"
    
    # 1. Сначала ищем АКТИВНЫЙ LIVE
    print("Проверка прямых эфиров...")
    for name, c_id in SOURCES.items():
        req = youtube.search().list(channelId=c_id, part='snippet', type='video', eventType='live')
        res = req.execute()
        if res.get('items'):
            v = res['items'][0]
            print(f"НАЙДЕН ЭФИР: {name}")
            return {'url': f"https://www.youtube.com/watch?v={v['id']['videoId']}", 
                    'title': "🔴 ПРЯМОЙ ЭФИР: " + translate_text(v['snippet']['title']),
                    'desc': translate_text(v['snippet']['description'][:300]), 'is_live': True}

    # 2. Если LIVE нет, ищем ЗАВЕРШЕННЫЕ трансляции за 3 дня
    print("Поиск недавних запусков (3 дня)...")
    for name, c_id in SOURCES.items():
        req = youtube.search().list(channelId=c_id, part='snippet', type='video', 
                                    eventType='completed', publishedAfter=three_days_ago, order='date')
        res = req.execute()
        if res.get('items'):
            v = res['items'][0]
            print(f"НАЙДЕН ЗАПУСК: {name}")
            return {'url': f"https://www.youtube.com/watch?v={v['id']['videoId']}", 
                    'title': "🚀 ЗАПУСК: " + translate_text(v['snippet']['title']),
                    'desc': translate_text(v['snippet']['description'][:300]), 'is_live': True}

    # 3. Если ничего событийного нет — обычное короткое видео
    print("Событий нет, ищем обычное видео...")
    source_name = random.choice(list(SOURCES.keys()))
    req = youtube.search().list(channelId=SOURCES[source_name], part='snippet', 
                                type='video', videoDuration='short', maxResults=5)
    res = req.execute()
    if res.get('items'):
        v = random.choice(res['items'])
        return {'url': f"https://www.youtube.com/watch?v={v['id']['videoId']}", 
                'title': translate_text(v['snippet']['title']),
                'desc': translate_text(v['snippet']['description'][:300]), 'is_live': False}
    return None

def post_daily_video():
    data = get_video_data()
    if not data: return

    # Формируем текст (ссылка на видео спрятана в первом эмодзи для "окошка")
    caption = (
        f"<a href='{data['url']}'>🎬</a> <b>{data['title']}</b>\n\n"
        f"ℹ️ <b>Описание:</b> {data['desc']}\n\n"
        f"\n\n"
        f"<a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
    )

    # Если это трансляция — шлем сразу текстом с окошком (скачать 2-х часовой эфир нельзя)
    if data.get('is_live'):
        print("Отправка трансляции/запуска через плеер...")
        bot.send_message(CHANNEL_NAME, caption, parse_mode='HTML', disable_web_page_preview=False)
    else:
        # Если это короткое видео — пробуем скачать
        video_file = download_video(data['url'])
        if video_file and os.path.exists(video_file):
            with open(video_file, 'rb') as v:
                bot.send_video(CHANNEL_NAME, v, caption=caption, parse_mode='HTML', supports_streaming=True)
            os.remove(video_file)
        else:
            bot.send_message(CHANNEL_NAME, caption, parse_mode='HTML', disable_web_page_preview=False)

if __name__ == "__main__":
    post_daily_video()
