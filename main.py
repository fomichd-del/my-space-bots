import os
import telebot
import json
import random
from threading import Thread
from flask import Flask

# --- 1. БЛОК ДЛЯ ПОДДЕРЖАНИЯ РАБОТЫ (FLASK) ---
# Это нужно, чтобы Render видел активность и не отключал бота
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
# Берем токен из переменных окружения, которые мы настроили в Render
TOKEN = os.getenv('TELEGRAM_TOKEN')
bot = telebot.TeleBot(TOKEN)

# Функция для загрузки данных из JSON
def load_data():
    try:
        with open('constellations.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Ошибка загрузки JSON: {e}")
        return {}

# --- 3. ОБРАБОТКА КОМАНД ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    # Создаем кнопки (эмодзи должны точно совпадать с текстом ниже!)
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = telebot.types.KeyboardButton("🎲 Случайное созвездие")
    item2 = telebot.types.KeyboardButton("📋 Список созвездий")
    markup.add(item1, item2)
    
    bot.send_message(
        message.chat.id, 
        "Привет! Я Мартин, твой гид по звездному небу. 🌌 Нажми на кнопку или напиши название созвездия!", 
        reply_markup=markup
    )

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    data = load_data()
    text = message.text.strip()

    # Проверка кнопки "Случайное созвездие" 🎲
    if text == "🎲 Случайное созвездие":
        if not data:
            bot.send_message(message.chat.id, "Извини, моя звездная карта пока пуста. Проверь файл JSON!")
            return
        
        const_id = random.choice(list(data.keys()))
        info = data[const_id]
        
        response = (
            f"✨ **{info.get('name', 'Неизвестно')}**\n\n"
            f"📜 **Мифология:** {info.get('mythology', 'В разработке...')}\n"
            f"🌟 **Ярчайшая звезда:** {info.get('brightest_star', 'Данных нет')}\n"
            f"💡 **Факт:** {info.get('fact', 'Это очень красивое созвездие!')}"
        )
        bot.send_message(message.chat.id, response, parse_mode='Markdown')
        return

    # Проверка кнопки "Список созвездий" 📋
    if text == "📋 Список созвездий":
        if not data:
            bot.send_message(message.chat.id, "Список пока пуст.")
            return
        
        names = [item['name'] for item in data.values()]
        full_list = "📍 **Доступные созвездия:**\n\n" + ", ".join(names)
        # Если список слишком длинный, Telegram может его не отправить, но для начала хватит
        bot.send_message(message.chat.id, full_list, parse_mode='Markdown')
        return

    # Если это не кнопка, ищем созвездие по названию
    found = False
    for item in data.values():
        if text.lower() in item['name'].lower():
            response = (
                f"✨ **{item['name']}**\n\n"
                f"📜 {item.get('mythology', '')}\n"
                f"💡 {item.get('fact', '')}"
            )
            bot.send_message(message.chat.id, response, parse_mode='Markdown')
            found = True
            break
            
    if not found:
        bot.send_message(message.chat.id, "Хм, такого созвездия я пока не знаю. Попробуй другое! 🔭")

# --- 4. ЗАПУСК ---
if __name__ == "__main__":
    keep_alive() # Запускаем Flask в отдельном потоке
    print("Мартин успешно запущен и слушает звезды...")
    bot.polling(none_stop=True)
