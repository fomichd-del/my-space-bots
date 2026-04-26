import os
import sys
import telebot
from telebot import types, apihelper
from threading import Thread
from flask import Flask
import time
from draw_map import generate_star_map

def log_print(msg):
    print(msg)
    sys.stdout.flush()

# УСТАНАВЛИВАЕМ ГИГАНТСКИЕ ТАЙМАУТЫ
apihelper.CONNECT_TIMEOUT = 120
apihelper.READ_TIMEOUT = 120

app = Flask('')

@app.route('/')
def home():
    return "Марти Астроном: Жду сигнал из космоса! 🔭"

def run_flask():
    port = int(os.environ.get("PORT", 7860))
    app.run(host='0.0.0.0', port=port)

TOKEN = os.environ.get('TELEGRAM_TOKEN', '').strip()

if TOKEN:
    bot = telebot.TeleBot(TOKEN, threaded=False)
    log_print("✅ [СИСТЕМА]: Код загружен. Режим глубокого ожидания.")

    @bot.message_handler(commands=['start'])
    def send_welcome(message):
        log_print(f"📩 [УСПЕХ]: Получен СТАРТ от {message.from_user.first_name}!")
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton("📍 Мое небо", request_location=True))
        bot.send_message(message.chat.id, "Прием! Я Марти Астроном. Наконец-то связь налажена! Нажми кнопку ниже.", reply_markup=markup)

    @bot.message_handler(content_types=['location'])
    def handle_location(message):
        log_print(f"📍 [ЛОКАЦИЯ]: Рисую карту...")
        bot.send_message(message.chat.id, "🛰 Навожу телескопы...")
        try:
            path = generate_star_map(message.location.latitude, message.location.longitude, message.from_user.first_name)
            with open(path, 'rb') as f:
                bot.send_photo(message.chat.id, f, caption="🌟 ТВОЁ НЕБО ГОТОВО! 🐩📸")
        except Exception as e:
            log_print(f"❌ [ОШИБКА]: {e}")
            bot.send_message(message.chat.id, "⚠️ Ошибка телескопа.")

    @bot.message_handler(func=lambda m: True)
    def echo_all(message):
        log_print(f"💬 [ТЕКСТ]: Получено сообщение: {message.text}")
        bot.reply_to(message, "Слышу тебя громко и четко! Нажми кнопку для карты.")

else:
    log_print("❌ [ОШИБКА]: Токен не найден!")
    bot = None

def start_martin():
    if not bot: return
    log_print("🚀 [ЭФИР]: Марти Астроном начал слушать космос...")
    
    while True:
        try:
            # УВЕЛИЧИВАЕМ ТАЙМАУТ ПОЛЛИНГА ДО 20 СЕКУНД
            bot.polling(none_stop=True, interval=2, timeout=20)
        except Exception as e:
            # Если это таймаут — это нормально для HF, просто пробуем снова
            if "timeout" in str(e).lower():
                time.sleep(1)
            else:
                log_print(f"📡 [СВЯЗЬ]: Попытка прорыва... ({e})")
                time.sleep(5)

if __name__ == "__main__":
    Thread(target=run_flask, daemon=True).start()
    start_martin()
