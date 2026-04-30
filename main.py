import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import os, time, concurrent.futures
from draw_map import generate_star_map
from flask import Flask
from threading import Thread
import wikipediaapi

# --- [КОСМИЧЕСКАЯ НАСТРОЙКА] ---
DATA_DIR = os.path.join(os.getcwd(), "data")
os.environ["STARPLOT_CACHE_DIR"] = DATA_DIR
os.environ["SOLAR_SYSTEM_EPHEMERIS"] = os.path.join(DATA_DIR, "de421.bsp")

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
bot = telebot.TeleBot(TELEGRAM_TOKEN, threaded=True)

# Википедия для расшифровки созвездий
wiki_wiki = wikipediaapi.Wikipedia(user_agent='MartySpaceBot/1.1', language='ru')

# Flask для поддержания жизни на Render
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
        "Я помогу тебе увидеть звезды, которые находятся прямо над тобой в эту секунду. "
        "Мои карты строятся на основе данных NASA и точных астрономических атласов.\n\n"
        "<b>Что ты получишь:</b>\n"
        "✅ Точное положение планет, Солнца и Луны.\n"
        "✅ Линии эклиптики и небесного экватора.\n"
        "✅ Объекты глубокого космоса (DSO).\n\n"
        "Жми <b>«📡 Мое небо»</b>, делись локацией, и начнем наше путешествие! 🚀"
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup, parse_mode='HTML')

@bot.message_handler(func=lambda message: message.text == "❓ Помощь и Инструкция")
def send_help(message):
    help_text = (
        "📖 <b>ГИД ПО ЗВЕЗДНОЙ КАРТЕ</b>\n\n"
        "1️⃣ <b>Ориентация:</b> На карте Восток (E) и Запад (W) поменяны местами. "
        "Это не ошибка! Звездную карту нужно держать <i>над головой</i>, а не смотреть на нее сверху вниз.\n\n"
        "2️⃣ <b>Линии на карте:</b>\n"
        "🔴 <b>Красный пунктир (Эклиптика)</b> — это видимый путь Солнца среди звезд в течение года. Вдоль этой линии можно найти планеты.\n"
        "🔵 <b>Синий пунктир (Небесный экватор)</b> — проекция земного экватора на небо. Он делит небо на северное и южное полушария.\n\n"
        "3️⃣ <b>Символы:</b>\n"
        "⚪️ <b>Маленькие кружочки</b> — это DSO (Deep Sky Objects). Сюда входят далекие галактики, туманности и звездные скопления.\n"
        "💫 <b>Размер звезд</b> на карте зависит от их яркости.\n\n"
        "Если карта кажется мелкой, используй кнопку <b>«Скачать оригинал»</b> под сообщением! 🔭"
    )
    bot.send_message(message.chat.id, help_text, parse_mode='HTML')

@bot.message_handler(content_types=['location'])
def handle_location(message):
    user_id = message.from_user.id
    old_file = f"sky_{user_id}.jpg"
    if os.path.exists(old_file):
        try: os.remove(old_file)
        except: pass

    try:
        loading_msg = bot.send_message(
            message.chat.id, 
            "📡 <b>Навожу телескопы...</b>\n\n"
            "<i>Рассчитываю положение планет, наношу сетку эклиптики и ищу объекты глубокого космоса специально для тебя!</i>", 
            parse_mode='HTML'
        )
        
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(
                generate_star_map, 
                message.location.latitude, 
                message.location.longitude, 
                message.from_user.first_name, 
                user_id
            )
            try:
                success, result, target_name, err_msg = future.result(timeout=110)
            except concurrent.futures.TimeoutError:
                bot.send_message(message.chat.id, "⏳ Космический таймаут! Попробуй повторить запрос.")
                return

        bot.delete_message(message.chat.id, loading_msg.message_id)

        if success:
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton(f"🌌 Досье на {target_name}", callback_data=f"wiki_{target_name}"))
            markup.add(InlineKeyboardButton("🖼️ Скачать оригинал (Full HD)", callback_data=f"orig_{user_id}"))
            
            caption = (
                f"✨ <b>Твое персональное небо готово!</b>\n\n"
                f"🎯 Твоя цель сегодня: созвездие <b>{target_name}</b> (отмечено розовым маркером).\n\n"
                "💡 <i>Совет: Найди на карте красную линию эклиптики — именно там сейчас «прогуливаются» планеты нашей системы.</i>"
            )
            
            with open(result, 'rb') as photo:
                bot.send_photo(
                    message.chat.id, photo, 
                    caption=caption, 
                    reply_markup=markup, parse_mode='HTML'
                )
        else:
            bot.send_message(message.chat.id, f"❌ Системный сбой: {result}")
            
    except Exception as e:
        bot.send_message(message.chat.id, f"🆘 Космические помехи: {str(e)}")

@bot.callback_query_handler(func=lambda call: call.data.startswith('orig_'))
def callback_original(call):
    user_id = call.data.replace('orig_', '')
    file_path = f"sky_{user_id}.jpg"
    
    if os.path.exists(file_path):
        bot.answer_callback_query(call.id, "Подключаюсь к архиву высокого качества...")
        with open(file_path, 'rb') as doc:
            bot.send_document(
                call.message.chat.id, 
                doc, 
                caption="📂 <b>Оригинал твоей карты.</b>\nБез сжатия Telegram, специально для детального изучения на большом экране! 💻",
                parse_mode='HTML'
            )
    else:
        bot.answer_callback_query(call.id, "⚠️ Карта устарела. Запроси локацию заново!", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data.startswith('wiki_'))
def callback_wiki(call):
    subject = call.data.replace('wiki_', '')
    bot.answer_callback_query(call.id, "Загружаю данные из Галактической Библиотеки...")
    
    # Пытаемся найти страницу именно как созвездие
    page = wiki_wiki.page(f"{subject.capitalize()} (созвездие)")
    if not page.exists(): page = wiki_wiki.page(subject.capitalize())
    
    if page.exists():
        summary = page.summary[:500] + "..."
        text = (
            f"🌌 <b>ОБЪЕКТ: {subject.upper()}</b>\n\n"
            f"{summary}\n\n"
            f"🔗 <a href='{page.fullurl}'>Читать полную историю</a>"
        )
        bot.send_message(call.message.chat.id, text, parse_mode='HTML', disable_web_page_preview=False)
    else:
        bot.send_message(call.message.chat.id, f"⚠️ Информации о созвездии «{subject}» в архивах нет.")

if __name__ == "__main__":
    # Запуск Flask в отдельном потоке
    Thread(target=run_server).start()
    
    # Запуск Telegram бота
    bot.remove_webhook()
    time.sleep(1)
    while True:
        try:
            print("📡 [СИСТЕМА] Марти слушает эфир...")
            bot.polling(non_stop=True, interval=2, timeout=90)
        except Exception as e:
            print(f"🔄 [РЕСТАРТ] Ошибка: {e}")
            time.sleep(5)
