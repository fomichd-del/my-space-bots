import os
import telebot
import json
import random
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

def get_current_season():
    month = datetime.now().month
    if month in [12, 1, 2]:
        return "winter"
    elif month in [3, 4, 5]:
        return "spring"
    elif month in [6, 7, 8]:
        return "summer"
    else:
        return "autumn"

# --- 3. ОБРАБОТКА КОМАНД ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = telebot.types.KeyboardButton("🎲 Случайное созвездие")
    item2 = telebot.types.KeyboardButton("📋 Список созвездий")
    
    # НОВАЯ КНОПКА: запрашивает местоположение
    item3 = telebot.types.KeyboardButton("📍 Определить мое небо", request_location=True)
    
    markup.add(item1, item2)
    markup.add(item3)
    
    bot.send_message(
        message.chat.id, 
        "Привет! Я Мартин. Нажми кнопку '📍 Определить мое небо', чтобы я узнал твои координаты и подготовил персональную карту!", 
        reply_markup=markup
    )

# НОВЫЙ ОБРАБОТЧИК: срабатывает, когда пользователь присылает локацию
@bot.message_handler(content_types=['location'])
def handle_location(message):
    if message.location is not None:
        lat = message.location.latitude
        lon = message.location.longitude
        
        # Пока что просто подтверждаем получение данных
        reply = f"📍 Координаты получены!\nШирота: {lat}\nДолгота: {lon}\n\nТеперь я знаю, под каким углом ты смотришь на звезды. Скоро я научусь рисовать карту именно для твоего места!"
        bot.send_message(message.chat.id, reply)

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    data = load_data()
    if not data:
        bot.send_message(message.chat.id, "Ошибка: Звездная карта не найдена. 🛰️")
        return

    text = message.text.strip()

    if text == "🎲 Случайное созвездие":
        season = get_current_season()
        seasonal_keys = [
            k for k, v in data.items() 
            if v.get('season') == season or v.get('season') == 'all year'
        ]
        target_keys = seasonal_keys if seasonal_keys else list(data.keys())
        const_id = random.choice(target_keys)
        info = data[const_id]
        
        response = (
            f"✨ **{info.get('name', 'Неизвестно')}**\n\n"
            f"🔭 **Описание:** {info.get('description', '...')}\n"
            f"📜 **История:** {info.get('history', '...')}\n"
            f"💡 **Секрет:** {info.get('secret', '...')}\n"
            f"📊 **Сложность:** {info.get('difficulty', '⭐⭐')}\n"
            f"📅 **Сезон:** {info.get('season', 'Не указан')}"
        )
        bot.send_message(message.chat.id, response, parse_mode='Markdown')
        return

    if text == "📋 Список созвездий":
        names = [item['name'] for item in data.values()]
        full_list = "📍 **Все 88 созвездий:**\n\n" + ", ".join(names)
        
        if len(full_list) > 4000:
            for x in range(0, len(full_list), 4000):
                bot.send_message(message.chat.id, full_list[x:x+4000], parse_mode='Markdown')
        else:
            bot.send_message(message.chat.id, full_list, parse_mode='Markdown')
        return

    found = False
    for item in data.values():
        if text.lower() in item['name'].lower():
            response = (
                f"✨ **{item['name']}**\n\n"
                f"📜 {item.get('history', 'История уточняется...')}\n"
                f"💡 {item.get('secret', 'Секретов пока нет.')}\n"
                f"📅 Сезон: {item.get('season', 'Не указан')}"
            )
            bot.send_message(message.chat.id, response, parse_mode='Markdown')
            found = True
            break
            
    if not found:
        bot.send_message(message.chat.id, "Хм, в моих атласах такого нет. Попробуй другое созвездие! 🔭")

# --- 4. ЗАПУСК ---
if __name__ == "__main__":
    keep_alive()
    print("Мартин успешно запущен!")
    bot.polling(none_stop=True)
