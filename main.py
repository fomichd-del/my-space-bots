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
    # Логика для глубоких ссылок (из канала)
    # Текст сообщения будет выглядеть так: "/start get_map"
    text_parts = message.text.split()
    
    if len(text_parts) > 1 and text_parts[1] == "get_map":
        # Создаем кнопку специально для карты
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        btn = telebot.types.KeyboardButton("📍 ОТПРАВИТЬ МОИ КООРДИНАТЫ", request_location=True)
        markup.add(btn)
        
        bot.send_message(message.chat.id, 
            "🛰 **Прием, штурман! Вижу запрос на персональную карту.**\n\n"
            "Нажми на большую кнопку внизу, чтобы я настроил линзы телескопов на твой город! 🐩🚀", 
            reply_markup=markup, parse_mode='Markdown')
        return

    # Если это обычный старт (без параметров)
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("🎲 Случайное созвездие", "📋 Список созвездий")
    markup.row(telebot.types.KeyboardButton("📍 Определить мое небо", request_location=True))
    
    bot.send_message(message.chat.id, "Привет! Я Мартин. 🌌 Чем займемся сегодня?", reply_markup=markup)

@bot.message_handler(content_types=['location'])
def handle_location(message):
    lat, lon = message.location.latitude, message.location.longitude
    user_name = message.from_user.first_name
    
    bot.send_message(message.chat.id, "🛰 Координаты в базе! Запускаю рендеринг звездной сферы...")
    
    try:
        photo_path = generate_star_map(lat, lon, user_name)
        with open(photo_path, 'rb') as photo:
            bot.send_photo(
                message.chat.id, 
                photo, 
                caption="🌟 **ТВОЁ НЕБО ГОТОВО!**\n\n"
                        "Делай скриншот и отправляй его в комментарии к посту в канале! "
                        "Марти ждет твои звезды! 🐩📸",
                parse_mode='Markdown',
                reply_markup=telebot.types.ReplyKeyboardRemove()
            )
    except Exception as e:
        bot.send_message(message.chat.id, "❌ Произошел сбой при рисовании. Но я всё равно вижу звезды над тобой!")

    # Показываем созвездие в зените
    key = get_best_constellation(lat, lon)
    data = load_data()
    info = data.get(key, {})
    bot.send_message(message.chat.id, format_full_info(key, info, "🔭 **Прямо сейчас над тобой:**\n\n"), parse_mode='Markdown')

@bot.message_handler(func=lambda message: True)
def handle_text(message):
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
