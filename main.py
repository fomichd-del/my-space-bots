import os
import telebot
from telebot import types, apihelper
from threading import Thread
from flask import Flask
import time
import requests
from draw_map import generate_star_map

# 1. ЖЕСТКИЕ ТАЙМАУТЫ
apihelper.CONNECT_TIMEOUT = 120
apihelper.READ_TIMEOUT = 120

app = Flask('')

@app.route('/')
def home():
    return "Мартин 24/7: Космический штурман в эфире! 🛰️"

def run_flask():
    port = int(os.environ.get("PORT", 7860))
    print(f"📡 [СИСТЕМА]: Веб-сервер на порту {port}")
    app.run(host='0.0.0.0', port=port)

# 2. ПОДГОТОВКА ТОКЕНА
TOKEN_RAW = os.environ.get('TELEGRAM_TOKEN', '')
TOKEN = TOKEN_RAW.strip().replace("'", "").replace('"', "")

# 3. ФУНКЦИЯ ПРОВЕРКИ СВЯЗИ (ПИНГ)
def check_telegram_connection():
    print(f"🔍 [ДИАГНОСТИКА]: Проверяю связь с api.telegram.org...")
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/getMe"
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            print(f"✅ [ДИАГНОСТИКА]: Связь с Telegram ЕСТЬ! Ответ: {response.json()['result']['username']}")
            return True
        else:
            print(f"❌ [ДИАГНОСТИКА]: Telegram ответил ошибкой: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ [ДИАГНОСТИКА]: Не могу достучаться до Telegram: {e}")
        return False

# 4. ЛОГИКА БОТА
if TOKEN:
    bot = telebot.TeleBot(TOKEN, threaded=False)
    
    @bot.message_handler(commands=['start'])
    def send_welcome(message):
        print(f"📩 [АКТИВНОСТЬ]: {message.from_user.first_name} нажал СТАРТ")
        text = message.text or ""
        if "get_map" in text:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            markup.add(types.KeyboardButton("📍 ПОКАЗАТЬ МОЁ НЕБО", request_location=True))
            bot.send_message(message.chat.id, "🛰 **Секретный код активен.**\nЖми на кнопку для карты! 🐩🔭", reply_markup=markup, parse_mode='Markdown')
        else:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add("🎲 Случайное созвездие")
            markup.add(types.KeyboardButton("📍 Мое небо", request_location=True))
            bot.send_message(message.chat.id, "Привет! Я Мартин. 🌌 Готов к работе!", reply_markup=markup)

    @bot.message_handler(content_types=['location'])
    def handle_location(message):
        bot.send_message(message.chat.id, "🛰 Секунду... Рисую!")
        try:
            path = generate_star_map(message.location.latitude, message.location.longitude, message.from_user.first_name)
            with open(path, 'rb') as f:
                bot.send_photo(message.chat.id, f, caption="🌟 ТВОЁ НЕБО ГОТОВО! 🐩📸", parse_mode='Markdown')
        except Exception as e:
            print(f"❌ [ОШИБКА РИСОВАНИЯ]: {e}")
            bot.send_message(message.chat.id, "⚠️ Ошибка телескопа.")
else:
    bot = None

# 5. ЗАПУСК
if __name__ == "__main__":
    # Запуск Flask
    t_flask = Thread(target=run_flask)
    t_flask.daemon = True
    t_flask.start()
    
    print("🚀 [БОТ]: Начинаю миссию...")
    
    if bot:
        while True:
            # Сначала ПИНГ, потом запуск
            if check_telegram_connection():
                try:
                    print("🧹 [БОТ]: Удаляю старые связи и вхожу в эфир...")
                    bot.remove_webhook()
                    bot.infinity_polling(timeout=90, long_polling_timeout=90)
                except Exception as e:
                    print(f"📡 [СВЯЗЬ]: Помехи ({e}). Перезапуск через 10 сек...")
                    time.sleep(10)
            else:
                print("⏳ [БОТ]: Жду восстановления связи с космосом (10 сек)...")
                time.sleep(10)
