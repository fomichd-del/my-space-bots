import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import os, time, concurrent.futures
from draw_map import generate_star_map
from flask import Flask
from threading import Thread
import wikipediaapi

# --- [ ИМПОРТ БАЗЫ КОСМИЧЕСКОГО ПАТРУЛЯ ] ---
from base_fact_star import CONSTELLATIONS

# --- [ КОСМИЧЕСКИЕ НАСТРОЙКИ ] ---
DATA_DIR = os.path.join(os.getcwd(), "data")
os.environ["STARPLOT_CACHE_DIR"] = DATA_DIR
os.environ["SOLAR_SYSTEM_EPHEMERIS"] = os.path.join(DATA_DIR, "de421.bsp")

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
bot = telebot.TeleBot(TELEGRAM_TOKEN, threaded=True)

# Википедия для глубокого погружения (как запасной вариант)
wiki_wiki = wikipediaapi.Wikipedia(user_agent='MartySpaceBot/1.1', language='ru')

# Flask для поддержания "жизни" сервера на Render
app = Flask(__name__)
@app.route('/')
def keep_alive(): return "Марти Астроном в эфире! 🛰️"
def run_server(): app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

# --- [ ПРИВЕТСТВИЕ: ЧТО, КТО И ЗАЧЕМ ] ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("📡 Мое небо", request_location=True))
    markup.add(KeyboardButton("❓ Как это работает?"))
    
    welcome_text = (
        f"Привет, {message.from_user.first_name}! 🐾 Я — <b>Марти Астроном</b> 🎓\n\n"
        "Я умею превращать твои координаты в <b>точную карту звездного неба</b>. "
        "В отличие от обычных картинок, я считаю положение планет и звезд именно для твоей точки на планете.\n\n"
        "<b>С чего начнем?</b>\n"
        "📍 Нажми <b>«📡 Мое небо»</b>, чтобы отправить геолокацию. Я сразу начну расчеты.\n"
        "📖 Или загляни в <b>«Помощь»</b>, если хочешь научиться читать мои карты."
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup, parse_mode='HTML')

# --- [ ИНСТРУКЦИЯ: ПОНЯТНО И ПОДРОБНО ] ---
@bot.message_handler(func=lambda message: message.text == "❓ Как это работает?")
def send_help(message):
    help_text = (
        "🧭 <b>ГИД ПО ТВОЕМУ ЛИЧНОМУ КОСМОСУ</b>\n\n"
        "<b>1. Что на карте?</b>\n"
        "Центр круга — это небо прямо над твоей головой. Я рисую Млечный Путь, границы созвездий и даже далекие галактики (DSO).\n\n"
        "<b>2. Линии и символы:</b>\n"
        "🔴 <b>Красная линия</b> — это путь Солнца и планет. Если хочешь увидеть Сатурн, ищи его здесь!\n"
        "☀️/🌙 — я отметил Солнце и Луну специальными значками, чтобы ты их сразу узнал.\n\n"
        "<b>3. Зачем нужна кнопка «Оригинал»?</b>\n"
        "Telegram сжимает фото. Если хочешь рассмотреть каждую звездочку в Full HD или поставить карту на обои — скачивай файл без сжатия."
    )
    bot.send_message(message.chat.id, help_text, parse_mode='HTML')

# --- [ ЛОГИКА ОЖИДАНИЯ: РАЗВЛЕКАЕМ ПОЛЬЗОВАТЕЛЯ ] ---
@bot.message_handler(content_types=['location'])
def handle_location(message):
    user_id = message.from_user.id
    try:
        # Статусы, объясняющие, что делает Марти прямо сейчас
        statuses = [
            "🛰 <b>Локация принята!</b> Связываюсь с серверами эфемерид...",
            "🔭 <b>Навожу линзы...</b> Ищу созвездие, которое станет твоей целью.",
            "📐 <b>Считаю время...</b> Настраиваю восход и закат под твой часовой пояс.",
            "🌌 <b>Рисую полотно...</b> Добавляю линии эклиптики и небесного экватора.",
            "🎨 <b>Финальные штрихи...</b> Ретуширую Млечный Путь.",
            "📸 <b>Проявляю снимок...</b> Еще минутку, космонавт! Проявление займет до 60 секунд, если карты нет, нажмите еще раз кнопку!"
        ]

        loading_msg = bot.send_message(message.chat.id, statuses[0], parse_mode='HTML')
        
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(
                generate_star_map, 
                message.location.latitude, 
                message.location.longitude, 
                message.from_user.first_name, 
                user_id
            )
            
            # Цикл смены статусов, пока работает draw_map.py
            status_index = 1
            while not future.done():
                time.sleep(11)
                if status_index < len(statuses):
                    try:
                        bot.edit_message_text(
                            chat_id=message.chat.id,
                            message_id=loading_msg.message_id,
                            text=statuses[status_index],
                            parse_mode='HTML'
                        )
                        status_index += 1
                    except: pass
            
            success, result, target_name, err_msg = future.result()

        bot.delete_message(message.chat.id, loading_msg.message_id)

        if success:
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton(f"🌌 Досье на {target_name}", callback_data=f"wiki_{target_name}"))
            markup.add(InlineKeyboardButton("🖼️ Скачать оригинал (Full HD)", callback_data=f"orig_{user_id}"))
            
            caption = (
                f"✨ <b>Твоя карта готова!</b>\n\n"
                f"🎯 <b>Твоя цель:</b> созвездие {target_name}.\n"
                f"Я отметил его розовым маркером. Попробуй найти его сегодня на небе!\n\n"
                "<i>Внизу карты я указал точное время восхода и заката для тебя. Удачной охоты за звездами!</i>"
            )
            
            with open(result, 'rb') as photo:
                bot.send_photo(
                    message.chat.id, photo, 
                    caption=caption, 
                    reply_markup=markup, parse_mode='HTML'
                )
        else:
            bot.send_message(message.chat.id, f"❌ <b>Ой! Сбой связи:</b> {result}")
            
    except Exception as e:
        bot.send_message(message.chat.id, f"🆘 <b>Космическое происшествие:</b> {str(e)}")

# --- [ ОБРАБОТЧИКИ КНОПОК ] ---
@bot.callback_query_handler(func=lambda call: call.data.startswith('orig_'))
def callback_original(call):
    user_id = call.data.replace('orig_', '')
    file_path = f"sky_{user_id}.jpg"
    
    if os.path.exists(file_path):
        bot.answer_callback_query(call.id, "Загружаю Full HD файл...")
        with open(file_path, 'rb') as doc:
            bot.send_document(
                call.message.chat.id, doc, 
                caption="📂 <b>Твой личный атлас.</b>\nИспользуй этот файл, если хочешь распечатать карту или рассмотреть детали.",
                parse_mode='HTML'
            )
    else:
        bot.answer_callback_query(call.id, "⚠️ Данные устарели. Запроси карту снова!", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data.startswith('wiki_'))
def callback_wiki(call):
    # Получаем имя цели (оно приходит капсом из draw_map.py, например "ОРИОН")
    subject = call.data.replace('wiki_', '').strip()
    bot.answer_callback_query(call.id, "Открываю архивы Патруля...")
    
    # 1. Сначала ищем в нашей авторской базе CONSTELLATIONS
    found_fact = None
    for item in CONSTELLATIONS:
        # Сравниваем в верхнем регистре, чтобы избежать ошибок с большими/маленькими буквами
        if item['name_ru'].upper() == subject.upper():
            found_fact = item
            break
            
    if found_fact:
        # Если нашли — формируем красивое сообщение с эмодзи
        text = (
            f"🌌 <b>{found_fact['name_ru'].upper()} ({found_fact['name_latin']})</b>\n\n"
            f"{found_fact['fact']}"
        )
        bot.send_message(call.message.chat.id, text, parse_mode='HTML')
    else:
        # 2. Если в нашей базе созвездия нет — используем Википедию как запасной вариант
        try:
            page = wiki_wiki.page(f"{subject.capitalize()} (созвездие)")
            if not page.exists(): 
                page = wiki_wiki.page(subject.capitalize())
            
            if page.exists():
                summary = page.summary[:500] + "..."
                text = (
                    f"🌌 <b>ИЗУЧАЕМ: {subject.upper()}</b>\n\n"
                    f"{summary}\n\n"
                    f"🔗 <a href='{page.fullurl}'>Читать полную историю</a>"
                )
                bot.send_message(call.message.chat.id, text, parse_mode='HTML', disable_web_page_preview=False)
            else:
                bot.send_message(call.message.chat.id, "⚠️ К сожалению, подробностей об этом объекте пока нет.")
        except Exception as e:
            bot.send_message(call.message.chat.id, "📡 Ошибка связи с глубоким космосом.")

if __name__ == "__main__":
    Thread(target=run_server).start()
    bot.remove_webhook()
    while True:
        try:
            print("📡 [СИСТЕМА] Марти слушает эфир...")
            bot.polling(non_stop=True, interval=2)
        except Exception as e:
            print(f"🔄 Рестарт из-за ошибки: {e}")
            time.sleep(5)
