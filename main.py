import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telebot import apihelper
import os, time, concurrent.futures, random
from pathlib import Path
from flask import Flask
from threading import Thread
# --- [ НОВЫЕ ДВИГАТЕЛИ 2026 ] ---
from google import genai 

# --- [ ИМПОРТ МОДУЛЕЙ КОРАБЛЯ ] ---
from draw_map import generate_star_map
from database import init_db, add_xp, get_user_stats, get_rank_name
from marty_chat import run_chat_bot 
from base_fact_star import CONSTELLATIONS
from vision_module import analyze_image 

# --- [ КОНФИГУРАЦИЯ ПУТЕЙ ] ---
TOKEN = os.getenv('TELEGRAM_TOKEN')
LOG_CHAT_ID = "-1003756164148"

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
PHOTO_SPACE_DIR = BASE_DIR / "photo_space"

OUTPUT_DIR.mkdir(exist_ok=True)

bot = telebot.TeleBot(TOKEN, threaded=True)
apihelper.CONNECT_TIMEOUT = 60
apihelper.READ_TIMEOUT = 90

# --- [ ЦЕНТР МОНИТОРИНГА И РАЗВЕДКА 2.0 ] ---
def send_log(text):
    try:
        bot.send_message(LOG_CHAT_ID, f"📡 <b>[LOG]:</b> {text}", parse_mode='HTML')
    except:
        print(f"Ошибка логирования: {text}")

def check_models():
    """Обновленная функция-разведчик для стандарта google-genai"""
    try:
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        print("🛰️ [РАЗВЕДКА] Запрашиваю список доступных моделей через новый протокол...")
        
        # В новой библиотеке метод получения списка моделей изменился
        for model in client.models.list():
            print(f"✅ Найдена модель: {model.name} (Поддерживает: {model.supported_actions})")
            
    except Exception as e:
        print(f"❌ ОШИБКА РАЗВЕДКИ: {e}")

# [ SPACE_FACTS, find_constellation_photo, get_instruction_text — без изменений ]
SPACE_FACTS = [
    "🔭 <b>Юстировка зеркал...</b> Собираю древние фотоны...",
    "🌌 <b>Факт дня:</b> Звезды, которые ты видишь сейчас — это «эхо» прошлого.",
    "🛸 <b>Сектор сканирования...</b> Проверяю пространство на аномалии.",
    "🪐 <b>Знание — сила:</b> Сатурн плавал бы в твоем бассейне.",
    "🌠 <b>Внимание:</b> Сквозь твое тело пролетают триллионы нейтрино."
]

def find_constellation_photo(name_latin):
    if not PHOTO_SPACE_DIR.exists(): return None
    target_name = name_latin.strip()
    file_path = PHOTO_SPACE_DIR / f"{target_name}.png"
    if file_path.exists(): return file_path
    for f in PHOTO_SPACE_DIR.iterdir():
        if f.stem.lower() == target_name.lower() and f.suffix.lower() == '.png':
            return f
    return None

def get_instruction_text():
    return (
        "📜 <b>БОРТОВОЙ УСТАВ ИССЛЕДОВАТЕЛЯ</b>\n"
        "───────────────────────\n\n"
        "Пилот, я — <b>Марти</b>, твой штурман! 🐾\n\n"
        "🛰️ <b>МОЕ НЕБО:</b> Жми на локацию — нарисую карту звезд над тобой.\n"
        "👁️ <b>ГЛАЗА МАРТИ:</b> Пришли фото неба — найду созвездия."
    )

# --- [ ОБРАБОТЧИКИ КОМАНД (start, location, wiki, orig) — без изменений ] ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("📡📡📡 МОЕ НЕБО", request_location=True))
    markup.add(KeyboardButton("❓❓ ИНСТРУКЦИЯ ПИЛОТА"))
    bot.send_message(message.chat.id, f"🛰️ <b>Системы прогреты, {message.from_user.first_name}!</b>", reply_markup=markup, parse_mode='HTML')

@bot.message_handler(func=lambda m: m.text == "❓❓ ИНСТРУКЦИЯ ПИЛОТА")
def handle_instruction(message):
    bot.send_message(message.chat.id, get_instruction_text(), parse_mode='HTML')

@bot.message_handler(content_types=['location'])
def handle_location(message):
    user_id, user_name = message.from_user.id, message.from_user.first_name
    status_msg = bot.send_message(message.chat.id, "🚀 <b>Запуск систем навигации...</b>", parse_mode='HTML')
    
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(generate_star_map, message.location.latitude, message.location.longitude, user_name, user_id)
        while not future.done():
            time.sleep(11)
            if not future.done():
                try: bot.edit_message_text(f"⏳ <b>Обработка...</b>\n\n{random.choice(SPACE_FACTS)}", message.chat.id, status_msg.message_id, parse_mode='HTML')
                except: pass
        success, res_jpg, res_png, target_name, err_msg = future.result()

    if success:
        add_xp(user_id, 15, user_name)
        stats = get_user_stats(user_id)
        rank = get_rank_name(stats)
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton(f"🌌 Досье: {target_name}", callback_data=f"wiki_{target_name}"))
        markup.add(InlineKeyboardButton("🖼️ Full HD", callback_data=f"orig_{user_id}"))
        with open(res_jpg, 'rb') as ph:
            bot.send_photo(message.chat.id, ph, caption=f"✨ <b>СЕКТОР ПРОСКАНИРОВАН!</b>\nНад тобой: {target_name}\nРанг: {rank}", reply_markup=markup, parse_mode='HTML')
    else:
        bot.send_message(message.chat.id, f"❌ Ошибка: {err_msg}")

@bot.callback_query_handler(func=lambda call: call.data.startswith('wiki_'))
def callback_wiki(call):
    subject = call.data.replace('wiki_', '').strip()
    found = next((item for item in CONSTELLATIONS if item['name_ru'].upper() == subject.upper()), None)
    if found:
        text = f"🌌 <b>ДОСЬЕ: {found['name_ru'].upper()}</b>\n\n{found['fact']}"
        photo_p = find_constellation_photo(found.get('name_latin', ''))
        if photo_p and photo_p.exists():
            with open(photo_p, 'rb') as ph: bot.send_photo(call.message.chat.id, ph, caption=text, parse_mode='HTML')
        else: bot.send_message(call.message.chat.id, text, parse_mode='HTML')

@bot.callback_query_handler(func=lambda call: call.data.startswith('orig_'))
def callback_orig(call):
    f_path = OUTPUT_DIR / f"fin_{call.data.replace('orig_', '')}.png"
    if f_path.exists():
        with open(f_path, 'rb') as doc: bot.send_document(call.message.chat.id, doc, caption="🚀 <b>Full HD оригинал.</b>", parse_mode='HTML')

# --- [ RUNNER ] ---
app = Flask(__name__)
@app.route('/')
def home(): return "Navigator Online"

def run_server():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

if __name__ == "__main__":
    init_db()
    check_models() 
    Thread(target=run_server, daemon=True).start()
    Thread(target=run_chat_bot, daemon=True).start()
    
    while True:
        try:
            bot.delete_webhook(drop_pending_updates=True)
            bot.polling(non_stop=True, interval=1, timeout=90)
        except Exception as e:
            time.sleep(10)
