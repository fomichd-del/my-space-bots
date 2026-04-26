import os
import telebot
import logging
from threading import Thread
from flask import Flask

# Включаем логирование в консоль Render
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask('')

@app.route('/')
def home():
    return "Мартин на связи! 🛰️"

def run():
    # Render требует порт 10000
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# Безопасный импорт художника
try:
    from draw_map import generate_star_map
    CAN_DRAW = True
    logger.info("✅ Модуль draw_map загружен")
except Exception as e:
    logger.error(f"❌ Ошибка загрузки draw_map: {e}")
    CAN_DRAW = False

TOKEN = os.getenv('TELEGRAM_TOKEN')
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    try:
        logger.info(f"Получена команда: {message.text}")
        
        # Проверяем наличие параметра get_map в ссылке
        if message.text and "get_map" in message.text:
            markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            markup.add(telebot.types.KeyboardButton("📍 ОТПРАВИТЬ КООРДИНАТЫ", request_location=True))
            
            bot.send_message(message.chat.id, 
                "🛰 Прием, штурман! Код доступа 'get_map' принят.\n\n"
                "Нажми кнопку ниже, чтобы я нарисовал твою карту! 🐩🚀", 
                reply_markup=markup)
        else:
            # Обычное меню, если зашли не по ссылке
            markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.row("🎲 Случайное созвездие", "📋 Список созвездий")
            markup.row(telebot.types.KeyboardButton("📍 Определить мое небо", request_location=True))
            
            bot.send_message(message.chat.id, "Привет! Я Мартин. 🌌 Чем займемся сегодня?", reply_markup=markup)
            
    except Exception as e:
        logger.error(f"Ошибка в блоке start: {e}")

@bot.message_handler(content_types=['location'])
def handle_location(message):
    bot.send_message(message.chat.id, "🛰 Получаю сигнал... Рисую твою карту!")
    if CAN_DRAW:
        try:
            path = generate_star_map(message.location.latitude, message.location.longitude, message.from_user.first_name)
            with open(path, 'rb') as f:
                bot.send_photo(message.chat.id, f, caption="🌟 ТВОЁ НЕБО ГОТОВО! 🐩📸")
        except Exception as e:
            logger.error(f"Ошибка рисования: {e}")
            bot.send_message(message.chat.id, "⚠️ Ошибка телескопа. Попробуй позже!")
    else:
        bot.send_message(message.chat.id, "🔭 Модуль рисования не активен.")

if __name__ == "__main__":
    # Запускаем веб-сервер в отдельном потоке
    Thread(target=run).start()
    logger.info("🚀 Бот запускает опрос (polling)...")
    bot.polling(none_stop=True)
