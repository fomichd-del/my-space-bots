import os
import telebot
from telebot import types, apihelper
from threading import Thread
from flask import Flask
import time
from draw_map import generate_star_map

# 1. СУПЕР-ТАЙМАУТЫ ДЛЯ СВЯЗИ
apihelper.CONNECT_TIMEOUT = 120
apihelper.READ_TIMEOUT = 120

app = Flask('')

@app.route('/')
def home():
    return "Мартин 24/7: Космический штурман на связи! 🛰️"

def run_flask():
    # Hugging Face слушает порт 7860
    port = int(os.environ.get("PORT", 7860))
    print(f"📡 [ВЕБ-СЕРВЕР]: Запуск на порту {port}...")
    app.run(host='0.0.0.0', port=port)

# 2. ПОДГОТОВКА ТОКЕНА
TOKEN_RAW = os.environ.get('TELEGRAM_TOKEN')
if not TOKEN_RAW:
    print("❌ [ОШИБКА]: Секрет 'TELEGRAM_TOKEN' не найден в настройках Space!")
    bot = None
else:
    TOKEN = TOKEN_RAW.strip().replace("'", "").replace('"', "")
    print(f"✅ [СИСТЕМА]: Токен загружен (Начало: {TOKEN[:5]})")
    bot = telebot.TeleBot(TOKEN, threaded=False)

# 3. КОМАНДНЫЙ ЦЕНТР МАРТИНА
if bot:
    @bot.message_handler(commands=['start'])
    def send_welcome(message):
        user_name = message.from_user.first_name
        print(f"📩 [АКТИВНОСТЬ]: Пользователь {user_name} нажал СТАРТ")
        
        text = message.text or ""
        if "get_map" in text:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            markup.add(types.KeyboardButton("📍 ПОКАЗАТЬ МОЁ НЕБО", request_location=True))
            
            bot.send_message(message.chat.id, 
                f"🛰 **Прием, штурман {user_name}! Секретный шлюз открыт.**\n\n"
                "Нажми кнопку ниже, чтобы я навел телескопы на твой город! 🐩🔭", 
                reply_markup=markup, parse_mode='Markdown')
        else:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.row("🎲 Случайное созвездие")
            markup.row(types.KeyboardButton("📍 Мое небо", request_location=True))
            
            bot.send_message(message.chat.id, 
                f"Привет, {user_name}! Я Мартин. 🌌\nЯ готов рисовать звездные карты для канала Space News!", 
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

# 4. ЗАПУСК ВСЕХ СИСТЕМ
if __name__ == "__main__":
    # Сначала запускаем Flask в фоновом потоке
    print("🚀 [1/2]: Запуск системы жизнеобеспечения (Flask)...")
    t_flask = Thread(target=run_flask)
    t_flask.daemon = True
    t_flask.start()
    
    # Даем серверу 3 секунды на старт
    time.sleep(3)
    
    if bot:
        print("🚀 [2/2]: Попытка прорыва в Telegram...")
        while True:
            try:
                # УДАЛЯЕМ WEBHOOK И ПРОВЕРЯЕМ СЕБЯ
                bot.remove_webhook()
                me = bot.get_me()
                print(f"🤖 [УСПЕХ]: Мартин (@{me.username}) в сети и слушает эфир!")
                
                # Бесконечный опрос
                bot.infinity_polling(timeout=90, long_polling_timeout=90)
                
            except Exception as e:
                print(f"📡 [СВЯЗЬ]: Помехи ({e}). Переподключение через 10 секунд...")
                time.sleep(10)
    else:
        print("⛔ [СТОП]: Бот не может быть запущен без токена.")
