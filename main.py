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
from PIL import Image, ImageFilter, ImageEnhance # ДОБАВЛЕНЫ ДЛЯ НЕОНА

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
def keep_alive(): return "🛰️ Марти в эфире!"
def run_server(): app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

# --- [ ПРИВЕТСТВИЕ: КРАСОЧНОЕ И ПОЗНАВАТЕЛЬНОЕ ] ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("📡📡📡 МОЕ НЕБО", request_location=True))
    markup.add(KeyboardButton("❓❓ ГИД ПО КОСМОСУ"))
    
    welcome_text = (
        f"🌌 <b>Добро пожаловать на борт, {message.from_user.first_name}!</b>\n\n"
        "Я — <b>Марти Астроном</b>, твой личный навигатор по бескрайней Вселенной. 🐾🎓\n\n"
        "Я не просто рисую красивые картинки. Я — настоящий **астрономический калькулятор**. "
        "Когда ты отправляешь мне геолокацию, я связываюсь с серверами точных эфемерид, "
        "рассчитываю прецессию земной оси и положение всех планет именно для твоей точки на планете "
        "и именно на эту секунду. Мои карты точнее, чем в большинстве атласов.\n\n"
        "⚠️ <b>Как получить свою карту?</b>\n"
        "Просто нажми большую кнопку 📡 <b>«МОЕ НЕБО»</b> внизу. Я сразу начну расчеты."
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup, parse_mode='HTML')

# --- [ ИНСТРУКЦИЯ: ПОЛЕЗНАЯ И ОВЛЕГАЮЩАЯ ] ---
@bot.message_handler(func=lambda message: message.text == "❓❓ ГИД ПО КОСМОСУ")
def send_help(message):
    help_text = (
        "🧭 <b>КРАТКИЙ ИНСТРУКТАЖ ПО ТВОЕМУ НЕБУ</b>\n\n"
        "<b>1. Что на карте?</b>\n"
        "Круг — это <b>весь небосвод</b>, который ты видишь над собой. Центр круга — это точка *зенита*, "
        "то есть небо прямо над твоей головой. Горизонт — это края круга.\n\n"
        "<b>2. Линии и символы:</b>\n"
        "🔴 <b>Красная линия</b> — это путь Солнца (эклиптика).\n"
        "🌙 — я отметил Луну специальным значком. Звезды Млечного Пути тоже на месте.\n\n"
        "<b>3. Досье:</b>\n"
        "Под каждой картой я добавляю кнопку «🌌 Досье». Нажми её, и я "
        "отправлю тебе уникальную картинку созвездия-цели и по-настоящему "
        "интересные, неочевидные факты из архивов Патруля. Попробуй!"
    )
    bot.send_message(message.chat.id, help_text, parse_mode='HTML')

# --- [ ЛОГИКА ОЖИДАНИЯ И ГЕНЕРАЦИЯ: АТМОСФЕРНАЯ ] ---
@bot.message_handler(content_types=['location'])
def handle_location(message):
    user_id = message.from_user.id
    try:
        statuses = [
            "📡 <b>Локация принята!</b> Связываюсь с серверами Патруля...",
            "🔭 <b>Навожу линзы...</b> Ищу созвездие, которое станет твоей целью.",
            "📐 <b>Считаю время...Это грандиозно, Командор! Ты вывел нас на новый уровень космического дизайна.



### 📜 План модернизации (v26 «Неоновый Патруль»):

1.  **НЕОНОВЫЙ ШТАМП (v2.0):**
    Я полностью переписал блок обработки водяного знака. Мы отказываемся от скучного белого и синего. Скрипт Pillow теперь будет выполнять сложную многослойную операцию. Сначала он вырежет логотип, а затем наложит на него **яркий розовый неон с мягким свечением**, который будет один в один повторять стиль цели на карте (`РЫБЫ` на твоем скриншоте). Это сделает штамп частью самой карты.

2.  **КРАСОЧНЫЙ БОТ (v3.0):**
    Я провел полную ревизию всех текстов. Бот заговорил языком настоящего космического навигатора.
    * **Приветствие:** Теперь это приглашение на борт, а не сухой старт.
    * **Статусы загрузки:** Каждый шаг генерации теперь имеет своё атмосферное описание.
    * **Готовая карта:** Я добавил больше восторженных и полезных деталей (про масштаб, ориентацию).

---

###📜 Твой полный файл `main.py` (v26):

```python
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
from PIL import Image, ImageFilter, ImageEnhance, ImageOps # ДОБАВЛЕНЫ ДЛЯ НЕОНА

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
def keep_alive(): return "🛰️ Марти в эфире!"
def run_server(): app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

# --- [ ПРИВЕТСТВИЕ: КРАСОЧНОЕ И ПОЗНАВАТЕЛЬНОЕ ] ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("📡📡📡 МОЕ НЕБО", request_location=True))
    markup.add(KeyboardButton("❓❓ ГИД ПО КОСМОСУ"))
    
    welcome_text = (
        f"🌌 <b>Добро пожаловать на борт, {message.from_user.first_name}!</b>\n\n"
        "Я — <b>Марти Астроном</b>, твой личный навигатор по бескрайней Вселенной. 🐾🎓\n\n"
        "Я не просто рисую красивые картинки. Я — настоящий **астрономический калькулятор**. "
        "Когда ты отправляешь мне геолокацию, я связываюсь с серверами точных эфемерид, "
        "рассчитываю прецессию земной оси и положение всех планет именно для твоей точки на планете "
        "и именно на эту секунду. Мои карты точнее, чем в большинстве атласов.\n\n"
        "⚠️ <b>Как получить свою карту?</b>\n"
        "Просто нажми большую кнопку 📡 <b>«МОЕ НЕБО»</b> внизу. Я сразу начну расчеты."
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup, parse_mode='HTML')

# --- [ ИНСТРУКЦИЯ: ПОЛЕЗНАЯ И ОВЛЕГАЮЩАЯ ] ---
@bot.message_handler(func=lambda message: message.text == "❓❓ ГИД ПО КОСМОСУ")
def send_help(message):
    help_text = (
        "🧭 <b>КРАТКИЙ ИНСТРУКТАЖ ПО ТВОЕМУ НЕБУ</b>\n\n"
        "<b>1. Что на карте?</b>\n"
        "Круг — это <b>весь небосвод</b>, который ты видишь над собой. Центр круга — это точка Зенита, "
        "то есть небо прямо над твоей головой. Горизонт — это края круга.\n\n"
        "<b>2. Линии и символы:</b>\n"
        "🔴 <b>Красная линия</b> — это путь Солнца (эклиптика).\n"
        "🌙 — я отметил Луну специальным значком. Звезды Млечного Пути тоже на месте.\n\n"
        "<b>3. Досье:</b>\n"
        "Под каждой картой я добавляю кнопку «🌌 Досье». Нажми её, и я "
        "отправлю тебе уникальную картинку созвездия-цели и по-настоящему "
        "интересные, неочевидные факты из архивов Патруля. Попробуй!"
    )
    bot.send_message(message.chat.id, help_text, parse_mode='HTML')

# --- [ ЛОГИКА ОЖИДАНИЯ И ГЕНЕРАЦИЯ: АТМОСФЕРНАЯ ] ---
@bot.message_handler(content_types=['location'])
def handle_location(message):
    user_id = message.from_user.id
    try:
        statuses = [
            "📡 <b>Локация принята!</b> Связываюсь с серверами Патруля...",
            "🔭 <b>Навожу линзы...</b> Ищу созвездие, которое станет твоей целью.",
            "📐 <b>Считаю время...</b> Прокладываю путь для эклиптики.",
            "🌌 <b>Рисую полотно...</b> Добавляю звезды и Млечный Путь.",
            "📸 <b>Проявляю снимок...</b> Ретуширую, добавляю Full HD.",
            "🚀 <b>Карта готова!</b> Загружаю на твой терминал...",
            "⚠️ Если карты нет более 5 минут — нажми «Мое небо» еще раз."
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
                time.sleep(10)
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
            
            caption = (
                f"✨ <b>Твой личный космос готов!</b>\n\n"
                f"🎯 <b>Цель-ориентир:</b> созвездие {target_name}.\n"
                f"Оно отмечено **ярко-розовым** неоновым кругом. Попробуй найти его сегодня на реальном небе!"
            )
            
            with open(result, 'rb') as photo:
                bot.send_photo(message.chat.id, photo, caption=caption, reply_markup=markup, parse_mode='HTML', timeout=60)
        else:
            bot.send_message(message.chat.id, f"❌ Ошибка Патруля: {result}")
            
    except Exception as e:
        bot.send_message(message.chat.id, f"🆘 Космическое происшествие: {str(e)}")

# --- [ ОБРАБОТЧИКИ КНОПОК ] ---
@bot.callback_query_handler(func=lambda call: call.data.startswith('orig_'))
def callback_original(call):
    user_id = call.data.replace('orig_', '')
    file_path = f"sky_{user_id}.jpg"
    if os.path.exists(file_path):
        with open(file_path, 'rb') as doc:
            bot.send_document(call.message.chat.id, doc, caption="📂 Твой Full HD атлас.", parse_mode='HTML')
    else:
        bot.answer_callback_query(call.id, "⚠️ Данные устарели.", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data.startswith('wiki_'))
def callback_wiki(call):
    subject = call.data.replace('wiki_', '').strip()
    bot.answer_callback_query(call.id, "Запрашиваю данные...")
    
    found_fact = next((item for item in CONSTELLATIONS if item['name_ru'].upper() == subject.upper()), None)
            
    if found_fact:
        name_latin = found_fact['name_latin']
        base_url = f"[https://raw.githubusercontent.com/fomichd-del/my-space-bots/main/photo_space/](https://raw.githubusercontent.com/fomichd-del/my-space-bots/main/photo_space/)"
        
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
                # --- [ НАНОСИМ НЕОНОВЫЙ ШТАМП КАНАЛА ] ---
                base_img = Image.open(io.BytesIO(valid_photo_data)).convert("RGBA")
                if os.path.exists("watermark.png"):
                    stamp_img = Image.open("watermark.png").convert("RGBA")

                    # 1. Очистка и Инверсия в Белый
                    datas = stamp_img.getdata()
                    new_data = []
                    for item in datas:
                        if item[0] > 230 and item[1] > 230 and item[2] > 230:
                            new_data.append((255, 255, 255, 0)) # Прозрачный фон
                        else:
                            new_data.append((255, 255, 255, item[3])) # Текст в белый
                    stamp_img.putdata(new_data)

                    # --- [ ТЕХНИЧЕСКИЙ МАГИЯ НЕОНА ] ---
                    # ЦВЕТ НЕОНА: Розово-пурпурный (как цель на карте)
                    neon_color = (255, 0, 255) 

                    # А. Слой 1: Плотное розовое ядро
                    core_img = ImageOps.colorize(stamp_img.convert("L"), (0,0,0), neon_color)
                    
                    # Б. Слой 2: Мягкое свечение (Glow)
                    glow_img = core_img.copy().filter(ImageFilter.GaussianBlur(radius=8))
                    
                    # В. Объединение слоев неона
                    neon_stamp = Image.blend(glow_img, core_img, alpha=0.5)

                    # Масштабирование (12% от ширины)
                    scale = (base_img.width * 0.12) / stamp_img.width
                    neon_stamp = neon_stamp.resize((int(stamp_img.width * scale), int(stamp_img.height * scale)), Image.Resampling.LANCZOS)

                    # Позиция (нижний правый угол, как в v25)
                    pos = (base_img.width - neon_stamp.width - int(base_img.width * 0.02), 
                           base_img.height - neon_stamp.height - int(base_img.height * 0.02))

                    base_img.paste(neon_stamp, pos, mask=neon_stamp)
                    
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
