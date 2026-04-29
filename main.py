import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import os, time, concurrent.futures, gc
from draw_map import generate_star_map
from flask import Flask
from threading import Thread
import wikipediaapi

# --- ИНИЦИАЛИЗАЦИЯ ---
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
bot = telebot.TeleBot(TELEGRAM_TOKEN, threaded=True)

wiki_wiki = wikipediaapi.Wikipedia(user_agent='MartySpaceBot/1.1', language='ru')

app = Flask(__name__)
@app.route('/')
def keep_alive(): return "Марти Астроном в эфире! 🛰️"
def run_server(): app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

# --- КОМАНДА START (ТВОЙ КРАСИВЫЙ ТЕКСТ) ---
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

# --- ИНСТРУКЦИЯ (ТВОЙ КРАСИВЫЙ ТЕКСТ) ---
@bot.message_handler(func=lambda message: message.text == "❓ Помощь и Инструкция")
def send_help(message):
    help_text = (
        "🧭 <b>КАК ЧИТАТЬ ЗВЕЗДНУЮ КАРТУ?</b>\n\n"
        "🔹 <b>Почему Восток (E) слева, а Запад (W) справа?</b>\n"
        "Это не ошибка! Обычную карту мы кладем на землю и смотрим <i>сверху вниз</i>. Звездную карту мы поднимаем над головой и смотрим <i>снизу вверх</i>.\n\n"
        "🔹 <b>Центр карты</b> — это Зенит (точка прямо над твоей макушкой).\n"
        "🔹 <b>[🎯 ЦЕЛЬ]</b> — я выбираю случайное созвездие и выделяю его. Нажми кнопку под картой, чтобы узнать о нем из архивов!\n\n"
        "Жми «📡 Мое небо»!"
    )
    bot.send_message(message.chat.id, help_text, parse_mode='HTML')

# --- ГЕНЕРАЦИЯ КАРТЫ С АВТО-ТАЙМАУТОМ ---
@bot.message_handler(content_types=['location'])
def handle_location(message):
    loading_msg = None
    try:
        loading_msg = bot.send_message(
            message.chat.id, 
            "📡 <b>Координаты получены!</b> Навожу линзы телескопов...\n\n"
            "<i>⏳ Это займет 30-40 секунд. Если я молчу дольше минуты — нажми кнопку еще раз.</i>", 
            parse_mode='HTML'
        )
        
        # Запускаем тяжелую задачу в отдельном потоке
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(
                generate_star_map, 
                message.location.latitude, 
                message.location.longitude, 
                message.from_user.first_name,
                message.from_user.id
            )
            try:
                # Если за 70 секунд не нарисовал — бросаем это дело
                success, result, target_name, err_msg = future.result(timeout=70)
            except concurrent.futures.TimeoutError:
                bot.send_message(message.chat.id, "⏳ <b>Космический таймаут!</b> Карта строится слишком долго. Попробуй еще раз.")
                return

        if success:
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton(f"🌌 Рассекретить архивы: {target_name}", callback_data=f"wiki_{target_name}"))
            
            with open(result, 'rb') as photo:
                bot.send_photo(
                    message.chat.id, photo, 
                    caption=f"✨ Твоя персональная проекция орбиты!\n🎯 Миссия: найти созвездие <b>{target_name}</b>", 
                    reply_markup=markup, parse_mode='HTML', timeout=120
                )
            if os.path.exists(result): os.remove(result)
        else:
            bot.send_message(message.chat.id, f"❌ Ошибка линз: {result}")

    except Exception as e:
        bot.send_message(message.chat.id, f"🆘 Космические помехи: {str(e)}")
    finally:
        if loading_msg:
            try: bot.delete_message(message.chat.id, loading_msg.message_id)
            except: pass
        gc.collect()

# --- ВИКИПЕДИЯ ---
@bot.callback_query_handler(func=lambda call: call.data.startswith('wiki_'))
def callback_wiki(call):
    subject = call.data.replace('wiki_', '')
    bot.answer_callback_query(call.id, "Загружаю данные...")
    search_term = subject.capitalize()
    page = wiki_wiki.page(f"{search_term} (созвездие)")
    if not page.exists(): page = wiki_wiki.page(search_term)
    
    if page.exists():
        summary = page.summary
        wiki_text = f"🌌 <b>ДОСЬЕ: {search_term.upper()}</b>\n\n{summary[:600]}...\n\n🔗 <a href='{page.fullurl}'>[ Открыть архив ]</a>"
        bot.send_message(call.message.chat.id, wiki_text, parse_mode='HTML')
    else:
        bot.send_message(call.message.chat.id, f"⚠️ Данные о «{search_term}» отсутствуют.")

# --- СИСТЕМА НЕПРЕРЫВНОГО ВЕЩАНИЯ ---
if __name__ == "__main__":
    Thread(target=run_server).start()
    
    print("🛰 [СИСТЕМА] Марти Астроном выходит на орбиту...")
    
    while True:
        try:
            bot.remove_webhook()
            print("📡 [СИСТЕМА] Слушаю эфир...")
            # non_stop=True заставляет его пытаться переподключиться при сбоях
            bot.polling(non_stop=True, interval=0, timeout=60)
        except Exception as e:
            print(f"💥 [ОШИБКА] Сбой связи, перезапуск через 5 сек: {e}")
            time.sleep(5)
