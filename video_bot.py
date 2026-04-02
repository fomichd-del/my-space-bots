import os
import telebot
from googleapiclient.discovery import build
import random

# Конфигурация из Secrets на GitHub
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
# Имя твоего канала из Secrets или используем дефолт
CHANNEL_NAME = os.getenv('CHANNEL_NAME') or '@vladislav_space'

bot = telebot.TeleBot(TELEGRAM_TOKEN)

# Темы для поиска (можно менять)
QUERIES = [
    "космос новости за неделю",
    "запуски ракет обзор",
    "астрономия интересные факты",
    "миссия артемида наса"
]

def get_video_data():
    if not YOUTUBE_API_KEY:
        raise Exception("ОШИБКА: YOUTUBE_API_KEY не найден в Secrets!")
    
    youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
    query = random.choice(QUERIES)
    
    request = youtube.search().list(
        q=query, part='snippet', maxResults=1, type='video', relevanceLanguage='ru', order='date'
    )
    response = request.execute()

    if response['items']:
        video = response['items'][0]
        v_id = video['id']['videoId']
        # На всякий случай обрабатываем опечатку в URL
        v_url = f"https://www.youtube.com/watch?v={v_id}"
        
        # Получаем заголовок и описание
        title = video['snippet']['title']
        # Описание часто длинное, берем только начало
        desc = video['snippet']['description'][:250] + "..."
        
        return {
            'url': v_url,
            'title': title,
            'desc': desc
        }
    return None

def post_daily_video():
    print("Начинаю поиск видео...")
    data = get_video_data()
    if not data:
        print("Видео не найдено.")
        return

    # Формируем текст сообщения в формате HTML
    # КЛЮЧЕВОЙ МОМЕНТ: Прячем ссылку в эмодзи в самом начале
    # <a href="URL">🎬</a> - ссылка будет внутри эмодзи
    # \u200b - невидимый символ после эмодзи, чтобы текст не прилипал
    caption = (
        f"<a href='{data['url']}'>🎬</a>\u200b<b>Тема: {data['title']}</b>\n\n"
        f"ℹ️ <b>Описание:</b> {data['desc']}\n\n"
        f"\n\n"
        f"<a href='https://t.me/vladislav_space'>Дневник юного космонавта</a>"
    )
    
    print(f"Попытка отправить пост в канал {CHANNEL_NAME}...")
    
    try:
        # Отправляем текстовое сообщение, в котором Ссылка на видео стоит ПЕРВОЙ
        # disabled_web_page_preview=False - ЭТОТ ПАРАМЕТР ВКЛЮЧАЕТ ПРЕДПРОСМОТР ССЫЛКИ
        bot.send_message(
            CHANNEL_NAME, 
            caption, 
            parse_mode='HTML', 
            disable_web_page_preview=False
        )
        print("Пост опубликован!")
    except Exception as e:
        print(f"Ошибка отправки сообщения: {e}")
        # Если не админ, лог покажет

if __name__ == "__main__":
    post_daily_video()
