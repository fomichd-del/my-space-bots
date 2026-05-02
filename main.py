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
from PIL import Image, ImageFilter, ImageOps, ImageEnhance

# --- [ ИМПОРТ БАЗЫ КОСМИЧЕСКОГО ПАТРУЛЯ ] ---
from base_fact_star import CONSTELLATIONS

# --- [ КОСМИЧЕСКИЕ НАСТРОЙКИ ] ---
DATA_DIR = os.path.join(os.getcwd(), "data")
os.environ["STARPLOT_CACHE_DIR"] = DATA_DIR
os.environ["SOLAR_SYSTEM_EPHEMERIS"] = os.path.join(DATA_DIR, "de421.bsp")

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

# Настройка таймаутов для тяжелых Full HD файлов
apihelper.CONNECT_TIMEOUT = 60
apihelper.READ_TIMEOUT = 90

bot = telebot.TeleBot(TELEGRAM_TOKEN, threaded=True)
wiki_wiki = wikipediaapi.Wikipedia(user_agent='MartySpaceBot/1.1', language='ru')

# Flask для поддержания жизни сервера на Render
app = Flask(__name__)
@app.route('/')
def keep_alive(): return "🛰️ Система Марти-1.1 в рабочем режиме!"
def run_server(): app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

# --- [ БАЗА ПОЗНАВАТЕЛЬНЫХ СОВЕТОВ ПРИ ЗАГРУЗКЕ ] ---
SPACE_TIPS = [
    "🔭 <b>Знаешь ли ты?</b> Свет от Солнца идет до Земли 8 минут и 20 секунд.",
    "🌌 <b>Совет:</b> Чтобы лучше видеть созвездия, дай глазам привыкнуть к темноте 15 минут.",
    "🛰️ <b>Факт:</b> На МКС закат и рассвет происходят каждые 45 минут!",
    "🌠 <b>Знаешь ли ты?</b> Созвездия на карте — это проекция, на самом деле звезды в них разделяют сотни световых лет.",
    "🍎 <b>Факт:</b> В космосе нет гравитации, поэтому пламя свечи там будет идеально круглым и синим.",
    "🪐 <b>Совет:</b> Самая яркая «звезда» на вечернем небе часто оказывается планетой Венерой или Юпитером."
]

# --- [ ПРИВЕТСТВИЕ ] ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("📡📡 МОЕ НЕБО", request_location=True))
    markup.add(KeyboardButton("❓ ГИД ПО БОТУ"))
    
    welcome_text = (
        f"🛰️ <b>Добро пожаловать на борт, {message.from_user.first_name}!</b>\n\n"
        "Я — <b>Марти</b>, твой персональный астрономический вычислитель. 🐾🎓\n\n"
        "Я не просто присылаю картинку. Я рассчитываю реальное положение небесных тел "
        "именно для твоих координат, учитывая время, дату и даже кривизну горизонта.\n\n"
        "🌟 <b>С чего начнем наше путешествие?</b>\n"
        "Жми <b>«📡 МОЕ НЕБО»</b>, и я проявлю для тебя текущую карту звезд над твоей головой!"
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup, parse_mode='HTML')

# --- [ ГИД ПО БОТУ ] ---
@bot.message_handler(func=lambda message: message.text == "❓ ГИД ПО БОТУ")
def send_help(message):
    help_text = (
        "🧭 <b>БОРТОВОЙ ЖУРНАЛ ИНСТРУКЦИЙ</b>\n\n"
        "<b>1. Точность расчетов:</b>\n"
        "Карта строится в реальном времени. Центр круга — это точка ровно над тобой (зенит).\n\n"
        "<b>2. Линии на карте:</b>\n"
        "🔴 Красная линия (Эклиптика) — это 'дорога', по которой движутся Солнце и планеты.\n\n"
        "<b>3. Досье Патруля:</b>\n"
        "Под картой всегда есть кнопка 🌌 <b>Досье</b>. Там я храню редкие фото и факты о созвездии, которое я выбрал для тебя целью на сегодня.\n\n"
        "<b>4. Качество:</b>\n"
        "Кнопка 🖼️ <b>Скачать оригинал</b> пришлет тебе файл без сжатия Telegram, пригодный для печати."
    )
    bot.send_message(message.chat.id, help_text, parse_mode='HTML')

# --- [ ГЕНЕРАЦИЯ С СОВЕТАМИ ] ---
@bot.message_handler(content_types=['location'])
def handle_location(message):
    user_id = message.from_user.id
    try:
        loading_statuses = [
            "📡 <b>Связь установлена!</b> Запрашиваю данные со спутников...",
            "🔭 <b>Настройка линз...</b> Рассчитываю положение планет.",
            "📐 <b>Коррекция времени...</b> Синхронизирую часы с атомным эталоном.",
            "🌌 <b>Прорисовка Млечного Пути...</b> Добавляю туманности.",
            "📸 <b>Финальная проявка...</b> Наношу разметку эклиптики."
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
                time.sleep(12) # Интервал обновления статуса
                if status_index < len(loading_statuses):
                    text = f"{loading_statuses[status_index]}\n\n{random.choice(SPACE_TIPS)}"
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
                f"✨ <b>Твоя карта готова, Командор!</b>\n\n"
                f"🎯 <b>Цель-ориентир:</b> созвездие <b>{target_name}</b>.\n"
                f"Оно отмечено розовым неоновым кругом. Желаю чистого неба!"
            )
            
            with open(result, 'rb') as photo:
                bot.send_photo(message.chat.id, photo, caption=caption, reply_markup=markup, parse_mode='HTML', timeout=60)
        else:
            bot.send_message(message.chat.id, f"❌ <b>Сбой систем:</b> {result}")
            
    except Exception as e:
        bot.send_message(message.chat.id, f"🆘 <b>Авария на мостике:</b> {str(e)}")

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
        bot.answer_callback_query(call.id, "⚠️ Данные устарели.", show_alert=True)

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
                # --- [ ТЕХНОЛОГИЯ НЕОНОВОГО ШТАМПА v27 ] ---
                base_img = Image.open(io.BytesIO(valid_photo_data)).convert("RGBA")
                if os.path.exists("watermark.png"):
                    stamp = Image.open("watermark.png").convert("RGBA")
                    
                    # 1. Жесткая чистка фона и перекрашивание в белый
                    pix = stamp.load()
                    for y in range(stamp.height):
                        for x in range(stamp.width):
                            r, g, b, a = pix[x, y]
                            if r > 210 and g > 210 and b > 210: pix[x, y] = (255, 255, 255, 0)
                            elif a > 0: pix[x, y] = (255, 255, 255, a)

                    # 2. Создание неонового свечения (Розовый/Пурпурный)
                    neon_color = (255, 0, 255) # RGB Розовый
                    glow = ImageOps.colorize(stamp.convert("L"), (0,0,0), neon_color)
                    glow = glow.filter(ImageFilter.GaussianBlur(radius=7)) # Мягкое свечение
                    
                    # 3. Наложение белого ядра на свечение
                    neon_final = Image.alpha_composite(glow.convert("RGBA"), stamp)

                    # Масштабирование (12%)
                    sw = int(base_img.width * 0.12)
                    sh = int(stamp.height * (sw / stamp.width))
                    neon_final = neon_final.resize((sw, sh), Image.Resampling.LANCZOS)

                    # Позиция (нижний правый угол)
                    pos = (base_img.width - sw - int(base_img.width * 0.02), 
                           base_img.height - sh - int(base_img.height * 0.02))

                    base_img.paste(neon_final, pos, mask=neon_final)
                    
                    buf = io.BytesIO()
                    base_img.convert("RGB").save(buf, format='JPEG', quality=95)
                    valid_photo_data = buf.getvalue()

                bot.send_photo(call.message.chat.id, valid_photo_data, caption="⭐️ <b>Эксклюзивно для: Дневник юного космонавта</b>", parse_mode='HTML')
            except: pass
                
        bot.send_message(call.message.chat.id, text, parse_mode='HTML')
    else:
        bot.send_message(call.message.chat.id, "📡 Данные по этому сектору отсутствуют.")

if __name__ == "__main__":
    Thread(target=run_server).start()
    bot.remove_webhook()
    print("📡 [СИСТЕМА] Марти слушает эфир...")
    bot.polling(non_stop=True, interval=2, timeout=60)
