import os
import telebot
from telebot import types
from threading import Thread
from flask import Flask
from draw_map import generate_star_map # Твой файл рисования

# --- 1. СИСТЕМА ЖИЗНЕОБЕСПЕЧЕНИЯ ДЛЯ HF ---
app = Flask('')
@app.route('/')
def home():
    return "Мартин на связи! Ракета Space News на орбите. 🛰️"

def run():
    # HF требует порт 7860
    port = int(os.environ.get("PORT", 7860))
    app.run(host='0.0.0.0', port=port)

# --- 2. НАСТРОЙКА БОТА ---
# Берём токен из секретов Hugging Face, которые ты добавил в Settings
TOKEN = os.environ.get('TELEGRAM_TOKEN')
bot = telebot.TeleBot(TOKEN)

# --- 3. ОБРАБОТКА КОМАНДЫ /START ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    text = message.text or ""
    
    # ПРОВЕРКА: Если человек пришел по кнопке "Включить карту" из канала
    if "get_map" in text:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add(types.KeyboardButton("📍 ПОКАЗАТЬ МОЁ НЕБО", request_location=True))
        
        bot.send_message(message.chat.id, 
            "🛰 **Прием, штурман! Секретный код распознан.**\n\n"
            "Нажми на кнопку ниже, чтобы я настроил линзы на твой город! 🐩🔭", 
            reply_markup=markup, parse_mode='Markdown')
    else:
        # Обычное меню
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("🎲 Случайное созвездие")
        markup.add(types.KeyboardButton("📍 Мое небо сейчас", request_location=True))
        
        bot.send_message(message.chat.id, 
            "Привет! Я Мартин. 🌌 Рад видеть тебя на борту!\n\n"
            "Выбирай команду на пульте управления!", reply_markup=markup)

# --- 4. РИСОВАНИЕ КАРТЫ (КОГДА НАЖАЛИ КНОПКУ) ---
@bot.message_handler(content_types=['location'])
def handle_location(message):
    bot.send_message(message.chat.id, "🛰 Секунду... Проявляю космический снимок!")
    try:
        # Вызываем твой draw_map.py
        path = generate_star_map(message.location.latitude, message.location.longitude, message.from_user.first_name)
        with open(path, 'rb') as f:
            bot.send_photo(message.chat.id, f, 
                           caption="🌟 **ТВОЁ НЕБО ГОТОВО!**\n\nВладик будет в восторге! Отправляй скрин в комментарии канала! 🐩📸",
                           parse_mode='Markdown')
    except Exception as e:
        bot.send_message(message.chat.id, "⚠️ Ошибка связи с телескопом. Попробуй позже!")

if __name__ == "__main__":
    # Запускаем Flask в отдельном потоке (для Hugging Face)
    Thread(target=run).start()
    # Запускаем самого бота
    bot.polling(none_stop=True)
