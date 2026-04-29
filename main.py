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
        "Моя главная задача — показать тебе точную копию звездного неба, которое находится прямо сейчас над твоей головой. "
        "Я умею рассчитывать орбиты планет, фазы Луны и время захода Солнца.\n\n"
        "Жми <b>«📡 Мое небо»</b>, делись локацией, и я соберу для тебя персональную звездную карту! 🚀"
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup, parse_mode='HTML')

@bot.message_handler(func=lambda message: message.text == "❓ Помощь и Инструкция")
def send_help(message):
    help_text = (
        "🧭 <b>КАК ЧИТАТЬ ЗВЕЗДНУЮ КАРТУ?</b>\n\n"
        "🔹 <b>Почему Восток (E) слева, а Запад (W) справа?</b>\n"
        "Это не ошибка! Обычную карту мы кладем на землю и смотрим <i>сверху вниз</i>. Звездную карту мы поднимаем над головой и смотрим <i>снизу вверх</i>. Встань лицом на Юг (S), подними телефон, и восток окажется точно по левую руку!\n\n"
        "🔹 <b>Центр карты</b> — это Зенит (точка прямо над твоей макушкой).\n"
        "🔹 <b>Края круга</b> — это линия горизонта вокруг тебя.\n"
        "🔹 <b>[🎯 ЦЕЛЬ]</b> — при каждом сканировании я выбираю случайное созвездие и выделяю его на карте. Нажми кнопку под картой, чтобы узнать о нем секретные данные из архивов!\n\n"
        "Попробуй прямо сейчас: жми «📡 Мое небо»!"
    )
    bot.send_message(message.chat.id, help_text, parse_mode='HTML')

@bot.message_handler(content_types=['location'])
def handle_location(message):
    try:
        loading_msg = bot.send_message(
            message.chat.id, 
            "📡 <b>Координаты получены!</b> Навожу линзы телескопов...\n\n"
            "<i>⏳ Построение точной карты и расчет орбит планет занимает 30-40 секунд. Если я не отвечаю дольше минуты — просто нажми кнопку еще раз.</i>", 
            parse_mode='HTML'
        )
        
        success, result, target_name, err_msg = generate_star_map(
            message.location.latitude, 
            message.location.longitude, 
            message.from_user.first_name
        )
        
        bot.delete_message(message.chat.id, loading_msg.message_id)

        if success:
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton(f"🌌 Рассекретить архивы: {target_name}", callback_data=f"wiki_{target_name}"))
            
            with open(result, 'rb') as photo:
                bot.send_photo(
                    message.chat.id, 
                    photo, 
                    caption=f"✨ Твоя персональная проекция орбиты!\n🎯 Миссия на сегодня: найти созвездие <b>{target_name}</b>", 
                    reply_markup=markup, 
                    parse_mode='HTML',
                    timeout=120
                )
            if os.path.exists(result): os.remove(result)
        else:
            bot.send_message(message.chat.id, f"❌ Ошибка калибровки линз: {result}")
    except Exception as e:
        bot.send_message(message.chat.id, f"🆘 Космические помехи: {str(e)}")

@bot.callback_query_handler(func=lambda call: call.data.startswith('wiki_'))
def callback_wiki(call):
    subject = call.data.replace('wiki_', '')
    bot.answer_callback_query(call.id, "Загружаю данные из Галактической Библиотеки...")
    
    search_term = subject.capitalize()
    page = wiki_wiki.page(f"{search_term} (созвездие)")
    if not page.exists():
        page = wiki_wiki.page(search_term)
    
    if page.exists():
        summary = page.summary
        short_desc = summary[:300] + "..." if len(summary) > 300 else summary
        history_desc = summary[300:900] + "..." if len(summary) > 300 else ""
        
        wiki_text = (
            f"🌌 <b>ДОСЬЕ: {search_term.upper()}</b>\n\n"
            f"📖 <b>Что это такое:</b>\n{short_desc}\n\n"
        )
        if history_desc:
            wiki_text += f"📜 <b>Научные факты и мифология:</b>\n{history_desc}\n\n"
            
        wiki_text += f"🔗 <a href='{page.fullurl}'>[ Открыть полный архив ]</a>"
        
        bot.send_message(call.message.chat.id, wiki_text, parse_mode='HTML')
    else:
        bot.send_message(call.message.chat.id, f"⚠️ Данные о «{search_term}» засекречены или отсутствуют.")

if __name__ == "__main__":
    Thread(target=run_server).start()
    bot.remove_webhook()
    time.sleep(2)
    bot.infinity_polling(timeout=90, skip_pending=True)
