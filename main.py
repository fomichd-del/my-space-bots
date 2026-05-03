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

# --- [ КОНФИГУРАЦИЯ ПУТЕЙ И СЕТИ ] ---
TOKEN = os.getenv('TELEGRAM_TOKEN')
LOG_CHAT_ID = "-1003756164148"

# Работаем через Path для стабильности на Linux/Render
BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
PHOTO_SPACE_DIR = BASE_DIR / "photo_space"

# Создаем папки, если их нет
OUTPUT_DIR.mkdir(exist_ok=True)
PHOTO_SPACE_DIR.mkdir(exist_ok=True)

bot = telebot.TeleBot(TOKEN, threaded=True)

# Увеличенные таймауты для тяжелых нейросетевых расчетов
apihelper.CONNECT_TIMEOUT = 60
apihelper.READ_TIMEOUT = 90

# --- [ ЦЕНТР МОНИТОРИНГА ] ---
def send_log(text):
    try:
        bot.send_message(LOG_CHAT_ID, f"📡 <b>[LOG]:</b> {text}", parse_mode='HTML')
    except Exception as e:
        print(f"Ошибка логирования: {e}")

# --- [ БАЗА ЗНАНИЙ ДЛЯ ОЖИДАНИЯ ] ---
SPACE_FACTS = [
    "🔭 Настраиваю линзы Хаббла... Собираю фотоны света.",
    "🌌 Знаешь ли ты? Звезды, которые ты видишь, — это свет из далекого прошлого.",
    "🛸 Проверяю сектор на наличие неопознанных объектов...",
    "🌠 Вычисляю траектории метеоритов, чтобы они не попали в кадр.",
    "🛰️ Синхронизируюсь со спутниками для точности координат 99.9%.",
    "🪐 Если бы Сатурн упал в океан, он бы плавал на поверхности.",
    "🌓 На Луне твой прыжок был бы в 6 раз выше и длиннее!"
]

# --- [ УМНЫЙ ПОИСК ФОТО В АРХИВЕ ] ---
def find_constellation_photo(name_latin):
    if not PHOTO_SPACE_DIR.exists(): return None
    target = name_latin.lower().strip()
    valid_extensions = {'.jpg', '.jpeg', '.png', '.webp'}
    for file_path in PHOTO_SPACE_DIR.iterdir():
        if file_path.suffix.lower() in valid_extensions:
            if file_path.stem.lower().strip() == target:
                return file_path
    return None

# --- [ ТЕКСТ ИНСТРУКЦИИ ] ---
def get_instruction_text():
    return (
        "📜 <b>УСТАВ КОСМИЧЕСКОГО ПАТРУЛЯ</b>\n"
        "───────────────────────\n\n"
        "Пилот, добро пожаловать! Я — Марти, твой ИИ-штурман. 🐾\n\n"
        "📡 <b>КНОПКА «МОЕ НЕБО»</b>\n"
        "Пришли свою локацию, и я отрисую карту звезд прямо над тобой в этот момент.\n"
        "🎁 <i>Награда: +15 XP.</i>\n\n"
        "📸 <b>АНАЛИЗ ФОТОГРАФИЙ</b>\n"
        "Пришли мне любое фото неба. Мои нейро-сенсоры попытаются распознать, что на нем изображено.\n"
        "🎁 <i>Награда: +10 XP.</i>\n\n"
        "🎖 <b>СИСТЕМА ЗВАНИЙ:</b>\n"
        "• <b>0-100 XP:</b> Кадет\n"
        "• <b>101-300 XP:</b> Исследователь\n"
        "• <b>301-600 XP:</b> Навигатор\n"
        "• <b>601-1000 XP:</b> Командор\n"
        "• <b>1000+ XP:</b> Адмирал Галактики\n\n"
        "🖼 <b>FULL HD ОРИГИНАЛЫ</b>\n"
        "После генерации карты ты можешь скачать её файлом без потери качества."
    )

# --- [ ОБРАБОТЧИКИ КОМАНД ] ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("📡📡📡 МОЕ НЕБО", request_location=True))
    markup.add(KeyboardButton("❓❓ ИНСТРУКЦИЯ ПИЛОТА"))
    
    welcome_text = (
        f"🛰️ <b>Связь установлена! Рад видеть тебя в рубке, пилот {message.from_user.first_name}!</b>\n\n"
        "Я готов к сканированию твоего сектора. С чего начнем? 🐾"
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup, parse_mode='HTML')

@bot.message_handler(func=lambda m: m.text == "❓❓ ИНСТРУКЦИЯ ПИЛОТА")
def handle_instruction(message):
    bot.send_message(message.chat.id, get_instruction_text(), parse_mode='HTML')

# --- [ АНАЛИЗ ФОТО (VISION) ] ---
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    status_msg = bot.reply_to(message, "📸 <b>Активирую нейро-сенсоры... Изучаю данные...</b>", parse_mode='HTML')
    
    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        description = analyze_image(downloaded_file) # Вызов твоего модуля Vision
        
        add_xp(user_id, 10, user_name)
        new_xp = get_user_stats(user_id)
        
        caption = (
            f"🔍 <b>ОТЧЕТ ШТУРМАНА:</b>\n\n{description}\n"
            f"─────────────────────\n"
            f"📈 <b>Данные сохранены!</b> +10 XP (Всего: {new_xp})"
        )
        bot.edit_message_text(caption, message.chat.id, status_msg.message_id, parse_mode='HTML')
    except Exception as e:
        send_log(f"🆘 Ошибка Vision: {e}")
        bot.edit_message_text("🛰️ <b>Внимание!</b> Не удалось распознать объект из-за помех.", message.chat.id, status_msg.message_id)

# --- [ СКАНИРОВАНИЕ НЕБА (LOCATION) ] ---
@bot.message_handler(content_types=['location'])
def handle_location(message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    
    status_msg = bot.send_message(message.chat.id, "🛰️ <b>Начинаю расчеты траекторий...</b>", parse_mode='HTML')
    
    try:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(generate_star_map, message.location.latitude, message.location.longitude, user_name, user_id)
            
            # --- ЦИКЛ ОБНОВЛЕНИЯ РАЗ В 11 СЕКУНД ---
            start_wait = time.time()
            while not future.done():
                time.sleep(11)
                if not future.done():
                    elapsed = int(time.time() - start_wait)
                    fact = random.choice(SPACE_FACTS)
                    try:
                        bot.edit_message_text(f"⏳ <b>Идет расчет ({elapsed}с):</b>\n{fact}", message.chat.id, status_msg.message_id, parse_mode='HTML')
                    except: pass

            success, res_jpg, res_png, target_name, err_msg = future.result()

        if success:
            add_xp(user_id, 15, user_name)
            current_xp = get_user_stats(user_id)
            rank = get_rank_name(current_xp)

            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton(f"🌌 Досье: {target_name}", callback_data=f"wiki_{target_name}"))
            markup.add(InlineKeyboardButton("🖼️ Получить Full HD", callback_data=f"orig_{user_id}"))
            
            caption = (
                f"✨ <b>СЕКТОР ПРОСКАНИРОВАН!</b>\n\n"
                f"Пилот <b>{user_name}</b>, твоя цель — созвездие <b>{target_name}</b>.\n"
                f"─────────────────────\n"
                f"🎖 <b>Звание:</b> {rank} | 📈 <b>Опыт:</b> {current_xp} XP"
            )
            
            with open(res_jpg, 'rb') as photo:
                bot.send_photo(message.chat.id, photo, caption=caption, reply_markup=markup, parse_mode='HTML')
            bot.delete_message(message.chat.id, status_msg.message_id)
            send_log(f"✅ Карта создана для {user_name} (XP: {current_xp})")
        else:
            bot.edit_message_text(f"❌ <b>Ошибка:</b> {err_msg}", message.chat.id, status_msg.message_id)
            
    except Exception as e:
        send_log(f"🆘 Критическая ошибка генерации: {e}")
        bot.send_message(message.chat.id, "💥 <b>Системный сбой!</b> Марти временно потерял ориентацию.")

# --- [ CALLBACKS: WIKI И FULL HD ] ---
@bot.callback_query_handler(func=lambda call: call.data.startswith('wiki_'))
def callback_wiki(call):
    subject = call.data.replace('wiki_', '').strip()
    bot.answer_callback_query(call.id, "Запрашиваю архивы...")
    
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
        bot.send_message(call.message.chat.id, "⚠️ Ошибка: данные об этом секторе отсутствуют.")

@bot.callback_query_handler(func=lambda call: call.data.startswith('orig_'))
def callback_orig(call):
    user_id = call.data.replace('orig_', '')
    file_path = OUTPUT_DIR / f"fin_{user_id}.png"
    
    if file_path.exists():
        bot.answer_callback_query(call.id, "Передача тяжелого файла...")
        with open(file_path, 'rb') as doc:
            bot.send_document(call.message.chat.id, doc, caption="🚀 <b>Твоя карта в Full HD (без сжатия).</b>", parse_mode='HTML')
    else:
        bot.answer_callback_query(call.id, "❌ Файл утерян. Сгенерируй заново.", show_alert=True)

# --- [ FLASK SERVER FOR RENDER ] ---
app = Flask(__name__)
@app.route('/')
def home(): return "Navigator Marty Status: Online"

def run_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- [ ЗАПУСК СИСТЕМ ] ---
if __name__ == "__main__":
    init_db()
    
    # 1. ЗАПУСКАЕМ СЕРВЕР ПЕРВЫМ (чтобы Render не убил процесс по таймауту порта)
    Thread(target=run_server, daemon=True).start()
    send_log("🛰️ <b>Flask сервер запущен. Порт активен.</b>")

    # 2. ЗАПУСКАЕМ ВТОРОГО БОТА (СОБЕСЕДНИКА)
    Thread(target=run_chat_bot, daemon=True).start()
    
    # 3. ОСНОВНОЙ ЦИКЛ ОПРОСА ТЕЛЕГРАМ
    send_log("🚀 <b>Штурман Марти на посту. Начинаю прием сигналов.</b>")
    
    while True:
        try:
            bot.remove_webhook()
            bot.polling(non_stop=True, interval=1, timeout=90)
        except Exception as e:
            send_log(f"⚠️ Ошибка поллинга: {e}. Перезапуск через 5 сек...")
            time.sleep(5)
