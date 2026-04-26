import os
import sys
import telebot
from telebot import types, apihelper
from threading import Thread
from flask import Flask
import time
import requests
from draw_map import generate_star_map

# Принудительная очистка логов
def log_print(msg):
    print(msg)
    sys.stdout.flush()

# 1. МАКСИМАЛЬНОЕ УСИЛЕНИЕ ТЕРПЕНИЯ (Таймауты 120 секунд)
apihelper.CONNECT_TIMEOUT = 120
apihelper.READ_TIMEOUT = 120
apihelper.LONG_POLLING_TIMEOUT = 120

app = Flask('')

@app.route('/')
def home():
    token_exists = "✅" if os.environ.get('TELEGRAM_TOKEN') else "❌"
    return f"<h1>Марти Астроном на связи!</h1><p>Токен: {token_exists}</p>"

def run_flask():
    port = int(os.environ.get("PORT", 7860))
    log_print(f"📡 [СЕРВЕР]: Запуск порта {port}")
    app.run(host='0.0.0.0', port=port)

# 2. ПОДГОТОВКА ТОКЕНА
TOKEN_RAW = os.environ.get('TELEGRAM_TOKEN', '')
TOKEN = TOKEN_RAW.strip().replace("'", "").replace('"', "")

if TOKEN:
    log_print(f"✅ [СИСТЕМА]: Токен загружен (Начало: {TOKEN[:5]}...)")
    # Используем threaded=False для стабильности на бесплатных хостингах
    bot = telebot.TeleBot(TOKEN, threaded=False)
    
    @bot.message_handler(commands=['start'])
    def send_welcome(message):
        log_print(f"📩 [АКТИВНОСТЬ]: {message.from_user.first_name} нажал СТАРТ")
        text = message.text or ""
        if "get_map" in text:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            markup.add(types.KeyboardButton("📍 ПОКАЗАТЬ МОЁ НЕБО", request_location=True))
            bot.send_message(message.chat.id, "🛰 **Секретный шлюз открыт.**\nЖми на кнопку для карты! 🐩🔭", reply_markup=markup, parse_mode='Markdown')
        else:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.row("🎲 Случайное созвездие")
            markup.row(types.KeyboardButton("📍 Мое небо", request_location=True))
            bot.send_message(message.chat.id, f"Привет! Я Марти Астроном. 🌌\n\nЯ твой новый помощник. Готов рисовать карты звезд!", reply_markup=markup)

    @bot.message_handler(content_types=['location'])
    def handle_location(message):
        log_print(f"📍 [ЛОКАЦИЯ]: Запрос от {message.from_user.first_name}")
        bot.send_message(message.chat.id, "🛰 Секунду... Навожу телескопы на твои координаты!")
        try:
            path = generate_star_map(message.location.latitude, message.location.longitude, message.from_user.first_name)
            with open(path, 'rb') as f:
                bot.send_photo(message.chat.id, f, caption="🌟 **ТВОЁ НЕБО ГОТОВО!**\n\nОтправляй его в канал! 🐩📸", parse_mode='Markdown')
        except Exception as e:
            log_print(f"❌ [ОШИБКА РИСОВАНИЯ]: {e}")
            bot.send_message(message.chat.id, "⚠️ Ошибка телескопа. Попробуй позже.")

    @bot.message_handler(content_types=['text'])
    def handle_text(message):
        log_print(f"💬 [ТЕКСТ]: Сообщение от {message.from_user.first_name}")
        bot.send_message(message.chat.id, "Слышу тебя! Чтобы увидеть карту звездного неба, нажми кнопку 'Мое небо'.")
else:
    log_print("❌ [КРИТИЧЕСКАЯ ОШИБКА]: TELEGRAM_TOKEN не найден!")
    bot = None

# 3. ФУНКЦИЯ ЗАПУСКА С ПОВТОРНЫМИ ПОПЫТКАМИ
def start_martin():
    if not bot: return
    
    log_print("🧹 [СИСТЕМА]: Сброс вебхуков...")
    try:
        # Увеличиваем таймаут и здесь
        requests.get(f"https://api.telegram.org/bot{TOKEN}/deleteWebhook?drop_pending_updates=True", timeout=30)
        log_print("✅ [СИСТЕМА]: Вебхуки сброшены.")
    except:
        log_print("⚠️ [СИСТЕМА]: Не удалось сбросить вебхуки сразу, идем дальше...")

    log_print("🚀 [БОТ]: Марти Астроном выходит в эфир!")
    
    while True:
        try:
            # Используем polling вместо infinity_polling для более жесткого контроля
            bot.polling(none_stop=True, timeout=120, long_polling_timeout=120)
        except Exception as e:
            log_print(f"📡 [СВЯЗЬ]: Помехи ({e}). Перезапуск через 10 сек...")
            time.sleep(10)

if __name__ == "__main__":
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()
    
    time.sleep(3)
    start_martin()
