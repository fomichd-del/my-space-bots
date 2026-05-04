import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telebot import apihelper
import os, time, concurrent.futures, random, io
from pathlib import Path
from flask import Flask
from threading import Thread, Timer 
import requests
from PIL import Image

# --- [ ИМПОРТ МОДУЛЕЙ КОРАБЛЯ ] ---
from draw_map import generate_star_map
from database import init_db, add_xp, get_user_stats, get_rank_name
from base_fact_star import CONSTELLATIONS

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
        except: pass
        
        def cleanup_original():
            try:
                if os.path.exists(res_png): 
                    os.remove(res_png)
                    print(f"🧹 [ОЧИСТКА]: Full HD файл {res_png} уничтожен.")
            except: pass
            
        Timer(900.0, cleanup_original).start()
    else:
        bot.edit_message_text(f"❌ <b>Сбой навигации:</b> {err_msg}", message.chat.id, status_msg.message_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith('wiki_'))
def callback_wiki(call):
    subject = call.data.replace('wiki_', '').strip()
    found = next((item for item in CONSTELLATIONS if item['name_ru'].upper() == subject.upper()), None)
    
    if found:
        name_latin = found['name_latin']
        base_url = f"https://raw.githubusercontent.com/fomichd-del/my-space-bots/main/photo_space/"
        text = f"🌌 <b>БОРТОВОЕ ДОСЬЕ: {found['name_ru'].upper()}</b>\n\n{found['fact']}"
        
        valid_photo_data = None
        for ext in [".png", ".jpg", ".jpeg", ".PNG", ".JPG"]:
            try:
                res = requests.get(f"{base_url}{name_latin}{ext}".replace(" ", "%20"), timeout=5)
                if res.status_code == 200:
                    valid_photo_data = res.content
                    break
            except: continue

        if valid_photo_data:
            try:
                base_img = Image.open(io.BytesIO(valid_photo_data)).convert("RGBA")
                if os.path.exists("watermark.png"):
                    stamp = Image.open("watermark.png").convert("RGBA")
                    pix = stamp.load()
                    for y in range(stamp.height):
                        for x in range(stamp.width):
                            r, g, b, a = pix[x, y]
                            if r > 210 and g > 210 and b > 210: pix[x, y] = (255, 255, 255, 0)
                            elif a > 0: pix[x, y] = (255, 255, 255, a)
                    sw = int(base_img.width * 0.12)
                    sh = int(stamp.height * (sw / stamp.width))
                    stamp = stamp.resize((sw, sh), Image.Resampling.LANCZOS)
                    pos = (base_img.width - sw - int(base_img.width * 0.02), 
                           base_img.height - sh - int(base_img.height * 0.02))
                    base_img.paste(stamp, pos, mask=stamp)
                    
                    buf = io.BytesIO()
                    base_img.convert("RGB").save(buf, format='JPEG', quality=95)
                    valid_photo_data = buf.getvalue()

                bot.send_photo(call.message.chat.id, valid_photo_data, caption=text, parse_mode='HTML')
            except:
                bot.send_message(call.message.chat.id, text, parse_mode='HTML')
        else:
            bot.send_message(call.message.chat.id, text, parse_mode='HTML')

@bot.callback_query_handler(func=lambda call: call.data.startswith('orig_'))
def callback_orig(call):
    f_path = OUTPUT_DIR / f"fin_{call.data.replace('orig_', '')}.png"
    if f_path.exists():
        with open(f_path, 'rb') as doc: 
            bot.send_document(call.message.chat.id, doc, caption="🚀 <b>Full HD оригинал вашего сектора.</b>", parse_mode='HTML')
    else:
        bot.answer_callback_query(call.id, "❌ Файл утерян (время хранения 15 мин истекло).", show_alert=True)

app = Flask(__name__)
@app.route('/')
def home(): return "<h1>Navigator Marty: Online</h1>"

if __name__ == "__main__":
    init_db()
    
    # 1. Запуск Flask
    Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000))), daemon=True).start()
    
    # 2. Запуск Навигатора
    print("🚀 Корабль Навигатор вышел на орбиту. Ожидаю команды...")
    
    # КРИТИЧЕСКИЙ ФИКС ДЛЯ ОШИБКИ 409:
    bot.remove_webhook()
    time.sleep(1) # Даем Telegram время «забыть» старое соединение
    
    bot.infinity_polling(skip_pending=True)
