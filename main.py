import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import os
from draw_map import generate_star_map
from flask import Flask
from threading import Thread

# === НАСТРОЙКИ ===
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
bot = telebot.TeleBot(TELEGRAM_TOKEN)
USER_FACTS = {} # Временное хранилище фактов для кнопок

# === МИНИ ВЕБ-СЕРВЕР ДЛЯ RENDER ===
app = Flask(__name__)

@app.route('/')
def keep_alive():
    return "Марти на связи! Системы работают. 🚀"

def run_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# === ЛОГИКА БОТА ===
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    item = KeyboardButton("📡 Мое небо", request_location=True)
    markup.add(item)
    
    welcome_text = (
        "🛰 <b>Навигационные системы инициализированы.</b>\n\n"
        "Штурман, нажми «Мое небо», чтобы я просканировал твой сектор."
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup, parse_mode='HTML')

@bot.message_handler(content_types=['location'])
def handle_location(message):
    lat = message.location.latitude
    lon = message.location.longitude
    user_name = message.from_user.first_name
    chat_id = message.chat.id

    loading_msg = bot.send_message(chat_id, "🔭 <i>Сканирую глубокий космос...</i>", parse_mode='HTML')

    # Генерируем карту
    success, result, target_name, target_fact = generate_star_map(lat, lon, user_name)

    bot.delete_message(chat_id, loading_msg.message_id)

    if success:
        USER_FACTS[chat_id] = target_fact
        
        markup = InlineKeyboardMarkup()
        fact_btn = InlineKeyboardButton(f"📖 Факт: {target_name}", callback_data="show_fact")
        markup.add(fact_btn)

        with open(result, 'rb') as photo:
            bot.send_photo(
                chat_id, 
                photo, 
                caption=f"✨ Сектор готов!\n🎯 Сегодня изучаем: <b>{target_name}</b>",
                reply_markup=markup,
                parse_mode='HTML'
            )
        os.remove(result) # Удаляем временный файл
    else:
        bot.send_message(chat_id, f"❌ Ошибка радара: {result}")

@bot.callback_query_handler(func=lambda call: call.data == "show_fact")
def callback_fact(call):
    chat_id = call.message.chat.id
    if chat_id in USER_FACTS:
        bot.answer_callback_query(call.id)
        bot.send_message(chat_id, f"📖 <b>ИНФО-БЛОК:</b>\n«{USER_FACTS[chat_id]}»", parse_mode='HTML')
    else:
        bot.answer_callback_query(call.id, "Данные устарели, запроси карту снова.")

# === ЗАПУСК ===
if __name__ == "__main__":
    # Запускаем сервер "будильник"
    Thread(target=run_server).start()
    print("🚀 Маяк запущен. Бот выходит на орбиту...")
    bot.infinity_polling()
