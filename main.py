import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telebot import apihelper
import os, time, concurrent.futures, random, io
from pathlib import Path
from flask import Flask, request, jsonify  # 🟢 Добавили request и jsonify для шлюза
from threading import Thread, Timer 
import requests
from PIL import Image
from datetime import datetime  # 🟢 Добавили для фиксации времени новостей

# --- [ ИМПОРТ МОДУЛЕЙ КОРАБЛЯ ] ---
from draw_map import generate_star_map
# 🟢 Добавили add_news в импорт из базы
from database import init_db, add_xp, get_user_stats, get_rank_name, add_news 
from base_fact_star import CONSTELLATIONS
# 🟢 ДОБАВЛЕНО: Пробуждаем Марти-Ученого из его файла
from marty_chat import start_marty_autonomous 
from game import menu, router

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

# --- [ ЛОГИРОВАНИЕ ] ---
def send_log(text):
    try: bot.send_message(LOG_CHAT_ID, f"🚨 **LOG:** `{text}`", parse_mode="Markdown")
    except: pass

# --- [ МАКСИМАЛЬНО ПОДРОБНАЯ ИНСТРУКЦИЯ ] ---
def get_instruction_text():
    return (
        "🚀 <b>БОРТОВОЙ УСТАВ КРЕЙСЕРА «НАВИГАТОР»</b>\n"
        "─────────────────────────\n\n"
        "<b>Пилот! Перед тобой руководство по управлению звездными системами:</b>\n\n"
        "📡 <b>1. Кнопка «МОЕ НЕБО» (Локация)</b>\n"
        "Нажми её и подтверди отправку геолокации. "
        "Бот мгновенно вычислит твой сектор и отрисует карту звезд.\n"
        "🎁 <i>Награда за вылет: +1 XP и +1 Пыль.</i>\n\n"
        "🌌 <b>2. Кнопка «ДОСЬЕ»</b>\n"
        "Выбираю самое яркое созвездие и готовлю секретную выписку.\n\n"
        "🖼️ <b>3. Кнопка «FULL HD» (Оригинал)</b>\n"
        "Файл хранится в памяти корабля <b>всего 15 минут</b>!\n\n"
        "🎖️ <b>4. Ранги и Опыт (XP)</b>\n"
        "Твои успехи фиксируются в общей базе данных Ориона.\n\n"
        "🤖 <b>ГДЕ МАРТИ?</b>\n"
        "Для общения с Ученым Псом Марти переходи: @Marty_Help_Bot"
    )

@bot.message_handler(func=lambda m: True, content_types=['text'])
def unified_text_handler(message):
    menu_kb = get_main_menu() 
    
    if message.text == "❓❓ ИНСТРУКЦИЯ ПИЛОТА":
        bot.send_message(message.chat.id, get_instruction_text(), reply_markup=menu_kb, parse_mode='HTML')
    elif message.text == "/start":
        welcome = (
            f"🛰️ <b>Системы Навигации инициализированы!</b>\n"
            f"Рад видеть тебя на мостике, пилот <b>{message.from_user.first_name}</b>!\n\n"
            f"Панель управления активирована в нижней части экрана. 🐾"
        )
        bot.send_message(message.chat.id, welcome, reply_markup=menu_kb, parse_mode='HTML')
    else:
        bot.send_message(
            message.chat.id, 
            "🛰️ <b>Я — Навигационный модуль.</b>\n\n"
            "Для общения переключись на канал Ученого Пса Марти: @Marty_Help_Bot", 
            reply_markup=menu_kb, 
            parse_mode='HTML'
        )

@bot.message_handler(content_types=['location'])
def handle_location(message):
    user_id, user_name = message.from_user.id, message.from_user.first_name
    status_msg = bot.send_message(message.chat.id, "🚀 <b>Прогреваю варп-двигатель...</b>", parse_mode='HTML')
    
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(generate_star_map, message.location.latitude, message.location.longitude, user_name, user_id)
        while not future.done():
            time.sleep(10)
            if not future.done():
                fact = random.choice(SPACE_FACTS)
                try: bot.edit_message_text(f"🛰️ <b>Идет сканирование горизонтa...</b>\n\n{fact}", message.chat.id, status_msg.message_id, parse_mode='HTML')
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
            f"Пилот <b>{user_name}</b>, твоя цель-ориентир — <b>{target_name}</b>.\n"
            f"─────────────────────\n"
            f"🎖️ <b>Твой текущий статус:</b> {rank}\n"
            f"📈 <b>Опыт экспедиции:</b> {stats} XP"
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

@bot.callback_query_handler(func=lambda call: call.data.startswith(('game', 'apoc')))
def game_engine(call):
    if call.data == "game_back_to_profile":
        report, kb = menu.get_main_games_menu()
        bot.edit_message_text(report, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
    else:
        main_router.handle_game_selection(bot, call)

# --- [ FLASK СЕРВЕР И API-ШЛЮЗ ] ---
app = Flask(__name__)

@app.route('/')
def home(): 
    return "<h1>Navigator Marty: Online</h1>"

# 🟢 НОВЫЙ ШЛЮЗ: Принимает новости от сторонних скриптов
@app.route('/orion_uplink', methods=['POST'])
def orion_uplink():
    try:
        data = request.json
        if data and 'text' in data:
            text = data['text']
            today = datetime.now().strftime("%Y-%m-%d")
            add_news(today, text) # Сохраняем новость в базу для вечернего дайджеста
            send_log(f"📡 API-Шлюз: Получена новость: {text[:30]}...")
            return jsonify({"status": "success"}), 200
        return jsonify({"status": "error", "message": "No text provided"}), 400
    except Exception as e:
        send_log(f"🚨 Ошибка API-шлюза: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    init_db()
    
    # Запуск Flask сервера (Render использует порт 10000)
    Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000))), daemon=True).start()
    
    # 🟢 ЗАПУСК МАРТИ-УЧЕНОГО
    Thread(target=start_marty_autonomous, daemon=True).start()
    
    print("🚀 Корабль Навигатор на орбите. Перезагрузка систем связи...")
    bot.remove_webhook()
    time.sleep(1) 
    
    bot.infinity_polling(skip_pending=True)
