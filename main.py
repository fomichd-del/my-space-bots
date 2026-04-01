import os
import telebot
import json
import random
from threading import Thread
from flask import Flask

# --- 1. БЛОК ДЛЯ ПОДДЕРЖАНИЯ РАБОТЫ (FLASK) ---
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
        # Убедитесь, что файл называется именно так в вашем репозитории
        with open('constellations.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Ошибка загрузки JSON: {e}")
        return {}

# --- 3. ОБРАБОТКА КОМАНД ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = telebot.types.KeyboardButton("🎲 Случайное созвездие")
    item2 = telebot.types.KeyboardButton("📋 Список созвездий")
    markup.add(item1, item2)
    
    bot.send_message(
        message.chat.id, 
        "Привет! Я Мартин, твой гид по 88 созвездиям. 🌌 Нажми на кнопку или напиши название!", 
        reply_markup=markup
    )

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    data = load_data()
    text = message.text.strip()

    if text == "🎲 Случайное созвездие":
        if not data:
            bot.send_message(message.chat.id, "Извини, моя звездная карта пока пуста.")
            return
        
        const_id = random.choice(list(data.keys()))
        info = data[const_id]
        
        # Собираем ответ, используя новые ключи из нашего JSON
        response = (
            f"✨ **{info.get('name', 'Неизвестно')}**\n\n"
            f"🔭 **Описание:** {info.get('description', 'Информация скоро появится...')}\n"
            f"📜 **История:** {info.get('history', 'В разработке...')}\n"
            f"💡 **Секрет:** {info.get('secret', 'Это очень красивое созвездие!')}\n"
            f"📊 **Сложность:** {info.get('difficulty', '⭐⭐')}\n"
            f"📅 **Сезон:** {info.get('season', 'Весь год')}"
        )
        bot.send_message(message.chat.id, response, parse_mode='Markdown')
        return

    if text == "📋 Список созвездий":
        if not data:
            bot.send_message(message.chat.id, "Список пока пуст.")
            return
        
        names = [item['name'] for item in data.values()]
        full_list = "📍 **Доступные созвездия:**\n\n" + ", ".join(names)
        
        # Если список очень длинный (больше 4096 символов), разбиваем его
        if len(full_list) > 4000:
            for x in range(0, len(full_list), 4000):
                bot.send_message(message.chat.id, full_list[x:x+4000], parse_mode='Markdown')
        else:
            bot.send_message(message.chat.id, full_list, parse_mode='Markdown')
        return

    # Поиск созвездия по названию
    found = False
    for item in data.values():
        if text.lower() in item['name'].lower():
            response = (
                f"✨ **{item['name']}**\n\n"
                f"📜 {item.get('history', '')}\n"
                f"💡 {item.get('secret', '')}\n"
                f"📅 Сезон: {item.get('season', 'Не указан')}"
            )
            bot.send_message(message.chat.id, response, parse_mode='Markdown')
            found = True
            break
            
    if not found:
        bot.send_message(message.chat.id, "Хм, такого созвездия я пока не знаю. Попробуй другое! 🔭")

# --- 4. ЗАПУСК ---
if __name__ == "__main__":
    keep_alive()
    print("Мартин успешно запущен и слушает звезды...")
    bot.polling(none_stop=True)
