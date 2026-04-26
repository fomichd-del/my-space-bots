import os
import sys
import telebot
from telebot import types, apihelper
from threading import Thread
from flask import Flask
import time
import requests
from draw_map import generate_star_map

# Принудительная очистка логов (чтобы всё сразу летело в консоль)
def log_print(msg):
    print(msg)
    sys.stdout.flush()

# 1. ТАЙМАУТЫ
apihelper.CONNECT_TIMEOUT = 120
apihelper.READ_TIMEOUT = 120

app = Flask('')

@app.route('/')
def home():
    token_status = "✅ НАЙДЕН" if os.environ.get('TELEGRAM_TOKEN') else "❌ ОТСУТСТВУЕТ"
    return f"""
    <h1>Марти Астроном: Бортовой компьютер</h1>
    <p>Статус токена в системе: <b>{token_status}</b></p>
    <p>Если статус 'ОТСУТСТВУЕТ', проверь Settings -> Secrets в Hugging Face!</p>
    """

def run_flask():
    port = int(os.environ.get("PORT", 7860))
    log_print(f"📡 [СЕРВЕР]: Запуск порта {port}")
    app.run(host='0.0.0.0', port=port)

# 2. ПОДГОТОВКА ТОКЕНА
TOKEN_RAW = os.environ.get('TELEGRAM_TOKEN', '')
TOKEN = TOKEN_RAW.strip().replace("'", "").replace('"', "")

if TOKEN:
    log_print(f"✅ [СИСТЕМА]: Токен загружен (Начало: {TOKEN[:5]}...)")
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
            bot.send_message(message.chat.id, f"Привет! Я Марти Астроном. 🌌 Готов к работе!", reply_markup=markup)

    @bot.message_handler(content_types=['location'])
    def handle_location(message):
        log_print(f"📍 [ЛОКАЦИЯ]: Запрос от {message.from_user.first_name}")
        bot.send_message(message.chat.id, "🛰 Секунду... Рисую!")
        try:
            path = generate_star_map(message.location.latitude, message.location.longitude, message.from_user.first_name)
            with open(path, 'rb') as f:
                bot.send_photo(message.chat.id, f, caption="🌟 ТВОЁ НЕБО ГОТОВО! 🐩📸", parse_mode='Markdown')
        except Exception as e:
            log_print(f"❌ [ОШИБКА РИСОВАНИЯ]: {e}")
            bot.send_message(message.chat.id, "⚠️ Ошибка телескопа.")

    @bot.message_handler(content_types=['text'])
    def handle_text(message):
        log_print(f"💬 [ТЕКСТ]: Сообщение от {message.from_user.first_name}: {message.text}")
        bot.send_message(message.chat.id, "Слышу тебя! Чтобы увидеть звезды, нажми кнопку 'Мое небо'.")
else:
    log_print("❌ [КРИТИЧЕСКАЯ ОШИБКА]: Переменная TELEGRAM_TOKEN не найдена!")
    bot = None

# 3. ФУНКЦИЯ ЗАПУСКА
def start_martin():
    if not bot:
        log_print("⛔ [СТОП]: Бот не может быть запущен, так как TOKEN пустой.")
        return
    
    log_print("🧹 [СИСТЕМА]: Сброс старых связей...")
    try:
        requests.get(f"https://api.telegram.org/bot{TOKEN}/deleteWebhook?drop_pending_updates=True", timeout=10)
    except Exception as e:
        log_print(f"⚠️ [СИСТЕМА]: Не удалось сбросить вебхук: {e}")

    log_print("🚀 [БОТ]: Марти Астроном выходит в эфир!")
    while True:
        try:
            bot.infinity_polling(timeout=90, long_polling_timeout=90, skip_pending=True)
        except Exception as e:
            log_print(f"📡 [СВЯЗЬ]: Ошибка ({e}). Переподключение через 10 сек...")
            time.sleep(10)

if __name__ == "__main__":
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()
    
    # Даем серверу чуть-чуть времени
    time.sleep(2)
    
    start_martin()
