import os
import telebot
from telebot import types
from threading import Thread
from flask import Flask
from draw_map import generate_star_map # Наш художник

# 1. СИСТЕМА ДЛЯ HUGGING FACE (Чтобы Space не засыпал)
app = Flask('')
@app.route('/')
def home():
    return "Мартин на связи! Ракета Space News на орбите. 🛰️"

def run():
    # HF требует порт 7860
    port = int(os.environ.get("PORT", 7860))
    app.run(host='0.0.0.0', port=port)

# 2. ПОЛУЧАЕМ ТОКЕН ИЗ "СЕЙФА" (Secrets)
TOKEN = os.environ.get('TELEGRAM_TOKEN')
bot = telebot.TeleBot(TOKEN)

# 3. ОБРАБОТЧИК START (Специально для канала Space News)
@bot.message_handler(commands=['start'])
def send_welcome(message):
    text = message.text or ""
    
    # Если в ссылке из канала есть get_map
    if "get_map" in text:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add(types.KeyboardButton("📍 ПОКАЗАТЬ МОЁ НЕБО", request_location=True))
        
        bot.send_message(message.chat.id, 
            "🛰 **Прием, штурман! Секретный шлюз открыт.**\n\n"
            "Нажми кнопку ниже, чтобы я прислал карту звезд над твоим городом! 🐩🔭", 
            reply_markup=markup, parse_mode='Markdown')
    else:
        # Обычное меню
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.row("🎲 Случайное созвездие")
        markup.row(types.KeyboardButton("📍 Определить мое небо", request_location=True))
        
        bot.send_message(message.chat.id, "Привет! Я Мартин. 🌌 Готов к наблюдениям!", reply_markup=markup)

# 4. ГЛАВНОЕ: ОБРАБОТКА ЛОКАЦИИ (РИСУЕМ КАРТУ)
@bot.message_handler(content_types=['location'])
def handle_location(message):
    # Теперь Мартин НЕ БУДЕТ просто писать "Привет", он будет РИСОВАТЬ
    bot.send_message(message.chat.id, "🛰 Секунду... Проявляю космический снимок!")
    try:
        # Вызываем функцию рисования
        path = generate_star_map(message.location.latitude, message.location.longitude, message.from_user.first_name)
        with open(path, 'rb') as f:
            bot.send_photo(message.chat.id, f, 
                           caption="🌟 **ТВОЁ НЕБО ГОТОВО!**\n\nСделай скриншот и отправляй его в комментарии канала Space News! 🐩📸",
                           parse_mode='Markdown')
    except Exception as e:
        bot.send_message(message.chat.id, "⚠️ Ошибка связи с телескопом. Попробуй позже!")

if __name__ == "__main__":
    # Запускаем Flask в отдельном потоке
    Thread(target=run).start()
    # Запускаем бота
    bot.polling(none_stop=True)
