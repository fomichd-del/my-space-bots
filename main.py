import os
import telebot
from telebot import types
from threading import Thread
from flask import Flask
import time

# --- НАСТРОЙКА FLASK (Для Hugging Face) ---
app = Flask('')

@app.route('/')
def home():
    return "Martin is Online! 🛰️"

def run():
    # Hugging Face ТРЕБУЕТ порт 7860
    app.run(host='0.0.0.0', port=7860)

# --- ЛОГИКА МАРТИНА ---
from draw_map import generate_star_map

TOKEN = os.getenv('TELEGRAM_TOKEN')
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    # Проверяем, пришел ли пользователь по ссылке с параметром (get_map)
    if "get_map" in message.text:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add(types.KeyboardButton("📍 ОТПРАВИТЬ КООРДИНАТЫ", request_location=True))
        bot.send_message(
            message.chat.id, 
            "🛰 **Секретный канал связи активирован!**\n\nНажми кнопку ниже, чтобы я настроил телескопы под твоё небо!", 
            reply_markup=markup, 
            parse_mode='Markdown'
        )
    else:
        # Обычное приветствие
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.row("🎲 Случайное созвездие")
        markup.row(types.KeyboardButton("📍 Мое небо", request_location=True))
        bot.send_message(
            message.chat.id, 
            "Привет, штурман! 🌌\nЯ Мартин, твой бортовой пёс-астроном.\n\nВыбирай команду на панели управления!", 
            reply_markup=markup
        )

@bot.message_handler(content_types=['location'])
def handle_location(message):
    bot.send_message(message.chat.id, "🛰 Принято! Разворачиваю антенны, начинаю рендеринг звездной карты...")
    try:
        # Генерируем карту
        path = generate_star_map(message.location.latitude, message.location.longitude, message.from_user.first_name)
        
        # Отправляем фото пользователю
        with open(path, 'rb') as photo:
            bot.send_photo(
                message.chat.id, 
                photo, 
                caption=f"🌟 ТВОЕ НЕБО ГОТОВО! 🐩🚀\n\nНа этой карте звезды именно так, как ты видишь их сейчас."
            )
    except Exception as e:
        print(f"Ошибка при генерации: {e}")
        bot.send_message(message.chat.id, "❌ Произошел сбой в системе навигации. Попробуй еще раз чуть позже.")

@bot.message_handler(func=lambda message: message.text == "🎲 Случайное созвездие")
def random_const(message):
    bot.send_message(message.chat.id, "🔭 Ищу интересное созвездие... (функция в разработке)")

# --- ЗАПУСК ---
if __name__ == "__main__":
    print("🚀 Мартин вышел на орбиту!")
    Thread(target=run).start()
    
    # Используем infinity_polling с увеличенным временем ожидания (тайм-аутом)
    # Это защитит от ошибок сети, которые мы видели в логах
    bot.infinity_polling(timeout=60, long_polling_timeout=25)
