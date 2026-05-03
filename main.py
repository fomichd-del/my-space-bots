import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telebot import apihelper
import os, time, concurrent.futures, random
from draw_map import generate_star_map
from flask import Flask
from threading import Thread
import wikipediaapi
import requests
import io
from PIL import Image

# --- [ ИМПОРТ МОДУЛЕЙ ИГРОВОЙ ЛОГИКИ ] ---
from database import init_db, add_xp, get_user_stats, get_rank_name

# ИМПОРТ НОВОГО БОТА-СОБЕСЕДНИКА
from marty_chat import run_chat_bot 

# --- [ ИМПОРТ БАЗЫ КОСМИЧЕСКОГО ПАТРУЛЯ ] ---
from base_fact_star import CONSTELLATIONS

# --- [ КОСМИЧЕСКИЕ НАСТРОЙКИ ] ---
DATA_DIR = os.path.join(os.getcwd(), "data")
os.environ["STARPLOT_CACHE_DIR"] = DATA_DIR
os.environ["SOLAR_SYSTEM_EPHEMERIS"] = os.path.join(DATA_DIR, "de421.bsp")

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
# ID вашей закрытой группы для логов
LOG_CHAT_ID = "-1003756164148"

# Настройка глубоких таймаутов для работы с тяжелыми изображениями
apihelper.CONNECT_TIMEOUT = 60
apihelper.READ_TIMEOUT = 90

bot = telebot.TeleBot(TELEGRAM_TOKEN, threaded=True)
wiki_wiki = wikipediaapi.Wikipedia(user_agent='MartySpaceBot/1.1', language='ru')

# --- [ ЦЕНТР МОНИТОРИНГА (ЛОГИ) ] ---
def send_log(message_text):
    """Отправляет отчеты о работе систем в закрытую группу"""
    try:
        bot.send_message(LOG_CHAT_ID, f"📡 <b>[ОТЧЕТ БОРТОВОГО КОМПЬЮТЕРА]</b>\n\n{message_text}", parse_mode='HTML')
    except Exception as e:
        print(f"Критическая ошибка логирования: {e}")

# Flask для поддержания жизни сервера на Render
app = Flask(__name__)
@app.route('/')
def keep_alive(): return "🛰️ Бортовой компьютер Марти работает в штатном режиме!"
def run_server(): 
    try:
        app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
    except Exception as e:
        send_log(f"🆘 Ошибка сервера Flask: {e}")

# --- [ БАЗА ЗНАНИЙ ПАТРУЛЯ ] ---
SPACE_FACTS = [
    "🔭 <b>Знаешь ли ты?</b> Свет от Солнца доходит до нас за 8 минут. Видя Солнце, мы всегда смотрим на 8 минут в прошлое.",
    "🌌 <b>Факт:</b> В нашей Галактике около 200 миллиардов звезд. Если бы ты считал их по одной в секунду, тебе понадобилось бы 6000 лет.",
    "🛰️ <b>На заметку:</b> На МКС космонавты видят 16 рассветов и закатов в сутки, так как станция облетает Землю за 90 минут.",
    "🌠 <b>Это интересно:</b> Большинство звезд, которые ты видишь, на самом деле двойные или даже тройные системы, вращающиеся друг вокруг друга.",
    "🪐 <b>Совет:</b> Сатурн — настолько легкая планета, что если бы существовал гигантский океан, он бы плавал на его поверхности, как поплавок.",
    "🍎 <b>Знание:</b> Гравитация на Луне в 6 раз слабее земной. Там ты смог бы прыгнуть выше своего роста без особых усилий."
]

# --- [ ПРИВЕТСТВИЕ ] ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    try:
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(KeyboardButton("📡📡📡 МОЕ НЕБО", request_location=True))
        markup.add(KeyboardButton("❓❓ ИНСТРУКЦИЯ ПИЛОТА"))
        
        welcome_text = (
            f"🛰️ <b>Добро пожаловать в центр управления, {message.from_user.first_name}!</b>\n\n"
            "Я — <b>Марти</b>, твой персональный астрономический вычислитель. 🐾🎓\n\n"
            "🚀 <b>Готов увидеть свой сектор космоса?</b>\n"
            "Жми кнопку 📡 <b>«МОЕ НЕБО»</b>. Я мгновенно приступлю к расчетам!"
        )
        bot.send_message(message.chat.id, welcome_text, reply_markup=markup, parse_mode='HTML')
    except Exception as e:
        send_log(f"⚠️ Ошибка в команде /start: {e}")

# --- [ ГЕНЕРАЦИЯ КАРТЫ ] ---
@bot.message_handler(content_types=['location'])
def handle_location(message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    try:
        loading_statuses = [
            "📡 <b>Сигнал получен!</b> Подключаюсь к базам данных NASA...",
            "🔭 <b>Настройка оптики...</b> Ищу созвездие-ориентир для тебя.",
            "📐 <b>Математический расчет...</b> Вычисляю высоту планет над горизонтом."
        ]

        loading_msg = bot.send_message(message.chat.id, loading_statuses[0], parse_mode='HTML')
        
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(
                generate_star_map, 
                message.location.latitude, 
                message.location.longitude, 
                user_name, 
                user_id
            )
            
            status_index = 1
            while not future.done():
                time.sleep(10)
                if status_index < len(loading_statuses):
                    text = f"{loading_statuses[status_index]}\n\n{random.choice(SPACE_FACTS)}"
                    try:
                        bot.edit_message_text(text, message.chat.id, loading_msg.message_id, parse_mode='HTML')
                        status_index += 1
                    except: pass
            
            success, result, target_name, err_msg = future.result()

        bot.delete_message(message.chat.id, loading_msg.message_id)

        if success:
            # --- [ НАЧИСЛЕНИЕ XP И ПРОВЕРКА РАНГА ] ---
            add_xp(user_id, 15, user_name)
            current_xp = get_user_stats(user_id)
            rank = get_rank_name(current_xp)

            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton(f"🌌 Досье на {target_name}", callback_data=f"wiki_{target_name}"))
            markup.add(InlineKeyboardButton("🖼️ Оригинал (Full HD)", callback_data=f"orig_{user_id}"))
            markup.add(InlineKeyboardButton("🤖 Спросить эксперта Марти", url="https://t.me/Marty_Help_Bot?start=channel_post"))
            
            caption = (
                f"✨ <b>Твоя персональная карта готова, {user_name}!</b>\n\n"
                f"🎯 <b>Твоя главная цель:</b> созвездие <b>{target_name}</b>.\n"
                f"─────────────────────\n"
                f"🎖 <b>Твой ранг:</b> {rank}\n"
                f"📈 <b>Опыт:</b> {current_xp} XP"
            )
            
            with open(result, 'rb') as photo:
                bot.send_photo(message.chat.id, photo, caption=caption, reply_markup=markup, parse_mode='HTML')
            send_log(f"✅ Успешная генерация карты для пользователя {user_name} ({user_id})")
        else:
            bot.send_message(message.chat.id, f"❌ <b>Ошибка систем навигации.</b>")
            send_log(f"❌ Ошибка генерации карты для {user_name}: {result}")
            
    except Exception as e:
        bot.send_message(message.chat.id, f"🆘 <b>Космическое происшествие!</b>")
        send_log(f"🆘 Критическая ошибка в handle_location: {e}")

# --- [ ОБРАБОТЧИК КНОПОК ] ---
@bot.callback_query_handler(func=lambda call: call.data.startswith('wiki_'))
def callback_wiki(call):
    try:
        subject = call.data.replace('wiki_', '').strip()
        bot.answer_callback_query(call.id, "Доступ к архивам разрешен...")
        
        found_fact = next((item for item in CONSTELLATIONS if item['name_ru'].upper() == subject.upper()), None)
                
        if found_fact:
            text = f"🌌 <b>{found_fact['name_ru'].upper()} ({found_fact['name_latin']})</b>\n\n{found_fact['fact']}"
            bot.send_message(call.message.chat.id, text, parse_mode='HTML')
        else:
            send_log(f"⚠️ Данные о созвездии '{subject}' не найдены в базе.")
    except Exception as e:
        send_log(f"🆘 Ошибка в callback_wiki: {e}")

if __name__ == "__main__":
    # --- [ ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ ПРИ СТАРТЕ ] ---
    init_db()
    
    # Запуск лога о старте системы
    send_log("🚀 <b>Все системы запущены. База данных активна.</b>")
    
    Thread(target=run_server).start()
    Thread(target=run_chat_bot).start()
    
    bot.remove_webhook()
    bot.polling(non_stop=True, interval=2, timeout=60)
