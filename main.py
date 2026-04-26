import os
import telebot
from telebot import types, apihelper
from threading import Thread
from flask import Flask
import time
from draw_map import generate_star_map

# 1. ГЛОБАЛЬНЫЕ НАСТРОЙКИ СВЯЗИ (Увеличиваем время ожидания до 60 секунд)
apihelper.CONNECT_TIMEOUT = 60
apihelper.READ_TIMEOUT = 60

# 2. СИСТЕМА ЖИЗНЕОБЕСПЕЧЕНИЯ (FLASK)
app = Flask('')

@app.route('/')
def home():
    return "Мартин на связи! Ракета Space News на орбите. 🛰️"

def run():
    # Hugging Face требует порт 7860
    port = int(os.environ.get("PORT", 7860))
    print(f"📡 Запуск веб-сервера на порту {port}...")
    app.run(host='0.0.0.0', port=port)

# 3. ПОЛУЧЕНИЕ ТОКЕНА ИЗ СЕКРЕТОВ (SETTINGS В HF)
TOKEN = os.environ.get('TELEGRAM_TOKEN')

# 4. ИНИЦИАЛИЗАЦИЯ БОТА С ПРОВЕРКОЙ
if not TOKEN:
    print("❌ ОШИБКА: Токен 'TELEGRAM_TOKEN' не найден в Secrets на Hugging Face!")
    bot = None
else:
    print(f"✅ Токен найден (начинается на {TOKEN[:5]}...)")
    # Создаем бота
    bot = telebot.TeleBot(TOKEN, threaded=False)

# 5. ОБРАБОТЧИКИ (КОМАНДЫ)
if bot:
    @bot.message_handler(commands=['start'])
    def send_welcome(message):
        text = message.text or ""
        print(f"📩 Получена команда /start. Текст: {text}")
        
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
            markup.row(types.KeyboardButton("📍 Определить небо", request_location=True))
            
            bot.send_message(message.chat.id, "Привет! Я Мартин. 🌌 Готов к наблюдениям!", reply_markup=markup)

    @bot.message_handler(content_types=['location'])
    def handle_location(message):
        print(f"📍 Получены координаты: {message.location.latitude}, {message.location.longitude}")
        bot.send_message(message.chat.id, "🛰 Секунду... Проявляю космический снимок!")
        try:
            path = generate_star_map(message.location.latitude, message.location.longitude, message.from_user.first_name)
            with open(path, 'rb') as f:
                bot.send_photo(message.chat.id, f, 
                               caption="🌟 **ТВОЁ НЕБО ГОТОВО!**\n\nОтправляй скрин в комментарии канала! 🐩📸",
                               parse_mode='Markdown')
        except Exception as e:
            print(f"❌ Ошибка рисования: {e}")
            bot.send_message(message.chat.id, "⚠️ Ошибка связи с телескопом.")

# 6. ЗАПУСК С ПОВТОРНЫМИ ПОПЫТКАМИ
if __name__ == "__main__":
    # Запускаем Flask
    Thread(target=run).start()
    
    if bot:
        print("🚀 Попытка авторизации в Telegram...")
        
        while True:
            try:
                # Проверяем, видит ли бот себя
                me = bot.get_me()
                print(f"🤖 УСПЕХ! Бот @{me.username} на связи!")
                
                # Запускаем прием сообщений
                bot.polling(none_stop=True, timeout=60, long_polling_timeout=60)
                
            except Exception as e:
                # Если упал (например, из-за таймаута) — ждем 10 сек и пробуем снова
                print(f"❌ Сбой связи: {e}. Переподключение через 10 секунд...")
                time.sleep(10)
    else:
        print("⛔ Бот не запущен, проверьте настройки токена.")
