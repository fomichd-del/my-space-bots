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
PHOTO_SPACE_DIR = BASE_DIR / "photo_space"

OUTPUT_DIR.mkdir(exist_ok=True)

bot = telebot.TeleBot(TOKEN, threaded=True)
apihelper.CONNECT_TIMEOUT = 60
apihelper.READ_TIMEOUT = 90

# --- [ ЦЕНТР МОНИТОРИНГА ] ---
def send_log(text):
    try:
        bot.send_message(LOG_CHAT_ID, f"📡 <b>[LOG]:</b> {text}", parse_mode='HTML')
    except:
        print(f"Ошибка логирования: {text}")

# --- [ АТМОСФЕРНЫЕ ФАКТЫ ДЛЯ ЭКРАНА ЗАГРУЗКИ ] ---
SPACE_FACTS = [
    "🔭 <b>Юстировка зеркал...</b> Собираю древние фотоны, которые летели к нам миллиарды лет.",
    "🌌 <b>Факт дня:</b> Звезды, которые ты видишь сейчас — это «эхо» прошлого. Некоторых из них уже нет в живых.",
    "🛸 <b>Сектор сканирования...</b> Проверяю пространство на наличие неопознанных сигналов и аномалий.",
    "🛰️ <b>Синхронизация...</b> Подключаюсь к глубокой сети дальней космической связи NASA.",
    "🪐 <b>Знание — сила:</b> Сатурн настолько легкий, что плавал бы в твоем бассейне (если бы он был размером с планету).",
    "🌠 <b>Внимание:</b> Каждую секунду сквозь твое тело пролетают триллионы нейтрино, выпущенных далекими звездами.",
    "🌓 <b>Для кадетов:</b> На Луне ты мог бы поднять автомобиль одной рукой, а прыгнуть — выше дома!"
]

# --- [ УМНЫЙ ПОИСК ФОТО В АРХИВЕ ] ---
def find_constellation_photo(name_latin):
    """Ищет файл в photo_space. Учитывает пробелы и расширение .png"""
    if not PHOTO_SPACE_DIR.exists(): return None
    
    # Имя латынь (например, 'Canes Venatici')
    target_name = name_latin.strip()
    
    # Пробуем найти прямое совпадение с .png
    file_path = PHOTO_SPACE_DIR / f"{target_name}.png"
    if file_path.exists():
        return file_path
    
    # Если не нашли, пробуем регистронезависимый поиск
    for f in PHOTO_SPACE_DIR.iterdir():
        if f.stem.lower() == target_name.lower() and f.suffix.lower() == '.png':
            return f
            
    return None

# --- [ ПОЛНОЦЕННЫЙ БОРТОВОЙ УСТАВ ] ---
def get_instruction_text():
    return (
        "📜 <b>БОРТОВОЙ УСТАВ ИССЛЕДОВАТЕЛЯ</b>\n"
        "───────────────────────\n\n"
        "Пилот, добро пожаловать в рубку! Я — <b>Марти</b>, твой персональный штурман и эксперт по космосу. 🐾\n\n"
        "🛰️ <b>СИСТЕМА «МОЕ НЕБО»</b>\n"
        "Используй кнопку локации. Я мгновенно свяжусь с орбитальной группировкой и отрисую карту звезд прямо над твоей головой. "
        "Это не просто картинка, а точный математический снимок твоего горизонта.\n"
        "🎁 <i>Награда за вылет: +15 XP.</i>\n\n"
        "👁️ <b>НЕЙРО-СКАНЕР «ГЛАЗА МАРТИ»</b>\n"
        "Пришли фото неба из своего архива. Мои алгоритмы проанализируют снимок и найдут на нем созвездия или небесные тела.\n"
        "🎁 <i>Награда за анализ: +10 XP.</i>\n\n"
        "🎖️ <b>ТВОЯ КАРЬЕРА (СИСТЕМА РАНГОВ):</b>\n"
        "Копи опыт (XP), чтобы продвигаться по службе:\n"
        "• <b>Кадет</b> (0-100 XP) — ты только учишься видеть.\n"
        "• <b>Исследователь</b> (101-300 XP) — твое имя знают в обсерваториях.\n"
        "• <b>Навигатор</b> (301-600 XP) — ты ведешь нас сквозь тьму.\n"
        "• <b>Командор</b> (601-1000 XP) — легенда флота.\n"
        "• <b>Адмирал Галактики</b> (1000+) — ты и есть космос.\n\n"
        "🖼️ <b>КНОПКА «FULL HD»</b>\n"
        "После генерации карты я подготовлю для тебя тяжелый файл без сжатия — идеален для твоих обоев или печати."
    )

# --- [ ПРИВЕТСТВИЕ ] ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("📡📡📡 МОЕ НЕБО", request_location=True))
    markup.add(KeyboardButton("❓❓ ИНСТРУКЦИЯ ПИЛОТА"))
    
    welcome_text = (
        f"🛰️ <b>Системы прогреты! Рад видеть тебя в рубке, пилот {message.from_user.first_name}!</b>\n\n"
        "Я готов к расчету траекторий и поиску звездных досье. Куда направим наши телескопы сегодня? 🐾"
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup, parse_mode='HTML')

@bot.message_handler(func=lambda m: m.text == "❓❓ ИНСТРУКЦИЯ ПИЛОТА")
def handle_instruction(message):
    bot.send_message(message.chat.id, get_instruction_text(), parse_mode='HTML')

# --- [ ГЕНЕРАЦИЯ КАРТЫ С ОБРАТНОЙ СВЯЗЬЮ ] ---
@bot.message_handler(content_types=['location'])
def handle_location(message):
    user_id, user_name = message.from_user.id, message.from_user.first_name
    status_msg = bot.send_message(message.chat.id, "🚀 <b>Запуск систем навигации... Начинаю расчет сектора.</b>", parse_mode='HTML')
    
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(generate_star_map, message.location.latitude, message.location.longitude, user_name, user_id)
        
        start_w = time.time()
        while not future.done():
            time.sleep(11)
            if not future.done():
                elapsed = int(time.time() - start_w)
                fact = random.choice(SPACE_FACTS)
                try: 
                    bot.edit_message_text(f"⏳ <b>Идет обработка данных ({elapsed}с):</b>\n\n{fact}", message.chat.id, status_msg.message_id, parse_mode='HTML')
                except: pass

        success, res_jpg, res_png, target_name, err_msg = future.result()

    if success:
        add_xp(user_id, 15, user_name)
        current_xp = get_user_stats(user_id)
        rank = get_rank_name(current_xp)
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton(f"🌌 Открыть досье: {target_name}", callback_data=f"wiki_{target_name}"))
        markup.add(InlineKeyboardButton("🖼️ Получить Full HD", callback_data=f"orig_{user_id}"))
        markup.add(InlineKeyboardButton("🤖 Обсудить с Марти-Ученым", url="https://t.me/Marty_Help_Bot?start=help"))
        
        caption = (
            f"✨ <b>СЕКТОР ПРОСКАНИРОВАН!</b>\n\n"
            f"Пилот <b>{user_name}</b>, прямо сейчас над тобой доминирует <b>{target_name}</b>.\n"
            f"─────────────────────\n"
            f"🎖️ <b>Ранг:</b> {rank}\n"
            f"📈 <b>Опыт:</b> {current_xp} XP (добавлено +15)"
        )
        with open(res_jpg, 'rb') as ph:
            bot.send_photo(message.chat.id, ph, caption=caption, reply_markup=markup, parse_mode='HTML')
        bot.delete_message(message.chat.id, status_msg.message_id)
    else:
        bot.edit_message_text(f"❌ <b>Ошибка связи:</b> {err_msg}", message.chat.id, status_msg.message_id)

# --- [ ДОСЬЕ И ОРИГИНАЛЫ ] ---
@bot.callback_query_handler(func=lambda call: call.data.startswith('wiki_'))
def callback_wiki(call):
    subject = call.data.replace('wiki_', '').strip()
    bot.answer_callback_query(call.id, "Запрашиваю данные из архива...")
    
    # Ищем в CONSTELLATIONS по name_ru
    found = next((item for item in CONSTELLATIONS if item['name_ru'].upper() == subject.upper()), None)
    
    if found:
        text = f"🌌 <b>БОРТОВОЕ ДОСЬЕ: {found['name_ru'].upper()}</b>\n\n{found['fact']}"
        photo_p = find_constellation_photo(found.get('name_latin', ''))
        
        # Кнопка для общения под досье
        m_chat = InlineKeyboardMarkup().add(InlineKeyboardButton("🤖 Обсудить это с Марти", url="https://t.me/Marty_Help_Bot?start=channel_post"))
        
        if photo_p and photo_p.exists():
            with open(photo_p, 'rb') as ph:
                bot.send_photo(call.message.chat.id, ph, caption=text, reply_markup=m_chat, parse_mode='HTML')
        else:
            bot.send_message(call.message.chat.id, text, reply_markup=m_chat, parse_mode='HTML')
    else:
        bot.send_message(call.message.chat.id, "⚠️ Данные об этом секторе временно недоступны.")

@bot.callback_query_handler(func=lambda call: call.data.startswith('orig_'))
def callback_orig(call):
    user_id = call.data.replace('orig_', '')
    f_path = OUTPUT_DIR / f"fin_{user_id}.png"
    if f_path.exists():
        bot.answer_callback_query(call.id, "Передаю тяжелый файл...")
        with open(f_path, 'rb') as doc:
            bot.send_document(call.message.chat.id, doc, caption="🚀 <b>Full HD оригинал для твоих архивов.</b>", parse_mode='HTML')
    else:
        bot.answer_callback_query(call.id, "❌ Файл утерян в гиперпространстве.", show_alert=True)

# --- [ RUNNER ] ---
app = Flask(__name__)
@app.route('/')
def home(): return "Navigator Online"

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
