import os
import telebot
import json
import random
import ephem
from threading import Thread
from flask import Flask
from datetime import datetime

# --- 1. ПОДДЕРЖКА РАБОТОСПОСОБНОСТИ (FLASK) ---
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
    """Определяет созвездие в зените над пользователем"""
    data = load_data()
    obs = ephem.Observer()
    obs.lat, obs.lon = str(lat), str(lon)
    obs.date = datetime.utcnow()
    try:
        _, zenith_const_id = ephem.constellation((obs.lat, obs.lon))
        for key, info in data.items():
            if info.get('id') == zenith_const_id:
                return key
    except: pass
    return random.choice(list(data.keys()))

def format_full_info(key, info, title_prefix=""):
    """Красивое оформление карточки созвездия"""
    name = info.get('name', key.replace('_', ' ').capitalize())
    return (
        f"{title_prefix}✨ **{name}**\n\n"
        f"🔭 **Описание:** {info.get('description', '...')}\n\n"
        f"📜 **История:** {info.get('history', '...')}\n\n"
        f"💡 **Секрет:** {info.get('secret', '...')}\n"
        f"📊 **Сложность:** {info.get('difficulty', '⭐⭐')}\n"
        f"📅 **Сезон:** {info.get('season', 'Не указан')}"
    )

# --- 4. ОБРАБОТКА КОМАНД ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🎲 Случайное созвездие", "📋 Список созвездий")
    markup.add(telebot.types.KeyboardButton("📍 Определить мое небо", request_location=True))
    bot.send_message(message.chat.id, "Привет! Я Мартин. 🌌 Нажми кнопку, чтобы начать!", reply_markup=markup)

@bot.message_handler(content_types=['location'])
def handle_location(message):
    key = get_best_constellation(message.location.latitude, message.location.longitude)
    data = load_data()
    info = data.get(key, {})
    reply = format_full_info(key, info, title_prefix="📍 **Твое небо настроено!**\n\n")
    bot.send_message(message.chat.id, reply, parse_mode='Markdown')

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    data = load_data()
    text = message.text.strip()

    if text == "🎲 Случайное созвездие":
        key = random.choice(list(data.keys()))
        info = data[key]
        bot.send_message(message.chat.id, format_full_info(key, info), parse_mode='Markdown')
        return

    if text == "📋 Список созвездий":
        seasons_map = {
            "winter": "❄️ **Зимние**",
            "spring": "🌱 **Весенние**",
            "summer": "☀️ **Летние**",
            "autumn": "🍂 **Осенние**",
            "all year": "🔄 **Видны всегда**"
        }
        
        # Собираем всё в одну строку
        full_list = "📍 **Атлас созвездий**\n\n"
        
        for season_id, title in seasons_map.items():
            group = [f"• {info.get('name')} {info.get('difficulty', '⭐')}" 
                     for k, info in data.items() if info.get('season') == season_id]
            if group:
                full_list += f"{title}\n" + "\n".join(group) + "\n\n"
        
        bot.send_message(message.chat.id, full_list, parse_mode='Markdown')
        return

    # Поиск по названию
    for key, info in data.items():
        if text.lower() in info.get('name', '').lower():
            bot.send_message(message.chat.id, format_full_info(key, info), parse_mode='Markdown')
            return
    bot.send_message(message.chat.id, "🔭 Такого созвездия нет в моих картах.")

if __name__ == "__main__":
    keep_alive()
    bot.polling(none_stop=True)
