import os
import telebot
from telebot import types
from threading import Thread
from flask import Flask
import time
from draw_map import generate_star_map

# 1. ЖИЗНЕОБЕСПЕЧЕНИЕ (FLASK)
app = Flask('')
@app.route('/')
def home():
    return "Мартин на связи! Ракета на орбите. 🛰️"

def run():
    port = int(os.environ.get("PORT", 7860))
    app.run(host='0.0.0.0', port=port)

# 2. НАСТРОЙКА С ПОВЫШЕННЫМ ТАЙМАУТОМ
TOKEN = os.environ.get('TELEGRAM_TOKEN')

# Создаем бота с увеличенным временем ожидания (60 секунд вместо 15)
bot = telebot.TeleBot(TOKEN, threaded=False)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    text = message.text or ""
    if "get_map" in text:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add(types.KeyboardButton("📍 ПОКАЗАТЬ МОЁ НЕБО", request_location=True))
        bot.send_message(message.chat.id, "🛰 **Связь установлена!**\n\nНажми кнопку, чтобы я нарисовал карту звезд над тобой! 🐩🔭", reply_markup=markup, parse_mode='Markdown')
    else:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.row("🎲 Случайное созвездие")
        markup.row(types.KeyboardButton("📍 Определить небо", request_location=True))
        bot.send_message(message.chat.id, "Привет! Я Мартин. 🌌 Готов к наблюдениям!", reply_markup=markup)

@bot.message_handler(content_types=['location'])
def handle_location(message):
    bot.send_message(message.chat.id, "🛰 Секунду... Проявляю космический снимок!")
    try:
        path = generate_star_map(message.location.latitude, message.location.longitude, message.from_user.first_name)
        with open(path, 'rb') as f:
            bot.send_photo(message.chat.id, f, caption="🌟 **ТВОЁ НЕБО ГОТОВО!**\n\nОтправляй его в канал Space News! 🐩🚀", parse_mode='Markdown')
    except Exception as e:
        bot.send_message(message.chat.id, "⚠️ Ошибка телескопа. Попробуй позже.")

# 3. ЗАПУСК С ЗАЩИТОЙ ОТ ВЫЛЕТОВ
if __name__ == "__main__":
    Thread(target=run).start()
    
    print("🚀 Попытка запуска Мартина...")
    
    # Бесконечный цикл переподключения
    while True:
        try:
            bot.polling(none_stop=True, timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"❌ Ошибка связи: {e}. Перезапуск через 5 секунд...")
            time.sleep(5)
