import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telebot import apihelper
import os, time, concurrent.futures, random
from draw_map import generate_star_map
from flask import Flask
from threading import Thread
import wikipediaapi
from PIL import Image

# --- [ СЛУЖЕБНЫЕ МОДУЛИ ] ---
from database import init_db, add_xp, get_user_stats, get_rank_name
from marty_chat import run_chat_bot 
from base_fact_star import CONSTELLATIONS
from vision_module import analyze_image 

# --- [ КОНФИГУРАЦИЯ ] ---
TOKEN = os.getenv('TELEGRAM_TOKEN')
LOG_CHAT_ID = "-1003756164148"

bot = telebot.TeleBot(TOKEN, threaded=True)

apihelper.CONNECT_TIMEOUT = 60
apihelper.READ_TIMEOUT = 90

# --- [ ЦЕНТР ЛОГИРОВАНИЯ ] ---
def send_log(text):
    try:
        bot.send_message(LOG_CHAT_ID, f"📡 <b>[ЖУРНАЛ СОБЫТИЙ]:</b> {text}", parse_mode='HTML')
    except Exception as e:
        print(f"Ошибка логирования: {e}")

# --- [ РАСШИРЕННАЯ ИНСТРУКЦИЯ ПИЛОТА ] ---
def get_instruction_text():
    return (
        "👨‍🚀 <b>ПОЛНОЕ РУКОВОДСТВО ПО ЭКСПЛУАТАЦИИ МАРТИ</b>\n"
        "───────────────────────\n\n"
        "Я здесь, чтобы сделать космос ближе! Вот что мы можем делать вместе:\n\n"
        "🛰 <b>1. СКАНИРОВАНИЕ «МОЕ НЕБО»</b>\n"
        "Жми на кнопку локации. Я подключусь к орбитальной группировке, вычислю твой сектор и построю карту звезд, которые находятся прямо над твоей головой.\n"
        "👉 <i>Зачем? Чтобы ты знал, на что смотришь в окно. (+15 XP)</i>\n\n"
        "📸 <b>2. ГЛАЗА МАРТИ (АНАЛИЗ ФОТО)</b>\n"
        "Просто пришли мне любое фото. Я прогоню его через свои визуальные фильтры. Если это созвездие — я его узнаю. Если это что-то другое — я расскажу, что вижу.\n"
        "👉 <i>Зачем? Для обучения и пополнения базы данных. (+10 XP)</i>\n\n"
        "🎖 <b>3. СИСТЕМА РАНГОВ И КАРЬЕРА</b>\n"
        "Твои действия приносят очки опыта (XP). Это твой путь во флоте:\n"
        "• <b>Кадет:</b> Начальный допуск.\n"
        "• <b>Исследователь:</b> Ты уже ориентируешься в Млечном Пути.\n"
        "• <b>Навигатор:</b> Способен прокладывать курсы.\n"
        "• <b>Командор:</b> Высший офицерский состав.\n"
        "• <b>Адмирал:</b> Легенда Галактики! 👑\n\n"
        "🖼 <b>4. ВЫСОКОЕ РАЗРЕШЕНИЕ</b>\n"
        "После генерации карты появится кнопка <b>Full HD</b>. Используй её, чтобы получить файл в максимальном качестве для печати или обоев."
    )

# --- [ ПРИВЕТСТВИЕ ] ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("📡📡📡 МОЕ НЕБО", request_location=True))
    markup.add(KeyboardButton("❓❓ ИНСТРУКЦИЯ ПИЛОТА"))
    
    welcome_text = (
        f"🛰️ <b>Прием! Пилот {message.from_user.first_name}, я на связи!</b>\n\n"
        "Я — <b>Марти</b>, твой верный напарник в этом бесконечном пространстве. 🐾\n"
        "Все системы в норме, реактор стабилен. Мы готовы к исследованиям!\n\n"
        "Хочешь взглянуть на текущий сектор неба или проанализировать данные со своих камер?"
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup, parse_mode='HTML')

# --- [ ГЛАЗА МАРТИ: АНАЛИЗ ИЗОБРАЖЕНИЙ ] ---
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    
    # Живой отклик Марти
    status_msg = bot.reply_to(message, "📸 <b>Загружаю данные в аналитический блок... Секунду...</b>", parse_mode='HTML')
    
    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        # Анализ через Vision-модуль
        description = analyze_image(downloaded_file)
        
        add_xp(user_id, 10, user_name)
        new_xp = get_user_stats(user_id)
        
        caption = (
            f"🔍 <b>АНАЛИЗ ЗАВЕРШЕН:</b>\n\n"
            f"{description}\n"
            f"─────────────────────\n"
            f"📈 <b>Прогресс пилота:</b> +10 XP (Всего: {new_xp})"
        )
        
        bot.edit_message_text(caption, message.chat.id, status_msg.message_id, parse_mode='Markdown')
        
        # Вероятность получить дополнительное поручение от Марти
        if random.random() < 0.25:
            tasks = [
                "🚀 <b>БОНУСНОЕ ЗАДАНИЕ:</b> Найди это созвездие в нашем «Досье» и прочитай факт о нём!",
                "📡 <b>СВЯЗЬ:</b> Передай эти данные другим пилотам, это важно для общего дела!",
                "👨‍🚀 <b>ПОДГОТОВКА:</b> Сделай глубокий вдох, пилот. Впереди много интересного!"
            ]
            bot.send_message(message.chat.id, f"🌟 <b>ВХОДЯЩЕЕ СООБЩЕНИЕ:</b>\n{random.choice(tasks)}", parse_mode='HTML')

    except Exception as e:
        send_log(f"🆘 Сбой Vision: {e}")
        bot.edit_message_text("🛰️ <b>Сигнал искажен!</b> Не удалось считать данные. Попробуй сделать более четкий снимок.", message.chat.id, status_msg.message_id)

# --- [ ИНСТРУКЦИЯ ] ---
@bot.message_handler(func=lambda message: message.text == "❓❓ ИНСТРУКЦИЯ ПИЛОТА")
def handle_instruction(message):
    bot.send_message(message.chat.id, get_instruction_text(), parse_mode='HTML')

# --- [ МОЕ НЕБО: ГЕНЕРАЦИЯ КАРТЫ ] ---
@bot.message_handler(content_types=['location'])
def handle_location(message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    
    # Создаем атмосферу работы систем
    loading_steps = [
        "🔭 <b>Разворачиваю линзы телескопа...</b>",
        "🛰️ <b>Синхронизируюсь со спутниками на орбите...</b>",
        "📐 <b>Просчитываю кривизну пространства в твоем секторе...</b>"
    ]
    status_msg = bot.send_message(message.chat.id, random.choice(loading_steps), parse_mode='HTML')
    
    try:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(generate_star_map, message.location.latitude, message.location.longitude, user_name, user_id)
            success, result, target_name, err_msg = future.result()

        if success:
            add_xp(user_id, 15, user_name)
            current_xp = get_user_stats(user_id)
            rank = get_rank_name(current_xp)

            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton(f"🌌 Открыть досье: {target_name}", callback_data=f"wiki_{target_name}"))
            # ВОЗВРАЩЕНА КНОПКА FULL HD
            markup.add(InlineKeyboardButton("🖼️ Получить Full HD оригинал", callback_data=f"orig_{user_id}"))
            markup.add(InlineKeyboardButton("🤖 Спросить Марти", url="https://t.me/Marty_Help_Bot?start=help"))
            
            caption = (
                f"✨ <b>ПОРТАЛ ОТКРЫТ!</b>\n\n"
                f"Пилот <b>{user_name}</b>, твоя персональная карта сектора готова.\n"
                f"🎯 <b>Цель для наблюдения:</b> созвездие <b>{target_name}</b>\n"
                f"─────────────────────\n"
                f"🎖 <b>Твой ранг:</b> {rank}\n"
                f"📈 <b>Опыт повышен:</b> {current_xp} XP"
            )
            
            with open(result, 'rb') as photo:
                bot.send_photo(message.chat.id, photo, caption=caption, reply_markup=markup, parse_mode='HTML')
            
            bot.delete_message(message.chat.id, status_msg.message_id)
            send_log(f"✅ Успешное сканирование для {user_name}.")
        else:
            bot.edit_message_text(f"❌ <b>Навигационный сбой:</b> {err_msg}", message.chat.id, status_msg.message_id)
    except Exception as e:
        send_log(f"🆘 Ошибка генерации: {e}")
        bot.send_message(message.chat.id, "💥 <b>Хьюстон, у нас проблемы!</b> Произошел технический сбой, попробуй перезапустить сканирование.")

# --- [ ДОСЬЕ (WIKI): ТЕПЕРЬ С ФОТО ] ---
@bot.callback_query_handler(func=lambda call: call.data.startswith('wiki_'))
def callback_wiki(call):
    subject = call.data.replace('wiki_', '').strip()
    bot.answer_callback_query(call.id, "Доступ к архивам разрешен...")
    
    found_fact = next((item for item in CONSTELLATIONS if item['name_ru'].upper() == subject.upper()), None)
    
    if found_fact:
        text = (
            f"🌌 <b>ДОСЬЕ: {found_fact['name_ru'].upper()}</b>\n"
            f"───────────────────────\n\n"
            f"{found_fact['fact']}\n\n"
            f"<i>Данные подтверждены. Конец связи.</i>"
        )
        
        # Проверяем, есть ли фото в данных созвездия
        if 'photo_path' in found_fact and os.path.exists(found_fact['photo_path']):
            with open(found_fact['photo_path'], 'rb') as photo:
                bot.send_photo(call.message.chat.id, photo, caption=text, parse_mode='HTML')
        else:
            # Если фото нет, просто шлем текст
            bot.send_message(call.message.chat.id, text, parse_mode='HTML')
    else:
        bot.send_message(call.message.chat.id, "⚠️ Данные об этом объекте временно засекречены или отсутствуют.")

# --- [ ОБРАБОТЧИК ДЛЯ КНОПКИ FULL HD ] ---
@bot.callback_query_handler(func=lambda call: call.data.startswith('orig_'))
def callback_orig(call):
    user_id = call.data.replace('orig_', '')
    bot.answer_callback_query(call.id, "Подготавливаю файл высокого разрешения...")
    
    # Предполагаем, что последняя сгенерированная карта лежит в папке output или temp
    file_path = f"output/star_map_{user_id}.png" # Путь должен соответствовать твоей функции generate_star_map
    
    if os.path.exists(file_path):
        with open(file_path, 'rb') as doc:
            bot.send_document(call.message.chat.id, doc, caption="🚀 <b>Твой снимок в оригинальном качестве.</b>", parse_mode='HTML')
    else:
        bot.send_message(call.message.chat.id, "❌ Файл не найден. Попробуй сгенерировать карту заново.")

# --- [ ЗАПУСК СИСТЕМ ] ---
app = Flask(__name__)
@app.route('/')
def home(): return "Marty Systems: Online"

def run_server():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

if __name__ == "__main__":
    init_db()
    send_log("🚀 <b>Центр управления Марти активирован. Полет нормальный!</b>")
    
    Thread(target=run_server).start()
    
    bot.remove_webhook()
    bot.polling(non_stop=True, interval=1)
