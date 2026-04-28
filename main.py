import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import os
import time
from draw_map import generate_star_map
from flask import Flask
from threading import Thread
import wikipediaapi

# === КОНФИГУРАЦИЯ ===
# Версия: 26.0 "Точная стыковка"
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
bot = telebot.TeleBot(TELEGRAM_TOKEN, threaded=True)

wiki_wiki = wikipediaapi.Wikipedia(user_agent='MartySpaceBot/1.1', language='ru')

app = Flask(__name__)
@app.route('/')
def keep_alive(): 
    return "Командный центр Марти v24.0 — RAM-Friendly в эфире! 🛰️"

def run_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("📡 Мое небо", request_location=True))
    
    welcome_text = (
        f"🛰 <b>Штурман {message.from_user.first_name}, системы Starplot 25.0 онлайн!</b>\n\n"
        "Проведена финальная аналитическая калибровка. Карта смещена по вашим расчетам."
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup, parse_mode='HTML')

@bot.message_handler(content_types=['location'])
def handle_location(message):
    try:
        bot.send_message(message.chat.id, "✅ Координаты приняты. Запускаю Starplot v25.0...")
        
        loading_msg = bot.send_message(message.chat.id, "🔭 <i>Рендеринг...</i>", parse_mode='HTML')
        
        success, result, target_name, err_msg = generate_star_map(
            message.location.latitude, 
            message.location.longitude, 
            message.from_user.first_name
        )
        
        bot.delete_message(message.chat.id, loading_msg.message_id)

        if success:
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton(f"📚 База: {target_name}", callback_data=f"wiki_{target_name}"))
            
            with open(result, 'rb') as photo:
                bot.send_photo(
                    message.chat.id, 
                    photo, 
                    caption=f"✨ Твое небо!\n🎯 Цель: <b>{target_name}</b>", 
                    reply_markup=markup, 
                    parse_mode='HTML',
                    timeout=120
                )
            if os.path.exists(result): os.remove(result)
        else:
            bot.send_message(message.chat.id, f"❌ Ошибка: {result}")
    except Exception as e:
        bot.send_message(message.chat.id, f"🆘 Ошибка: {str(e)}")

if __name__ == "__main__":
    Thread(target=run_server).start()
    bot.remove_webhook()
    time.sleep(2)
    bot.infinity_polling(timeout=90, skip_pending=True)
