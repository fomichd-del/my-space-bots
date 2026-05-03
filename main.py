import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telebot import apihelper
import os, time, concurrent.futures, random
from pathlib import Path
from flask import Flask
from threading import Thread

# --- [ ИМПОРТ МОДУЛЕЙ ] ---
from draw_map import generate_star_map
from database import init_db, add_xp, get_user_stats, get_rank_name
from marty_chat import run_chat_bot 
from base_fact_star import CONSTELLATIONS
from vision_module import analyze_image 

TOKEN = os.getenv('TELEGRAM_TOKEN')
LOG_CHAT_ID = "-1003756164148"
BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

bot = telebot.TeleBot(TOKEN, threaded=True)
apihelper.CONNECT_TIMEOUT = 60
apihelper.READ_TIMEOUT = 90

SPACE_FACTS = [
    "🔭 Настраиваю линзы Хаббла... Собираю фотоны.",
    "🌌 Звезды, которые ты видишь, — это свет из далекого прошлого.",
    "🛸 Проверяю сектор на наличие неопознанных объектов...",
    "🛰️ Синхронизируюсь со спутниками для точности координат 99.9%.",
    "🪐 Сатурн настолько легкий, что плавал бы в океане.",
    "🌠 В нашей галактике больше звезд, чем песчинок на всех пляжах Земли."
]

def send_log(text):
    try: bot.send_message(LOG_CHAT_ID, f"📡 <b>[LOG]:</b> {text}", parse_mode='HTML')
    except: print(text)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("📡📡📡 МОЕ НЕБО", request_location=True))
    markup.add(KeyboardButton("❓❓ ИНСТРУКЦИЯ ПИЛОТА"))
    bot.send_message(message.chat.id, f"🛰️ <b>Связь установлена, пилот {message.from_user.first_name}!</b>", reply_markup=markup, parse_mode='HTML')

@bot.message_handler(func=lambda m: m.text == "❓❓ ИНСТРУКЦИЯ ПИЛОТА")
def handle_instruction(message):
    text = (
        "📜 <b>УСТАВ ИССЛЕДОВАТЕЛЯ</b>\n"
        "• <b>«МОЕ НЕБО»</b>: Получи карту звезд над собой.\n"
        "• <b>Фото</b>: Пришли фото неба, я его изучу.\n"
        "• <b>XP</b>: Повышай ранг от Кадета до Адмирала!\n"
        "• <b>Full HD</b>: Скачивай оригиналы карт файлом."
    )
    bot.send_message(message.chat.id, text, parse_mode='HTML')

@bot.message_handler(content_types=['location'])
def handle_location(message):
    user_id, user_name = message.from_user.id, message.from_user.first_name
    status_msg = bot.send_message(message.chat.id, "🚀 <b>Запуск систем навигации...</b>", parse_mode='HTML')
    
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(generate_star_map, message.location.latitude, message.location.longitude, user_name, user_id)
        
        start_w = time.time()
        while not future.done():
            time.sleep(11)
            if not future.done():
                elapsed = int(time.time() - start_w)
                fact = random.choice(SPACE_FACTS)
                try: bot.edit_message_text(f"⏳ <b>Идет расчет ({elapsed}с):</b>\n{fact}", message.chat.id, status_msg.message_id, parse_mode='HTML')
                except: pass

        # Ожидаем 5 значений от функции
        success, res_jpg, res_png, target_name, err_msg = future.result()

    if success:
        add_xp(user_id, 15, user_name)
        current_xp = get_user_stats(user_id)
        rank = get_rank_name(current_xp)
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton(f"🌌 Досье: {target_name}", callback_data=f"wiki_{target_name}"))
        markup.add(InlineKeyboardButton("🖼️ Получить Full HD", callback_data=f"orig_{user_id}"))
        
        caption = f"✨ <b>Готово! Сектор: {target_name}</b>\n🎖 <b>Ранг:</b> {rank} | 📈 <b>XP:</b> {current_xp}"
        with open(res_jpg, 'rb') as ph:
            bot.send_photo(message.chat.id, ph, caption=caption, reply_markup=markup, parse_mode='HTML')
        bot.delete_message(message.chat.id, status_msg.message_id)
    else:
        bot.edit_message_text(f"❌ <b>Ошибка:</b> {err_msg}", message.chat.id, status_msg.message_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith('orig_'))
def callback_orig(call):
    user_id = call.data.replace('orig_', '')
    f_path = OUTPUT_DIR / f"fin_{user_id}.png"
    if f_path.exists():
        bot.answer_callback_query(call.id, "Передаю оригинал...")
        with open(f_path, 'rb') as doc:
            bot.send_document(call.message.chat.id, doc, caption="🚀 <b>Карта в Full HD.</b>", parse_mode='HTML')
    else:
        bot.answer_callback_query(call.id, "❌ Файл утерян.", show_alert=True)

# --- [ FLASK И ЗАПУСК ] ---
app = Flask(__name__)
@app.route('/')
def home(): return "Online"

def run_server():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

if __name__ == "__main__":
    init_db()
    Thread(target=run_server, daemon=True).start()
    Thread(target=run_chat_bot, daemon=True).start()
    
    while True:
        try:
            bot.delete_webhook(drop_pending_updates=True)
            bot.polling(non_stop=True, interval=1, timeout=90)
        except Exception as e:
            time.sleep(10)
