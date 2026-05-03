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
from vision_module import analyze_image  # НОВЫЙ МОДУЛЬ ЗРЕНИЯ

# --- [ НАСТРОЙКИ СИСТЕМЫ ] ---
TOKEN = os.getenv('TELEGRAM_TOKEN')
LOG_CHAT_ID = "-1003756164148"

bot = telebot.TeleBot(TOKEN, threaded=True)

apihelper.CONNECT_TIMEOUT = 60
apihelper.READ_TIMEOUT = 90

# --- [ ЛОГИРОВАНИЕ ] ---
def send_log(text):
    try:
        bot.send_message(LOG_CHAT_ID, f"📡 <b>[LOG]:</b> {text}", parse_mode='HTML')
    except Exception as e:
        print(f"Ошибка логирования: {e}")

# --- [ ИНСТРУКЦИЯ (ОБНОВЛЕНА) ] ---
def get_instruction_text():
    return (
        "📖 <b>БОРТОВОЙ ЖУРНАЛ ПИЛОТА</b>\n\n"
        "🚀 <b>Твои возможности:</b>\n"
        "1. <b>«МОЕ НЕБО»</b> — получи карту звезд прямо над тобой (+15 XP).\n"
        "2. <b>«ГЛАЗА МАРТИ»</b> — просто пришли мне фото любого предмета, созвездия или рисунка. Я проанализирую его и дам справку (+10 XP).\n"
        "3. <b>«ОБЩЕНИЕ»</b> — нажми кнопку «Спросить Марти», чтобы поболтать со мной.\n\n"
        "🎖 <b>ТВОЙ РАНГ:</b>\n"
        "Чем больше XP, тем выше звание. Стань Адмиралом Галактики! 👑"
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
        "Готов просканировать твой сектор пространства или изучить твои снимки?"
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup, parse_mode='HTML')

# --- [ ОБРАБОТЧИК ФОТО (ГЛАЗА МАРТИ) ] ---
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    
    status_msg = bot.reply_to(message, "📸 <b>Настраиваю фокус... Изучаю объект...</b>", parse_mode='HTML')
    
    try:
        # Скачиваем фото
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        # Анализируем через Gemini
        description = analyze_image(downloaded_file)
        
        # Начисляем XP
        add_xp(user_id, 10, user_name)
        new_xp = get_user_stats(user_id)
        
        caption = f"{description}\n\n─────────────────────\n📈 <b>+10 XP</b> (Всего: {new_xp})"
        
        bot.edit_message_text(caption, message.chat.id, status_msg.message_id, parse_mode='Markdown')
        send_log(f"📸 Анализ фото для {user_name}. Всего XP: {new_xp}")
        
        # Диверсификация: шанс 30% получить задание
        if random.random() < 0.3:
            missions = [
                "🚀 Задание: Нарисуй это созвездие и пришли мне!",
                "📡 Задание: Найди этот объект в энциклопедии.",
                "👨‍🚀 Задание: Расскажи маме или папе один факт о космосе!"
            ]
            bot.send_message(message.chat.id, f"🌟 <b>СЕКРЕТНОЕ ЗАДАНИЕ:</b>\n{random.choice(missions)}", parse_mode='HTML')

    except Exception as e:
        send_log(f"🆘 Ошибка Vision: {e}")
        bot.edit_message_text("🛰️ Космические помехи прервали сигнал.", message.chat.id, status_msg.message_id)

# --- [ ОБРАБОТЧИК ТЕКСТОВЫХ КНОПОК ] ---
@bot.message_handler(func=lambda message: message.text == "❓❓ ИНСТРУКЦИЯ ПИЛОТА")
def handle_instruction(message):
    bot.send_message(message.chat.id, get_instruction_text(), parse_mode='HTML')

# --- [ ГЕНЕРАЦИЯ КАРТЫ ] ---
@bot.message_handler(content_types=['location'])
def handle_location(message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    status_msg = bot.send_message(message.chat.id, "🛰️ <b>Сканирую горизонт...</b>", parse_mode='HTML')
    
    try:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(generate_star_map, message.location.latitude, message.location.longitude, user_name, user_id)
            success, result, target_name, err_msg = future.result()

        if success:
            add_xp(user_id, 15, user_name)
            current_xp = get_user_stats(user_id)
            rank = get_rank_name(current_xp)

            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton(f"🌌 Досье на {target_name}", callback_data=f"wiki_{target_name}"))
            markup.add(InlineKeyboardButton("🤖 Спросить эксперта Марти", url="https://t.me/Marty_Help_Bot?start=help"))
            
            caption = (
                f"✨ <b>Твоя персональная карта готова, {user_name}!</b>\n\n"
                f"🎯 <b>Твоя главная цель:</b> созвездие <b>{target_name}</b>\n"
                f"─────────────────────\n"
                f"🎖 <b>Твой ранг:</b> {rank}\n"
                f"📈 <b>Опыт:</b> {current_xp} XP"
            )
            
            with open(result, 'rb') as photo:
                bot.send_photo(message.chat.id, photo, caption=caption, reply_markup=markup, parse_mode='HTML')
            
            bot.delete_message(message.chat.id, status_msg.message_id)
            send_log(f"✅ Карта создана для {user_name}. XP: {current_xp}")
        else:
            bot.edit_message_text(f"❌ Ошибка навигации: {err_msg}", message.chat.id, status_msg.message_id)
    except Exception as e:
        send_log(f"🆘 Ошибка карты: {e}")
        bot.send_message(message.chat.id, "💥 Сбой систем навигации.")

@bot.callback_query_handler(func=lambda call: call.data.startswith('wiki_'))
def callback_wiki(call):
    subject = call.data.replace('wiki_', '').strip()
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
    send_log("🚀 <b>Система управления Марти запущена.</b>")
    
    Thread(target=run_server).start()
    # Thread(target=run_chat_bot).start() # Если этот бот использует тот же токен, возникнет 409 Conflict.
    
    bot.remove_webhook()
    bot.polling(non_stop=True, interval=1)
