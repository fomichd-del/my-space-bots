import os
import telebot
from telebot import types, apihelper
from threading import Thread
from flask import Flask
import time
from draw_map import generate_star_map

# 1. МАКСИМАЛЬНАЯ ВЫНОСЛИВОСТЬ СВЯЗИ
apihelper.CONNECT_TIMEOUT = 120
apihelper.READ_TIMEOUT = 120

app = Flask('')

@app.route('/')
def home():
    return "Мартин на связи! Ракета Space News на орбите. 🛰️"

def run():
    port = int(os.environ.get("PORT", 7860))
    print(f"📡 СИСТЕМА: Веб-сервер запущен на порту {port}")
    app.run(host='0.0.0.0', port=port)

# 2. ПОДГОТОВКА ПАСПОРТА (ТОКЕНА)
TOKEN_RAW = os.environ.get('TELEGRAM_TOKEN')
if not TOKEN_RAW:
    print("❌ КРИТИЧЕСКАЯ ОШИБКА: Токен не найден в Secrets!")
    bot = None
else:
    TOKEN = TOKEN_RAW.strip().replace("'", "").replace('"', "")
    print(f"✅ СИСТЕМА: Токен загружен (Начало: {TOKEN[:5]})")
    bot = telebot.TeleBot(TOKEN, threaded=False)

# 3. КОМАНДНЫЙ ЦЕНТР
if bot:
    @bot.message_handler(commands=['start'])
    def send_welcome(message):
        # ЭТОТ ПРИНТ МЫ ДОЛЖНЫ УВИДЕТЬ В ЛОГАХ ПРИ НАЖАТИИ СТАРТ
        print(f"🚀 СООБЩЕНИЕ: Получена команда /start от {message.from_user.first_name}")
        
        text = message.text or ""
        if "get_map" in text:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            markup.add(types.KeyboardButton("📍 ПОКАЗАТЬ МОЁ НЕБО", request_location=True))
            bot.send_message(message.chat.id, 
                "🛰 **Прием, штурман! Секретный код распознан.**\n\n"
                "Нажми кнопку ниже, чтобы я настроил линзы на твой город! 🐩🔭", 
                reply_markup=markup, parse_mode='Markdown')
        else:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.row("🎲 Случайное созвездие")
            markup.row(types.KeyboardButton("📍 Мое небо", request_location=True))
            bot.send_message(message.chat.id, 
                "Привет! Я Мартин. 🌌\nЯ готов рисовать звездные карты для канала Space News!", 
                reply_markup=markup)

    @bot.message_handler(content_types=['location'])
    def handle_location(message):
        print(f"📍 ЛОКАЦИЯ: Получены координаты от {message.from_user.first_name}")
        bot.send_message(message.chat.id, "🛰 Секунду... Настраиваю линзы!")
        try:
            path = generate_star_map(message.location.latitude, message.location.longitude, message.from_user.first_name)
            with open(path, 'rb') as f:
                bot.send_photo(message.chat.id, f, 
                               caption="🌟 **ТВОЁ НЕБО ГОТОВО!**\n\nВладик, смотри какие звезды! 🐩📸", 
                               parse_mode='Markdown')
        except Exception as e:
            print(f"❌ ОШИБКА РИСОВАНИЯ: {e}")
            bot.send_message(message.chat.id, "⚠️ Ошибка телескопа.")

# 4. ЗАПУСК ДВИГАТЕЛЕЙ
if __name__ == "__main__":
    t = Thread(target=run)
    t.daemon = True
    t.start()
    
    if bot:
        print("🛰 МАРТИН: Вхожу в режим прослушивания эфира...")
        while True:
            try:
                bot.polling(none_stop=True, timeout=90, long_polling_timeout=90)
            except Exception as e:
                print(f"📡 СВЯЗЬ: Помехи в эфире ({e}). Переподключение...")
                time.sleep(5)
