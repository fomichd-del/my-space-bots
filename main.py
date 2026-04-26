import os
import sys
import telebot
from telebot import types
from threading import Thread
from flask import Flask
import time
from draw_map import generate_star_map

# Принудительный вывод в консоль
def log_print(msg):
    print(msg)
    sys.stdout.flush()

app = Flask('')

@app.route('/')
def home():
    return "Марти Астроном: В эфире!"

def run_flask():
    port = int(os.environ.get("PORT", 7860))
    app.run(host='0.0.0.0', port=port)

# ПОДГОТОВКА ТОКЕНА
TOKEN = os.environ.get('TELEGRAM_TOKEN', '').strip()

if TOKEN:
    # Инициализация БЕЗ автоматических запросов к API
    bot = telebot.TeleBot(TOKEN, threaded=False)
    log_print("✅ [СИСТЕМА]: Код загружен. Попытка скрытого подключения...")

    @bot.message_handler(commands=['start'])
    def send_welcome(message):
        log_print(f"📩 [АКТИВНОСТЬ]: Старт!")
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
        log_print(f"💬 [ТЕКСТ]: Есть контакт!")
        bot.reply_to(message, "Я на связи!")

else:
    log_print("❌ [ОШИБКА]: Нет токена!")
    bot = None

def start_martin():
    if not bot: return
    log_print("🚀 [ЭФИР]: Марти Астроном заступил на дежурство!")
    
    while True:
        try:
            # Используем самый короткий интервал и таймаут, чтобы не раздражать прокси Hugging Face
            bot.polling(none_stop=True, interval=2, timeout=20)
        except Exception as e:
            # Если ошибка SSL — не паникуем, просто ждем и пробуем снова
            log_print(f"📡 [СВЯЗЬ]: Ищу сигнал... ({e})")
            time.sleep(10)

if __name__ == "__main__":
    Thread(target=run_flask, daemon=True).start()
    start_martin()
