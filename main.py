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
# 🟢 ДОБАВЛЕНО: Пробуждаем Марти-Ученого из его файла
from marty_chat import start_marty_autonomous 

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

# --- [ ФУНКЦИЯ СОЗДАНИЯ ГЛАВНОГО МЕНЮ ] ---
def get_main_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("📡📡📡 МОЕ НЕБО", request_location=True))
    markup.add(KeyboardButton("❓❓ ИНСТРУКЦИЯ ПИЛОТА"))
    return markup

# --- [ ТЕХНИЧЕСКИЕ СТАТУСЫ ДЛЯ ЭКРАНА ЗАГРУЗКИ ] ---
SPACE_FACTS = [
    "🔭 <b>Юстировка линз...</b> Собираю фотоны, летевшие к нам миллиарды лет, чтобы точно отрисовать твой горизонт.",
    "🌌 <b>Синхронизация с эфемеридами...</b> Рассчитываю точное положение планет относительно твоего дома.",
    "🛸 <b>Сектор сканирования...</b> Проверяю пространство на наличие гравитационных аномалий.",
    "🛰️ <b>Deep Space Network...</b> Подключаюсь к сети дальней связи для уточнения координат звезд.",
    "🪐 <b>Внимание:</b> Плотность Сатурна меньше плотности воды. Он бы плавал в обычном океане!",
    "🌠 <b>Квантовый поток:</b> Каждую секунду через тебя пролетают триллионы нейтрино от Солнца."
]

# --- [ МАКСИМАЛЬНО ПОДРОБНАЯ ИНСТРУКЦИЯ ] ---
def get_instruction_text():
    return (
        "🚀 <b>БОРТОВОЙ УСТАВ КРЕЙСЕРА «НАВИГАТОР»</b>\n"
        "─────────────────────────\n\n"
        "<b>Пилот! Перед тобой руководство по управлению звездными системами:</b>\n\n"
        "📡 <b>1. Кнопка «МОЕ НЕБО» (Локация)</b>\n"
        "Это главная навигационная функция. Нажми её и подтверди отправку геолокации. "
        "Бот мгновенно вычислит твой сектор и отрисует карту звезд, планет и Млечного Пути именно над твоей крышей. "
        "Центр круга — это зенит (точка над головой), края — твой реальный горизонт.\n"
        "🎁 <i>Награда за вылет: +15 XP.</i>\n\n"
        "🌌 <b>2. Кнопка «ДОСЬЕ»</b>\n"
        "Появляется под готовой картой. Я выбираю самое яркое созвездие в твоем секторе (цель) "
        "и готовлю секретную выписку: его историю, фото в высоком качестве и научные факты.\n\n"
        "🖼️ <b>3. Кнопка «FULL HD» (Оригинал)</b>\n"
        "Телеграм сжимает фото. Чтобы получить четкий снимок для печати или обоев — жми эту кнопку. "
        "Файл хранится в памяти корабля <b>всего 15 минут</b>, потом он самоуничтожается для экономии ресурсов!\n\n"
        "🎖️ <b>4. Ранги и Опыт (XP)</b>\n"
        "Твои успехи фиксируются в базе данных. Чем больше вылетов, тем выше звание:\n"
        "• <b>Кадет</b> (0-100) | <b>Исследователь</b> (101-300)\n"
        "• <b>Навигатор</b> (301-600) | <b>Командор</b> (601+)\n\n"
        "🤖 <b>ГДЕ МАРТИ?</b>\n"
        "Я — Навигатор (мозг корабля). Если хочешь поговорить о смысле бытия или спросить совета "
        "у Ученого Пса Марти — переходи по связи: @Marty_Help_Bot"
    )

@bot.message_handler(func=lambda m: True, content_types=['text'])
def unified_text_handler(message):
    menu = get_main_menu() 
    
    if message.text == "❓❓ ИНСТРУКЦИЯ ПИЛОТА":
        bot.send_message(message.chat.id, get_instruction_text(), reply_markup=menu, parse_mode='HTML')
    elif message.text == "/start":
        welcome = (
            f"🛰️ <b>Системы Навигации инициализированы!</b>\n"
            f"Рад видеть тебя на мостике, пилот <b>{message.from_user.first_name}</b>!\n\n"
            f"Я — твой бортовой компьютер. Готов проложить курс через тернии к звездам. "
            f"Панель управления активирована в нижней части экрана. 🐾"
        )
        bot.send_message(message.chat.id, welcome, reply_markup=menu, parse_mode='HTML')
    else:
        bot.send_message(
            message.chat.id, 
            "🛰️ <b>Я — Навигационный модуль.</b> Моя задача — расчет звездных карт.\n\n"
            "Для общения переключись на канал Ученого Пса Марти: @Marty_Help_Bot\n"
            "Или выбери команду на панели ниже:", 
            reply_markup=menu, 
            parse_mode='HTML'
        )

@bot.message_handler(content_types=['location'])
def handle_location(message):
    user_id, user_name = message.from_user.id, message.from_user.first_name
    status_msg = bot.send_message(message.chat.id, "🚀 <b>Прогреваю варп-двигатель... Подключаюсь к спутникам.</b>", parse_mode='HTML')
    
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
        add_xp(user_id, 1, user_name)
        stats = get_user_stats(user_id)
        rank = get_rank_name(stats)
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton(f"🌌 Открыть досье: {target_name}", callback_data=f"wiki_{target_name}"))
        markup.add(InlineKeyboardButton("🖼️ Получить Full HD", callback_data=f"orig_{user_id}"))
        markup.add(InlineKeyboardButton("🤖 Марти-Ученый", url="https://t.me/Marty_Help_Bot?start=help"))
        
        caption = (
            f"✨ <b>СЕКТОР ПРОСКАНИРОВАН УСПЕШНО!</b>\n\n"
            f"Пилот <b>{user_name}</b>, твоя цель-ориентир на сегодня — <b>{target_name}</b>.\n"
            f"Оно выделено на карте розовым неоновым кругом.\n"
            f"─────────────────────\n"
            f"🎖️ <b>Твой текущий статус:</b> {rank}\n"
            f"📈 <b>Опыт экспедиции:</b> {stats} XP (начислено +15)"
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
                    print(f"🧹 [ОЧИСТКА]: Full HD {res_png} удален.")
            except: pass
        Timer(900.0, cleanup_original).start()
    else:
        bot.edit_message_text(f"❌ <b>Критический сбой навигации:</b> {err_msg}", message.chat.id, status_msg.message_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith('wiki_'))
def callback_wiki(call):
    subject = call.data.replace('wiki_', '').strip()
    bot.answer_callback_query(call.id, "Запрашиваю данные...")
    
    found = next((item for item in CONSTELLATIONS if item['name_ru'].upper() == subject.upper()), None)
    if found:
        name_latin = found['name_latin']
        base_url = f"https://raw.githubusercontent.com/fomichd-del/my-space-bots/main/photo_space/"
        text = f"🌌 <b>БОРТОВОЕ ДОСЬЕ ПАТРУЛЯ: {found['name_ru'].upper()}</b>\n\n{found['fact']}"
        
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
    
    # Запуск Flask
    Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000))), daemon=True).start()
    
    # 🟢 ЗАПУСК МАРТИ-УЧЕНОГО (Просыпайся, Марти!)
    Thread(target=start_marty_autonomous, daemon=True).start()
    
    # КРИТИЧЕСКИЙ ФИКС ОШИБКИ 409
    print("🚀 Корабль Навигатор на орбите. Перезагрузка систем связи...")
    bot.remove_webhook()
    time.sleep(1) 
    
    bot.infinity_polling(skip_pending=True)
