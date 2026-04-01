import os
import telebot
import json
import random
import ephem
from threading import Thread
from flask import Flask
from datetime import datetime

# --- ПОДДЕРЖКА РАБОТОСПОСОБНОСТИ ---
app = Flask('')
@app.route('/')
def home(): return "Мартин на связи! 🛰️"

def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive(): Thread(target=run).start()

# --- НАСТРОЙКА БОТА ---
TOKEN = os.getenv('TELEGRAM_TOKEN')
bot = telebot.TeleBot(TOKEN)

def load_data():
    try:
        with open('constellations.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except: return {}

def get_visible_const(lat, lon):
    data = load_data()
    obs = ephem.Observer()
    obs.lat, obs.lon = str(lat), str(lon)
    obs.date = datetime.utcnow()
    
    # Определяем созвездие прямо в зените
    try:
        zenith_const_id = ephem.constellation((obs.lat, obs.lon))[1]
        for key, info in data.items():
            if info.get('id') == zenith_const_id:
                return key
    except: pass
    return random.choice(list(data.keys()))

# --- ОБРАБОТКА КОМАНД ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🎲 Случайное созвездие", "📋 Список созвездий")
    markup.add(telebot.types.KeyboardButton("📍 Определить мое небо", request_location=True))
    bot.send_message(message.chat.id, "Привет! Я Мартин. Отправь локацию, чтобы увидеть свое небо! 🔭", reply_markup=markup)

@bot.message_handler(content_types=['location'])
def handle_location(message):
    key = get_visible_const(message.location.latitude, message.location.longitude)
    info = load_data().get(key, {})
    res = f"📍 Над тобой сейчас: **{info.get('name', key)}**\n\n✨ {info.get('description')}\n\n💡 {info.get('secret')}"
    bot.send_message(message.chat.id, res, parse_mode='Markdown')

@bot.message_handler(func=lambda m: True)
def handle_text(message):
    data = load_data()
    if message.text == "🎲 Случайное созвездие":
        key = random.choice(list(data.keys()))
        info = data[key]
        bot.send_message(message.chat.id, f"✨ **{info.get('name')}**\n\n{info.get('description')}", parse_mode='Markdown')
    elif message.text == "📋 Список созвездий":
        names = [v.get('name') for v in data.values()]
        bot.send_message(message.chat.id, f"📍 Все 88 созвездий:\n\n" + ", ".join(names[:40])) # Часть списка

if __name__ == "__main__":
    keep_alive()
    bot.polling(none_stop=True)
