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

# Увеличиваем время ожидания для тяжелых карт
apihelper.CONNECT_TIMEOUT = 60
apihelper.READ_TIMEOUT = 90

bot = telebot.TeleBot(TELEGRAM_TOKEN, threaded=True)
wiki_wiki = wikipediaapi.Wikipedia(user_agent='MartySpaceBot/1.1', language='ru')

# Flask для поддержания жизни сервера на Render
app = Flask(__name__)
@app.route('/')
def keep_alive(): return "🛰️ Система Марти в рабочем режиме!"
def run_server(): app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

# --- [ БАЗА ЗНАНИЙ: ПОЗНАВАТЕЛЬНЫЕ ФАКТЫ ] ---
SPACE_FACTS = [
    "🔭 Свет от Солнца идет до Земли 8 минут и 20 секунд.",
    "🌌 На МКС рассвет происходит каждые 90 минут!",
    "🛰️ В космосе абсолютно тихо, так как там нет воздуха для передачи звука.",
    "🌠 Чёрная дыра — это объект с настолько сильной гравитацией, что его не может покинуть даже свет.",
    "🍎 Если бы Земля была размером с яблоко, МКС летала бы в 2 сантиметрах от её поверхности.",
    "🪐 В нашей Галактике (Млечный Путь) больше звезд, чем песчинок на всех пляжах Земли вместе взятых."
]

# --- [ ПРИВЕТСТВИЕ: ДЛИННОЕ И ОБЪЯСНЯЮЩЕЕ ] ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("📡📡📡 МОЕ НЕБО", request_location=True))
    markup.add(KeyboardButton("❓❓ ГИД ПО КОСМОСУ"))
    
    welcome_text = (
        f"🛰️ <b>Добро пожаловать на борт, {message.from_user.first_name}!</b>\n\n"
        "Я — <b>Марти</b>, твой персональный астрономический вычислитель. 🐾🎓\n\n"
        "Я не просто рисую красивые картинки. Мой алгоритм — это настоящий **космический навигатор**.\n\n"
        "Когда ты отправляешь мне свою геолокацию, я не ищу ее в Google Maps. Вместо этого "
        "я связываюсь с серверами точных эфемерид (математических баз данных движения небесных тел), "
        "рассчитываю, в какой точке Земли ты стоишь, учитываю текущую дату, прецессию и нутацию земной оси.\n\n"
        "На основе этих данных я строю **абсолютно точную** проекцию звезд, Млечного Пути и планет, "
        "которые ты можешь увидеть над собой в эту самую секунду.\n\n"
        "📍 <b>Как получить свою карту?</b>\n"
        "Просто нажми большую кнопку 📡📡📡 <b>«МОЕ НЕБО»</b> внизу. Я сразу начну расчеты."
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup, parse_mode='HTML')

# --- [ ИНСТРУКЦИЯ: ПОЛЕЗНАЯ И ОВЛЕГАЮЩАЯ ] ---
@bot.message_handler(func=lambda message: message.text == "❓❓ ГИД ПО КОСМОСУ")
def send_help(message):
    help_text = (
        "🧭 <b>КРАТКИЙ ИНСТРУКТАЖ ПО КОСМИЧЕСКОЙ НАВИГАЦИИ</b>\n\n"
        "<b>1. Что на карте?</b>\n"
        "Круг — это <b>весь небосвод</b>, который ты видишь над собой. Центр круга — это точка Зенита (небо прямо над твоей головой). Горизонт — это края круга.\n\n"
        "<b>2. Линии и символы:</b>\n"
        "🔴 <b>Красная линия (Эклиптика)</b> — это 'дорога', по которой движутся Солнце и все планеты.\n"
        "☀️/🌙 — я отметил Солнце и Луну специальными значками. Звезды Млечного Пути тоже на месте.\n\n"
        "<b>3. Досье Патруля:</b>\n"
        "Под каждой картой я добавляю кнопку «🌌 Досье». Нажми её, и я "
        "отправлю тебе уникальную картинку созвездия-цели и по-настоящему "
        "интересные, неочевидные факты из архивов Патруля. Попробуй!"
    )
    bot.send_message(message.chat.id, help_text, parse_mode='HTML')

# --- [ ГЕНЕРАЦИЯ С СОВЕТАМИ И ФАКТАМИ ] ---
@bot.message_handler(content_types=['location'])
def handle_location(message):
    user_id = message.from_user.id
    try:
        loading_statuses = [
            "🛰 <b>Локация принята!</b> Связываюсь с серверами Патруля...",
            "🔭 <b>Навожу линзы...</b> Ищу созвездие, которое станет твоей целью.",
            "📐 <b>Считаю время...</b> Настраиваю эклиптику.",
            "🌌 <b>Рисую полотно...</b> Добавляю Млечный Путь.",
            "📸 <b>Проявляю снимок...</b> Еще минутку, космонавт!"
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
                time.sleep(12)
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
            markup.add(InlineKeyboardButton("🖼️ Скачать оригинал", callback_data=f"orig_{user_id}"))
            
            caption = (
                f"✨ <b>Твой личный космос готов!</b>\n\n"
                f"🎯 <b>Цель-ориентир:</b> созвездие <b>{target_name}</b>.\n"
                f"Оно отмечено **розовым неоновым** кругом. Попробуй найти его сегодня на реальном небе!"
            )
            
            with open(result, 'rb') as photo:
                bot.send_photo(message.chat.id, photo, caption=caption, reply_markup=markup, parse_mode='HTML', timeout=60)
        else:
            bot.send_message(message.chat.id, f"❌ <b>Сбой систем:</b> {result}")
            
    except Exception as e:
        bot.send_message(message.chat.id, f"🆘 <b>Космическое происшествие:</b> {str(e)}")

# --- [ ОБРАБОТЧИКИ КНОПОК ] ---
@bot.callback_query_handler(func=lambda call: call.data.startswith('orig_'))
def callback_original(call):
    user_id = call.data.replace('orig_', '')
    file_path = f"sky_{user_id}.jpg"
    if os.path.exists(file_path):
        bot.answer_callback_query(call.id, "Загружаю Full HD файл...")
        with open(file_path, 'rb') as doc:
            bot.send_document(call.message.chat.id, doc, caption="📂 <b>Твой личный звездный атлас.</b>", parse_mode='HTML')
    else:
        bot.answer_callback_query(call.id, "⚠️ Данные устарели.", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data.startswith('wiki_'))
def callback_wiki(call):
    subject = call.data.replace('wiki_', '').strip()
    bot.answer_callback_query(call.id, "Открываю архивы Патруля...")
    
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
                # --- [ УМНЫЙ ШТАМП: «КЛАССИЧЕСКАЯ БЕЛИЗНА» (v28) ] ---
                base_img = Image.open(io.BytesIO(valid_photo_data)).convert("RGBA")
                if os.path.exists("watermark.png"):
                    stamp_img = Image.open("watermark.png").convert("RGBA")

                    # 1. МАГИЯ: Превращаем БЕЛЫЙ фон штампа в ПРОЗРАЧНЫЙ
                    datas = stamp_img.getdata()
                    new_data = []
                    for item in datas:
                        # Если пиксель светлый (почти белый), делаем его прозрачным
                        if item[0] > 230 and item[1] > 230 and item[2] > 230:
                            new_data.append((255, 255, 255, 0)) # 0 = полная прозрачность
                        else:
                            # --- [ ИНЖЕНЕРНЫЙ ФИКС: ЧИСТЫЙ БЕЛЫЙ ЦВЕТ ] ---
                            # Если пиксель имеет цвет (не фон), делаем его solid white (255, 255, 255),
                            # сохраняя при этом оригинальную прозрачность. Это удалит синий цвет и рваные края.
                            new_data.append((255, 255, 255, item[3]))
                    stamp_img.putdata(new_data)

                    # 2. РАЗМЕР: 12% от ширины картинки созвездия
                    scale = (base_img.width * 0.12) / stamp_img.width
                    stamp_img = stamp_img.resize((int(stamp_img.width * scale), int(stamp_img.height * scale)), Image.Resampling.LANCZOS)

                    # 3. ПОЗИЦИЯ: Устанавливаем в правый нижний угол
                    pos = (base_img.width - stamp_img.width - int(base_img.width * 0.02), 
                           base_img.height - stamp_img.height - int(base_img.height * 0.02))

                    # Накладываем прозрачный белый штамп
                    base_img.paste(stamp_img, pos, mask=stamp_img)

                    watermarked_img = base_img.convert("RGB")
                    output_bytes = io.BytesIO()
                    watermarked_img.save(output_bytes, format='JPEG', quality=95)
                    final_photo_data = output_bytes.getvalue()
                else:
                    final_photo_data = valid_photo_data

                bot.send_photo(call.message.chat.id, final_photo_data, caption="⭐️ Канал: <b>Дневник юного космонавта</b>", parse_mode='HTML', timeout=40)
            except Exception as e:
                print(f"Ошибка штампа: {e}")
                bot.send_photo(call.message.chat.id, valid_photo_data, caption="⭐️ Канал: <b>Дневник юного космонавта</b>", parse_mode='HTML')
                
        bot.send_message(call.message.chat.id, text, parse_mode='HTML')
    else:
        try:
            page = wiki_wiki.page(f"{subject.capitalize()} (созвездие)")
            if not page.exists(): page = wiki_wiki.page(subject.capitalize())
            if page.exists():
                summary = page.summary[:500] + "..."
                text = f"🌌 <b>ИЗУЧАЕМ: {subject.upper()}</b>\n\n{summary}\n\n🔗 <a href='{page.fullurl}'>Википедия</a>"
                bot.send_message(call.message.chat.id, text, parse_mode='HTML')
        except:
            bot.send_message(call.message.chat.id, "📡 Ошибка связи.")

if __name__ == "__main__":
    Thread(target=run_server).start()
    bot.remove_webhook()
    while True:
        try:
            print("📡 [СИСТЕМА] Марти слушает эфир...")
            bot.polling(non_stop=True, interval=2, timeout=60)
        except Exception as e:
            time.sleep(5)
