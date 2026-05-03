import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telebot import apihelper
import os, time, concurrent.futures, random
from pathlib import Path
from flask import Flask
from threading import Thread

# --- [ ЛОКАЛЬНЫЕ МОДУЛИ ] ---
from draw_map import generate_star_map
from database import init_db, add_xp, get_user_stats, get_rank_name
from marty_chat import run_chat_bot 
from base_fact_star import CONSTELLATIONS
from vision_module import analyze_image 

# --- [ КОНФИГУРАЦИЯ ] ---
TOKEN = os.getenv('TELEGRAM_TOKEN')
LOG_CHAT_ID = "-1003756164148"
BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True) # Создаем папку, если её нет

bot = telebot.TeleBot(TOKEN, threaded=True)
apihelper.CONNECT_TIMEOUT = 60
apihelper.READ_TIMEOUT = 90

SPACE_FACTS = [
    "🔭 Настраиваю линзы Хаббла... почти готово!",
    "🌌 Знаешь ли ты? Звезды, которые ты видишь, — это свет из прошлого.",
    "🛸 Ищу следы внеземных цивилизаций в твоем секторе...",
    "🌠 Вычисляю траектории метеоритов, чтобы они не попали в кадр.",
    "🛰️ Соединяюсь со спутниками ГЛОНАСС и GPS для точности 99.9%.",
    "🪐 Сатурн мог бы плавать в воде, если бы нашелся такой океан."
]

def send_log(text):
    try: bot.send_message(LOG_CHAT_ID, f"📡 <b>[LOG]:</b> {text}", parse_mode='HTML')
    except: print(f"Ошибка лога: {text}")

# --- [ ИНСТРУКЦИЯ И РАНГИ ] ---
def get_instruction_text():
    return (
        "📜 <b>УСТАВ КОСМИЧЕСКОГО ПАТРУЛЯ</b>\n"
        "───────────────────────\n\n"
        "<b>Твои возможности:</b>\n"
        "1️⃣ <b>«МОЕ НЕБО»</b> — мгновенное фото космоса над тобой.\n"
        "2️⃣ <b>Анализ фото</b> — пришли мне снимок неба, и я скажу, что на нем.\n\n"
        "🎖 <b>СИСТЕМА ЗВАНИЙ:</b>\n"
        "• <b>0-100 XP: Кадет</b> (Учишься отличать Луну от прожектора)\n"
        "• <b>101-300 XP: Исследователь</b> (Знаешь путь по звездам)\n"
        "• <b>301-600 XP: Навигатор</b> (Твой дом — Млечный Путь)\n"
        "• <b>601-1000 XP: Командор</b> (Управляешь звездными флотами)\n"
        "• <b>1000+ XP: Адмирал Галактики</b> (Легенда системы)\n\n"
        "<i>За каждое небо: +15 XP. За анализ фото: +10 XP.</i>"
    )

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("📡📡📡 МОЕ НЕБО", request_location=True))
    markup.add(KeyboardButton("❓❓ ИНСТРУКЦИЯ ПИЛОТА"))
    bot.send_message(message.chat.id, f"🛰️ <b>Связь установлена, пилот {message.from_user.first_name}!</b>", reply_markup=markup, parse_mode='HTML')

@bot.message_handler(func=lambda m: m.text == "❓❓ ИНСТРУКЦИЯ ПИЛОТА")
def handle_instruction(message):
    bot.send_message(message.chat.id, get_instruction_text(), parse_mode='HTML')

# --- [ ГЕНЕРАЦИЯ С МОНИТОРИНГОМ 11 СЕКУНД ] ---
@bot.message_handler(content_types=['location'])
def handle_location(message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    
    status_msg = bot.send_message(message.chat.id, "🚀 <b>Запуск двигателей... Начинаю расчеты.</b>", parse_mode='HTML')
    
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(generate_star_map, message.location.latitude, message.location.longitude, user_name, user_id)
        
        # Цикл обновления статуса раз в 11 секунд
        start_time = time.time()
        while not future.done():
            time.sleep(11)
            if not future.done():
                elapsed = int(time.time() - start_time)
                fact = random.choice(SPACE_FACTS)
                try:
                    bot.edit_message_text(f"⏳ <b>Процесс идет ({elapsed}с):</b>\n{fact}", message.chat.id, status_msg.message_id, parse_mode='HTML')
                except: pass

        success, result_jpg, result_png, target_name, err_msg = future.result()

    if success:
        add_xp(user_id, 15, user_name)
        current_xp = get_user_stats(user_id)
        rank = get_rank_name(current_xp)

        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton(f"🌌 Досье: {target_name}", callback_data=f"wiki_{target_name}"))
        markup.add(InlineKeyboardButton("🖼️ Получить Full HD", callback_data=f"orig_{user_id}"))
        
        caption = (f"✨ <b>Готово! Твой сектор: {target_name}</b>\n\n"
                   f"🎖 <b>Ранг:</b> {rank}\n📈 <b>Опыт:</b> {current_xp} XP (+15 за вылет)")
        
        with open(result_jpg, 'rb') as photo:
            bot.send_photo(message.chat.id, photo, caption=caption, reply_markup=markup, parse_mode='HTML')
        bot.delete_message(message.chat.id, status_msg.message_id)
    else:
        bot.edit_message_text(f"❌ <b>Ошибка:</b> {err_msg}", message.chat.id, status_msg.message_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith('orig_'))
def callback_orig(call):
    user_id = call.data.replace('orig_', '')
    file_path = OUTPUT_DIR / f"fin_{user_id}.png"
    
    if file_path.exists():
        bot.answer_callback_query(call.id, "Отправляю оригинал...")
        with open(file_path, 'rb') as doc:
            bot.send_document(call.message.chat.id, doc, caption="🚀 <b>Full HD Карта (без сжатия)</b>", parse_mode='HTML')
    else:
        bot.answer_callback_query(call.id, "❌ Файл не найден. Сгенерируй карту заново.", show_alert=True)

# --- [ ОСТАЛЬНОЙ КОД (Flask, Polling) ] ---
# ... (оставь как было в твоем main)
