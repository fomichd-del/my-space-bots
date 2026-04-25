import os
import telebot
import json
import random
import ephem
from threading import Thread
from flask import Flask
from datetime import datetime
from draw_map import generate_star_map  # Подключаем твой новый модуль рисования

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
    # Проверка на переход из канала (глубокая ссылка)
    if "get_map" in message.text:
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add(telebot.types.KeyboardButton("📍 Отправить локацию для карты", request_location=True))
        bot.send_message(message.chat.id, 
            "🚀 Привет! Я готов нарисовать твою карту неба. Нажми кнопку ниже, чтобы я настроил телескопы на твои координаты!", 
            reply_markup=markup)
        return

    # Обычный старт бота
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🎲 Случайное созвездие", "📋 Список созвездий")
    markup.add(telebot.types.KeyboardButton("📍 Определить мое небо", request_location=True))
    bot.send_message(message.chat.id, "Привет! Я Мартин. 🌌 Выбирай команду или отправь координаты!", reply_markup=markup)

@bot.message_handler(content_types=['location'])
def handle_location(message):
    lat = message.location.latitude
    lon = message.location.longitude
    user_name = message.from_user.first_name
    
    bot.send_message(message.chat.id, "🛰 Принимаю сигнал... Рисую твою персональную карту!")
    
    # 1. Генерируем изображение через draw_map.py
    try:
        photo_path = generate_star_map(lat, lon, user_name)
        with open(photo_path, 'rb') as photo:
            bot.send_photo(
                message.chat.id, 
                photo, 
                caption="🌟 Вот твоё небо прямо сейчас! Сделай скриншот и поделись им в комментариях канала. 🐩🚀",
                reply_markup=telebot.types.ReplyKeyboardRemove()
            )
    except Exception as e:
        bot.send_message(message.chat.id, "❌ Упс! Ошибка при проявке космического снимка. Но я все равно вижу звезды!")

    # 2. Текстовая информация о созвездии в зените
    key = get_best_constellation(lat, lon)
    data = load_data()
    info = data.get(key, {})
    reply = format_full_info(key, info, title_prefix="🔭 **Прямо над тобой сейчас:**\n\n")
    bot.send_message(message.chat.id, reply, parse_mode='Markdown')

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    data = load_data()
    text = message.text.strip()

    # Кнопка: Случайное созвездие
    if text == "🎲 Случайное созвездие":
        key = random.choice(list(data.keys()))
        info = data[key]
        bot.send_message(message.chat.id, format_full_info(key, info), parse_mode='Markdown')
        return

    # Кнопка: Список созвездий
    if text == "📋 Список созвездий":
        seasons_map = {
            "winter": "❄️ **Зимние**",
            "spring": "🌱 **Весенние**",
            "summer": "☀️ **Летние**",
            "autumn": "🍂 **Осенние**",
            "all year": "🔄 **Видны всегда**"
        }
        
        full_message = "📍 **Атлас созвездий**\n\n"
        for season_id, title in seasons_map.items():
            group = [f"• {info.get('name')} {info.get('difficulty', '⭐')}" 
                     for k, info in data.items() if info.get('season') == season_id]
            if group:
                full_message += f"{title}\n" + "\n".join(group) + "\n\n"
        
        bot.send_message(message.chat.id, full_message, parse_mode='Markdown')
        return

    # Поиск по названию созвездия
    for key, info in data.items():
        if text.lower() in info.get('name', '').lower():
            bot.send_message(message.chat.id, format_full_info(key, info), parse_mode='Markdown')
            return
            
    bot.send_message(message.chat.id, "🔭 Такого созвездия нет в моих картах. Попробуй другое!")

if __name__ == "__main__":
    keep_alive()
    bot.polling(none_stop=True)
