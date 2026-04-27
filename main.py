import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import os
from draw_map import generate_star_map

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# Глобальный словарь для временного хранения фактов
USER_FACTS = {}

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
        "🔭 <i>Позиция зафиксирована. Обработка данных глубокого космоса. Генерирую звездную карту...</i>",
        parse_mode='HTML'
    )

    # Получаем 4 параметра из draw_map!
    success, result, target_name, target_fact = generate_star_map(lat, lon, user_name)

    bot.delete_message(chat_id, loading_msg.message_id)

    if success:
        # Сохраняем факт в памяти бота для этого пользователя
        USER_FACTS[chat_id] = target_fact
        
        # Создаем Inline-кнопку под фото
        markup = InlineKeyboardMarkup()
        fact_btn = InlineKeyboardButton(f"📖 Узнать факт: {target_name}", callback_data="show_fact")
        markup.add(fact_btn)

        with open(result, 'rb') as photo:
            bot.send_photo(
                chat_id, 
                photo, 
                caption=f"✨ Твоя звездная карта готова, Штурман!\n🎯 Главная цель на сегодня: <b>{target_name}</b>",
                reply_markup=markup,
                parse_mode='HTML'
            )
        os.remove(result)
    else:
        bot.send_message(chat_id, f"❌ Системный сбой радара: {result}")

# Обработчик нажатия на Inline-кнопку
@bot.callback_query_handler(func=lambda call: call.data == "show_fact")
def callback_fact(call):
    chat_id = call.message.chat.id
    if chat_id in USER_FACTS:
        fact = USER_FACTS[chat_id]
        bot.answer_callback_query(call.id) # Убираем "часики" загрузки на кнопке
        bot.send_message(chat_id, f"📖 <b>СЕКРЕТНЫЙ ФАКТ:</b>\n«{fact}»", parse_mode='HTML')
    else:
        bot.answer_callback_query(call.id, "Данные устарели. Запроси карту снова!")

if __name__ == "__main__":
    print("🚀 Бот Астроном запущен!")
    bot.infinity_polling()
