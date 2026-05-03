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

# --- [ НАСТРОЙКИ СИСТЕМЫ ] ---
TOKEN = os.getenv('TELEGRAM_TOKEN')
LOG_CHAT_ID = "-1003756164148"

bot = telebot.TeleBot(TOKEN, threaded=True)

# Увеличиваем таймауты для работы с нейросетевыми изображениями
apihelper.CONNECT_TIMEOUT = 60
apihelper.READ_TIMEOUT = 90

# --- [ ЛОГИРОВАНИЕ ] ---
def send_log(text):
    try:
        bot.send_message(LOG_CHAT_ID, f"📡 <b>[LOG]:</b> {text}", parse_mode='HTML')
    except Exception as e:
        print(f"Ошибка логирования: {e}")

# --- [ СИСТЕМА РАНГОВ И ИНСТРУКЦИЯ ] ---
def get_instruction_text():
    return (
        "📖 <b>БОРТОВОЙ ЖУРНАЛ ПИЛОТА</b>\n\n"
        "Добро пожаловать в программу «Звездный Патруль». Твоя задача — исследовать ночное небо и пополнять базу знаний.\n\n"
        "🚀 <b>Как это работает:</b>\n"
        "1. Нажми <b>«МОЕ НЕБО»</b> и поделись геолокацией.\n"
        "2. Бот вычислит звезды, которые находятся прямо над тобой в этот момент.\n"
        "3. Ты получишь <b>персональную карту</b> с выделенным созвездием-целью.\n\n"
        "🎖 <b>СИСТЕМА РАНГОВ И ОПЫТА (XP):</b>\n"
        "За каждое сканирование неба тебе начисляется <b>15 XP</b>. Опыт нужен для продвижения по службе:\n"
        "• <b>Кадет:</b> Новичок, только начавший путь.\n"
        "• <b>Исследователь:</b> Ты уже знаешь, где Полярная звезда.\n"
        "• <b>Навигатор:</b> Способен провести корабль сквозь астероидное поле.\n"
        "• <b>Командор:</b> Легенда флота, знающая каждый квадрант.\n\n"
        "<i>Чем выше ранг, тем больше секретных функций откроется в будущем!</i>"
    )

# --- [ ПРИВЕТСТВИЕ ] ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("📡📡📡 МОЕ НЕБО", request_location=True))
    markup.add(KeyboardButton("❓❓ ИНСТРУКЦИЯ ПИЛОТА"))
    
    welcome_text = (
        f"🛰️ <b>Центр управления на связи, пилот {message.from_user.first_name}!</b>\n\n"
        "Я — <b>Марти</b>, твой ИИ-штурман. 🐾\n"
        "Готов просканировать твой сектор пространства?"
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup, parse_mode='HTML')

# --- [ ОБРАБОТЧИК ТЕКСТОВЫХ КНОПОК ] ---
@bot.message_handler(func=lambda message: message.text == "❓❓ ИНСТРУКЦИЯ ПИЛОТА")
def handle_instruction(message):
    """Теперь эта функция отвечает на нажатие кнопки инструкции"""
    bot.send_message(message.chat.id, get_instruction_text(), parse_mode='HTML')

# --- [ ГЕНЕРАЦИЯ КАРТЫ (LOCATION) ] ---
@bot.message_handler(content_types=['location'])
def handle_location(message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    
    status_msg = bot.send_message(message.chat.id, "🛰️ <b>Начинаю сканирование горизонта...</b>", parse_mode='HTML')
    
    try:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(
                generate_star_map, 
                message.location.latitude, 
                message.location.longitude, 
                user_name, 
                user_id
            )
            success, result, target_name, err_msg = future.result()

        if success:
            # Начисляем опыт (логика внутри database.py)
            add_xp(user_id, 15, user_name)
            current_xp = get_user_stats(user_id)
            rank = get_rank_name(current_xp)

            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton(f"🌌 Досье на {target_name}", callback_data=f"wiki_{target_name}"))
            markup.add(InlineKeyboardButton("🤖 Спросить Марти", url="https://t.me/Marty_Help_Bot?start=help"))
            
            caption = (
                f"✨ <b>Сектор просканирован успешно!</b>\n\n"
                f"🎯 <b>Объект интереса:</b> созвездие <b>{target_name}</b>\n"
                f"─────────────────────\n"
                f"🎖 <b>Твой текущий ранг:</b> {rank}\n"
                f"📈 <b>Прогресс:</b> {current_xp} XP (добавлено +15)"
            )
            
            with open(result, 'rb') as photo:
                bot.send_photo(message.chat.id, photo, caption=caption, reply_markup=markup, parse_mode='HTML')
            
            bot.delete_message(message.chat.id, status_msg.message_id)
            send_log(f"✅ Карта создана для {user_name}. Ранг: {rank}")
        else:
            bot.edit_message_text(f"❌ Ошибка навигации: {err_msg}", message.chat.id, status_msg.message_id)
            
    except Exception as e:
        send_log(f"🆘 Ошибка: {e}")
        bot.send_message(message.chat.id, "💥 Произошел сбой систем. Попробуй позже.")

# --- [ WIKI И ДРУГИЕ CALLBACKS ] ---
@bot.callback_query_handler(func=lambda call: call.data.startswith('wiki_'))
def callback_wiki(call):
    subject = call.data.replace('wiki_', '').strip()
    bot.answer_callback_query(call.id, "Загружаю данные из архивов...")
    
    found_fact = next((item for item in CONSTELLATIONS if item['name_ru'].upper() == subject.upper()), None)
    if found_fact:
        text = f"🌌 <b>{found_fact['name_ru'].upper()}</b>\n\n{found_fact['fact']}"
        bot.send_message(call.message.chat.id, text, parse_mode='HTML')

# --- [ SERVER & LAUNCH ] ---
app = Flask(__name__)
@app.route('/')
def home(): return "Online"

def run_server():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

if __name__ == "__main__":
    init_db()
    send_log("🚀 <b>Марти-Бот запущен. Все системы в норме.</b>")
    
    Thread(target=run_server).start()
    Thread(target=run_chat_bot).start() # Второй бот-собеседник
    
    bot.remove_webhook()
    bot.polling(non_stop=True, interval=2)
