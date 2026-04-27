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

# Инициализация Википедии (русский язык)
wiki_wiki = wikipediaapi.Wikipedia(
    user_agent='MartyAstrobot/1.0 (https://t.me/vladislav_space)',
    language='ru'
)

# Текст инструкции для штурманов
INSTRUCTIONS_TEXT = (
    "📖 <b>ИНСТРУКЦИЯ ПО НАВИГАЦИИ</b> 🚀\n\n"
    "<b>Как читать карту:</b>\n"
    "🧭 <b>Внешнее кольцо:</b> Твой горизонт. С — Север, Ю — Юг, В — Восток, З — Запад.\n"
    "🎯 <b>[ЦЕЛЬ]:</b> Созвездие, выделенное розовым. Это твой главный объект для поиска.\n"
    "🌕 <b>ЛУНА:</b> Белый круг. Самый яркий ориентир в ночном небе.\n"
    "☀️ <b>СОЛНЦЕ:</b> Оранжевый круг (виден, если солнце еще не ушло глубоко за горизонт).\n"
    "🪐 <b>ПЛАНЕТЫ:</b> Подписаны и отмечены цветными точками (Марс, Юпитер и др.).\n"
    "✨ <b>ЛИНИИ:</b> Золотистые контуры созвездий.\n\n"
    "<i>Совет: Повернись лицом в сторону нужной буквы (например, Ю — Юг) и подними телефон к небу. Объекты на экране совпадут с реальностью!</i>"
)

# === ВЕБ-СЕРВЕР (МАЯК ДЛЯ RENDER) ===
app = Flask(__name__)

@app.route('/')
def keep_alive():
    return "Марти на связи! Модули навигации и энциклопедии активны. 🚀"

def run_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# === ОБРАБОТКА КОМАНД ===
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("📡 Мое небо", request_location=True))
    markup.add(KeyboardButton("📖 Инструкция"))
    
    welcome_msg = (
        "🛰 <b>Бортовой компьютер приветствует тебя, Штурман!</b>\n\n"
        "Системы синхронизированы. Жми «Мое небо», чтобы получить карту своего сектора, "
        "или загляни в «Инструкцию», если нужно откалибровать зрение."
    )
    bot.send_message(message.chat.id, welcome_msg, reply_markup=markup, parse_mode='HTML')

@bot.message_handler(func=lambda m: m.text == "📖 Инструкция")
def show_help(message):
    bot.send_message(message.chat.id, INSTRUCTIONS_TEXT, parse_mode='HTML')

@bot.message_handler(content_types=['location'])
def handle_location(message):
    chat_id = message.chat.id
    loading_msg = bot.send_message(chat_id, "🔭 <i>Синхронизация с орбитальными телескопами...</i>", parse_mode='HTML')

    # Генерация карты
    success, result, target_name, target_fact = generate_star_map(
        message.location.latitude, 
        message.location.longitude, 
        message.from_user.first_name
    )

    bot.delete_message(chat_id, loading_msg.message_id)

    if success:
        markup = InlineKeyboardMarkup()
        # Кнопка «База данных» теперь ведет в Википедию
        markup.add(InlineKeyboardButton(f"📚 База данных: {target_name}", callback_data=f"wiki_{target_name}"))

        with open(result, 'rb') as photo:
            bot.send_photo(
                chat_id, 
                photo, 
                caption=f"✨ Сектор просканирован!\n🎯 Твоя цель сегодня: <b>{target_name}</b>",
                reply_markup=markup,
                parse_mode='HTML'
            )
        os.remove(result)
    else:
        bot.send_message(chat_id, f"❌ Ошибка связи: {result}")

@bot.callback_query_handler(func=lambda call: call.data.startswith('wiki_'))
def callback_wiki(call):
    subject = call.data.replace('wiki_', '')
    bot.answer_callback_query(call.id, "Запрашиваю архивы Википедии...")
    
    page = wiki_wiki.page(subject)
    if page.exists():
        # Берем первые 1200 символов описания
        summary = page.summary[:1200] + "..."
        response = (
            f"📖 <b>{subject.upper()}</b>\n\n"
            f"{summary}\n\n"
            f"🔗 <a href='{page.fullurl}'>Читать полную статью в Википедии</a>"
        )
    else:
        response = "⚠️ В открытых архивах данные об этом объекте отсутствуют."

    bot.send_message(call.message.chat.id, response, parse_mode='HTML')

if __name__ == "__main__":
    # Запуск маяка
    Thread(target=run_server).start()
    print("🚀 Маяк в эфире!")
    
    # Запуск бота
    print("🚀 Марти Астроном запущен!")
    bot.infinity_polling(timeout=20, long_polling_timeout=10)
