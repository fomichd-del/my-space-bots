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
    bot = telebot.TeleBot(TOKEN, threaded=False)
    
    @bot.message_handler(commands=['start'])
    def start(message):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn = types.KeyboardButton("📍 Мое небо", request_location=True)
        markup.add(btn)
        bot.send_message(message.chat.id, "Прием! Жми кнопку 'Мое небо'!", reply_markup=markup)

    @bot.message_handler(content_types=['location'])
    def handle_location(message):
        bot.send_message(message.chat.id, "🛰 Координаты приняты. Запускаю рендер...")
        try:
            lat = message.location.latitude
            lon = message.location.longitude
            
            # Получаем статус (успех или ошибка) и результат
            success, result = generate_star_map(lat, lon, message.from_user.first_name)
            
            if success:
                with open(result, 'rb') as photo:
                    bot.send_photo(message.chat.id, photo, caption="✨ Карта готова!")
            else:
                # ЕСЛИ ОШИБКА - БОТ ПРИШЛЕТ ЕЕ ТЕБЕ В ЧАТ
                bot.send_message(message.chat.id, f"⚠️ ТЕХНИЧЕСКИЙ ОТЧЕТ:\n{result}")
                
        except Exception as e:
            bot.send_message(message.chat.id, f"⚠️ Ошибка в main.py:\n{str(e)}")

    def start_polling():
        while True:
            try:
                bot.remove_webhook()
                bot.polling(none_stop=True, interval=1, timeout=20)
            except Exception as e:
                time.sleep(5)

    if __name__ == "__main__":
        t = Thread(target=run_flask)
        t.start()
        start_polling()
