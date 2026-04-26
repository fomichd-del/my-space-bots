import os
import sys
import telebot
from telebot import types
from threading import Thread
from flask import Flask
import time
from draw_map import generate_star_map

def log_print(msg):
    print(msg)
    sys.stdout.flush()

app = Flask('')

@app.route('/')
def home():
    return "Марти Астроном: Режим Спринтера активен! 🏃‍♂️"

def run_flask():
    port = int(os.environ.get("PORT", 7860))
    app.run(host='0.0.0.0', port=port)

TOKEN = os.environ.get('TELEGRAM_TOKEN', '').strip()

if TOKEN:
    bot = telebot.TeleBot(TOKEN, threaded=False)
    log_print("✅ [СИСТЕМА]: Код загружен. Переходим на короткие дистанции.")

    @bot.message_handler(commands=['start'])
    def send_welcome(message):
        log_print(f"📩 [АКТИВНОСТЬ]: Старт от {message.from_user.first_name}")
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton("📍 Мое небо", request_location=True))
        bot.send_message(message.chat.id, "Прием! Я Марти Астроном. Нажми кнопку ниже!", reply_markup=markup)

    @bot.message_handler(content_types=['location'])
    def handle_location(message):
        log_print(f"📍 [ЛОКАЦИЯ]: Запрос принят.")
        bot.send_message(message.chat.id, "🛰 Рисую карту звезд...")
        try:
            path = generate_star_map(message.location.latitude, message.location.longitude, message.from_user.first_name)
            with open(path, 'rb') as f:
                bot.send_photo(message.chat.id, f, caption="🌟 ТВОЁ НЕБО ГОТОВО! 🐩📸")
        except Exception as e:
            log_print(f"❌ [ОШИБКА]: {e}")
            bot.send_message(message.chat.id, "⚠️ Ошибка телескопа.")

    @bot.message_handler(func=lambda m: True)
    def echo_all(message):
        log_print(f"💬 [ТЕКСТ]: Контакт! Получено: {message.text}")
        bot.reply_to(message, "Я на связи! Нажми кнопку для карты.")

else:
    log_print("❌ [ОШИБКА]: Нет токена!")
    bot = None

def start_martin():
    if not bot: return
    log_print("🚀 [ЭФИР]: Марти Астроном начал сканирование...")
    
    while True:
        try:
            # ТАЙМАУТ 10 СЕКУНД — чтобы успеть до разрыва связи сервером
            bot.polling(none_stop=True, interval=1, timeout=10, long_polling_timeout=5)
        except Exception as e:
            # Если это таймаут — не пишем его в логи как ошибку, это норма
            if "read timeout" not in str(e).lower():
                log_print(f"📡 [СВЯЗЬ]: {e}")
            time.sleep(2)

if __name__ == "__main__":
    Thread(target=run_flask, daemon=True).start()
    start_martin()
