import os
import telebot
from telebot import types
from flask import Flask
from threading import Thread
from draw_map import generate_star_map

# 1. Настройка Flask (чтобы Render видел, что бот работает)
app = Flask('')

@app.route('/')
def home():
    return "Марти Астроном: Связь с Землей установлена! 🚀"

def run_flask():
    # Render сам назначит порт
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# 2. Настройка бота
TOKEN = os.environ.get('TELEGRAM_TOKEN')
bot = telebot.TeleBot(TOKEN, threaded=False)

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn = types.KeyboardButton("📍 Мое небо", request_location=True)
    markup.add(btn)
    bot.send_message(message.chat.id, f"Прием, {message.from_user.first_name}! Я Марти Астроном. 🐩🔭\nНажми кнопку ниже, и я нарисую карту звезд прямо над тобой!", reply_markup=markup)

@bot.message_handler(content_types=['location'])
def handle_location(message):
    bot.send_message(message.chat.id, "🛰 Секунду! Навожу телескопы на твои координаты...")
    try:
        path = generate_star_map(message.location.latitude, message.location.longitude, message.from_user.first_name)
        with open(path, 'rb') as photo:
            bot.send_photo(message.chat.id, photo, caption="🌟 ТВОЁ НЕБО ГОТОВО! 📸")
    except Exception as e:
        bot.send_message(message.chat.id, "⚠️ Техническая заминка в обсерватории. Попробуй еще раз.")

@bot.message_handler(func=lambda m: True)
def echo(message):
    bot.reply_to(message, "Я тебя слышу! Используй кнопку 'Мое небо', чтобы увидеть звезды.")

if __name__ == "__main__":
    # Запускаем "маяк" для Render
    t = Thread(target=run_flask)
    t.start()
    
    # Запускаем бота
    print("🚀 Марти Астроном вышел на орбиту!")
    bot.infinity_polling()
