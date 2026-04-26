import os
import telebot
from telebot import types, apihelper
from threading import Thread
from flask import Flask
import time
import requests
from draw_map import generate_star_map

# 1. НАСТРОЙКИ СВЯЗИ
apihelper.CONNECT_TIMEOUT = 120
apihelper.READ_TIMEOUT = 120

app = Flask('')

@app.route('/')
def home():
    return "Марти Астроном готов к наблюдениям! 🔭🐩"

def run_flask():
    port = int(os.environ.get("PORT", 7860))
    print(f"📡 [СЕРВЕР]: Запуск порта {port}")
    app.run(host='0.0.0.0', port=port)

# 2. ПОДГОТОВКА ТОКЕНА
TOKEN_RAW = os.environ.get('TELEGRAM_TOKEN', '')
TOKEN = TOKEN_RAW.strip().replace("'", "").replace('"', "")

if TOKEN:
    bot = telebot.TeleBot(TOKEN, threaded=False)
    
    @bot.message_handler(commands=['start'])
    def send_welcome(message):
        print(f"📩 [АКТИВНОСТЬ]: {message.from_user.first_name} зашел в обсерваторию")
        text = message.text or ""
        
        # Проверка секретного шлюза из канала
        if "get_map" in text:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            markup.add(types.KeyboardButton("📍 ПОКАЗАТЬ МОЁ НЕБО", request_location=True))
            bot.send_message(message.chat.id, 
                "🛰 **Прием, штурман! Секретный шлюз открыт.**\n\n"
                "Нажми кнопку ниже, чтобы я навел телескопы на твой город! 🐩🔭", 
                reply_markup=markup, parse_mode='Markdown')
        else:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.row("🎲 Случайное созвездие")
            markup.row(types.KeyboardButton("📍 Мое небо", request_location=True))
            bot.send_message(message.chat.id, 
                f"Привет, {message.from_user.first_name}! Я Марти Астроном. 🌌\n\n"
                "Я живу на Hugging Face и помогаю рисовать звездные карты для канала!", 
                reply_markup=markup)

    @bot.message_handler(content_types=['location'])
    def handle_location(message):
        print(f"📍 [ЛОКАЦИЯ]: Рисую карту для {message.from_user.first_name}")
        bot.send_message(message.chat.id, "🛰 Секунду... Проявляю космический снимок!")
        try:
            # Используем функцию из draw_map.py
            path = generate_star_map(message.location.latitude, message.location.longitude, message.from_user.first_name)
            with open(path, 'rb') as f:
                bot.send_photo(message.chat.id, f, 
                               caption="🌟 **ТВОЁ НЕБО ГОТОВО!**\n\nОтправляй его в канал! 🐩📸", 
                               parse_mode='Markdown')
        except Exception as e:
            print(f"❌ [ОШИБКА]: {e}")
            bot.send_message(message.chat.id, "⚠️ Ошибка телескопа. Попробуй позже.")

    @bot.message_handler(content_types=['text'])
    def handle_text(message):
        print(f"💬 [ТЕКСТ]: Сообщение от {message.from_user.first_name}")
        bot.send_message(message.chat.id, "Слышу тебя! Чтобы увидеть звезды, нажми кнопку 'Мое небо'.")

else:
    print("❌ [ОШИБКА]: ТОКЕН НЕ НАЙДЕН!")
    bot = None

# 3. ФУНКЦИЯ ЗАПУСКА
def start_martin():
    if not bot: return
    
    # Принудительный сброс вебхуков для чистого старта
    try:
        requests.get(f"https://api.telegram.org/bot{TOKEN}/deleteWebhook?drop_pending_updates=True", timeout=5)
    except: pass

    print("🚀 [БОТ]: Марти Астроном выходит в эфир...")
    while True:
        try:
            bot.infinity_polling(timeout=90, long_polling_timeout=90, skip_pending=True)
        except Exception as e:
            print(f"📡 [СВЯЗЬ]: Помехи ({e}). Переподключение через 5 сек...")
            time.sleep(5)

if __name__ == "__main__":
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()
    
    start_martin()
