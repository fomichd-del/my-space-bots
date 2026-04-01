import os
import telebot
import json
import random
import ephem
from threading import Thread
from flask import Flask
from datetime import datetime

# --- 1. ПОДДЕРЖКА РАБОТОСПОСОБНОСТИ ---
app = Flask('')
@app.route('/')
def home(): return "Мартин на связи! 🛰️"

def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive(): Thread(target=run).start()

# --- 2. НАСТРОЙКА БОТА ---
TOKEN = os.getenv('TELEGRAM_TOKEN')
bot = telebot.TeleBot(TOKEN)

def load_data():
    try:
        with open('constellations.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except: return {}

# --- 3. АСТРОНОМИЧЕСКАЯ ЛОГИКА ---

def get_best_constellation(lat, lon):
    """Находит созвездие, которое сейчас прямо над пользователем"""
    data = load_data()
    obs = ephem.Observer()
    obs.lat, obs.lon = str(lat), str(lon)
    obs.date = datetime.utcnow()
    
    try:
        # Библиотека определяет созвездие по координатам зенита
        _, zenith_const_id = ephem.constellation((obs.lat, obs.lon))
        
        # Ищем это созвездие в нашей базе по ID
        for key, info in data.items():
            if info.get('id') == zenith_const_id:
                return key
    except:
        pass
    return random.choice(list(data.keys()))

# --- 4. ОБРАБОТКА КОМАНД ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🎲 Случайное созвездие", "📋 Список созвездий")
    markup.add(telebot.types.KeyboardButton("📍 Определить мое небо", request_location=True))
    
    bot.send_message(
        message.chat.id, 
        "Привет! Я Мартин. 🌌 Нажми кнопку ниже, и я покажу, что сияет прямо над тобой!", 
        reply_markup=markup
    )

@bot.message_handler(content_types=['location'])
def handle_location(message):
    lat = message.location.latitude
    lon = message.location.longitude
    
    # Делаем расчет
    const_key = get_best_constellation(lat, lon)
    info = load_data().get(const_key, {})
    
    response = (
        f"📍 **Твое небо настроено!**\n"
        f"Прямо сейчас над тобой главенствует:\n\n"
        f"✨ **{info.get('name', const_key)}**\n"
        f"🔭 {info.get('description', 'Загадочное созвездие...')}\n\n"
        f"📜 {info.get('history', 'История скрыта в веках.')}\n"
        f"💡 **Секрет:** {info.get('secret')}"
    )
    bot.send_message(message.chat.id, response, parse_mode='Markdown')

@bot.message_handler(func=lambda m: True)
def handle_text(message):
    data = load_data()
    if message.text == "🎲 Случайное созвездие":
        key = random.choice(list(data.keys()))
        info = data[key]
        bot.send_message(message.chat.id, f"✨ **{info.get('name')}**\n\n{info.get('description')}", parse_mode='Markdown')
    elif message.text == "📋 Список созвездий":
        names = [v.get('name') for v in data.values()]
        bot.send_message(message.chat.id, f"📍 В моем атласе 88 созвездий:\n\n" + ", ".join(names[:40]) + "...")

if __name__ == "__main__":
    keep_alive()
    bot.polling(none_stop=True)
