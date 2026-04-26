import os
import telebot
from telebot import types, apihelper
from threading import Thread
from flask import Flask
import time
from draw_map import generate_star_map

# 1. МАКСИМАЛЬНЫЕ ТАЙМАУТЫ (Чтобы не бояться лагов сети)
apihelper.CONNECT_TIMEOUT = 120
apihelper.READ_TIMEOUT = 120

app = Flask('')

@app.route('/')
def home():
    # Эта страница нужна, чтобы Hugging Face видел: бот работает
    return "Мартин 24/7: Космический штурман в эфире! 🛰️"

def run_flask():
    port = int(os.environ.get("PORT", 7860))
    print(f"📡 [СИСТЕМА]: Веб-сервер запущен на порту {port}")
    app.run(host='0.0.0.0', port=port)

# 2. ПОДГОТОВКА ТОКЕНА
TOKEN_RAW = os.environ.get('TELEGRAM_TOKEN')
if not TOKEN_RAW:
    print("❌ [ОШИБКА]: Токен 'TELEGRAM_TOKEN' не найден в Secrets!")
    bot = None
else:
    TOKEN = TOKEN_RAW.strip().replace("'", "").replace('"', "")
    print(f"✅ [СИСТЕМА]: Токен загружен (Начало: {TOKEN[:5]})")
    bot = telebot.TeleBot(TOKEN, threaded=False)

# 3. КОМАНДНЫЙ ЦЕНТР (ЛОГИКА БОТА)
if bot:
    @bot.message_handler(commands=['start'])
    def send_welcome(message):
        user_name = message.from_user.first_name
        print(f"📩 [АКТИВНОСТЬ]: {user_name} нажал СТАРТ")
        
        text = message.text or ""
        if "get_map" in text:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            markup.add(types.KeyboardButton("📍 ПОКАЗАТЬ МОЁ НЕБО", request_location=True))
            
            bot.send_message(message.chat.id, 
                f"🛰 **Прием, штурман {user_name}! Секретный канал открыт.**\n\n"
                "Жми кнопку ниже, я настрою линзы на твой город! 🐩🔭", 
                reply_markup=markup, parse_mode='Markdown')
        else:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.row("🎲 Случайное созвездие")
            markup.row(types.KeyboardButton("📍 Мое небо", request_location=True))
            
            bot.send_message(message.chat.id, 
                f"Привет, {user_name}! Я Мартин. 🌌\nЯ готов рисовать карты для Space News!", 
                reply_markup=markup)

    @bot.message_handler(content_types=['location'])
    def handle_location(message):
        print(f"📍 [ЛОКАЦИЯ]: Рисую карту для {message.from_user.first_name}")
        bot.send_message(message.chat.id, "🛰 Секунду... Проявляю космический снимок!")
        try:
            path = generate_star_map(message.location.latitude, message.location.longitude, message.from_user.first_name)
            with open(path, 'rb') as f:
                bot.send_photo(message.chat.id, f, 
                               caption="🌟 **ТВОЁ НЕБО ГОТОВО!**\n\nВладик, смотри какие звезды! 🐩📸", 
                               parse_mode='Markdown')
        except Exception as e:
            print(f"❌ [ОШИБКА РИСОВАНИЯ]: {e}")
            bot.send_message(message.chat.id, "⚠️ Ошибка телескопа. Попробуй позже.")

# 4. ФУНКЦИЯ БЕСКОНЕЧНОГО ПОДКЛЮЧЕНИЯ
def run_bot():
    if not bot: return
    
    print("🚀 [БОТ]: Начинаю попытки прорыва в Telegram...")
    while True:
        try:
            # Сначала принудительно чистим вебхуки
            bot.remove_webhook()
            # Пытаемся запустить прослушивание сообщений
            bot.infinity_polling(timeout=90, long_polling_timeout=90)
        except Exception as e:
            print(f"📡 [СВЯЗЬ]: Помехи ({e}). Переподключение через 5 секунд...")
            time.sleep(5)

# 5. ЗАПУСК ВСЕГО
if __name__ == "__main__":
    # Запускаем сайт-заглушку, чтобы HF не ругался
    t_flask = Thread(target=run_flask)
    t_flask.daemon = True
    t_flask.start()
    
    # Сразу запускаем бота
    run_bot()
