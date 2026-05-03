import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telebot import apihelper
import os, time, concurrent.futures, random
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

# Настройка глубоких таймаутов для работы с тяжелыми изображениями
apihelper.CONNECT_TIMEOUT = 60
apihelper.READ_TIMEOUT = 90

bot = telebot.TeleBot(TELEGRAM_TOKEN, threaded=True)
wiki_wiki = wikipediaapi.Wikipedia(user_agent='MartySpaceBot/1.1', language='ru')

# Flask для поддержания жизни сервера на Render
app = Flask(__name__)
@app.route('/')
def keep_alive(): return "🛰️ Бортовой компьютер Марти работает в штатном режиме!"
def run_server(): app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

# --- [ БАЗА ЗНАНИЙ ПАТРУЛЯ ] ---
SPACE_FACTS = [
    "🔭 <b>Знаешь ли ты?</b> Свет от Солнца доходит до нас за 8 минут. Видя Солнце, мы всегда смотрим на 8 минут в прошлое.",
    "🌌 <b>Факт:</b> В нашей Галактике около 200 миллиардов звезд. Если бы ты считал их по одной в секунду, тебе понадобилось бы 6000 лет.",
    "🛰️ <b>На заметку:</b> На МКС космонавты видят 16 рассветов и закатов в сутки, так как станция облетает Землю за 90 минут.",
    "🌠 <b>Это интересно:</b> Большинство звезд, которые ты видишь, на самом деле двойные или даже тройные системы, вращающиеся друг вокруг друга.",
    "🪐 <b>Совет:</b> Сатурн — настолько легкая планета, что если бы существовал гигантский океан, он бы плавал на его поверхности, как поплавок.",
    "🍎 <b>Знание:</b> Гравитация на Луне в 6 раз слабее земной. Там ты смог бы прыгнуть выше своего роста без особых усилий."
]

# --- [ ПРИВЕТСТВИЕ: МАКСИМАЛЬНО ПОЛЕЗНОЕ ] ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("📡📡📡 МОЕ НЕБО", request_location=True))
    markup.add(KeyboardButton("❓❓ ИНСТРУКЦИЯ ПИЛОТА"))
    
    welcome_text = (
        f"🛰️ <b>Добро пожаловать в центр управления, {message.from_user.first_name}!</b>\n\n"
        "Я — <b>Марти</b>, твой персональный астрономический вычислитель. 🐾🎓\n\n"
        "<b>В чем моя уникальность?</b>\n"
        "Я не просто генерирую картинку. Я провожу сложнейший математический расчет: "
        "беру твои координаты, учитываю текущую секунду, наклон земной оси и положение "
        "планет в Солнечной системе. В итоге ты получаешь <b>персональный снимок неба</b>, "
        "который находится прямо над твоей головой в данный момент.\n\n"
        "🚀 <b>Готов увидеть свой сектор космоса?</b>\n"
        "Жми кнопку 📡 <b>«МОЕ НЕБО»</b>. Я мгновенно приступлю к расчетам!"
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup, parse_mode='HTML')

# --- [ ГИД: ДЛИННЫЙ И ПОЗНАВАТЕЛЬНЫЙ ] ---
@bot.message_handler(func=lambda message: message.text == "❓❓ ИНСТРУКЦИЯ ПИЛОТА")
def send_help(message):
    help_text = (
        "🧭 <b>РУКОВОДСТВО ПО ЧТЕНИЮ ЗВЕЗДНЫХ КАРТ</b>\n\n"
        "<b>1. Что такое Зенит?</b>\n"
        "Центр круга на моей карте — это небо прямо над твоей макушкой. Края круга — это твой горизонт. "
        "Если звезда нарисована сбоку, ищи ее ближе к горизонту.\n\n"
        "<b>2. Зачем нужна красная линия?</b>\n"
        "Это <b>Эклиптика</b>. Воображаемая линия, по которой 'ходят' Солнце, Луна и все планеты. "
        "Если ты хочешь найти Сатурн или Юпитер, ищи их строго вдоль этой линии.\n\n"
        "<b>3. Что такое Досье?</b>\n"
        "Я выбираю одно созвездие, которое лучше всего видно в твоем регионе, и готовлю на него справку: "
        "редкий снимок в высоком качестве и научные факты, которых нет в школьных учебниках.\n\n"
        "<b>4. Как получить лучший файл?</b>\n"
        "Telegram сильно сжимает фото. Чтобы рассмотреть каждую звездочку, используй кнопку 🖼️ <b>Оригинал</b>."
    )
    bot.send_message(message.chat.id, help_text, parse_mode='HTML')

# --- [ ГЕНЕРАЦИЯ С ИНТЕРЕСНЫМИ ФАКТАМИ ] ---
@bot.message_handler(content_types=['location'])
def handle_location(message):
    user_id = message.from_user.id
    try:
        loading_statuses = [
            "📡 <b>Сигнал получен!</b> Подключаюсь к базам данных NASA...",
            "🔭 <b>Настройка оптики...</b> Ищу созвездие-ориентир для тебя.",
            "📐 <b>Математический расчет...</b> Вычисляю высоту планет над горизонтом.",
            "🌌 <b>Прорисовка атмосферы...</b> Добавляю Млечный Путь и туманности.",
            "📸 <b>Финальная обработка...</b> Еще пара секунд, Командор!"
        ]

        loading_msg = bot.send_message(message.chat.id, loading_statuses[0], parse_mode='HTML')
        
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
                time.sleep(11) # Даем пользователю время прочитать совет
                if status_index < len(loading_statuses):
                    text = f"{loading_statuses[status_index]}\n\n{random.choice(SPACE_FACTS)}"
                    try:
                        bot.edit_message_text(text, message.chat.id, loading_msg.message_id, parse_mode='HTML')
                        status_index += 1
                    except: pass
            
            success, result, target_name, err_msg = future.result()

        bot.delete_message(message.chat.id, loading_msg.message_id)

        if success:
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton(f"🌌 Досье на {target_name}", callback_data=f"wiki_{target_name}"))
            markup.add(InlineKeyboardButton("🖼️ Оригинал (Full HD)", callback_data=f"orig_{user_id}"))
            
            caption = (
                f"✨ <b>Твоя персональная карта готова!</b>\n\n"
                f"🎯 <b>Твоя главная цель:</b> созвездие <b>{target_name}</b>.\n"
                f"Я выделил его розовым неоновым кругом. Именно оно сейчас — ярчайшее украшение твоего неба!"
            )
            
            with open(result, 'rb') as photo:
                bot.send_photo(message.chat.id, photo, caption=caption, reply_markup=markup, parse_mode='HTML', timeout=60)
        else:
            bot.send_message(message.chat.id, f"❌ <b>Ошибка систем навигации:</b> {result}")
            
    except Exception as e:
        bot.send_message(message.chat.id, f"🆘 <b>Космическое происшествие:</b> {str(e)}")

# --- [ ОБРАБОТЧИКИ КНОПОК ] ---
@bot.callback_query_handler(func=lambda call: call.data.startswith('orig_'))
def callback_original(call):
    user_id = call.data.replace('orig_', '')
    file_path = f"sky_{user_id}.jpg"
    if os.path.exists(file_path):
        bot.answer_callback_query(call.id, "Загружаю массив данных...")
        with open(file_path, 'rb') as doc:
            bot.send_document(call.message.chat.id, doc, caption="📂 <b>Твой личный звездный атлас.</b>", parse_mode='HTML')
    else:
        bot.answer_callback_query(call.id, "⚠️ Данные устарели, запроси новую карту.", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data.startswith('wiki_'))
def callback_wiki(call):
    subject = call.data.replace('wiki_', '').strip()
    bot.answer_callback_query(call.id, "Доступ к архивам разрешен...")
    
    found_fact = next((item for item in CONSTELLATIONS if item['name_ru'].upper() == subject.upper()), None)
            
    if found_fact:
        name_latin = found_fact['name_latin']
        base_url = f"https://raw.githubusercontent.com/fomichd-del/my-space-bots/main/photo_space/"
        
        valid_photo_data = None
        for ext in [".png", ".jpg", ".jpeg", ".PNG", ".JPG"]:
            try:
                res = requests.get(f"{base_url}{name_latin}{ext}".replace(" ", "%20"), timeout=5)
                if res.status_code == 200:
                    valid_photo_data = res.content
                    break
            except: continue
        
        text = f"🌌 <b>{found_fact['name_ru'].upper()} ({found_fact['name_latin']})</b>\n\n{found_fact['fact']}"
        
        if valid_photo_data:
            try:
                # --- [ ТЕХНОЛОГИЯ КРИСТАЛЬНОГО ШТАМПА ] ---
                base_img = Image.open(io.BytesIO(valid_photo_data)).convert("RGBA")
                if os.path.exists("watermark.png"):
                    stamp = Image.open("watermark.png").convert("RGBA")
                    
                    pix = stamp.load()
                    for y in range(stamp.height):
                        for x in range(stamp.width):
                            r, g, b, a = pix[x, y]
                            # Удаляем фон и принудительно перекрашиваем в чистый белый
                            if r > 220 and g > 220 and b > 220: pix[x, y] = (255, 255, 255, 0)
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

                bot.send_photo(call.message.chat.id, valid_photo_data, caption="⭐️ <b>Эксклюзивно для канала: Дневник юного космонавта</b>", parse_mode='HTML')
            except: pass
                
        bot.send_message(call.message.chat.id, text, parse_mode='HTML')
    else:
        bot.send_message(call.message.chat.id, "📡 Ошибка: Данные по этому сектору отсутствуют.")

if __name__ == "__main__":
    Thread(target=run_server).start()
    bot.remove_webhook()
    print("📡 [СИСТЕМА] Марти слушает эфир...")
    bot.polling(non_stop=True, interval=2, timeout=60)
