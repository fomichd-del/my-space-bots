import os
import telebot
import json
import random
import ephem
from threading import Thread
from flask import Flask
from datetime import datetime

# --- БЕЗОПАСНЫЙ ИМПОРТ ---
try:
    from draw_map import generate_star_map
    CAN_DRAW = True
except ImportError:
    print("⚠️ ПРЕДУПРЕЖДЕНИЕ: Файл draw_map.py не найден. Работаю в текстовом режиме.")
    CAN_DRAW = False

# --- 1. ПОДДЕРЖКА РАБОТОСПОСОБНОСТИ ---
app = Flask('')
@app.route('/')
def home(): return "Мартин на связи! 🛰️"

def run(): app.run(host='0.0.0.0', port=10000) # Render предпочитает порт 10000
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
    name = info.get('name', key.replace('_', ' ').capitalize())
    return (
        f"{title_prefix}✨ **{name}**\n\n"
        f"🔭 **Описание:** {info.get('description', '...')}\n"
        f"📜 **История:** {info.get('history', '...')}\n"
        f"💡 **Секрет:** {info.get('secret', '...')}\n"
        f"📊 **Сложность:** {info.get('difficulty', '⭐⭐')}\n"
        f"📅 **Сезон:** {info.get('season', 'Не указан')}"
    )

# --- 4. ОБРАБОТКА КОМАНД ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    text_parts = message.text.split()
    if len(text_parts) > 1 and text_parts[1] == "get_map":
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add(telebot.types.KeyboardButton("📍 ОТПРАВИТЬ КООРДИНАТЫ", request_location=True))
        bot.send_message(message.chat.id, 
            "🛰 **Вижу запрос на карту!**\n\nНажми кнопку ниже, чтобы я настроил линзы телескопов!", 
            reply_markup=markup, parse_mode='Markdown')
        return

    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("🎲 Случайное созвездие", "📋 Список созвездий")
    markup.row(telebot.types.KeyboardButton("📍 Определить мое небо", request_location=True))
    bot.send_message(message.chat.id, "Привет! Я Мартин. 🌌 Чем займемся?", reply_markup=markup)

@bot.message_handler(content_types=['location'])
def handle_location(message):
    lat, lon = message.location.latitude, message.location.longitude
    user_name = message.from_user.first_name
    bot.send_message(message.chat.id, "🛰 Координаты в базе! Сканирую небо...")
    
    if CAN_DRAW:
        try:
            photo_path = generate_star_map(lat, lon, user_name)
            with open(photo_path, 'rb') as photo:
                bot.send_photo(message.chat.id, photo, caption="🌟 ТВОЁ НЕБО ГОТОВО! 🐩📸")
        except:
            bot.send_message(message.chat.id, "⚠️ Ошибка при рисовании карты. Но созвездие я нашел!")
    else:
        bot.send_message(message.chat.id, "🔭 Режим фото на техобслуживании. Смотри текстовый отчет!")

    key = get_best_constellation(lat, lon)
    bot.send_message(message.chat.id, format_full_info(key, load_data().get(key, {}), "🔭 Сейчас над тобой:\n\n"), parse_mode='Markdown')

if __name__ == "__main__":
    keep_alive()
    bot.polling(none_stop=True)
