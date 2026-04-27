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

wiki_wiki = wikipediaapi.Wikipedia(
    user_agent='MartyAstrobot/1.0 (https://t.me/vladislav_space)',
    language='ru'
)

app = Flask(__name__)
@app.route('/')
def keep_alive(): return "Марти 10.0 Зодиак активен! 🚀"

def run_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("📡 Мое небо", request_location=True))
    markup.add(KeyboardButton("📖 Инструкция"))
    bot.send_message(message.chat.id, "🛰 <b>Бортовой компьютер «Зодиак 10.0» запущен!</b>\n\nШтурман, я загрузил полный атлас Зодиака и основные созвездия.", reply_markup=markup, parse_mode='HTML')

@bot.message_handler(func=lambda m: m.text == "📖 Инструкция")
def show_help(message):
    bot.send_message(message.chat.id, (
        "📖 <b>ИНСТРУКЦИЯ ЗОДИАКАЛЬНОГО АТЛАСА</b>\n\n"
        "♌ <b>Зодиак:</b> Все 12 созвездий отрисованы полностью.\n"
        "✨ <b>Сияние:</b> Звезды имеют дифракционные лучи (кресты).\n"
        "🪐 <b>Планеты:</b> Отмечены крупными знаками ♂, ♃, ♄.\n"
        "☀️ <b>Солнце:</b> Яркий оранжевый диск с подписью.\n"
        "🎯 <b>Цель:</b> Подсвечена розовым неоном."
    ), parse_mode='HTML')

@bot.message_handler(content_types=['location'])
def handle_location(message):
    loading_msg = bot.send_message(message.chat.id, "🔭 <i>Идет рендеринг Гранд-Атласа... Подключение к Википедии...</i>", parse_mode='HTML')
    success, result, target_name, _ = generate_star_map(message.location.latitude, message.location.longitude, message.from_user.first_name)
    bot.delete_message(message.chat.id, loading_msg.message_id)

    if success:
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton(f"📚 База данных: {target_name}", callback_data=f"wiki_{target_name}"))
        with open(result, 'rb') as photo:
            bot.send_photo(message.chat.id, photo, caption=f"✨ Карта готова, Штурман!\n🎯 Изучаем созвездие: <b>{target_name}</b>", reply_markup=markup, parse_mode='HTML')
        os.remove(result)
    else:
        bot.send_message(message.chat.id, f"❌ Ошибка рендеринга: {result}")

@bot.callback_query_handler(func=lambda call: call.data.startswith('wiki_'))
def callback_wiki(call):
    subject = call.data.replace('wiki_', '')
    bot.answer_callback_query(call.id, "Запрос к архивам...")
    search_term = subject.capitalize()
    page = wiki_wiki.page(f"{search_term} (созвездие)")
    if not page.exists(): page = wiki_wiki.page(search_term)
    
    if page.exists():
        bot.send_message(call.message.chat.id, f"📖 <b>{search_term.upper()}</b>\n\n{page.summary[:1500]}...\n\n🔗 <a href='{page.fullurl}'>Читать далее</a>", parse_mode='HTML')
    else:
        bot.send_message(call.message.chat.id, f"⚠️ Данные не найдены.")

if __name__ == "__main__":
    Thread(target=run_server).start()
    bot.infinity_polling(timeout=30)
