import os
import telebot
import json
import random
import ephem
from threading import Thread
from flask import Flask
from datetime import datetime
from draw_map import generate_star_map

# --- 1. ЖИЗНЕОБЕСПЕЧЕНИЕ (RENDER) ---
app = Flask('')
@app.route('/')
def home(): return "Мартин на связи! 🛰️"

def run():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- 2. НАСТРОЙКА БОТА ---
TOKEN = os.getenv('TELEGRAM_TOKEN')
bot = telebot.TeleBot(TOKEN)

def load_data():
    try:
        with open('constellations.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except: return {}

# --- 3. ЛОГИКА ---
def get_best_constellation(lat, lon):
    data = load_data()
    obs = ephem.Observer()
    obs.lat, obs.lon = str(lat), str(lon)
    obs.date = datetime.utcnow()
    try:
        _, zenith_const_id = ephem.constellation((obs.lat, obs.lon))
        for key, info in data.items():
            if info.get('id') == zenith_const_id: return key
    except: pass
    return random.choice(list(data.keys()))

# --- 4. ОБРАБОТЧИК START ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    # Проверяем текст сообщения целиком
    full_text = message.text or ""
    
    # Если в команде есть get_map (даже если Telegram склеил их)
    if "get_map" in full_text:
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add(telebot.types.KeyboardButton("📍 ОТПРАВИТЬ МОИ КООРДИНАТЫ", request_location=True))
        
        bot.send_message(message.chat.id, 
            "🛰 **Прием, штурман! Секретный код распознан.**\n\n"
            "Нажми кнопку ниже, чтобы я прислал тебе карту неба над твоей головой! 🐩🚀", 
            reply_markup=markup, parse_mode='Markdown')
        return

    # Обычное приветствие
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("🎲 Случайное созвездие", "📋 Список созвездий")
    markup.row(telebot.types.KeyboardButton("📍 Определить мое небо", request_location=True))
    bot.send_message(message.chat.id, "Привет! Я Мартин. 🌌 Чем займемся?", reply_markup=markup)

@bot.message_handler(content_types=['location'])
def handle_location(message):
    bot.send_message(message.chat.id, "🛰 Секунду, настраиваю линзы телескопов...")
    try:
        path = generate_star_map(message.location.latitude, message.location.longitude, message.from_user.first_name)
        with open(path, 'rb') as f:
            bot.send_photo(message.chat.id, f, caption="🌟 **ТВОЁ НЕБО ГОТОВО!**\n\nСкорее отправляй скриншот в комментарии канала! 🐩📸")
    except:
        bot.send_message(message.chat.id, "⚠️ Ошибка связи! Но созвездие я нашел.")

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    # Логика кнопок (Случайное, Список и т.д.) остается прежней
    if message.text == "🎲 Случайное созвездие":
        data = load_data()
        key = random.choice(list(data.keys()))
        bot.send_message(message.chat.id, f"✨ **{data[key].get('name')}**\n\n{data[key].get('description')}", parse_mode='Markdown')

if __name__ == "__main__":
    Thread(target=run).start()
    bot.polling(none_stop=True)
