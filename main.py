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
def home():
    return "Мартин на связи! 🛰️"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- 2. НАСТРОЙКА БОТА ---
TOKEN = os.getenv('TELEGRAM_TOKEN')
bot = telebot.TeleBot(TOKEN)

def load_data():
    try:
        with open('constellations.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Ошибка загрузки JSON: {e}")
        return {}

# --- 3. АСТРОНОМИЧЕСКАЯ ЛОГИКА ---

def get_best_constellation(lat, lon):
    """Определяет созвездие, которое сейчас находится в зените над пользователем"""
    data = load_data()
    obs = ephem.Observer()
    obs.lat = str(lat)
    obs.lon = str(lon)
    obs.date = datetime.utcnow()
    
    try:
        # Получаем ID созвездия по координатам (например, 'Ori')
        _, zenith_const_id = ephem.constellation((obs.lat, obs.lon))
        
        # Ищем ключ созвездия в нашей базе, сопоставляя его с ID
        for key, info in data.items():
            if info.get('id') == zenith_const_id:
                return key
    except Exception as e:
        print(f"Ошибка астро-расчета: {e}")
    
    # Если расчет не удался, выбираем случайное из базы
    return random.choice(list(data.keys()))

def format_full_info(key, info, title_prefix=""):
    """Форматирует полный текст карточки созвездия"""
    name = info.get('name', key.replace('_', ' ').capitalize())
    return (
        f"{title_prefix}✨ **{name}**\n\n"
        f"🔭 **Описание:** {info.get('description', 'Информация скоро появится...')}\n\n"
        f"📜 **История:** {info.get('history', 'Легенды этого созвездия пока скрыты...')}\n\n"
        f"💡 **Секрет:** {info.get('secret', 'Мартин еще изучает этот объект.')}\n"
        f"📊 **Сложность:** {info.get('difficulty', '⭐⭐')}\n"
        f"📅 **Сезон:** {info.get('season', 'Не указан')}"
    )

# --- 4. ОБРАБОТКА КОМАНД ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🎲 Случайное созвездие", "📋 Список созвездий")
    markup.add(telebot.types.KeyboardButton("📍 Определить мое небо", request_location=True))
    
    bot.send_message(
        message.chat.id, 
        "Привет! Я Мартин, твой персональный астро-навигатор. 🌌\n\n"
        "Нажми '📍 Определить мое небо', чтобы я узнал, какие звезды светят тебе прямо сейчас!", 
        reply_markup=markup
    )

@bot.message_handler(content_types=['location'])
def handle_location(message):
    if message.location:
        # Находим созвездие над головой
        key = get_best_constellation(message.location.latitude, message.location.longitude)
        data = load_data()
        info = data.get(key, {})
        
        text = format_full_info(key, info, title_prefix="📍 **Твое небо настроено!**\nПрямо сейчас над тобой:\n\n")
        bot.send_message(message.chat.id, text, parse_mode='Markdown')

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
        names = [info.get('name', k) for k, info in data.items()]
        full_list = "📍 **Все 88 созвездий в моем атласе:**\n\n" + ", ".join(names)
        
        # Разбиваем на части, если список длинный
        for x in range(0, len(full_list), 4000):
            bot.send_message(message.chat.id, full_list[x:x+4000], parse_mode='Markdown')
        return

    # Поиск по названию
    found = False
    for key, info in data.items():
        if text.lower() in info.get('name', '').lower() or text.lower() in key.lower():
            bot.send_message(message.chat.id, format_full_info(key, info), parse_mode='Markdown')
            found = True
            break
            
    if not found:
        bot.send_message(message.chat.id, "🔭 В моих звездных картах такого созвездия нет. Попробуй другое!")

# --- 5. ЗАПУСК ---
if __name__ == "__main__":
    keep_alive()
    print("Мартин успешно заступил на дежурство! 🚀")
    bot.polling(none_stop=True)
