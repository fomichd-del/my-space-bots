import os
import telebot
from telebot import types, apihelper
from threading import Thread
from flask import Flask
import time
from draw_map import generate_star_map

# 1. ЖЕСТКИЕ ТАЙМАУТЫ (Чтобы Hugging Face не сбрасывал соединение)
apihelper.CONNECT_TIMEOUT = 120
apihelper.READ_TIMEOUT = 120

app = Flask('')

@app.route('/')
def home():
    return "Мартин на связи! Ракета Space News на орбите. 🛰️"

def run():
    # Hugging Face требует порт 7860
    port = int(os.environ.get("PORT", 7860))
    print(f"📡 Веб-сервер запущен на порту {port}")
    app.run(host='0.0.0.0', port=port)

# 2. ЗАГРУЗКА ТОКЕНА
TOKEN_RAW = os.environ.get('TELEGRAM_TOKEN')

if not TOKEN_RAW:
    print("❌ ОШИБКА: Токен не найден в Secrets на Hugging Face!")
    bot = None
else:
    # Очищаем токен от пробелов и кавычек, если они затесались
    TOKEN = TOKEN_RAW.strip().replace("'", "").replace('"', "")
    print(f"✅ Токен загружен (Начало: {TOKEN[:5]})")
    bot = telebot.TeleBot(TOKEN, threaded=False)

# 3. ОБРАБОТЧИКИ КОМАНД
if bot:
    @bot.message_handler(commands=['start'])
    def send_welcome(message):
        # Добавляем лог, чтобы видеть активность в консоли HF
        print(f"📩 КТО-ТО НАПИСАЛ БОТУ! ID: {message.from_user.id}")
        text = message.text or ""
        
        if "get_map" in text:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            markup.add(types.KeyboardButton("📍 ПОКАЗАТЬ МОЁ НЕБО", request_location=True))
            bot.send_message(message.chat.id, 
                "🛰 **Прием! Код 'get_map' активен.**\n\n"
                "Жми на кнопку ниже, чтобы я нарисовал карту звезд! 🐩🔭", 
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
        print(f"📍 ПОЛУЧЕНА ЛОКАЦИЯ: {message.location.latitude}, {message.location.longitude}")
        bot.send_message(message.chat.id, "🛰 Секунду... Настраиваю линзы на твои координаты!")
        try:
            path = generate_star_map(message.location.latitude, message.location.longitude, message.from_user.first_name)
            with open(path, 'rb') as f:
                bot.send_photo(message.chat.id, f, 
                               caption="🌟 **ТВОЁ НЕБО ГОТОВО!**\n\nОтправляй его в канал Space News! 🐩📸", 
                               parse_mode='Markdown')
        except Exception as e:
            print(f"❌ ОШИБКА РИСОВАНИЯ: {e}")
            bot.send_message(message.chat.id, "⚠️ Ошибка телескопа. Попробуй позже.")

# 4. ЗАПУСК БЕЗ ЗАДЕРЖЕК
if __name__ == "__main__":
    # Запускаем Flask в отдельном потоке
    t = Thread(target=run)
    t.daemon = True
    t.start()
    
    if bot:
        print("🚀 ВХОДИМ В РЕЖИМ ОЖИДАНИЯ СООБЩЕНИЙ (Polling)...")
        while True:
            try:
                # Запускаем сразу, без предварительных проверок
                bot.polling(none_stop=True, timeout=120, long_polling_timeout=120)
            except Exception as e:
                print(f"📡 Потеря связи: {e}. Переподключение через 10 секунд...")
                time.sleep(10)
    else:
        print("⛔ Бот не запущен из-за проблем с токеном.")
