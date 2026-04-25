import os
import telebot
import json
import random
import ephem
from threading import Thread
from flask import Flask
from datetime import datetime
from draw_map import generate_star_map

# --- 1. ПОДДЕРЖКА РАБОТОСПОСОБНОСТИ ---
app = Flask('')
@app.route('/')
def home(): return "Мартин на связи! 🛰️"
def keep_alive(): Thread(target=lambda: app.run(host='0.0.0.0', port=8080)).start()

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
    # УСИЛЕННАЯ ПРОВЕРКА: ищем 'get_map' в тексте сообщения
    if "get_map" in message.text:
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add(telebot.types.KeyboardButton("📍 Отправить локацию для карты", request_location=True))
        
        bot.send_message(message.chat.id, 
            "🛰 **Прием! Вижу запрос на карту неба.**\n\n"
            "Чтобы я настроил линзы телескопов на твой город, нажми кнопку ниже. "
            "Я нарисую карту и сразу пришлю её тебе! 🐩🚀", 
            reply_markup=markup, parse_mode='Markdown')
        return

    # Обычное меню
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🎲 Случайное созвездие", "📋 Список созвездий")
    markup.add(telebot.types.KeyboardButton("📍 Определить мое небо", request_location=True))
    bot.send_message(message.chat.id, "Привет! Я Мартин. 🌌 Чем займемся сегодня?", reply_markup=markup)

@bot.message_handler(content_types=['location'])
def handle_location(message):
    lat, lon = message.location.latitude, message.location.longitude
    user_name = message.from_user.first_name
    
    bot.send_message(message.chat.id, "🛰 Координаты получены. Запускаю рендеринг звездной сферы...")
    
    try:
        photo_path = generate_star_map(lat, lon, user_name)
        with open(photo_path, 'rb') as photo:
            bot.send_photo(
                message.chat.id, 
                photo, 
                caption="🌟 **ТВОЁ НЕБО ГОТОВО!**\n\n"
                        "Делай скриншот и отправляй его в комментарии к посту! "
                        "Марти будет очень рад увидеть твои звезды! 🐩📸",
                parse_mode='Markdown',
                reply_markup=telebot.types.ReplyKeyboardRemove()
            )
    except Exception as e:
        bot.send_message(message.chat.id, "❌ Ошибка при рисовании карты. Но я все равно посчитал созвездие!")

    # Инфо про созвездие
    key = get_best_constellation(lat, lon)
    data = load_data()
    info = data.get(key, {})
    bot.send_message(message.chat.id, format_full_info(key, info, "🔭 **Прямо сейчас над тобой:**\n\n"), parse_mode='Markdown')

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    data = load_data()
    text = message.text.strip()

    if text == "🎲 Случайное созвездие":
        key = random.choice(list(data.keys()))
        info = data[key]
        bot.send_message(message.chat.id, format_full_info(key, info), parse_mode='Markdown')
    
    elif text == "📋 Список созвездий":
        seasons_map = {"winter": "❄️", "spring": "🌱", "summer": "☀️", "autumn": "🍂", "all year": "🔄"}
        full_message = "📍 **Атлас созвездий**\n\n"
        for s_id, icon in seasons_map.items():
            group = [f"• {inf.get('name')} {inf.get('difficulty', '⭐')}" 
                     for k, inf in data.items() if inf.get('season') == s_id]
            if group:
                full_message += f"{icon} **{s_id.upper()}**\n" + "\n".join(group) + "\n\n"
        bot.send_message(message.chat.id, full_message, parse_mode='Markdown')
    
    else:
        # Поиск по названию
        found = False
        for key, info in data.items():
            if text.lower() in info.get('name', '').lower():
                bot.send_message(message.chat.id, format_full_info(key, info), parse_mode='Markdown')
                found = True
                break
        if not found:
            bot.send_message(message.chat.id, "🔭 В моих звездных атласах такого нет. Попробуй другое!")

if __name__ == "__main__":
    keep_alive()
    bot.polling(none_stop=True)
