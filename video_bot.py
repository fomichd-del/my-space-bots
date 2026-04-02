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

# Список каналов
SOURCES = {
    "NASA": "UCOV19_pU-Z58VdB1YfSkA3w",
    "SpaceX": "UCtI0Hodo5o5dUb67FeUjDeA",
    "Alpha Centauri": "UC6mD3sE6ZJ_W_7_xI0KxhSg",
    "NASASpaceflight": "UCSUu1lih2nj6Z1qbd1E9Vag",
    "Roscosmos": "UCOS_m87vNfS6E_5An_Ym2pA"
}

def translate_and_summarize(text, max_len=400):
    try:
        translated = translator.translate(text)
        if len(translated) > max_len:
            trimmed = translated[:max_len]
            last_p = max(trimmed.rfind('.'), trimmed.rfind('!'), trimmed.rfind('?'))
            return translated[:last_p + 1] if last_p > 200 else trimmed + "..."
        return translated
    except: return text[:max_len]

def get_video_data():
    youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
    three_days_ago = (datetime.utcnow() - timedelta(days=3)).isoformat() + "Z"
    
    print("--- Сканирование на наличие прямых эфиров ---")
    all_live = []
    for name, c_id in SOURCES.items():
        try:
            req = youtube.search().list(channelId=c_id, part='snippet', type='video', eventType='live')
            res = req.execute()
            if res.get('items'):
                all_live.extend(res['items'])
        except: continue

    # ПРИОРЕТЕТ: Ищем Артемиду или Луну
    if all_live:
        priority_keys = ['artemis', 'moon', 'lunar', 'луна', 'sls', 'orion']
        for v in all_live:
            title = v['snippet']['title'].lower()
            if any(k in title for k in priority_keys):
                print(f"Найдено приоритетное событие: {v['snippet']['title']}")
                return {
                    'url': f"https://www.youtube.com/watch?v={v['id']['videoId']}",
                    'title': "🌕 МИССИЯ АРТЕМИДА: " + translator.translate(v['snippet']['title']),
                    'desc': translate_and_summarize(v['snippet']['description']),
                    'is_live': True
                }
        
        # Если Луны нет, берем просто первый живой эфир
        v = all_live[0]
        return {
            'url': f"https://www.youtube.com/watch?v={v['id']['videoId']}",
            'title': "🔴 ПРЯМОЙ ЭФИР: " + translator.translate(v['snippet']['title']),
            'desc': translate_and_summarize(v['snippet']['description']),
            'is_live': True
        }

    # 2. Поиск недавних событий (3 дня)
    print("Эфиров нет, ищем запуски за 3 дня...")
    for name, c_id in SOURCES.items():
        req = youtube.search().list(channelId=c_id, part='snippet', type='video', 
                                    eventType='completed', publishedAfter=three_days_ago, order='date')
        res = req.execute()
        if res.get('items'):
            v = res['items'][0]
            return {
                'url': f"https://www.youtube.com/watch?v={v['id']['videoId']}",
                'title': "🚀 НЕДАВНИЙ ЗАПУСК: " + translator.translate(v['snippet']['title']),
                'desc': translate_and_summarize(v['snippet']['description']),
                'is_live': True
            }

    # 3. Обычное видео (на крайний случай)
    print("Событий нет, ищем короткое видео...")
    c_id = random.choice(list(SOURCES.values()))
    req = youtube.search().list(channelId=c_id, part='snippet', type='video', videoDuration='short', maxResults=3)
    res = req.execute()
    if res.get('items'):
        v = random.choice(res['items'])
        return {
            'url': f"https://www.youtube.com/watch?v={v['id']['videoId']}",
            'title': translator.translate(v['snippet']['title']),
            'desc': translate_and_summarize(v['snippet']['description']),
            'is_live': False
        }
    return None

def post_daily_video():
    data = get_video_data()
    if not data:
        print("Ничего не найдено.")
        return

    # Невидимый символ для превью НАВЕРХУ
    hidden_link = f"<a href='{data['url']}'>\u200b</a>"
    
    caption = (
        f"{hidden_link}<b>{data['title']}</b>\n\n"
        f"ℹ️ {data['desc']}\n\n"
        f"\n\n"
        f"<a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
    )

    if data.get('is_live'):
        # Эфиры — только через плеер (они слишком длинные)
        bot.send_message(CHANNEL_NAME, caption, parse_mode='HTML', disable_web_page_preview=False)
    else:
        # Короткие видео — пробуем скачать
        ydl_opts = {'format': 'best[ext=mp4][filesize<50M]/worst', 'outtmpl': 'vid.mp4', 'quiet': True}
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([data['url']])
            with open('vid.mp4', 'rb') as v:
                bot.send_video(CHANNEL_NAME, v, caption=caption, parse_mode='HTML', supports_streaming=True)
            os.remove('vid.mp4')
        except:
            bot.send_message(CHANNEL_NAME, caption, parse_mode='HTML', disable_web_page_preview=False)

if __name__ == "__main__":
    post_daily_video()
