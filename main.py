import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telebot import apihelper
import os, time, concurrent.futures, random
from pathlib import Path
from flask import Flask
from threading import Thread

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
PHOTO_SPACE_DIR = BASE_DIR / "photo_space" # Папка с фото созвездий из GitHub

OUTPUT_DIR.mkdir(exist_ok=True)

bot = telebot.TeleBot(TOKEN, threaded=True)
apihelper.CONNECT_TIMEOUT = 60
apihelper.READ_TIMEOUT = 90

# --- [ АТМОСФЕРНЫЕ СООБЩЕНИЯ ОЖИДАНИЯ ] ---
SPACE_FACTS = [
    "🔭 <b>Настройка линз...</b> Собираю фотоны света, летевшие к нам миллионы лет.",
    "🌌 <b>Справка:</b> Звезды, которые ты видишь сейчас, — это «призраки» прошлого. Многих из них уже не существует.",
    "🛸 <b>Сканирование...</b> Проверяю твой сектор на наличие аномалий и неопознанных объектов.",
    "🛰️ <b>Связь со спутниками...</b> Синхронизирую координаты с точностью до миллисекунды.",
    "🪐 <b>Факт:</b> Если бы Сатурн можно было опустить в гигантский океан, он бы плавал на поверхности, как пробка.",
    "🌠 <b>Внимание:</b> Прямо сейчас сквозь тебя пролетают триллионы нейтрино, выпущенных далекими звездами.",
    "🌓 <b>На заметку:</b> На Луне твой прыжок был бы в 6 раз выше. Там каждый кадет — супермен!"
]

def send_log(text):
    try: bot.send_message(LOG_CHAT_ID, f"📡 <b>[LOG]:</b> {text}", parse_mode='HTML')
    except: print(text)

# --- [ УМНЫЙ ПОИСК ФОТО В АРХИВЕ ] ---
def find_constellation_photo(name_latin):
    """Ищет файл в photo_space, соответствующий латинскому названию созвездия"""
    if not PHOTO_SPACE_DIR.exists(): return None
    target = name_latin.lower().strip().replace(" ", "_")
    valid_extensions = {'.jpg', '.jpeg', '.png', '.webp'}
    
    for file_path in PHOTO_SPACE_DIR.iterdir():
        if file_path.suffix.lower() in valid_extensions:
            if file_path.stem.lower().strip() == target:
                return file_path
    return None

# --- [ РАСШИРЕННАЯ ИНСТРУКЦИЯ ] ---
def get_instruction_text():
    return (
        "📜 <b>БОРТОВОЙ УСТАВ ИССЛЕДОВАТЕЛЯ</b>\n"
        "───────────────────────\n\n"
        "Пилот, добро пожаловать на борт! Я — <b>Марти</b>, твой ИИ-штурман. 🐾\n"
        "Моя задача — сделать космос понятным и близким. Вот твои модули:\n\n"
        "📡 <b>МОДУЛЬ «МОЕ НЕБО»</b>\n"
        "Отправь свою геолокацию, и я мгновенно отрисую карту звезд, которые находятся прямо над твоей головой. "
        "Это не просто картинка, а точный математический расчет твоего горизонта.\n"
        "🎁 <i>Награда: +15 XP.</i>\n\n"
        "📸 <b>НЕЙРО-СКАНЕР «ГЛАЗА МАРТИ»</b>\n"
        "Пришли мне любое фото ночного неба. Мои нейросети проанализируют объекты и попытаются узнать созвездия.\n"
        "🎁 <i>Награда: +10 XP.</i>\n\n"
        "🎖 <b>КАРЬЕРНАЯ ЛЕСТНИЦА (РАНГИ):</b>\n"
        "За каждое действие ты получаешь опыт (XP). Повышай свой допуск:\n"
        "• <b>Кадет</b> (0-100 XP)\n"
        "• <b>Исследователь</b> (101-300 XP)\n"
        "• <b>Навигатор</b> (301-600 XP)\n"
        "• <b>Командор</b> (601-1000 XP)\n"
        "• <b>Адмирал Галактики</b> (1000+ XP)\n\n"
        "🖼 <b>ОРИГИНАЛЫ В FULL HD</b>\n"
        "После каждой генерации ты можешь запросить файл без сжатия для печати или обоев."
    )

# --- [ ОБРАБОТЧИКИ ] ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("📡📡📡 МОЕ НЕБО", request_location=True))
    markup.add(KeyboardButton("❓❓ ИНСТРУКЦИЯ ПИЛОТА"))
    
    welcome_text = (
        f"🛰️ <b>Связь установлена! Рад видеть тебя в рубке, пилот {message.from_user.first_name}!</b>\n\n"
        "Все системы прогреты и готовы к сканированию. Куда направим телескопы? 🐾"
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup, parse_mode='HTML')

@bot.message_handler(func=lambda m: m.text == "❓❓ ИНСТРУКЦИЯ ПИЛОТА")
def handle_instruction(message):
    bot.send_message(message.chat.id, get_instruction_text(), parse_mode='HTML')

@bot.message_handler(content_types=['location'])
def handle_location(message):
    user_id, user_name = message.from_user.id, message.from_user.first_name
    status_msg = bot.send_message(message.chat.id, "🚀 <b>Запуск двигателей... Начинаю расчет сектора.</b>", parse_mode='HTML')
    
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(generate_star_map, message.location.latitude, message.location.longitude, user_name, user_id)
        
        start_w = time.time()
        while not future.done():
            time.sleep(11)
            if not future.done():
                elapsed = int(time.time() - start_w)
                fact = random.choice(SPACE_FACTS)
                try: bot.edit_message_text(f"⏳ <b>Идет обработка данных ({elapsed}с):</b>\n\n{fact}", message.chat.id, status_msg.message_id, parse_mode='HTML')
                except: pass

        success, res_jpg, res_png, target_name, err_msg = future.result()

    if success:
        add_xp(user_id, 15, user_name)
        current_xp = get_user_stats(user_id)
        rank = get_rank_name(current_xp)
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton(f"🌌 Открыть досье: {target_name}", callback_data=f"wiki_{target_name}"))
        markup.add(InlineKeyboardButton("🖼️ Получить Full HD", callback_data=f"orig_{user_id}"))
        # ВОЗВРАЩАЕМ КНОПКУ К БОТУ МАРТИ
        markup.add(InlineKeyboardButton("🤖 Спросить эксперта Марти", url="https://t.me/Marty_Help_Bot?start=help"))
        
        caption = (
            f"✨ <b>СЕКТОР ПРОСКАНИРОВАН УСПЕШНО!</b>\n\n"
            f"Пилот <b>{user_name}</b>, прямо сейчас над тобой доминирует созвездие <b>{target_name}</b>.\n"
            f"─────────────────────\n"
            f"🎖 <b>Твой ранг:</b> {rank}\n"
            f"📈 <b>Твой опыт:</b> {current_xp} XP (добавлено +15)"
        )
        with open(res_jpg, 'rb') as ph:
            bot.send_photo(message.chat.id, ph, caption=caption, reply_markup=markup, parse_mode='HTML')
        bot.delete_message(message.chat.id, status_msg.message_id)
    else:
        bot.edit_message_text(f"❌ <b>Ошибка навигации:</b> {err_msg}", message.chat.id, status_msg.message_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith('wiki_'))
def callback_wiki(call):
    subject = call.data.replace('wiki_', '').strip()
    bot.answer_callback_query(call.id, "Запрашиваю данные из архива...")
    
    # Поиск в базе из base_fact_star.py
    found = next((item for item in CONSTELLATIONS if item['name_ru'].upper() == subject.upper()), None)
    if found:
        text = f"🌌 <b>БОРТОВОЕ ДОСЬЕ: {found['name_ru'].upper()}</b>\n\n{found['fact']}"
        photo_path = find_constellation_photo(found.get('name_latin', ''))
        
        if photo_path and photo_path.exists():
            with open(photo_path, 'rb') as ph:
                bot.send_photo(call.message.chat.id, ph, caption=text, parse_mode='HTML')
        else:
            bot.send_message(call.message.chat.id, text, parse_mode='HTML')
    else:
        bot.send_message(call.message.chat.id, "⚠️ Данные об этом секторе засекречены или отсутствуют.")

@bot.callback_query_handler(func=lambda call: call.data.startswith('orig_'))
def callback_orig(call):
    user_id = call.data.replace('orig_', '')
    f_path = OUTPUT_DIR / f"fin_{user_id}.png"
    if f_path.exists():
        bot.answer_callback_query(call.id, "Подготавливаю файл...")
        with open(f_path, 'rb') as doc:
            bot.send_document(call.message.chat.id, doc, caption="🚀 <b>Твой оригинал в максимальном качестве.</b>", parse_mode='HTML')
    else:
        bot.answer_callback_query(call.id, "❌ Файл не найден в кэше.", show_alert=True)

# --- [ SERVER ] ---
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
