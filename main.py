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

# Инициализация Википедии
wiki_wiki = wikipediaapi.Wikipedia(
    user_agent='MartyAstrobot/1.0 (https://t.me/vladislav_space)',
    language='ru'
)

INSTRUCTIONS = (
    "📖 <b>ИНСТРУКЦИЯ ШТУРМАНА</b> 🚀\n\n"
    "🧭 <b>Кольцо:</b> Твой компас. С — Север, Ю — Юг, В — Восток, З — Запад.\n"
    "🎯 <b>[ЦЕЛЬ]:</b> Жирное розовое созвездие. Это твоя мишень.\n"
    "🌕 <b>ЛУНА:</b> Большой белый круг.\n"
    "☀️ <b>СОЛНЦЕ:</b> Оранжевый круг (виден днем/на закате).\n"
    "🪐 <b>ЦВЕТНЫЕ ТОЧКИ:</b> Планеты Солнечной системы.\n"
    "✨ <b>ЛИНИИ:</b> Контуры созвездий с их названиями."
)

app = Flask(__name__)
@app.route('/')
def keep_alive(): return "Марти в эфире! 🛰️"

def run_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("📡 Мое небо", request_location=True))
    markup.add(KeyboardButton("📖 Инструкция"))
    bot.send_message(message.chat.id, "🛰 <b>Бортовой компьютер активен!</b>\n\nИспользуй кнопки управления.", reply_markup=markup, parse_mode='HTML')

@bot.message_handler(func=lambda m: m.text == "📖 Инструкция")
def show_help(message):
    bot.send_message(message.chat.id, INSTRUCTIONS, parse_mode='HTML')

@bot.message_handler(content_types=['location'])
def handle_location(message):
    loading_msg = bot.send_message(message.chat.id, "🔭 <i>Синхронизация...</i>", parse_mode='HTML')
    success, result, target_name, _ = generate_star_map(message.location.latitude, message.location.longitude, message.from_user.first_name)
    bot.delete_message(message.chat.id, loading_msg.message_id)

    if success:
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton(f"📚 База данных: {target_name}", callback_data=f"wiki_{target_name}"))
        with open(result, 'rb') as photo:
            bot.send_photo(message.chat.id, photo, caption=f"✨ Сектор просканирован!\n🎯 Твоя цель сегодня: <b>{target_name}</b>", reply_markup=markup, parse_mode='HTML')
        os.remove(result)

@bot.callback_query_handler(func=lambda call: call.data.startswith('wiki_'))
def callback_wiki(call):
    subject = call.data.replace('wiki_', '')
    bot.answer_callback_query(call.id, "Запрашиваю архивы...")
    
    # Умный поиск: пробуем найти как созвездие
    page = wiki_wiki.page(f"{subject} (созвездие)")
    if not page.exists():
        page = wiki_wiki.page(subject)
    
    if page.exists():
        text = page.summary[:1200] + "..."
        bot.send_message(call.message.chat.id, f"📖 <b>{subject.upper()}</b>\n\n{text}\n\n🔗 <a href='{page.fullurl}'>Читать полностью</a>", parse_mode='HTML')
    else:
        bot.send_message(call.message.chat.id, f"⚠️ Данные о «{subject}» не найдены в архивах.")

if __name__ == "__main__":
    Thread(target=run_server).start()
    bot.infinity_polling(timeout=20, long_polling_timeout=10)
