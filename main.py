import os
import telebot
from telebot import types, apihelper
from threading import Thread
from flask import Flask
import time
from draw_map import generate_star_map

# 1. МАКСИМАЛЬНОЕ УСИЛЕНИЕ СИГНАЛА (Таймауты до 2 минут)
apihelper.CONNECT_TIMEOUT = 120
apihelper.READ_TIMEOUT = 120

app = Flask('')

@app.route('/')
def home():
    return "Мартин на связи! Ракета Space News на орбите. 🛰️"

def run_flask():
    port = int(os.environ.get("PORT", 7860))
    print(f"📡 СИСТЕМА: Веб-сервер запущен на порту {port}")
    app.run(host='0.0.0.0', port=port)

# 2. ПОДГОТОВКА ТОКЕНА
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
        print(f"🚀 СООБЩЕНИЕ: Получена команда /start от {message.from_user.first_name}")
        text = message.text or ""
        
        if "get_map" in text:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            markup.add(types.KeyboardButton("📍 ПОКАЗАТЬ МОЁ НЕБО", request_location=True))
            bot.send_message(message.chat.id, 
                "🛰 **Прием, штурман! Секретный шлюз открыт.**\n\n"
                "Нажми кнопку ниже, чтобы я прислал карту звезд над твоим городом! 🐩🔭", 
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

# 4. ЗАПУСК БОТА (С ЗАЩИТОЙ ОТ ЗАВИСАНИЯ)
def run_bot():
    if not bot: return
    
    while True:
        try:
            print("🧹 ОЧИСТКА: Пробуем удалить Webhooks...")
            bot.remove_webhook()
            
            print("🤖 ПРОВЕРКА: Авторизация...")
            me = bot.get_me()
            print(f"🤖 УСПЕХ: Я залогинился как @{me.username}")
            
            print("🛰 МАРТИН: Начинаю слушать эфир (Polling)...")
            bot.polling(none_stop=True, timeout=90, long_polling_timeout=90)
            
        except Exception as e:
            print(f"📡 СВЯЗЬ: Ошибка ({e}). Переподключение через 10 секунд...")
            time.sleep(10)

if __name__ == "__main__":
    # 1. Сначала запускаем Flask (чтобы Hugging Face видел, что мы живы)
    t_flask = Thread(target=run_flask)
    t_flask.daemon = True
    t_flask.start()
    
    # 2. Даем серверу HF 5 секунд "прогреться"
    time.sleep(5)
    
    # 3. Запускаем бота в основном потоке
    run_bot()
