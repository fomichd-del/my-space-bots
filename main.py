import os
import telebot
import json
import random
import ephem
from threading import Thread
from flask import Flask
from datetime import datetime
from draw_map import generate_star_map # Наш новый файл

app = Flask('')
@app.route('/')
def home(): return "Мартин на связи! 🛰️"
def keep_alive(): Thread(target=lambda: app.run(host='0.0.0.0', port=8080)).start()

TOKEN = os.getenv('TELEGRAM_TOKEN')
bot = telebot.TeleBot(TOKEN)

def load_data():
    try:
        with open('constellations.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except: return {}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    # Если человек пришел по кнопке из канала
    if "get_map" in message.text:
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add(telebot.types.KeyboardButton("📍 Отправить локацию для карты", request_location=True))
        bot.send_message(message.chat.id, "🚀 Привет! Чтобы я нарисовал карту неба над твоей головой, нажми на кнопку внизу!", reply_markup=markup)
        return

    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🎲 Случайное созвездие", "📋 Список созвездий")
    markup.add(telebot.types.KeyboardButton("📍 Определить мое небо", request_location=True))
    bot.send_message(message.chat.id, "Привет! Я Мартин. 🌌 Выбирай команду!", reply_markup=markup)

@bot.message_handler(content_types=['location'])
def handle_location(message):
    lat, lon = message.location.latitude, message.location.longitude
    user_name = message.from_user.first_name
    bot.send_message(message.chat.id, "🛰 Принимаю координаты... Рисую твою карту!")
    
    photo_path = generate_star_map(lat, lon, user_name)
    
    with open(photo_path, 'rb') as photo:
        bot.send_photo(message.chat.id, photo, 
                       caption="🌟 Вот твоё небо! Скорее делай скриншот и отправляй его в комментарии канала! 🐩🚀",
                       reply_markup=telebot.types.ReplyKeyboardRemove())

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    # Тут остается твоя логика поиска созвездий (🎲 Случайное и т.д.)
    # Просто оставь код из своего старого main.py ниже
    pass

if __name__ == "__main__":
    keep_alive()
    bot.polling(none_stop=True)
