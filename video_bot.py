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

SOURCES = {
    "SpaceX": "UCtI0Hodo5o5dUb67FeUjDeA",
    "NASA": "UCOV19_pU-Z58VdB1YfSkA3w",
    "Alpha Centauri": "UC6mD3sE6ZJ_W_7_xI0KxhSg",
    "Roscosmos": "UCOS_m87vNfS6E_5An_Ym2pA",
    "NASASpaceflight": "UCSUu1lih2nj6Z1qbd1E9Vag"
}

def translate_and_summarize(text, max_len=400):
    """Переводит и ограничивает длину описания для лаконичности"""
    try:
        translated = translator.translate(text)
        if len(translated) > max_len:
            # Обрезаем до max_len и пытаемся найти последний знак препинания для красоты
            trimmed = translated[:max_len]
            last_period = max(trimmed.rfind('.'), trimmed.rfind('!'), trimmed.rfind('?'))
            if last_period > (max_len // 2): # Если точка есть хотя бы в середине обрезка
                return translated[:last_period + 1]
            return trimmed + "..."
        return translated
    except:
        return text[:max_len] + "..."

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
    three_days_ago = (datetime.utcnow() - timedelta(days=3)).isoformat() + "Z"
    
    # 1. Поиск LIVE
    for name, c_id in SOURCES.items():
        req = youtube.search().list(channelId=c_id, part='snippet', type='video', eventType='live')
        res = req.execute()
        if res.get('items'):
            v = res['items'][0]
            return {'url': f"https://www.youtube.com/watch?v={v['id']['videoId']}", 
                    'title': "🔴 ПРЯМОЙ ЭФИР: " + translator.translate(v['snippet']['title']),
                    'desc': translate_and_summarize(v['snippet']['description']), 'is_live': True}

    # 2. Поиск завершенных эфиров за 3 дня
    for name, c_id in SOURCES.items():
        req = youtube.search().list(channelId=c_id, part='snippet', type='video', 
                                    eventType='completed', publishedAfter=three_days_ago, order='date')
        res = req.execute()
        if res.get('items'):
            v = res['items'][0]
            return {'url': f"https://www.youtube.com/watch?v={v['id']['videoId']}", 
                    'title': "🚀 ЗАПУСК: " + translator.translate(v['snippet']['title']),
                    'desc': translate_and_summarize(v['snippet']['description']), 'is_live': True}

    # 3. Обычное видео
    source_name = random.choice(list(SOURCES.keys()))
    req = youtube.search().list(channelId=SOURCES[source_name], part='snippet', 
                                type='video', videoDuration='short', maxResults=5)
    res = req.execute()
    if res.get('items'):
        v = random.choice(res['items'])
        return {'url': f"https://www.youtube.com/watch?v={v['id']['videoId']}", 
                'title': translator.translate(v['snippet']['title']),
                'desc': translate_and_summarize(v['snippet']['description']), 'is_live': False}
    return None

def post_daily_video():
    data = get_video_data()
    if not data: return

    # Невидимый символ со ссылкой для того, чтобы превью (окошко) было НАВЕРХУ, если шлем текстом
    hidden_link = f"<a href='{data['url']}'>\u200b</a>"
    
    caption = (
        f"{hidden_link}<b>{data['title']}</b>\n\n"
        f"ℹ️ {data['desc']}\n\n"
        f"\n\n"
        f"<a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
    )

    if data.get('is_live'):
        # Трансляции всегда текстом с окошком (они слишком длинные для загрузки)
        bot.send_message(CHANNEL_NAME, caption, parse_mode='HTML', disable_web_page_preview=False)
    else:
        video_file = download_video(data['url'])
        if video_file and os.path.exists(video_file):
            with open(video_file, 'rb') as v:
                # В send_video видео автоматически будет НАД текстом
                bot.send_video(CHANNEL_NAME, v, caption=caption, parse_mode='HTML', supports_streaming=True)
            os.remove(video_file)
        else:
            # Если файл не скачался — шлем текстом, но скрытая ссылка в начале поставит плеер наверх
            bot.send_message(CHANNEL_NAME, caption, parse_mode='HTML', disable_web_page_preview=False)

if __name__ == "__main__":
    post_daily_video()
