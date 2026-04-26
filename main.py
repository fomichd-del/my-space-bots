import os
import telebot
from telebot import types, apihelper
from threading import Thread
from flask import Flask
import time
import requests
import logging
from draw_map import generate_star_map

# 1. ОСТАВЛЯЕМ ГЛУБОКИЙ РАДАР (для отслеживания всех пакетов)
telebot.logger.setLevel(logging.DEBUG)

apihelper.CONNECT_TIMEOUT = 120
apihelper.READ_TIMEOUT = 120

app = Flask('')

@app.route('/')
def home():
    return "Мартин на связи! Ракета Space News на орбите. 🛰️"

def run_flask():
    port = int(os.environ.get("PORT", 7860))
    print(f"📡 [СЕРВЕР]: Запуск порта {port}")
    app.run(host='0.0.0.0', port=port)

# 2. ПОДГОТОВКА ТОКЕНА
TOKEN_RAW = os.environ.get('TELEGRAM_TOKEN', '')
TOKEN = TOKEN_RAW.strip().replace("'", "").replace('"', "")

if TOKEN:
    print(f"✅ [СИСТЕМА]: Токен загружен (Начало: {TOKEN[:5]}...)")
    bot = telebot.TeleBot(TOKEN, threaded=False)
    
    # --- ОБРАБОТЧИК СТАРТА ---
    @bot.message_handler(commands=['start'])
    def send_welcome(message):
        print(f"📩 [АКТИВНОСТЬ]: {message.from_user.first_name} нажал СТАРТ")
        text = message.text or ""
        if "get_map" in text:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            markup.add(types.KeyboardButton("📍 ПОКАЗАТЬ МОЁ НЕБО", request_location=True))
            bot.send_message(message.chat.id, "🛰 **Секретный шлюз открыт.**\nЖми на кнопку для карты! 🐩🔭", reply_markup=markup, parse_mode='Markdown')
        else:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.row("🎲 Случайное созвездие")
            markup.row(types.KeyboardButton("📍 Мое небо", request_location=True))
            bot.send_message(message.chat.id, "Привет! Я Мартин. 🌌 Готов к работе!", reply_markup=markup)

    # --- ОБРАБОТЧИК ЛОКАЦИИ (ГЕНЕРАЦИЯ КАРТЫ) ---
    @bot.message_handler(content_types=['location'])
    def handle_location(message):
        print(f"📍 [ЛОКАЦИЯ]: Рисую для {message.from_user.first_name}")
        bot.send_message(message.chat.id, "🛰 Секунду... Навожу телескопы!")
        try:
            path = generate_star_map(message.location.latitude, message.location.longitude, message.from_user.first_name)
            with open(path, 'rb') as f:
                bot.send_photo(message.chat.id, f, caption="🌟 ТВОЁ НЕБО ГОТОВО! 🐩📸", parse_mode='Markdown')
        except Exception as e:
            print(f"❌ [ОШИБКА РИСОВАНИЯ]: {e}")
            bot.send_message(message.chat.id, "⚠️ Ошибка телескопа. Попробуй позже.")

    # --- НОВЫЙ ВСЕЯДНЫЙ РАДАР (ДЛЯ ЛЮБОГО ТЕКСТА) ---
    @bot.message_handler(content_types=['text'])
    def handle_text(message):
        print(f"💬 [ТЕКСТ]: Получено сообщение '{message.text}' от {message.from_user.first_name}")
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.row("🎲 Случайное созвездие")
        markup.row(types.KeyboardButton("📍 Мое небо", request_location=True))
        bot.send_message(message.chat.id, f"Слышу тебя, штурман! Ты сказал: {message.text}. Но я пока лучше всего реагирую на команды и кнопки.", reply_markup=markup)

else:
    print("❌ [ОШИБКА]: ТОКЕН НЕ НАЙДЕН!")
    bot = None

# 3. ПРЯМОЙ СБРОС И ЗАПУСК (ОБХОД ЗАВИСАНИЯ)
def start_martin():
    if not bot: return
    
    print("🧹 [СИСТЕМА]: Прямой сброс старых настроек (5 сек на ответ)...")
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/deleteWebhook?drop_pending_updates=True"
        requests.get(url, timeout=5)
        print("✅ [СИСТЕМА]: Путь чист!")
    except Exception as e:
        print(f"⚠️ [СИСТЕМА]: Сброс проигнорирован (нормально): {e}")

    print("🚀 [БОТ]: Вхожу в эфир Telegram...")
    while True:
        try:
            # skip_pending=True игнорирует старые клики, чтобы бот не "захлебнулся"
            bot.infinity_polling(timeout=90, long_polling_timeout=90, skip_pending=True)
        except Exception as e:
            print(f"📡 [СВЯЗЬ]: Помехи ({e}). Жду 5 сек...")
            time.sleep(5)

# 4. ГЛАВНЫЙ ЗАПУСК
if __name__ == "__main__":
    flask_thread = Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    
    start_martin()
