import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telebot import apihelper
import os, time, concurrent.futures, random
from draw_map import generate_star_map
from flask import Flask
from threading import Thread
from PIL import Image

# --- [ ЛОКАЛЬНЫЕ МОДУЛИ КОРАБЛЯ ] ---
from database import init_db, add_xp, get_user_stats, get_rank_name
from marty_chat import run_chat_bot 
from base_fact_star import CONSTELLATIONS
from vision_module import analyze_image 

# --- [ КОНФИГУРАЦИЯ ] ---
TOKEN = os.getenv('TELEGRAM_TOKEN')
LOG_CHAT_ID = "-1003756164148"
PHOTO_SPACE_DIR = "photo_space" # Папка с твоими генерациями

bot = telebot.TeleBot(TOKEN, threaded=True)

apihelper.CONNECT_TIMEOUT = 60
apihelper.READ_TIMEOUT = 90

# --- [ ЦЕНТР МОНИТОРИНГА ] ---
def send_log(text):
    try:
        bot.send_message(LOG_CHAT_ID, f"📡 <b>[LOG]:</b> {text}", parse_mode='HTML')
    except Exception as e:
        print(f"Ошибка логирования: {e}")

# --- [ УМНЫЙ ПОИСК ФОТО В АРХИВЕ ] ---
def find_constellation_photo(name_latin):
    """Ищет фото в папке, игнорируя регистр, пробелы и расширение (.jpg/.png)"""
    if not os.path.exists(PHOTO_SPACE_DIR):
        return None
    
    # Очищаем целевое имя: в нижний регистр и убираем лишние пробелы
    target = name_latin.lower().strip()
    
    # Список файлов в папке
    files = os.listdir(PHOTO_SPACE_DIR)
    
    for file in files:
        # Разбиваем на имя и расширение
        f_name, f_ext = os.path.splitext(file)
        
        # Сравниваем имя (без учета регистра и пробелов)
        if f_name.lower().strip() == target and f_ext.lower() in ['.jpg', '.png', '.jpeg']:
            return os.path.join(PHOTO_SPACE_DIR, file)
            
    return None

# --- [ ИНСТРУКЦИЯ (ОПИСАНИЕ ВСЕХ СИСТЕМ) ] ---
def get_instruction_text():
    return (
        "📜 <b>БОРТОВОЙ УСТАВ ИССЛЕДОВАТЕЛЯ</b>\n"
        "───────────────────────\n\n"
        "Пилот, перед тобой руководство по эксплуатации систем «Марти»:\n\n"
        "📡 <b>СИСТЕМА «МОЕ НЕБО»</b>\n"
        "Я запрашиваю данные со спутников и на основе твоей геолокации рисую карту звезд твоего сектора.\n"
        "👉 <i>Результат: Карта звездного неба и +15 XP.</i>\n\n"
        "📸 <b>МОДУЛЬ «ГЛАЗА МАРТИ»</b>\n"
        "Пришли мне фото любого небесного объекта или рисунка. Мои сенсоры проанализируют картинку и выдадут отчет.\n"
        "👉 <i>Результат: Анализ объекта и +10 XP.</i>\n\n"
        "🗂 <b>АРХИВ «ДОСЬЕ»</b>\n"
        "Под картой неба есть кнопка доступа к моим личным записям. Там хранятся снимки и факты, собранные вручную.\n\n"
        "🎖 <b>КАРЬЕРНАЯ ЛЕСТНИЦА (XP)</b>\n"
        "Твой ранг определяет уровень доступа к данным:\n"
        "• <b>Кадет</b> (0-100 XP)\n"
        "• <b>Исследователь</b> (101-500 XP)\n"
        "• <b>Навигатор</b> (501-1500 XP)\n"
        "• <b>Адмирал Галактики</b> (1500+ XP) 👑\n\n"
        "🖼 <b>КНОПКА «FULL HD»</b>\n"
        "Запроси файл в высоком разрешении, чтобы рассмотреть детали без потери качества."
    )

# --- [ ПРИВЕТСТВИЕ ] ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("📡📡📡 МОЕ НЕБО", request_location=True))
    markup.add(KeyboardButton("❓❓ ИНСТРУКЦИЯ ПИЛОТА"))
    
    welcome_text = (
        f"🛰️ <b>Связь установлена! Рад видеть тебя в рубке, пилот {message.from_user.first_name}!</b>\n\n"
        "Я — <b>Марти</b>, твой навигатор. 🐾\n"
        "Все системы прогреты. Мы готовы сканировать новые сектора или изучать твои снимки. Что прикажешь?"
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup, parse_mode='HTML')

# --- [ АНАЛИЗ ФОТО ] ---
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    
    status_msg = bot.reply_to(message, "📸 <b>Настраиваю оптику... Сверяю данные с каталогами...</b>", parse_mode='HTML')
    
    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        description = analyze_image(downloaded_file)
        
        add_xp(user_id, 10, user_name)
        new_xp = get_user_stats(user_id)
        
        caption = (
            f"🔍 <b>ОТЧЕТ ШТУРМАНА:</b>\n\n"
            f"{description}\n"
            f"─────────────────────\n"
            f"📈 <b>Данные внесены в журнал!</b>\n"
            f"Зачислено: <b>+10 XP</b> (Всего: {new_xp})"
        )
        bot.edit_message_text(caption, message.chat.id, status_msg.message_id, parse_mode='Markdown')

    except Exception as e:
        send_log(f"🆘 Ошибка Vision: {e}")
        bot.edit_message_text("🛰️ <b>Внимание!</b> Не удалось распознать объект. Попробуй сделать более четкий снимок.", message.chat.id, status_msg.message_id)

# --- [ СКАНИРОВАНИЕ НЕБА ] ---
@bot.message_handler(content_types=['location'])
def handle_location(message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    
    status_msg = bot.send_message(message.chat.id, "🛰️ <b>Запрашиваю данные с орбиты... Вычисляю положение звезд...</b>", parse_mode='HTML')
    
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
            # УПЛОТНЕННАЯ КНОПКА СВЯЗИ
            markup.add(InlineKeyboardButton("📡 КАНАЛ ШТУРМАНА", url="https://t.me/Marty_Help_Bot?start=help"))
            
            caption = (
                f"✨ <b>СЕКТОР ПРОСКАНИРОВАН!</b>\n\n"
                f"Пилот <b>{user_name}</b>, прямо сейчас над тобой сияет <b>{target_name}</b>.\n"
                f"─────────────────────\n"
                f"🎖 <b>Статус:</b> {rank}\n"
                f"📈 <b>Опыт:</b> {current_xp} XP (+15)"
            )
            with open(result, 'rb') as photo:
                bot.send_photo(message.chat.id, photo, caption=caption, reply_markup=markup, parse_mode='HTML')
            
            bot.delete_message(message.chat.id, status_msg.message_id)
            send_log(f"✅ Успешное картографирование для {user_name}.")
        else:
            bot.edit_message_text(f"❌ <b>Ошибка навигации:</b> {err_msg}", message.chat.id, status_msg.message_id)

    except Exception as e:
        send_log(f"🆘 Ошибка генерации: {e}")
        bot.send_message(message.chat.id, "💥 <b>Системный сбой!</b> Штурман Марти временно потерял связь. Давай попробуем еще раз.")

# --- [ ДОСЬЕ С УМНЫМ ПОИСКОМ ФОТО ] ---
@bot.callback_query_handler(func=lambda call: call.data.startswith('wiki_'))
def callback_wiki(call):
    subject = call.data.replace('wiki_', '').strip()
    bot.answer_callback_query(call.id, "Извлекаю данные из архивов...")
    
    found_fact = next((item for item in CONSTELLATIONS if item['name_ru'].upper() == subject.upper()), None)
    
    if found_fact:
        text = (
            f"🌌 <b>БОРТОВОЕ ДОСЬЕ: {found_fact['name_ru'].upper()}</b>\n"
            f"───────────────────────\n\n"
            f"{found_fact['fact']}\n\n"
            f"<i>Данные проверены штурманом Марти.</i>"
        )
        
        # Использование функции умного поиска
        photo_path = find_constellation_photo(found_fact['name_latin'])
        
        if photo_path:
            with open(photo_path, 'rb') as photo:
                bot.send_photo(call.message.chat.id, photo, caption=text, parse_mode='HTML')
        else:
            bot.send_message(call.message.chat.id, text, parse_mode='HTML')
            send_log(f"⚠️ Фото для {found_fact['name_latin']} не найдено в {PHOTO_SPACE_DIR}")
    else:
        bot.send_message(call.message.chat.id, "⚠️ Данные об этом секторе отсутствуют.")

# --- [ ОБРАБОТКА ИНСТРУКЦИИ ] ---
@bot.message_handler(func=lambda message: message.text == "❓❓ ИНСТРУКЦИЯ ПИЛОТА")
def handle_instruction(message):
    bot.send_message(message.chat.id, get_instruction_text(), parse_mode='HTML')

# --- [ ВЫДАЧА ОРИГИНАЛА КАРТЫ ] ---
@bot.callback_query_handler(func=lambda call: call.data.startswith('orig_'))
def callback_orig(call):
    user_id = call.data.replace('orig_', '')
    bot.answer_callback_query(call.id, "Подготавливаю файл...")
    
    file_path = f"output/star_map_{user_id}.png"
    
    if os.path.exists(file_path):
        with open(file_path, 'rb') as doc:
            bot.send_document(call.message.chat.id, doc, caption="🚀 <b>Твой снимок в оригинальном качестве.</b>", parse_mode='HTML')
    else:
        bot.send_message(call.message.chat.id, "❌ Файл утерян. Попробуй сканировать небо заново.")

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
