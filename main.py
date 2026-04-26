import os
import sys
import telebot
from telebot import types, apihelper
from threading import Thread
from flask import Flask
import time
from draw_map import generate_star_map

# Принудительная очистка вывода логов
def log_print(msg):
    print(msg)
    sys.stdout.flush()

# 1. НАСТРОЙКИ СВЯЗИ
apihelper.CONNECT_TIMEOUT = 120
apihelper.READ_TIMEOUT = 120

app = Flask('')

@app.route('/')
def home():
    status = "✅" if os.environ.get('TELEGRAM_TOKEN') else "❌"
    return f"<h1>Орбитальная станция Марти</h1><p>Связь: {status}</p>"

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
        bot.send_message(message.chat.id, "🛰 Секунду... Навожу телескопы!")
        try:
            path = generate_star_map(message.location.latitude, message.location.longitude, message.from_user.first_name)
            with open(path, 'rb') as f:
                bot.send_photo(message.chat.id, f, caption="🌟 ТВОЁ НЕБО ГОТОВО! 🐩📸", parse_mode='Markdown')
        except Exception as e:
            log_print(f"❌ [ОШИБКА РИСОВАНИЯ]: {e}")
            bot.send_message(message.chat.id, "⚠️ Ошибка телескопа.")

    @bot.message_handler(content_types=['text'])
    def handle_text(message):
        log_print(f"💬 [ТЕКСТ]: Сообщение от {message.from_user.first_name}")
        bot.send_message(message.chat.id, "Слышу тебя! Чтобы увидеть карту, нажми кнопку 'Мое небо'.")
else:
    log_print("❌ [КРИТИЧЕСКАЯ ОШИБКА]: Токен не найден!")
    bot = None

# 3. ФУНКЦИЯ ЗАПУСКА
def start_martin():
    if not bot: return
    
    log_print("🚀 [БОТ]: Марти Астроном выходит в эфир!")
    while True:
        try:
            # Прямой запуск без лишних проверок
            bot.polling(none_stop=True, timeout=90)
        except Exception as e:
            log_print(f"📡 [СВЯЗЬ]: Помехи ({e}). Переподключение через 10 сек...")
            time.sleep(10)

if __name__ == "__main__":
    # Запускаем Flask
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()
    
    # Сразу запускаем бота
    start_martin()
