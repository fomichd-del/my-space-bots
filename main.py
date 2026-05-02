import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telebot import apihelper
import os, time, concurrent.futures
from draw_map import generate_star_map
from flask import Flask
from threading import Thread
import wikipediaapi
import requests
import io
from PIL import Image

# --- [ ИМПОРТ БАЗЫ КОСМИЧЕСКОГО ПАТРУЛЯ ] ---
from base_fact_star import CONSTELLATIONS

# --- [ КОСМИЧЕСКИЕ НАСТРОЙКИ ] ---
DATA_DIR = os.path.join(os.getcwd(), "data")
os.environ["STARPLOT_CACHE_DIR"] = DATA_DIR
os.environ["SOLAR_SYSTEM_EPHEMERIS"] = os.path.join(DATA_DIR, "de421.bsp")

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

# --- [ ФИКС ТАЙМАУТОВ ] ---
apihelper.CONNECT_TIMEOUT = 60
apihelper.READ_TIMEOUT = 90

bot = telebot.TeleBot(TELEGRAM_TOKEN, threaded=True)

# Википедия
wiki_wiki = wikipediaapi.Wikipedia(user_agent='MartySpaceBot/1.1', language='ru')

# Flask для Render
app = Flask(__name__)
@app.route('/')
def keep_alive(): return "Марти Астроном в эфире! 🛰️"
def run_server(): app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

# --- [ ПРИВЕТСТВИЕ ] ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("📡 Мое небо", request_location=True))
    markup.add(KeyboardButton("❓ Как это работает?"))
    
    welcome_text = (
        f"Привет, {message.from_user.first_name}! 🐾 Я — <b>Марти Астроном</b> 🎓\n\n"
        "Я умею превращать твои координаты в <b>точную карту звездного неба</b>.\n\n"
        "📍 Нажми <b>«📡 Мое небо»</b>, чтобы отправить геолокацию."
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup, parse_mode='HTML')

# --- [ ИНСТРУКЦИЯ ] ---
@bot.message_handler(func=lambda message: message.text == "❓ Как это работает?")
def send_help(message):
    help_text = (
        "🧭 <b>ГИД ПО ТВОЕМУ ЛИЧНОМУ КОСМОСУ</b>\n\n"
        "<b>1. Что на карте?</b>\n"
        "Центр круга — это небо прямо над твоей головой.\n\n"
        "<b>2. Линии:</b>\n"
        "🔴 <b>Красная линия</b> — эклиптика (путь Солнца).\n\n"
        "<b>3. Досье:</b>\n"
        "Жми кнопку под картой для получения фактов о цели."
    )
    bot.send_message(message.chat.id, help_text, parse_mode='HTML')

# --- [ ЛОГИКА ОЖИДАНИЯ И ГЕНЕРАЦИЯ ] ---
@bot.message_handler(content_types=['location'])
def handle_location(message):
    user_id = message.from_user.id
    try:
        statuses = [
            "🛰 <b>Локация принята!</b> Связываюсь с серверами...",
            "🔭 <b>Навожу линзы...</b> Ищу созвездие-цель.",
            "📐 <b>Считаю время...</b>",
            "🌌 <b>Рисую полотно...</b>",
            "📸 <b>Проявляю снимок...</b> Еще минутку!"
        ]

        loading_msg = bot.send_message(message.chat.id, statuses[0], parse_mode='HTML')
        
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(
                generate_star_map, 
                message.location.latitude, 
                message.location.longitude, 
                message.from_user.first_name, 
                user_id
            )
            
            status_index = 1
            while not future.done():
                time.sleep(11)
                if status_index < len(statuses):
                    try:
                        bot.edit_message_text(statuses[status_index], message.chat.id, loading_msg.message_id, parse_mode='HTML')
                        status_index += 1
                    except: pass
            
            success, result, target_name, err_msg = future.result()

        bot.delete_message(message.chat.id, loading_msg.message_id)

        if success:
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton(f"🌌 Досье на {target_name}", callback_data=f"wiki_{target_name}"))
            markup.add(InlineKeyboardButton("🖼️ Скачать оригинал", callback_data=f"orig_{user_id}"))
            
            caption = f"✨ <b>Твоя карта готова!</b>\n\n🎯 <b>Твоя цель:</b> {target_name}."
            
            with open(result, 'rb') as photo:
                bot.send_photo(message.chat.id, photo, caption=caption, reply_markup=markup, parse_mode='HTML', timeout=60)
        else:
            bot.send_message(message.chat.id, f"❌ Ошибка: {result}")
            
    except Exception as e:
        bot.send_message(message.chat.id, f"🆘 Ошибка: {str(e)}")

# --- [ ОБРАБОТЧИКИ КНОПОК ] ---
@bot.callback_query_handler(func=lambda call: call.data.startswith('orig_'))
def callback_original(call):
    user_id = call.data.replace('orig_', '')
    file_path = f"sky_{user_id}.jpg"
    if os.path.exists(file_path):
        with open(file_path, 'rb') as doc:
            bot.send_document(call.message.chat.id, doc, caption="📂 Твой атлас.", parse_mode='HTML')
    else:
        bot.answer_callback_query(call.id, "⚠️ Файл удален.", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data.startswith('wiki_'))
def callback_wiki(call):
    subject = call.data.replace('wiki_', '').strip()
    bot.answer_callback_query(call.id, "Запрашиваю данные Патруля...")
    
    found_fact = next((item for item in CONSTELLATIONS if item['name_ru'].upper() == subject.upper()), None)
            
    if found_fact:
        name_latin = found_fact['name_latin']
        base_url = f"https://raw.githubusercontent.com/fomichd-del/my-space-bots/main/photo_space/"
        
        formats = [".png", ".jpg", ".jpeg", ".PNG", ".JPG"] 
        name_variants = [name_latin, name_latin.title(), name_latin.lower()]
        
        valid_photo_data = None
        for variant in name_variants:
            for ext in formats:
                try:
                    response = requests.get(f"{base_url}{variant}{ext}".replace(" ", "%20"), timeout=5)
                    if response.status_code == 200:
                        valid_photo_data = response.content
                        break
                except: continue
            if valid_photo_data: break
        
        text = f"🌌 <b>{found_fact['name_ru'].upper()}</b>\n\n{found_fact['fact']}"
        
        if valid_photo_data:
            try:
                # --- [ УЛУЧШЕННЫЙ ШТАМП: ПРЯМАЯ КОРРЕКЦИЯ ЦВЕТА ] ---
                base_img = Image.open(io.BytesIO(valid_photo_data)).convert("RGBA")
                if os.path.exists("watermark.png"):
                    stamp_img = Image.open("watermark.png").convert("RGBA")

                    # Очистка и перекрашивание
                    pixels = stamp_img.load()
                    for y in range(stamp_img.height):
                        for x in range(stamp_img.width):
                            r, g, b, a = pixels[x, y]
                            # Если пиксель светлый (фон) - в прозрачность
                            if r > 220 and g > 220 and b > 220:
                                pixels[x, y] = (255, 255, 255, 0)
                            # Если пиксель имеет цвет (логотип) - в чистый белый с сохранением прозрачности
                            elif a > 0:
                                pixels[x, y] = (255, 255, 255, a)

                    # Масштабирование (12% от ширины)
                    scale = (base_img.width * 0.12) / stamp_img.width
                    stamp_img = stamp_img.resize((int(stamp_img.width * scale), int(stamp_img.height * scale)), Image.Resampling.LANCZOS)

                    # Позиция (нижний правый угол)
                    pos = (base_img.width - stamp_img.width - int(base_img.width * 0.02), 
                           base_img.height - stamp_img.height - int(base_img.height * 0.02))

                    base_img.paste(stamp_img, pos, mask=stamp_img)
                    
                    output = io.BytesIO()
                    base_img.convert("RGB").save(output, format='JPEG', quality=95)
                    valid_photo_data = output.getvalue()

                bot.send_photo(call.message.chat.id, valid_photo_data, caption="⭐️ Канал: <b>Дневник юного космонавта</b>", parse_mode='HTML')
            except: pass
                
        bot.send_message(call.message.chat.id, text, parse_mode='HTML')
    else:
        bot.send_message(call.message.chat.id, "📡 Данные не найдены.")

if __name__ == "__main__":
    Thread(target=run_server).start()
    bot.remove_webhook()
    bot.polling(non_stop=True, interval=2, timeout=60)
