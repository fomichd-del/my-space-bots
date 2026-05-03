import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telebot import apihelper
import os, time, concurrent.futures, random
from pathlib import Path
from draw_map import generate_star_map
from flask import Flask
from threading import Thread

# --- [ ЛОКАЛЬНЫЕ МОДУЛИ КОРАБЛЯ ] ---
from database import init_db, add_xp, get_user_stats, get_rank_name
from marty_chat import run_chat_bot 
from base_fact_star import CONSTELLATIONS
from vision_module import analyze_image 

# --- [ КОНФИГУРАЦИЯ ] ---
TOKEN = os.getenv('TELEGRAM_TOKEN')
LOG_CHAT_ID = "-1003756164148"
# Используем Path для надежности путей
BASE_DIR = Path(__file__).resolve().parent
PHOTO_SPACE_DIR = BASE_DIR / "photo_space"
OUTPUT_DIR = BASE_DIR / "output"

bot = telebot.TeleBot(TOKEN, threaded=True)

# Глубокие таймауты для тяжелых нейросетевых запросов
apihelper.CONNECT_TIMEOUT = 60
apihelper.READ_TIMEOUT = 90

# --- [ ЦЕНТР МОНИТОРИНГА ] ---
def send_log(text):
    try:
        bot.send_message(LOG_CHAT_ID, f"📡 <b>[LOG]:</b> {text}", parse_mode='HTML')
    except Exception as e:
        print(f"Критический сбой логирования: {e}")

# --- [ УМНЫЙ ПОИСК ФОТО В АРХИВЕ ] ---
def find_constellation_photo(name_latin):
    """Ищет фото, игнорируя регистр, лишние символы и расширения."""
    if not PHOTO_SPACE_DIR.exists():
        return None
    
    target = name_latin.lower().strip()
    valid_extensions = {'.jpg', '.jpeg', '.png', '.webp'}
    
    for file_path in PHOTO_SPACE_DIR.iterdir():
        if file_path.suffix.lower() in valid_extensions:
            if file_path.stem.lower().strip() == target:
                return file_path
    return None

# --- [ ИНСТРУКЦИЯ ] ---
def get_instruction_text():
    return (
        "📜 <b>БОРТОВОЙ УСТАВ ИССЛЕДОВАТЕЛЯ</b>\n"
        "───────────────────────\n\n"
        "Пилот, добро пожаловать в систему навигации Марти! 🐾\n\n"
        "📡 <b>СИСТЕМА «МОЕ НЕБО»</b>\n"
        "Жми кнопку локации. Я свяжусь со спутниками и отрисую карту звезд прямо над твоей головой.\n"
        "👉 <i>Бонус: +15 XP к твоему рангу.</i>\n\n"
        "📸 <b>МОДУЛЬ «ГЛАЗА МАРТИ»</b>\n"
        "Пришли фото неба или созвездия. Мои алгоритмы проанализируют снимок и найдут совпадения в архивах.\n"
        "👉 <i>Бонус: +10 XP.</i>\n\n"
        "🎖 <b>ТВОЯ КАРЬЕРА (РАНГ)</b>\n"
        "Копи опыт (XP), чтобы продвигаться во флоте: от Кадета до Адмирала Галактики.\n\n"
        "🖼 <b>КНОПКА «FULL HD»</b>\n"
        "Доступна после генерации карты. Я пришлю файл без сжатия для твоих архивов."
    )

# --- [ ОБРАБОТЧИКИ КОМАНД ] ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("📡📡📡 МОЕ НЕБО", request_location=True))
    markup.add(KeyboardButton("❓❓ ИНСТРУКЦИЯ ПИЛОТА"))
    
    welcome_text = (
        f"🛰️ <b>Связь установлена! Рад видеть тебя в рубке, пилот {message.from_user.first_name}!</b>\n\n"
        "Я — <b>Марти</b>, твой персональный штурман. Мои системы готовы к сканированию или анализу твоих снимков. 🐾\n"
        "С чего начнем?"
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup, parse_mode='HTML')

@bot.message_handler(func=lambda m: m.text == "❓❓ ИНСТРУКЦИЯ ПИЛОТА")
def handle_instruction(message):
    bot.send_message(message.chat.id, get_instruction_text(), parse_mode='HTML')

# --- [ АНАЛИЗ ФОТО ] ---
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    status_msg = bot.reply_to(message, "📸 <b>Активирую нейро-сенсоры... Изучаю данные...</b>", parse_mode='HTML')
    
    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        description = analyze_image(downloaded_file)
        
        add_xp(user_id, 10, user_name)
        new_xp = get_user_stats(user_id)
        
        caption = (
            f"🔍 <b>ОТЧЕТ ШТУРМАНА:</b>\n\n{description}\n"
            f"─────────────────────\n"
            f"📈 <b>Данные сохранены!</b> +10 XP (Всего: {new_xp})"
        )
        bot.edit_message_text(caption, message.chat.id, status_msg.message_id, parse_mode='Markdown')
    except Exception as e:
        send_log(f"🆘 Ошибка Vision: {e}")
        bot.edit_message_text("🛰️ <b>Внимание!</b> Не удалось распознать объект из-за помех.", message.chat.id, status_msg.message_id)

# --- [ СКАНИРОВАНИЕ НЕБА ] ---
@bot.message_handler(content_types=['location'])
def handle_location(message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    status_msg = bot.send_message(message.chat.id, "🛰️ <b>Вычисляю положение звезд... Сверяю координаты...</b>", parse_mode='HTML')
    
    try:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(generate_star_map, message.location.latitude, message.location.longitude, user_name, user_id)
            success, result, target_name, err_msg = future.result()

        if success:
            add_xp(user_id, 15, user_name)
            current_xp = get_user_stats(user_id)
            rank = get_rank_name(current_xp)

            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton(f"🌌 Открыть досье: {target_name}", callback_data=f"wiki_{target_name}"))
            markup.add(InlineKeyboardButton("🖼️ Получить Full HD оригинал", callback_data=f"orig_{user_id}"))
            markup.add(InlineKeyboardButton("📡 КАНАЛ ШТУРМАНА", url="https://t.me/Marty_Help_Bot?start=help"))
            
            caption = (
                f"✨ <b>СЕКТОР ПРОСКАНИРОВАН!</b>\n\n"
                f"Пилот <b>{user_name}</b>, прямо сейчас над тобой сияет <b>{target_name}</b>.\n"
                f"─────────────────────\n"
                f"🎖 <b>Статус:</b> {rank} | 📈 <b>Опыт:</b> {current_xp} XP"
            )
            with open(result, 'rb') as photo:
                bot.send_photo(message.chat.id, photo, caption=caption, reply_markup=markup, parse_mode='HTML')
            bot.delete_message(message.chat.id, status_msg.message_id)
        else:
            bot.edit_message_text(f"❌ <b>Ошибка навигации:</b> {err_msg}", message.chat.id, status_msg.message_id)
    except Exception as e:
        send_log(f"🆘 Ошибка генерации: {e}")
        bot.send_message(message.chat.id, "💥 <b>Системный сбой!</b> Марти потерял ориентацию.")

# --- [ ДОСЬЕ И ОРИГИНАЛЫ ] ---
@bot.callback_query_handler(func=lambda call: call.data.startswith('wiki_'))
def callback_wiki(call):
    subject = call.data.replace('wiki_', '').strip()
    bot.answer_callback_query(call.id, "Запрашиваю данные из архива...")
    
    found_fact = next((item for item in CONSTELLATIONS if item['name_ru'].upper() == subject.upper()), None)
    if found_fact:
        text = f"🌌 <b>БОРТОВОЕ ДОСЬЕ: {found_fact['name_ru'].upper()}</b>\n\n{found_fact['fact']}"
        photo_path = find_constellation_photo(found_fact.get('name_latin', ''))
        
        if photo_path and photo_path.exists():
            with open(photo_path, 'rb') as photo:
                bot.send_photo(call.message.chat.id, photo, caption=text, parse_mode='HTML')
        else:
            bot.send_message(call.message.chat.id, text, parse_mode='HTML')
    else:
        bot.send_message(call.message.chat.id, "⚠️ Данные об этом секторе отсутствуют.")

@bot.callback_query_handler(func=lambda call: call.data.startswith('orig_'))
def callback_orig(call):
    user_id = call.data.replace('orig_', '')
    bot.answer_callback_query(call.id, "Подготавливаю файл...")
    file_path = OUTPUT_DIR / f"star_map_{user_id}.png"
    
    if file_path.exists():
        with open(file_path, 'rb') as doc:
            bot.send_document(call.message.chat.id, doc, caption="🚀 <b>Твой снимок без сжатия.</b>", parse_mode='HTML')
    else:
        bot.send_message(call.message.chat.id, "❌ Файл утерян в гиперпространстве.")

# --- [ SERVER ] ---
app = Flask(__name__)
@app.route('/')
def home(): return "Navigator Marty Status: Online"

def run_server():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

if __name__ == "__main__":
    init_db()
    send_log("🚀 <b>Штурман Марти на посту. Системы в норме!</b>")
    Thread(target=run_server).start()
    bot.remove_webhook()
    bot.polling(non_stop=True, interval=1)
