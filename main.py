import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import os
import time
from draw_map import generate_star_map
from flask import Flask
from threading import Thread
import wikipediaapi

# === КОНФИГУРАЦИЯ СИСТЕМЫ ===
# Версия протокола: 23.0 "Центрифуга"
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
bot = telebot.TeleBot(TELEGRAM_TOKEN, threaded=True)

# Настройка Wikipedia (Русский сектор)
wiki_wiki = wikipediaapi.Wikipedia(
    user_agent='MartySpaceBot/1.1 (https://t.me/vladislav_space)', 
    language='ru'
)

# === МИНИ-СЕРВЕР ДЛЯ RENDER (Keep-Alive) ===
app = Flask(__name__)
@app.route('/')
def keep_alive(): 
    return "Командный центр Марти 23.0 в эфире! 🛰️ Состояние систем: Номинальное."

def run_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# === ОБРАБОТЧИКИ КОМАНД ===

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("📡 Мое небо", request_location=True))
    
    welcome_text = (
        f"🛰 <b>Штурман {message.from_user.first_name}, системы Starplot 23.0 онлайн!</b>\n\n"
        "Я провел ювелирную калибровку оптики. Смещение скорректировано.\n\n"
        "Нажми кнопку ниже, чтобы запустить сканирование сектора."
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup, parse_mode='HTML')

@bot.message_handler(content_types=['location'])
def handle_location(message):
    try:
        # Статус-отчет 1
        bot.send_message(message.chat.id, "✅ Координаты приняты. Запускаю Starplot v23.0...")
        
        # Статус-отчет 2 (индикация процесса)
        loading_msg = bot.send_message(
            message.chat.id, 
            "🔭 <i>Произвожу глубокий рендеринг небесной сферы... Это займет около минуты.</i>", 
            parse_mode='HTML'
        )
        
        # Генерация карты (вызов функции из draw_map.py)
        success, result, target_name, err_msg = generate_star_map(
            message.location.latitude, 
            message.location.longitude, 
            message.from_user.first_name
        )
        
        # Удаляем сообщение о загрузке, когда карта готова
        bot.delete_message(message.chat.id, loading_msg.message_id)

        if success:
            bot.send_message(message.chat.id, "🚀 Карта готова! Вывожу на главный экран...")
            
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton(f"📚 База данных: {target_name}", callback_data=f"wiki_{target_name}"))
            
            with open(result, 'rb') as photo:
                # Увеличенный таймаут до 120 сек для тяжелых файлов на медленном интернете
                bot.send_photo(
                    message.chat.id, 
                    photo, 
                    caption=f"✨ Твое персональное небо!\n🎯 Главная цель в секторе: <b>{target_name}</b>", 
                    reply_markup=markup, 
                    parse_mode='HTML',
                    timeout=120
                )
            
            # Удаление временного файла после отправки
            if os.path.exists(result):
                os.remove(result)
        else:
            # Отчет об ошибке в draw_map.py (например, нехватка памяти)
            bot.send_message(message.chat.id, f"❌ Ошибка бортовых систем:\n<code>{result}</code>", parse_mode='HTML')
            
    except Exception as e:
        # Отчет о критической ошибке в самом обработчике
        bot.send_message(message.chat.id, f"🆘 Критическая ошибка связи: <code>{str(e)}</code>", parse_mode='HTML')

@bot.callback_query_handler(func=lambda call: call.data.startswith('wiki_'))
def callback_wiki(call):
    subject = call.data.replace('wiki_', '')
    bot.answer_callback_query(call.id, "Запрос к архивам...")
    
    search_term = subject.capitalize()
    page = wiki_wiki.page(f"{search_term} (созвездие)")
    if not page.exists():
        page = wiki_wiki.page(search_term)
    
    if page.exists():
        bot.send_message(
            call.message.chat.id, 
            f"📖 <b>{search_term.upper()}</b>\n\n{page.summary[:1500]}...\n\n🔗 <a href='{page.fullurl}'>Читать полную статью</a>", 
            parse_mode='HTML'
        )
    else:
        bot.send_message(call.message.chat.id, f"⚠️ Данные о «{search_term}» не найдены.")

# === ЗАПУСК ===
if __name__ == "__main__":
    # Запуск сервера-заглушки
    Thread(target=run_server).start()
    
    # Сброс старых соединений (защита от ошибки 409)
    print("🛰️ Сброс старых каналов связи...")
    bot.remove_webhook()
    time.sleep(2)
    
    print("🚀 Марти 23.0 на боевом дежурстве!")
    
    # Запуск бота с игнорированием старых команд
    bot.infinity_polling(timeout=90, skip_pending=True, long_polling_timeout=40)
