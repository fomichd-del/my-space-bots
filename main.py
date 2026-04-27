import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import os
from draw_map import generate_star_map
from flask import Flask
from threading import Thread

# === НАСТРОЙКИ ===
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
bot = telebot.TeleBot(TELEGRAM_TOKEN)
USER_FACTS = {} 

# === МИНИ ВЕБ-СЕРВЕР (МАЯК ДЛЯ RENDER) ===
app = Flask(__name__)

@app.route('/')
def keep_alive():
    return "Марти на связи! Системы работают штатно. 🚀"

def run_server():
    # Render автоматически передает нужный порт
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# === ЛОГИКА БОТА ===
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    item = KeyboardButton("📡 Мое небо", request_location=True)
    markup.add(item)
    
    welcome_text = (
        "🛰 <b>Добро пожаловать на мостик, Штурман!</b>\n\n"
        "Системы навигации в норме. Запроси «Мое небо», и я выведу данные сканирования сектора."
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup, parse_mode='HTML')

@bot.message_handler(content_types=['location'])
def handle_location(message):
    lat = message.location.latitude
    lon = message.location.longitude
    user_name = message.from_user.first_name
    chat_id = message.chat.id

    loading_msg = bot.send_message(
        chat_id, 
        "🔭 <i>Позиция зафиксирована. Обработка данных глубокого космоса...</i>",
        parse_mode='HTML'
    )

    # Запуск генератора карты
    success, result, target_name, target_fact = generate_star_map(lat, lon, user_name)

    bot.delete_message(chat_id, loading_msg.message_id)

    if success:
        USER_FACTS[chat_id] = target_fact
        
        markup = InlineKeyboardMarkup()
        fact_btn = InlineKeyboardButton(f"📖 Узнать факт: {target_name}", callback_data="show_fact")
        markup.add(fact_btn)

        with open(result, 'rb') as photo:
            bot.send_photo(
                chat_id, 
                photo, 
                caption=f"✨ Твоя звездная карта готова!\n🎯 Сегодня изучаем: <b>{target_name}</b>",
                reply_markup=markup,
                parse_mode='HTML'
            )
        os.remove(result)
    else:
        bot.send_message(chat_id, f"❌ Ошибка связи с телескопом: {result}")

@bot.callback_query_handler(func=lambda call: call.data == "show_fact")
def callback_fact(call):
    chat_id = call.message.chat.id
    if chat_id in USER_FACTS:
        bot.answer_callback_query(call.id) 
        bot.send_message(chat_id, f"📖 <b>СЕКРЕТНЫЙ ФАКТ:</b>\n«{USER_FACTS[chat_id]}»", parse_mode='HTML')
    else:
        bot.answer_callback_query(call.id, "Данные устарели. Запроси карту снова!")

if __name__ == "__main__":
    # Запуск маяка в отдельном потоке
    Thread(target=run_server).start()
    print("🚀 Маяк для Render запущен!")
    
    # Запуск бота с защитой от ConnectionError
    print("🚀 Бот Астроном в эфире!")
    bot.infinity_polling(timeout=15, long_polling_timeout=5)
