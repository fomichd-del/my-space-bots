import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import os
from draw_map import generate_star_map
from flask import Flask
from threading import Thread
import wikipediaapi

# === НАСТРОЙКИ ===
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# Инициализация Википедии (на русском языке)
# User-agent нужен для соблюдения правил Википедии
wiki_wiki = wikipediaapi.Wikipedia(
    user_agent='MartyAstrobot/1.0 (https://t.me/vladislav_space)',
    language='ru'
)

# === МИНИ ВЕБ-СЕРВЕР ДЛЯ RENDER (МАЯК) ===
app = Flask(__name__)

@app.route('/')
def keep_alive():
    return "Марти на связи! Модуль Википедии активен. 🚀"

def run_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# === ЛОГИКА БОТА ===
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    item = KeyboardButton("📡 Мое небо", request_location=True)
    markup.add(item)
    
    welcome_text = (
        "🛰 <b>Бортовой компьютер активирован.</b>\n\n"
        "Штурман, я подключился к глобальным архивам знаний. "
        "Запроси «Мое небо», и я не только отрисую карту, но и смогу рассказать всё о любой цели!"
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup, parse_mode='HTML')

@bot.message_handler(content_types=['location'])
def handle_location(message):
    lat = message.location.latitude
    lon = message.location.longitude
    user_name = message.from_user.first_name
    chat_id = message.chat.id

    loading_msg = bot.send_message(
        chat_id, 
        "🔭 <i>Захват координат... Подключение к спутникам связи...</i>",
        parse_mode='HTML'
    )

    # Запуск генератора (аргументы и возвращаемые значения те же)
    success, result, target_name, target_fact = generate_star_map(lat, lon, user_name)

    bot.delete_message(chat_id, loading_msg.message_id)

    if success:
        # Мы больше не храним факт в USER_FACTS, 
        # вместо этого мы будем искать информацию по target_name
        markup = InlineKeyboardMarkup()
        # Кнопка теперь вызывает поиск в Википедии
        fact_btn = InlineKeyboardButton(f"📜 Глубокое сканирование: {target_name}", callback_data=f"wiki_{target_name}")
        markup.add(fact_btn)

        with open(result, 'rb') as photo:
            bot.send_photo(
                chat_id, 
                photo, 
                caption=f"✨ Карта сектора готова, Штурман!\n🎯 Навигатор сфокусирован на: <b>{target_name}</b>",
                reply_markup=markup,
                parse_mode='HTML'
            )
        os.remove(result)
    else:
        bot.send_message(chat_id, f"❌ Сбой систем: {result}")

@bot.callback_query_handler(func=lambda call: call.data.startswith('wiki_'))
def callback_wiki(call):
    # Извлекаем название созвездия из callback_data
    subject = call.data.replace('wiki_', '')
    chat_id = call.message.chat.id
    
    bot.answer_callback_query(call.id, "Запрашиваю архивы Википедии...")
    
    # Ищем страницу
    page = wiki_wiki.page(subject)
    
    if page.exists():
        # Берем краткое содержание (summary)
        # Ограничиваем длину, чтобы не превысить лимит сообщения Telegram
        description = page.summary[:1500] + "..."
        
        response = (
            f"📖 <b>АРХИВНЫЕ ДАННЫЕ: {subject.upper()}</b>\n\n"
            f"{description}\n\n"
            f"🔗 <a href='{page.fullurl}'>Читать полную статью в Википедии</a>"
        )
    else:
        response = f"⚠️ В текущем секторе архивы пусты. Попробуйте просканировать другую цель!"

    bot.send_message(chat_id, response, parse_mode='HTML', disable_web_page_preview=False)

if __name__ == "__main__":
    Thread(target=run_server).start()
    print("🚀 Маяк и Вики-модуль запущены!")
    bot.infinity_polling(timeout=20, long_polling_timeout=10)
