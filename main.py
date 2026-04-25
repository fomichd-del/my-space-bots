import os
import telebot
from flask import Flask
from threading import Thread

# --- 1. СИСТЕМА ЖИЗНЕОБЕСПЕЧЕНИЯ (ДЛЯ RENDER) ---
app = Flask('')

@app.route('/')
def home():
    return "Мартин на связи и готов к полету! 🛰️"

def run():
    # Render ОБЯЗАТЕЛЬНО требует этот порт
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- 2. НАСТРОЙКА БОТА ---
TOKEN = os.getenv('TELEGRAM_TOKEN')
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "🛰 Привет! Я Мартин. Системы перезагружены в аварийном режиме. Скоро я снова смогу рисовать карты!")

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, "Прием! Я тебя слышу, но пока работаю в режиме отладки.")

# --- 3. ЗАПУСК ---
if __name__ == "__main__":
    keep_alive() # Сначала запускаем сервер для Render
    print("🚀 Мартин вышел на орбиту!")
    bot.polling(none_stop=True)
