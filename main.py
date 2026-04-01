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
        # Загружаем нашу базу из 88 созвездий
        with open('constellations.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Ошибка загрузки JSON: {e}")
        return {}

def get_current_season():
    """Определяет текущий сезон на основе месяца сервера"""
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
    markup.add(item1, item2)
    
    bot.send_message(
        message.chat.id, 
        "Привет! Я Мартин. 🌌 Я подготовил для тебя карту из 88 созвездий. "
        "Нажми на кубик, и я подберу что-то подходящее для текущего сезона!", 
        reply_markup=markup
    )

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    data = load_data()
    if not data:
        bot.send_message(message.chat.id, "Ошибка: Звездная карта не найдена. 🛰️")
        return

    text = message.text.strip()

    # ЛОГИКА: Случайное созвездие по сезону
    if text == "🎲 Случайное созвездие":
        season = get_current_season()
        
        # Фильтруем: берем созвездия текущего сезона ИЛИ те, что видны круглый год
        seasonal_keys = [
            k for k, v in data.items() 
            if v.get('season') == season or v.get('season') == 'all year'
        ]
        
        # Если по сезону ничего не нашли (на всякий случай), берем любое
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

    # ЛОГИКА: Список всех созвездий
    if text == "📋 Список созвездий":
        names = [item['name'] for item in data.values()]
        full_list = "📍 **Все 88 созвездий:**\n\n" + ", ".join(names)
        
        # Разбиваем сообщение, если оно слишком длинное для Telegram
        if len(full_list) > 4000:
            for x in range(0, len(full_list), 4000):
                bot.send_message(message.chat.id, full_list[x:x+4000], parse_mode='Markdown')
        else:
            bot.send_message(message.chat.id, full_list, parse_mode='Markdown')
        return

    # ЛОГИКА: Поиск созвездия вручную
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
