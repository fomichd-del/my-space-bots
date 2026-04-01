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
    """Находит созвездие, которое сейчас прямо над пользователем (в зените)"""
    data = load_data()
    obs = ephem.Observer()
    obs.lat = str(lat)
    obs.lon = str(lon)
    obs.date = datetime.utcnow()
    
    try:
        # ephem возвращает кортеж, где второй элемент — это ID созвездия (например, 'Ori')
        _, zenith_const_id = ephem.constellation((obs.lat, obs.lon))
        
        # Ищем созвездие в нашей базе, сопоставляя ID
        for key, info in data.items():
            if info.get('id') == zenith_const_id:
                return key
    except Exception as e:
        print(f"Ошибка расчёта неба: {e}")
    
    # Если расчет не удался, выбираем любое
    return random.choice(list(data.keys()))

def format_const_reply(key, info, prefix=""):
    """Вспомогательная функция для красивого оформления текста"""
    return (
        f"{prefix}✨ **{info.get('name', key.capitalize())}**\n\n"
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
    item1 = telebot.types.KeyboardButton("🎲 Случайное созвездие")
    item2 = telebot.types.KeyboardButton("📋 Список созвездий")
    item3 = telebot.types.KeyboardButton("📍 Определить мое небо", request_location=True)
    
    markup.add(item1, item2)
    markup.add(item3)
    
    bot.send_message(
        message.chat.id, 
        "Привет! Я Мартин, твой звездный гид. ✨ Нажми 'Определить мое небо', и я настрою телескоп под твои координаты!", 
        reply_markup=markup
    )

@bot.message_handler(content_types=['location'])
def handle_location(message):
    if message.location:
        # Расчет созвездия по локации
        key = get_best_constellation(message.location.latitude, message.location.longitude)
        data = load_data()
        info = data.get(key, {})
        
        reply = format_const_reply(key, info, prefix="📍 **Твои координаты приняты!**\nПрямо сейчас над тобой:\n\n")
        bot.send_message(message.chat.id, reply, parse_mode='Markdown')

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    data = load_data()
    text = message.text.strip()

    if text == "🎲 Случайное созвездие":
        key = random.choice(list(data.keys()))
        info = data[key]
        bot.send_message(message.chat.id, format_const_reply(key, info), parse_mode='Markdown')
        return

    if text == "📋 Список созвездий":
        names = [info.get('name', k) for k, info in data.items()]
        full_list = "📍 **Все 88 созвездий в моем атласе:**\n\n" + ", ".join(names)
        
        # Разбиваем на части, если список слишком длинный для Telegram
        for x in range(0, len(full_list), 4000):
            bot.send_message(message.chat.id, full_list[x:x+4000], parse_mode='Markdown')
        return

    # Поиск созвездия по вводу названия
    found = False
    for key, info in data.items():
        if text.lower() in info.get('name', '').lower() or text.lower() in key.lower():
            bot.send_message(message.chat.id, format_const_reply(key, info), parse_mode='Markdown')
            found = True
            break
            
    if not found:
        bot.send_message(message.chat.id, "Хм, в моих атласах такого нет. Попробуй другое созвездие! 🔭")

# --- 5. ЗАПУСК ---
if __name__ == "__main__":
    keep_alive()
    print("Мартин успешно запущен и готов к работе!")
    bot.polling(none_stop=True)
