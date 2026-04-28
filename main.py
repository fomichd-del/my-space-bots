import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import os
import time
from draw_map import generate_star_map
from flask import Flask
from threading import Thread
import wikipediaapi

# === КОНФИГУРАЦИЯ ===
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
# threaded=True позволяет обрабатывать несколько запросов, не блокируя основной поток
bot = telebot.TeleBot(TELEGRAM_TOKEN, threaded=True)

# Настройка Wikipedia
wiki_wiki = wikipediaapi.Wikipedia(
    user_agent='MartySpaceBot/1.1 (https://t.me/your_bot)', 
    language='ru'
)

app = Flask(__name__)
@app.route('/')
def keep_alive(): return "Борт Марти 14.1 в норме! 🛰️"

def run_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("📡 Мое небо", request_location=True))
    bot.send_message(
        message.chat.id, 
        f"🛰 <b>Штурман {message.from_user.first_name}, системы Starplot 14.1 онлайн!</b>\n\nОтправь локацию, и я просканирую сектор над твоей головой.", 
        reply_markup=markup, 
        parse_mode='HTML'
    )

@bot.message_handler(content_types=['location'])
def handle_location(message):
    loading_msg = bot.send_message(message.chat.id, "🔭 <i>Запуск глубокого рендеринга... Пожалуйста, подождите.</i>", parse_mode='HTML')
    
    # Генерация карты
    success, result, target_name, err_msg = generate_star_map(
        message.location.latitude, 
        message.location.longitude, 
        message.from_user.first_name
    )
    
    bot.delete_message(message.chat.id, loading_msg.message_id)

    if success:
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton(f"📚 База данных: {target_name}", callback_data=f"wiki_{target_name}"))
        
        with open(result, 'rb') as photo:
            # timeout=90 дает боту больше времени на загрузку тяжелого файла в Telegram
            bot.send_photo(
                message.chat.id, 
                photo, 
                caption=f"✨ Твое персональное небо!\n🎯 Главная цель в секторе: <b>{target_name}</b>", 
                reply_markup=markup, 
                parse_mode='HTML',
                timeout=90
            )
        if os.path.exists(result):
            os.remove(result)
    else:
        bot.send_message(message.chat.id, f"❌ Ошибка бортовых систем: {result}")

@bot.callback_query_handler(func=lambda call: call.data.startswith('wiki_'))
def callback_wiki(call):
    subject = call.data.replace('wiki_', '')
    bot.answer_callback_query(call.id, "Запрос к архивам...")
    
    search_term = subject.capitalize()
    page = wiki_wiki.page(f"{search_term} (созвездие)")
    if not page.exists():
        page = wiki_wiki.page(search_term)
    
    if page.exists():
        bot.send_message(
            call.message.chat.id, 
            f"📖 <b>{search_term.upper()}</b>\n\n{page.summary[:1500]}...\n\n🔗 <a href='{page.fullurl}'>Читать полную статью</a>", 
            parse_mode='HTML'
        )
    else:
        bot.send_message(call.message.chat.id, f"⚠️ Данные о «{search_term}» не найдены в базе.")

if __name__ == "__main__":
    Thread(target=run_server).start()
    
    # Решение ошибки 409: сброс старых соединений перед запуском
    print("Очистка старых сессий Telegram...")
    bot.remove_webhook()
    time.sleep(1)
    
    print("Марти 14.1 запущен!")
    # skip_pending=True игнорирует сообщения, пришедшие пока бот был выключен
    bot.infinity_polling(timeout=90, skip_pending=True, long_polling_timeout=40)
