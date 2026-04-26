import os
import telebot
from telebot import types, apihelper
from threading import Thread
from flask import Flask
import time
from draw_map import generate_star_map

# 1. ТАЙМАУТЫ (Даем время на медленный интернет)
apihelper.CONNECT_TIMEOUT = 90
apihelper.READ_TIMEOUT = 90

app = Flask('')

@app.route('/')
def home():
    return "Мартин на связи! Ракета Space News на орбите. 🛰️"

def run_flask():
    port = int(os.environ.get("PORT", 7860))
    print(f"📡 [СЕРВЕР]: Запуск порта {port}")
    app.run(host='0.0.0.0', port=port)

# 2. ПОДГОТОВКА ТОКЕНА
TOKEN_RAW = os.environ.get('TELEGRAM_TOKEN', '')
TOKEN = TOKEN_RAW.strip().replace("'", "").replace('"', "")

# 3. ЛОГИКА БОТА
if TOKEN:
    print(f"✅ [СИСТЕМА]: Токен загружен (87451...)")
    bot = telebot.TeleBot(TOKEN, threaded=False)
    
    @bot.message_handler(commands=['start'])
    def send_welcome(message):
        print(f"📩 [АКТИВНОСТЬ]: {message.from_user.first_name} нажал СТАРТ")
        text = message.text or ""
        if "get_map" in text:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            markup.add(types.KeyboardButton("📍 ПОКАЗАТЬ МОЁ НЕБО", request_location=True))
            bot.send_message(message.chat.id, "🛰 **Секретный шлюз открыт.**\nЖми на кнопку для карты! 🐩🔭", reply_markup=markup, parse_mode='Markdown')
        else:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add("🎲 Случайное созвездие")
            markup.add(types.KeyboardButton("📍 Мое небо", request_location=True))
            bot.send_message(message.chat.id, "Привет! Я Мартин. 🌌 Готов к работе!", reply_markup=markup)

    @bot.message_handler(content_types=['location'])
    def handle_location(message):
        print(f"📍 [ЛОКАЦИЯ]: Рисую для {message.from_user.first_name}")
        bot.send_message(message.chat.id, "🛰 Секунду... Рисую!")
        try:
            path = generate_star_map(message.location.latitude, message.location.longitude, message.from_user.first_name)
            with open(path, 'rb') as f:
                bot.send_photo(message.chat.id, f, caption="🌟 ТВОЁ НЕБО ГОТОВО! 🐩📸", parse_mode='Markdown')
        except Exception as e:
            print(f"❌ [ОШИБКА РИСОВАНИЯ]: {e}")
            bot.send_message(message.chat.id, "⚠️ Ошибка телескопа.")
else:
    print("❌ [ОШИБКА]: ТОКЕН НЕ НАЙДЕН!")
    bot = None

# 4. ФУНКЦИЯ ЗАПУСКА БОТА
def start_martin():
    if not bot: return
    print("🚀 [БОТ]: Пытаюсь войти в эфир Telegram...")
    while True:
        try:
            bot.remove_webhook()
            # Используем infinity_polling для автоматического перезапуска
            bot.infinity_polling(timeout=90, long_polling_timeout=90)
        except Exception as e:
            print(f"📡 [СВЯЗЬ]: Помехи ({e}). Жду 10 сек...")
            time.sleep(10)

# 5. ГЛАВНЫЙ ЗАПУСК
if __name__ == "__main__":
    # Запускаем сайт в отдельном потоке
    flask_thread = Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    
    # Запускаем Мартина в основном потоке
    start_martin()
