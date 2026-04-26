import os
import sys
import telebot
from telebot import types
from threading import Thread
from flask import Flask
import time
from draw_map import generate_star_map

# Отключаем лишний шум
def log_print(msg):
    print(msg)
    sys.stdout.flush()

app = Flask('')

@app.route('/')
def home():
    return "Марти Астроном: Полет нормальный! 🚀"

def run_flask():
    port = int(os.environ.get("PORT", 7860))
    app.run(host='0.0.0.0', port=port)

# 1. ПОДГОТОВКА ТОКЕНА
TOKEN = os.environ.get('TELEGRAM_TOKEN', '').strip()

if TOKEN:
    bot = telebot.TeleBot(TOKEN, threaded=False)
    log_print("✅ [СИСТЕМА]: Марти готов к прыжку!")

    @bot.message_handler(commands=['start'])
    def send_welcome(message):
        log_print(f"📩 [АКТИВНОСТЬ]: Старт от {message.from_user.first_name}")
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton("📍 Мое небо", request_location=True))
        bot.send_message(message.chat.id, "Привет! Я Марти Астроном. Нажми на кнопку, и я пришлю карту звезд!", reply_markup=markup)

    @bot.message_handler(content_types=['location'])
    def handle_location(message):
        log_print(f"📍 [ЛОКАЦИЯ]: Запрос от {message.from_user.first_name}")
        bot.send_message(message.chat.id, "🛰 Настраиваю линзы телескопа...")
        try:
            path = generate_star_map(message.location.latitude, message.location.longitude, message.from_user.first_name)
            with open(path, 'rb') as f:
                bot.send_photo(message.chat.id, f, caption="🌟 ТВОЁ НЕБО ГОТОВО! 🐩📸")
        except Exception as e:
            log_print(f"❌ [ОШИБКА]: {e}")
            bot.send_message(message.chat.id, "⚠️ Ошибка связи с обсерваторией.")

    @bot.message_handler(func=lambda m: True)
    def echo_all(message):
        log_print(f"💬 [ТЕКСТ]: Получено: {message.text}")
        bot.reply_to(message, "Прием! Я тебя слышу. Нажми 'Мое небо' для карты.")
else:
    log_print("❌ [ОШИБКА]: Токен не найден в Secrets!")
    bot = None

# 2. МАКСИМАЛЬНО ПРОСТОЙ ЦИКЛ
def start_martin():
    if not bot: return
    log_print("🚀 [ЭФИР]: Марти Астроном вошел в чат!")
    while True:
        try:
            # Уменьшаем таймаут, чтобы не "висеть" на линии долго
            bot.polling(none_stop=True, timeout=30, long_polling_timeout=10)
        except Exception as e:
            log_print(f"📡 [СВЯЗЬ]: Помехи... Пробую еще раз. ({e})")
            time.sleep(5)

if __name__ == "__main__":
    Thread(target=run_flask, daemon=True).start()
    start_martin()
