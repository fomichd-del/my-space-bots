import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import os
import time
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

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("📡 Мое небо", request_location=True))
    markup.add(KeyboardButton("❓ Помощь и Инструкция"))
    
    welcome_text = (
        f"Привет, {message.from_user.first_name}! 🐾 Я — <b>Марти Астроном</b> 🎓\n\n"
        "Жми <b>«📡 Мое небо»</b>, делись локацией, и я соберу для тебя персональную звездную карту! 🚀"
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup, parse_mode='HTML')

@bot.message_handler(content_types=['location'])
def handle_location(message):
    try:
        loading_msg = bot.send_message(
            message.chat.id, 
            "📡 <b>Координаты получены!</b> Навожу линзы телескопов...", 
            parse_mode='HTML'
        )
        
        # Передаем ID пользователя для создания уникального файла
        success, result, target_name, err_msg = generate_star_map(
            message.location.latitude, 
            message.location.longitude, 
            message.from_user.first_name,
            message.from_user.id
        )
        
        bot.delete_message(message.chat.id, loading_msg.message_id)

        if success:
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton(f"🌌 Рассекретить архивы: {target_name}", callback_data=f"wiki_{target_name}"))
            
            with open(result, 'rb') as photo:
                bot.send_photo(
                    message.chat.id, 
                    photo, 
                    caption=f"✨ Твоя персональная проекция!\n🎯 Цель: <b>{target_name}</b>", 
                    reply_markup=markup, 
                    parse_mode='HTML'
                )
            # Удаляем персональный файл сразу после отправки
            if os.path.exists(result): os.remove(result)
        else:
            bot.send_message(message.chat.id, f"❌ Ошибка калибровки: {result}")
    except Exception as e:
        bot.send_message(message.chat.id, f"🆘 Космические помехи: {str(e)}")

# Обработка Wiki остается без изменений, как в твоем золотом стандарте
@bot.callback_query_handler(func=lambda call: call.data.startswith('wiki_'))
def callback_wiki(call):
    subject = call.data.replace('wiki_', '')
    bot.answer_callback_query(call.id, "Загружаю данные из Архивов...")
    search_term = subject.capitalize()
    page = wiki_wiki.page(f"{search_term} (созвездие)")
    if not page.exists(): page = wiki_wiki.page(search_term)
    
    if page.exists():
        summary = page.summary
        wiki_text = f"🌌 <b>ДОСЬЕ: {search_term.upper()}</b>\n\n{summary[:600]}...\n\n"
        wiki_text += f"🔗 <a href='{page.fullurl}'>[ Полный архив ]</a>"
        bot.send_message(call.message.chat.id, wiki_text, parse_mode='HTML')
    else:
        bot.send_message(call.message.chat.id, f"⚠️ Данные о «{search_term}» отсутствуют.")

if __name__ == "__main__":
    Thread(target=run_server).start()
    bot.remove_webhook()
    bot.infinity_polling(timeout=90, skip_pending=True)
