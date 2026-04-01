import os
import telebot
import json
import random
from threading import Thread
from flask import Flask

# --- БЛОК АНТИ-СОН (FLASK) ---
app = Flask('')

@app.route('/')
def home():
    return "I'm alive!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- ОСНОВНАЯ ЛОГИКА БОТА ---
TOKEN = os.getenv('TELEGRAM_TOKEN')
bot = telebot.TeleBot(TOKEN)

def load_data():
    try:
        with open('constellations.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Ошибка чтения JSON: {e}")
        return {}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = telebot.types.KeyboardButton("✨ Случайное созвездие")
    item2 = telebot.types.KeyboardButton("🔍 Список всех")
    markup.add(item1, item2)
    
    bot.send_message(
        message.chat.id, 
        "Привет! Я Мартин, твой гид по 88 созвездиям. Нажми кнопку или напиши название созвездия!", 
        reply_markup=markup
    )

@bot.message_handler(func=lambda message: message.text == "✨ Случайное созвездие")
def random_const(message):
    data = load_data()
    if data:
        const_id = random.choice(list(data.keys()))
        info = data[const_id]
        response = (
            f"✨ **{info['name']}** ({info['latin']})\n\n"
            f"📜 **Мифология:** {info['mythology']}\n"
            f"🌟 **Ярчайшая звезда:** {info['brightest_star']}\n"
            f"🗓 **Лучшее время:** {info['best_time']}\n"
            f"💡 **Факт:** {info['fact']}"
        )
        bot.send_message(message.chat.id, response, parse_mode='Markdown')

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    data = load_data()
    # Поиск по названию
    found = False
    for item in data.values():
        if message.text.lower() in item['name'].lower():
            response = (
                f"✅ Нашел!\n\n"
                f"✨ **{item['name']}**\n"
                f"📜 {item['mythology']}\n"
                f"💡 {item['fact']}"
            )
            bot.send_message(message.chat.id, response, parse_mode='Markdown')
            found = True
            break
    if not found:
        bot.send_message(message.chat.id, "Хм, такого созвездия я не знаю. Попробуй еще раз!")

# --- ЗАПУСК ---
if __name__ == "__main__":
    keep_alive()  # Запускаем сервер для поддержания активности
    print("Бот запущен и сервер активен!")
    bot.polling(none_stop=True)
