import os
import telebot
import yt_dlp
from googleapiclient.discovery import build
import random
import time
from deep_translator import GoogleTranslator

# Конфигурация
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
CHANNEL_NAME = os.getenv('CHANNEL_NAME') or '@vladislav_space'

bot = telebot.TeleBot(TELEGRAM_TOKEN)
translator = GoogleTranslator(source='auto', target='ru')

SOURCES = {
    "NASA": "UCOV19_pU-Z58VdB1YfSkA3w",
    "SpaceX": "UCtI0Hodo5o5dUb67FeUjDeA",
    "Alpha Centauri": "UC6mD3sE6ZJ_W_7_xI0KxhSg",
    "Космос Просто": "UC5pCHu36K7idvX_V5vVpAnA"
}

def translate_text(text):
    try:
        return translator.translate(text)
    except:
        return text

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
    source_name = random.choice(list(SOURCES.keys()))
    channel_id = SOURCES[source_name]
    
    print(f"Ищу на канале {source_name}...")
    request = youtube.search().list(
        channelId=channel_id, part='snippet', maxResults=5, type='video', order='date'
    )
    res = request.execute()
    
    if res.get('items'):
        video = random.choice(res['items'])
        raw_title = video['snippet']['title']
        raw_desc = video['snippet']['description']
        
        print("Перевожу текст...")
        title = translate_text(raw_title)
        desc = translate_text(raw_desc[:300]) # Переводим только первые 300 символов
        
        return {
            'url': f"https://www.youtube.com/watch?v={video['id']['videoId']}",
            'title': title,
            'desc': desc + "..."
        }
    return None

def post_daily_video():
    data = get_video_data()
    if not data: return

    video_file = download_video(data['url'])
    
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
        # Шлем текст без превью (убираем нижний бар)
        bot.send_message(CHANNEL_NAME, caption, parse_mode='HTML', disable_web_page_preview=True)

if __name__ == "__main__":
    post_daily_video()
