import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telebot import apihelper
import os, time, concurrent.futures, random
from draw_map import generate_star_map
from flask import Flask
from threading import Thread
import wikipediaapi
from PIL import Image

# --- [ ИМПОРТ МОДУЛЕЙ ИГРОВОЙ ЛОГИКИ ] ---
from database import init_db, add_xp, get_user_stats, get_rank_name
from marty_chat import run_chat_bot 
from base_fact_star import CONSTELLATIONS
from vision_module import analyze_image 

# --- [ НАСТРОЙКИ СИСТЕМЫ ] ---
TOKEN = os.getenv('TELEGRAM_TOKEN')
LOG_CHAT_ID = "-1003756164148"

bot = telebot.TeleBot(TOKEN, threaded=True)

apihelper.CONNECT_TIMEOUT = 60
apihelper.READ_TIMEOUT = 90

# --- [ ЦЕНТР СВЯЗИ (ЛОГИ) ] ---
def send_log(text):
    try:
        bot.send_message(LOG_CHAT_ID, f"📡 <b>[БОРТОВОЙ ЖУРНАЛ]:</b> {text}", parse_mode='HTML')
    except Exception as e:
        print(f"Ошибка логирования: {e}")

# --- [ ПОДРОБНАЯ ИНСТРУКЦИЯ ] ---
def get_instruction_text():
    return (
        "📖 <b>ПОЛНОЕ РУКОВОДСТВО ПИЛОТА «МАРТИ»</b>\n"
        "───────────────────────\n\n"
        "Привет! Я — <b>Марти</b>, твой навигатор. Чтобы наше путешествие было продуктивным, изучи мои системы:\n\n"
        "🛰 <b>СЕКТОР «МОЕ НЕБО»</b>\n"
        "Отправь мне свою геолокацию. Я сверю координаты с картами звездного неба и покажу, какие созвездия сейчас смотрят на тебя. \n"
        "<i>Награда: +15 XP за каждое сканирование.</i>\n\n"
        "📸 <b>СЕКТОР «ГЛАЗА МАРТИ»</b>\n"
        "Пришли мне фото — будь то ночное небо, рисунок созвездия или просто что-то интересное. Я подключу свои нейро-архивы, проанализирую объект и выдам справку.\n"
        "<i>Награда: +10 XP за анализ.</i>\n\n"
        "🎖 <b>СИСТЕМА ДОПУСКОВ (РАНГИ)</b>\n"
        "XP — это твой опыт исследователя. Чем его больше, тем выше твой статус во флоте:\n"
        "• <b>Кадет:</b> Ты только учишься отличать Луну от прожектора.\n"
        "• <b>Исследователь:</b> Твои отчеты уже цитируют в штабе.\n"
        "• <b>Навигатор:</b> Ты видишь путь сквозь туманности.\n"
        "• <b>Адмирал:</b> Тебе подчиняются звезды! 👑\n\n"
        "🤖 <b>ОБЩЕНИЕ</b>\n"
        "Если тебе одиноко в глубоком космосе, жми «Спросить Марти» под любой картой — я всегда готов поболтать о вечном."
    )

# --- [ ПРИВЕТСТВИЕ ] ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("📡📡📡 МОЕ НЕБО", request_location=True))
    markup.add(KeyboardButton("❓❓ ИНСТРУКЦИЯ ПИЛОТА"))
    
    welcome_text = (
        f"🛰️ <b>Протокол приветствия активирован! Рад видеть тебя, пилот {message.from_user.first_name}!</b>\n\n"
        "Я — <b>Марти</b>. Мои сенсоры прогреты, а базы данных готовы к работе. 🐾\n\n"
        "Что предпримем? Можем просканировать твой текущий сектор неба или изучить снимки, которые ты сделал в пути. Выбирай кнопку внизу или просто пришли мне фото!"
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup, parse_mode='HTML')

# --- [ ОБРАБОТЧИК ФОТО (ГЛАЗА МАРТИ) ] ---
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    
    # Эффект живого общения
    responses = ["Так-так, открываю диафрагму...", "Секунду, сверяю картинку с архивами...", "Хм, интересный объект! Сейчас изучу..."]
    status_msg = bot.reply_to(message, f"📸 <b>{random.choice(responses)}</b>", parse_mode='HTML')
    
    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        # Передаем Марти на "изучение"
        description = analyze_image(downloaded_file)
        
        add_xp(user_id, 10, user_name)
        new_xp = get_user_stats(user_id)
        
        caption = (
            f"🔍 <b>ОТЧЕТ ПО СНИМКУ:</b>\n\n"
            f"{description}\n"
            f"─────────────────────\n"
            f"📈 <b>Данные внесены в журнал!</b>\n"
            f"Получено: <b>+10 XP</b> (Всего: {new_xp})"
        )
        
        bot.edit_message_text(caption, message.chat.id, status_msg.message_id, parse_mode='Markdown')
        
        # Секретные задания для вовлечения
        if random.random() < 0.3:
            missions = [
                "🚀 <b>ЭКСПЕДИЦИЯ:</b> Попробуй найти этот объект на реальном небе сегодня ночью!",
                "📡 <b>СВЯЗЬ:</b> Расскажи об этом факте другу, за это звезды будут тебе благосклонны.",
                "✍️ <b>АРХИВ:</b> Сделай зарисовку этого объекта в свой бумажный блокнот!"
            ]
            bot.send_message(message.chat.id, f"🌟 <b>ВНЕОЧЕРЕДНОЕ ЗАДАНИЕ:</b>\n{random.choice(missions)}", parse_mode='HTML')

    except Exception as e:
        send_log(f"🆘 Ошибка сенсоров (Vision): {e}")
        bot.edit_message_text("🛰️ <b>Помехи в сигнале!</b> Мои сенсоры не смогли распознать объект из-за космической пыли. Попробуй еще раз.", message.chat.id, status_msg.message_id, parse_mode='HTML')

# --- [ ИНСТРУКЦИЯ ] ---
@bot.message_handler(func=lambda message: message.text == "❓❓ ИНСТРУКЦИЯ ПИЛОТА")
def handle_instruction(message):
    bot.send_message(message.chat.id, get_instruction_text(), parse_mode='HTML')

# --- [ ГЕНЕРАЦИЯ КАРТЫ ] ---
@bot.message_handler(content_types=['location'])
def handle_location(message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    
    # Красивый статус подготовки
    prep_steps = ["Настраиваю связь со спутниками...", "Пробиваюсь сквозь атмосферные помехи...", "Запрашиваю данные у орбитальной группировки..."]
    status_msg = bot.send_message(message.chat.id, f"🛰️ <b>{random.choice(prep_steps)}</b>", parse_mode='HTML')
    
    try:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(generate_star_map, message.location.latitude, message.location.longitude, user_name, user_id)
            success, result, target_name, err_msg = future.result()

        if success:
            add_xp(user_id, 15, user_name)
            current_xp = get_user_stats(user_id)
            rank = get_rank_name(current_xp)

            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton(f"🌌 Изучить созвездие {target_name}", callback_data=f"wiki_{target_name}"))
            # ВОЗВРАЩЕНА КНОПКА FULL HD
            markup.add(InlineKeyboardButton("🖼️ Получить оригинал (Full HD)", callback_data=f"orig_{user_id}"))
            markup.add(InlineKeyboardButton("🤖 Спросить Марти", url="https://t.me/Marty_Help_Bot?start=help"))
            
            caption = (
                f"✨ <b>КАРТА СЕКТОРА ПОСТРОЕНА!</b>\n\n"
                f"Пилот <b>{user_name}</b>, прямо сейчас над тобой раскинулось небо во всей красе.\n"
                f"🎯 <b>Твоя главная цель для наблюдения:</b> созвездие <b>{target_name}</b>\n"
                f"─────────────────────\n"
                f"🎖 <b>Твой статус:</b> {rank}\n"
                f"📈 <b>Общий опыт:</b> {current_xp} XP (Начислено +15)"
            )
            
            with open(result, 'rb') as photo:
                bot.send_photo(message.chat.id, photo, caption=caption, reply_markup=markup, parse_mode='HTML')
            
            bot.delete_message(message.chat.id, status_msg.message_id)
            send_log(f"✅ Успешное сканирование неба: {user_name}.")
        else:
            bot.edit_message_text(f"❌ <b>Ошибка навигации:</b> {err_msg}. Мои системы говорят, что здесь слишком густые туманности.", message.chat.id, status_msg.message_id, parse_mode='HTML')
    except Exception as e:
        send_log(f"🆘 Критический сбой карты: {e}")
        bot.send_message(message.chat.id, "💥 <b>ОЙ-ОЙ!</b> Произошел системный сбой. Мой хвост подсказывает, что нужно попробовать еще раз через минуту.")

# --- [ ПОДРОБНОСТИ О СОЗВЕЗДИИ ] ---
@bot.callback_query_handler(func=lambda call: call.data.startswith('wiki_'))
def callback_wiki(call):
    subject = call.data.replace('wiki_', '').strip()
    bot.answer_callback_query(call.id, "Запрашиваю данные из архивов...")
    
    found_fact = next((item for item in CONSTELLATIONS if item['name_ru'].upper() == subject.upper()), None)
    if found_fact:
        text = (
            f"📖 <b>АРХИВНАЯ СПРАВКА: {found_fact['name_ru'].upper()}</b>\n"
            f"───────────────────────\n\n"
            f"{found_fact['fact']}\n\n"
            f"<i>Интересно, правда? Продолжай исследования!</i>"
        )
        bot.send_message(call.message.chat.id, text, parse_mode='HTML')

# --- [ SERVER & LAUNCH ] ---
app = Flask(__name__)
@app.route('/')
def home(): return "Бортовой компьютер Марти в штатном режиме."

def run_server():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

if __name__ == "__main__":
    init_db()
    send_log("🚀 <b>Марти готов к вылету. Системы в норме!</b>")
    
    Thread(target=run_server).start()
    
    bot.remove_webhook()
    bot.polling(non_stop=True, interval=1)
