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

# === ВЕБ-СЕРВЕР (МАЯК) ===
app = Flask(__name__)
@app.route('/')
def keep_alive(): return "Марти в эфире! Визуализация 2.0 запущена. 🚀"

def run_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# === ОБРАБОТКА КОМАНД ===
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("📡 Мое небо", request_location=True))
    markup.add(KeyboardButton("📖 Инструкция"))
    bot.send_message(message.chat.id, "🛰 <b>Бортовой компьютер обновлен до версии High-Res!</b>\n\nЖми «Мое небо», чтобы увидеть обновленную карту.", reply_markup=markup, parse_mode='HTML')

@bot.message_handler(func=lambda m: m.text == "📖 Инструкция")
def show_help(message):
    help_text = (
        "📖 <b>ГАЙД ПО КАРТЕ 2.0</b>\n\n"
        "✨ <b>Звезды:</b> Большие точки — ярчайшие светила.\n"
        "🏛 <b>Созвездия:</b> Подписаны на русском. Цель выделена ярким неоном.\n"
        "🪐 <b>Планеты:</b> Отмечены символами (♂, ♃). Расшифровка — внизу карты.\n"
        "🌕 <b>Луна:</b> Показывает текущую фазу.\n"
        "☀️ <b>Солнце:</b> Желтый диск (виден, если день)."
    )
    bot.send_message(message.chat.id, help_text, parse_mode='HTML')

@bot.message_handler(content_types=['location'])
def handle_location(message):
    loading_msg = bot.send_message(message.chat.id, "🔭 <i>Рендеринг высокодетализированной карты...</i>", parse_mode='HTML')
    success, result, target_name, _ = generate_star_map(message.location.latitude, message.location.longitude, message.from_user.first_name)
    bot.delete_message(message.chat.id, loading_msg.message_id)

    if success:
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton(f"📚 База данных: {target_name}", callback_data=f"wiki_{target_name}"))
        with open(result, 'rb') as photo:
            bot.send_photo(message.chat.id, photo, caption=f"✨ Твое небо сегодня!\n🎯 Цель: <b>{target_name}</b>", reply_markup=markup, parse_mode='HTML')
        os.remove(result)

@bot.callback_query_handler(func=lambda call: call.data.startswith('wiki_'))
def callback_wiki(call):
    subject = call.data.replace('wiki_', '')
    bot.answer_callback_query(call.id, "Связь с Википедией...")
    page = wiki_wiki.page(f"{subject} (созвездие)")
    if not page.exists(): page = wiki_wiki.page(subject)
    if page.exists():
        bot.send_message(call.message.chat.id, f"📖 <b>{subject.upper()}</b>\n\n{page.summary[:1000]}...\n\n🔗 <a href='{page.fullurl}'>Читать далее</a>", parse_mode='HTML')
    else:
        bot.send_message(call.message.chat.id, "⚠️ Данные не найдены.")

if __name__ == "__main__":
    Thread(target=run_server).start()
    bot.infinity_polling(timeout=20)
