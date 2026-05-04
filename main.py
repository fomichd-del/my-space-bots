import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telebot import apihelper
import os, time, concurrent.futures, random
from pathlib import Path
from flask import Flask
from threading import Thread, Timer 
from google import genai 

# --- [ ИМПОРТ МОДУЛЕЙ КОРАБЛЯ ] ---
from draw_map import generate_star_map
from database import init_db, add_xp, get_user_stats, get_rank_name
from base_fact_star import CONSTELLATIONS
from vision_module import analyze_image 
# ВАЖНО: Мы больше не импортируем handle_text_logic! Мы импортируем только команду запуска.

# --- [ КОНФИГУРАЦИЯ ПУТЕЙ ] ---
# ВАЖНО: Используется ТОЛЬКО токен основного бота (Навигатора)
TOKEN = os.getenv('TELEGRAM_TOKEN')
LOG_CHAT_ID = "-1003756164148"
BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
PHOTO_SPACE_DIR = BASE_DIR / "photo_space"
OUTPUT_DIR.mkdir(exist_ok=True)

bot = telebot.TeleBot(TOKEN, threaded=True)
apihelper.CONNECT_TIMEOUT = 60
apihelper.READ_TIMEOUT = 90

# --- [ АТМОСФЕРНЫЕ ФАКТЫ ДЛЯ ЭКРАНА ЗАГРУЗКИ ] ---
SPACE_FACTS = [
    "🔭 <b>Юстировка зеркал...</b> Собираю фотоны, летевшие к нам миллиарды лет.",
    "🌌 <b>Факт:</b> Звезды, которые ты видишь — это «эхо» прошлого.",
    "🛸 <b>Сектор сканирования...</b> Ищу неопознанные сигналы в твоем квадранте.",
    "🛰️ <b>Синхронизация...</b> Подключаюсь к сети дальней связи Deep Space Network.",
    "🪐 <b>Знание — сила:</b> Плотность Сатурна меньше плотности воды. Он бы плавал!",
    "🌠 <b>Внимание:</b> Каждую секунду сквозь тебя пролетают триллионы нейтрино."
]

def get_instruction_text():
    return (
        "🚀 <b>БОРТОВОЙ ЖУРНАЛ КРЕЙСЕРА «МАРТИ»</b>\n"
        "───────────────────────\n"
        "Пилот, добро пожаловать! Я — Навигатор. Вот как работают наши системы:\n\n"
        "📡 <b>СИСТЕМА «МОЕ НЕБО»</b>\n"
        "Отправь свою геолокацию, и я рассчитаю положение звезд.\n"
        "🎁 <i>Награда: +15 XP.</i>\n\n"
        "🎖️ <b>ТВОЯ КАРЬЕРА (РАНГИ):</b>\n"
        "• <b>Кадет</b> (0-100 XP)\n"
        "• <b>Исследователь</b> (101-300 XP)\n"
        "• <b>Навигатор</b> (301-600 XP)\n"
        "• <b>Командор</b> (601+ XP)\n\n"
        "🤖 <b>ОБЩЕНИЕ И ПОМОЩЬ:</b>\n"
        "Для разговоров с бортовым ИИ перейди на выделенный канал связи: @Marty_Help_Bot"
    )

@bot.message_handler(func=lambda m: True, content_types=['text'])
def unified_text_handler(message):
    if message.text == "❓❓ ИНСТРУКЦИЯ ПИЛОТА":
        bot.send_message(message.chat.id, get_instruction_text(), parse_mode='HTML')
    elif message.text == "/start":
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(KeyboardButton("📡📡📡 МОЕ НЕБО", request_location=True))
        markup.add(KeyboardButton("❓❓ ИНСТРУКЦИЯ ПИЛОТА"))
        
        welcome = (
            f"🛰️ <b>Системы инициализированы!</b>\n"
            f"Рад видеть тебя в рубке, пилот <b>{message.from_user.first_name}</b>!\n\n"
            f"Я готов к прыжку. Выбирай протокол на панели управления ниже. 🐾"
        )
        bot.send_message(message.chat.id, welcome, reply_markup=markup, parse_mode='HTML')
    else:
        # Навигатор больше не пытается отвечать за Марти. Он вежливо направляет пользователя.
        bot.send_message(message.chat.id, "🛰️ Я — Навигационный модуль. Для общения переключись на канал Ученого Пса Марти: @Marty_Help_Bot")

@bot.message_handler(content_types=['location'])
def handle_location(message):
    user_id, user_name = message.from_user.id, message.from_user.first_name
    status_msg = bot.send_message(message.chat.id, "🚀 <b>Начинаю прогрев варп-двигателя...</b>", parse_mode='HTML')
    
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(generate_star_map, message.location.latitude, message.location.longitude, user_name, user_id)
        while not future.done():
            time.sleep(10)
            if not future.done():
                fact = random.choice(SPACE_FACTS)
                try: bot.edit_message_text(f"🛰️ <b>Идет сканирование горизонта...</b>\n\n{fact}", message.chat.id, status_msg.message_id, parse_mode='HTML')
                except: pass
        success, res_jpg, res_png, target_name, err_msg = future.result()

    if success:
        add_xp(user_id, 15, user_name)
        stats = get_user_stats(user_id)
        rank = get_rank_name(stats)
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton(f"🌌 Досье на {target_name}", callback_data=f"wiki_{target_name}"))
        markup.add(InlineKeyboardButton("🖼️ Скачать в Full HD", callback_data=f"orig_{user_id}"))
        markup.add(InlineKeyboardButton("🤖 Обсудить с Марти-Ученым", url="https://t.me/Marty_Help_Bot?start=help"))
        
        caption = (
            f"✨ <b>ОБЪЕКТ ОБНАРУЖЕН!</b>\n\n"
            f"Пилот <b>{user_name}</b>, над твоими координатами доминирует <b>{target_name}</b>.\n"
            f"─────────────────────\n"
            f"🎖️ <b>Твой статус:</b> {rank}\n"
            f"📈 <b>Прогресс:</b> {stats} XP (+15 за навигацию)"
        )
        with open(res_jpg, 'rb') as ph:
            bot.send_photo(message.chat.id, ph, caption=caption, reply_markup=markup, parse_mode='HTML')
        bot.delete_message(message.chat.id, status_msg.message_id)

        try:
            if os.path.exists(res_jpg): os.remove(res_jpg)
        except Exception as e: 
            print(f"Ошибка удаления JPG: {e}")
        
        def cleanup_original():
            try:
                if os.path.exists(res_png): 
                    os.remove(res_png)
                    print(f"🧹 [ОЧИСТКА]: Full HD файл {res_png} уничтожен по таймауту.")
            except: pass
            
        Timer(900.0, cleanup_original).start()

    else:
        bot.edit_message_text(f"❌ <b>Сбой навигации:</b> {err_msg}", message.chat.id, status_msg.message_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith('wiki_'))
def callback_wiki(call):
    subject = call.data.replace('wiki_', '').strip()
    found = next((item for item in CONSTELLATIONS if item['name_ru'].upper() == subject.upper()), None)
    if found:
        text = f"🌌 <b>БОРТОВОЕ ДОСЬЕ: {found['name_ru'].upper()}</b>\n\n{found['fact']}"
        bot.send_message(call.message.chat.id, text, parse_mode='HTML')

@bot.callback_query_handler(func=lambda call: call.data.startswith('orig_'))
def callback_orig(call):
    f_path = OUTPUT_DIR / f"fin_{call.data.replace('orig_', '')}.png"
    if f_path.exists():
        with open(f_path, 'rb') as doc: bot.send_document(call.message.chat.id, doc, caption="🚀 Full HD оригинал.")
    else:
        bot.answer_callback_query(call.id, "❌ Файл утерян в гиперпространстве (время хранения истекло).", show_alert=True)

app = Flask(__name__)
@app.route('/')
def home(): return "<h1>Marty Navigator: Online</h1>"

if __name__ == "__main__":
    init_db()
    
    # 1. Запуск Flask (для Render)
    Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000))), daemon=True).start()
    
    # 2. Запуск Автономного Марти
    try:
        from marty_chat import start_marty_autonomous
        Thread(target=start_marty_autonomous, daemon=True).start()
    except Exception as e:
        print(f"❌ Системный сбой запуска Марти: {e}")
    
    # 3. Запуск Навигатора
    print("🚀 Корабль Навигатор вышел на орбиту. Ожидаю локации...")
    bot.remove_webhook()
    bot.infinity_polling(skip_pending=True)
