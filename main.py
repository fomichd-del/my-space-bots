import os
import telebot
from telebot import types
import json
import random
from threading import Thread
from flask import Flask

# 1. ЧИСТЫЙ ЗАПУСК СЕРВЕРА ДЛЯ RENDER
app = Flask('')
@app.route('/')
def home(): return "Мартин на связи! 🛰️"

def run():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# 2. ПОДКЛЮЧАЕМ РИСОВАЛКУ (БЕЗОПАСНО)
try:
    from draw_map import generate_star_map
    CAN_DRAW = True
except Exception as e:
    print(f"⚠️ Ошибка импорта draw_map: {e}")
    CAN_DRAW = False

# 3. НАСТРОЙКА БОТА
TOKEN = os.getenv('TELEGRAM_TOKEN')
bot = telebot.TeleBot(TOKEN)

# 4. ОБРАБОТКА КОМАНДЫ СТАРТ
@bot.message_handler(commands=['start', 'старт'])
def send_welcome(message):
    text = message.text or ""
    
    # СЛУЧАЙ 1: ПЕРЕХОД ИЗ КАНАЛА (есть код get_map)
    if "get_map" in text:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        # Создаем кнопку запроса локации
        location_button = types.KeyboardButton("📍 ОТПРАВИТЬ МОИ КООРДИНАТЫ", request_location=True)
        markup.add(location_button)
        
        bot.send_message(message.chat.id, 
            "🛰 **Прием, штурман! Секретный код распознан.**\n\n"
            "Нажми на большую кнопку внизу, чтобы я настроил линзы телескопов на твой город! 🐩🚀", 
            reply_markup=markup, parse_mode='Markdown')
    
    # СЛУЧАЙ 2: ОБЫЧНЫЙ СТАРТ
    else:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = types.KeyboardButton("🎲 Случайное созвездие")
        btn2 = types.KeyboardButton("📋 Список созвездий")
        btn3 = types.KeyboardButton("📍 Определить мое небо", request_location=True)
        markup.add(btn1, btn2)
        markup.add(btn3)
        
        bot.send_message(message.chat.id, 
            "Привет! Я Мартин. 🌌 Твой верный космический пес-штурман.\n\n"
            "Выбирай команду на пульте управления! 👇", 
            reply_markup=markup)

# 5. ОБРАБОТКА ЛОКАЦИИ (КОГДА НАЖАЛИ КНОПКУ)
@bot.message_handler(content_types=['location'])
def handle_location(message):
    bot.send_message(message.chat.id, "🛰 Принимаю координаты... Начинаю рендеринг звездной сферы!")
    
    if CAN_DRAW:
        try:
            # Рисуем карту
            lat, lon = message.location.latitude, message.location.longitude
            name = message.from_user.first_name or "Исследователь"
            path = generate_star_map(lat, lon, name)
            
            with open(path, 'rb') as photo:
                bot.send_photo(message.chat.id, photo, 
                               caption="🌟 **ТВОЁ НЕБО ГОТОВО!**\n\nСкорее делай скриншот и отправляй его в комментарии канала! 🐩📸",
                               parse_mode='Markdown')
        except Exception as e:
            bot.send_message(message.chat.id, f"⚠️ Упс! Телескоп немного запотел (ошибка). Попробуй позже!")
    else:
        bot.send_message(message.chat.id, "🔭 Хьюстон, у нас проблемы! Модуль рисования не найден.")

# 6. ТЕСТОВАЯ КОМАНДА (ПРОВЕРКА СВЯЗИ)
@bot.message_handler(func=lambda message: message.text == "Привет")
def say_hi(message):
    bot.send_message(message.chat.id, "Гав! Я на связи! 🐩🛰")

if __name__ == "__main__":
    Thread(target=run).start()
    print("🚀 Мартин вышел на орбиту!")
    bot.polling(none_stop=True)
