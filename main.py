import os
import telebot
from telebot import types
from flask import Flask
from threading import Thread
from draw_map import generate_star_map

# 1. Настройка Flask (Маяк для Render)
app = Flask('')

@app.route('/')
def home():
    return "OK" # Короткий ответ для Cron-job

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# 2. Настройка бота
TOKEN = os.environ.get('TELEGRAM_TOKEN', '').strip()

if TOKEN:
    bot = telebot.TeleBot(TOKEN, threaded=False)

    @bot.message_handler(commands=['start'])
    def start(message):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn = types.KeyboardButton("📍 Мое небо", request_location=True)
        markup.add(btn)
        bot.send_message(message.chat.id, 
                         f"Прием, {message.from_user.first_name}! Я Марти Астроном. 🐩🔭\n"
                         f"Нажми кнопку ниже, и я нарисую карту звезд прямо над тобой!", 
                         reply_markup=markup)

    @bot.message_handler(content_types=['location'])
    def handle_location(message):
        bot.send_message(message.chat.id, "🛰 Запускаю обсерваторию... Секунду.")
        path = None
        try:
            lat = message.location.latitude
            lon = message.location.longitude
            user_name = message.from_user.first_name or "Пилот"
            
            # Генерация карты через наш draw_map
            path = generate_star_map(lat, lon, user_name)
            
            if path and os.path.exists(path):
                with open(path, 'rb') as photo:
                    bot.send_photo(message.chat.id, photo, caption="✨ ТВОЁ ПЕРСОНАЛЬНОЕ НЕБО ГОТОВО!")
                os.remove(path) # Удаляем временный файл
            else:
                bot.send_message(message.chat.id, "⚠️ Ошибка: Карта не была создана. Проверь логи!")
                
        except Exception as e:
            print(f"Ошибка в main: {e}")
            bot.send_message(message.chat.id, f"⚠️ Сбой систем: {e}")
            if path and os.path.exists(path):
                os.remove(path)

    @bot.message_handler(func=lambda m: True)
    def echo(message):
        bot.reply_to(message, "Я тебя слышу! Используй кнопку 'Мое небо', чтобы увидеть звезды.")

else:
    print("❌ ОШИБКА: Токен не найден!")
    bot = None

if __name__ == "__main__":
    t = Thread(target=run_flask)
    t.start()
    
    if bot:
        print("🚀 Марти Астроном вышел на орбиту!")
        bot.infinity_polling(timeout=20, long_polling_timeout=10)
