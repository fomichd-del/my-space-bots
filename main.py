import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import os, time, signal
from draw_map import generate_star_map
from flask import Flask
from threading import Thread
import wikipediaapi

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
bot = telebot.TeleBot(TELEGRAM_TOKEN, threaded=True)

wiki_wiki = wikipediaapi.Wikipedia(user_agent='MartySpaceBot/1.1', language='ru')

app = Flask(__name__)
@app.route('/')
def keep_alive(): return "Марти Астроном в эфире! 🛰️"
def run_server(): app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

# Функция для прерывания зависших процессов
def timeout_handler(signum, frame):
    raise Exception("Космический тайм-аут: расчет занял слишком много времени!")

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("📡 Мое небо", request_location=True))
    markup.add(KeyboardButton("❓ Помощь и Инструкция"))
    bot.send_message(message.chat.id, f"Привет, {message.from_user.first_name}! 🐾\nЖми <b>«📡 Мое небо»</b>!", parse_mode='HTML', reply_markup=markup)

@bot.message_handler(content_types=['location'])
def handle_location(message):
    # Устанавливаем таймер на 60 секунд (если бот зависнет — он выдаст ошибку и сбросится)
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(60) 
    
    try:
        loading_msg = bot.send_message(message.chat.id, "📡 <b>Координаты получены!</b> Построение карты...", parse_mode='HTML')
        
        # Передаем ID пользователя для уникальности файла
        success, result, target_name, err_msg = generate_star_map(
            message.location.latitude, 
            message.location.longitude, 
            message.from_user.first_name,
            message.from_user.id
        )
        
        bot.delete_message(message.chat.id, loading_msg.message_id)

        if success:
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton(f"🌌 Архивы: {target_name}", callback_data=f"wiki_{target_name}"))
            
            with open(result, 'rb') as photo:
                bot.send_photo(
                    message.chat.id, photo, 
                    caption=f"🎯 Цель: <b>{target_name}</b>", 
                    reply_markup=markup, parse_mode='HTML', 
                    timeout=120 # Увеличенное время ожидания для загрузки
                )
            if os.path.exists(result): os.remove(result)
        else:
            bot.send_message(message.chat.id, f"❌ Ошибка калибровки: {result}")
    except Exception as e:
        bot.send_message(message.chat.id, f"🆘 Космические помехи: {str(e)}")
    finally:
        signal.alarm(0) # Отключаем таймер в любом случае

# Википедия (оставляем твою рабочую логику)
@bot.callback_query_handler(func=lambda call: call.data.startswith('wiki_'))
def callback_wiki(call):
    subject = call.data.replace('wiki_', '')
    bot.answer_callback_query(call.id, "Загружаю данные...")
    page = wiki_wiki.page(f"{subject} (созвездие)")
    if not page.exists(): page = wiki_wiki.page(subject)
    if page.exists():
        bot.send_message(call.message.chat.id, f"🌌 <b>{subject.upper()}</b>\n\n{page.summary[:600]}...", parse_mode='HTML')
    else:
        bot.send_message(call.message.chat.id, "⚠️ Данные отсутствуют.")

if __name__ == "__main__":
    Thread(target=run_server).start()
    bot.remove_webhook()
    # Более настойчивый режим опроса
    bot.infinity_polling(timeout=90, long_polling_timeout=90, skip_pending=True)
