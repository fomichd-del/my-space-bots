import os
import telebot
from telebot import types
import json
import random
from threading import Thread
from flask import Flask
from draw_map import generate_star_map

# 1. ЗАГЛУШКА ДЛЯ HF (Чтобы Space не засыпал)
app = Flask('')
@app.route('/')
def home(): return "Martin Star Bot is running! 🛰️"

def run():
    # Hugging Face обычно использует порт 7860
    port = int(os.environ.get("PORT", 7860))
    app.run(host='0.0.0.0', port=port)

# 2. ПОЛУЧАЕМ ТОКЕН ИЗ СЕКРЕТОВ
TOKEN = os.environ.get('TELEGRAM_TOKEN')
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    if "get_map" in message.text:
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
    bot.send_message(message.chat.id, "🛰 Начинаю рендеринг звездной сферы...")
    try:
        path = generate_star_map(message.location.latitude, message.location.longitude, message.from_user.first_name)
        with open(path, 'rb') as f:
            bot.send_photo(message.chat.id, f, caption="🌟 **ТВОЁ НЕБО ГОТОВО!**\n\nОтправляй его в канал Space News! 🐩🚀", parse_mode='Markdown')
    except Exception as e:
        bot.send_message(message.chat.id, "⚠️ Ошибка телескопа. Попробуй позже.")

if __name__ == "__main__":
    Thread(target=run).start()
    bot.polling(none_stop=True)
