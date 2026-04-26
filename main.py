import os
import telebot
from telebot import types
from flask import Flask
from threading import Thread
import time
from draw_map import generate_star_map

app = Flask('')

@app.route('/')
def home():
    return "OK"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

TOKEN = os.environ.get('TELEGRAM_TOKEN', '').strip()

if TOKEN:
    # Отключаем многопоточность для стабильности на Render
    bot = telebot.TeleBot(TOKEN, threaded=False)
    
    # СБРОС СТАРЫХ СОЕДИНЕНИЙ (решает ошибку 409)
    bot.remove_webhook()
    time.sleep(1) 

    @bot.message_handler(commands=['start'])
    def start(message):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn = types.KeyboardButton("📍 Мое небо", request_location=True)
        markup.add(btn)
        bot.send_message(message.chat.id, "Привет! Я Марти. Жми кнопку, чтобы увидеть звезды!", reply_markup=markup)

    @bot.message_handler(content_types=['location'])
    def handle_location(message):
        bot.send_message(message.chat.id, "🛰 Обсерватория запущена...")
        path = None
        try:
            # Математика ephem иногда требует float
            lat = float(message.location.latitude)
            lon = float(message.location.longitude)
            path = generate_star_map(lat, lon, message.from_user.first_name)
            
            if path and os.path.exists(path):
                with open(path, 'rb') as photo:
                    bot.send_photo(message.chat.id, photo, caption="✨ ТВОЕ НЕБО ГОТОВО!")
                os.remove(path)
            else:
                bot.send_message(message.chat.id, "⚠️ Ошибка рисования. Проверь draw_map.py")
        except Exception as e:
            bot.send_message(message.chat.id, f"⚠️ Сбой: {e}")

else:
    bot = None

if __name__ == "__main__":
    t = Thread(target=run_flask)
    t.start()
    if bot:
        print("🚀 Марти готов к труду!")
        # Бесконечный цикл с защитой от вылетов
        while True:
            try:
                bot.polling(none_stop=True, interval=0, timeout=20)
            except Exception as e:
                print(f"Ошибка полинга: {e}")
                time.sleep(5)
