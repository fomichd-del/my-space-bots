import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import os
import time
from draw_map import generate_star_map
from flask import Flask
from threading import Thread
import wikipediaapi

# === КОНФИГУРАЦИЯ ===
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
# threaded=True позволяет боту не "зависать" при выполнении тяжелых задач
bot = telebot.TeleBot(TELEGRAM_TOKEN, threaded=True)

# Настройка Wikipedia для работы с русским сектором
wiki_wiki = wikipediaapi.Wikipedia(
    user_agent='MartyCosmosBot/1.1 (https://t.me/vladislav_space)', 
    language='ru'
)

# === СЕРВЕР ДЛЯ KEEP-ALIVE (Render) ===
app = Flask(__name__)
@app.route('/')
def keep_alive(): 
    return "Командный центр Марти 14.2 в эфире! 🛰️"

def run_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# === ОБРАБОТЧИКИ КОМАНД ===

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("📡 Мое небо", request_location=True))
    
    welcome_text = (
        f"🛰 <b>Штурман {message.from_user.first_name}, системы Starplot 14.2 онлайн!</b>\n\n"
        "Я готов просканировать сектор над твоей головой. "
        "Жми кнопку ниже, чтобы отправить координаты."
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup, parse_mode='HTML')

@bot.message_handler(content_types=['location'])
def handle_location(message):
    try:
        # ШАГ 1: Подтверждение
        bot.send_message(message.chat.id, "✅ Координаты приняты. Проверяю топливо...")
        
        # ШАГ 2: Визуальная индикация работы
        loading_msg = bot.send_message(
            message.chat.id, 
            "🔭 <i>Запуск глубокого рендеринга... Пожалуйста, подождите.</i>", 
            parse_mode='HTML'
        )
        
        # ШАГ 3: Генерация (вызов из draw_map.py)
        success, result, target_name, err_msg = generate_star_map(
            message.location.latitude, 
            message.location.longitude, 
            message.from_user.first_name
        )
        
        # Удаляем сообщение о загрузке
        bot.delete_message(message.chat.id, loading_msg.message_id)

        if success:
            bot.send_message(message.chat.id, "🚀 Карта построена! Передаю по зашифрованному каналу...")
            
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton(f"📚 База данных: {target_name}", callback_data=f"wiki_{target_name}"))
            
            with open(result, 'rb') as photo:
                # timeout=120 крайне важен для медленных серверов
                bot.send_photo(
                    message.chat.id, 
                    photo, 
                    caption=f"✨ Твое персональное небо!\n🎯 Главная цель: <b>{target_name}</b>", 
                    reply_markup=markup, 
                    parse_mode='HTML',
                    timeout=120
                )
            
            # Очистка временного файла
            if os.path.exists(result):
                os.remove(result)
        else:
            # Если generate_star_map вернула False
            bot.send_message(message.chat.id, f"❌ Ошибка бортовых систем:\n<code>{result}</code>", parse_mode='HTML')
            
    except Exception as e:
        # Если всё вообще пошло не по плану
        bot.send_message(message.chat.id, f"🆘 Критическая системная ошибка: <code>{str(e)}</code>", parse_mode='HTML')

@bot.callback_query_handler(func=lambda call: call.data.startswith('wiki_'))
def callback_wiki(call):
    subject = call.data.replace('wiki_', '')
    bot.answer_callback_query(call.id, "Запрос к архивам Википедии...")
    
    search_term = subject.capitalize()
    # Пытаемся найти страницу именно как созвездие
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
        bot.send_message(call.message.chat.id, f"⚠️ Данные о «{search_term}» отсутствуют в архивах.")

# === ТОЧКА ВХОДА ===
if __name__ == "__main__":
    # 1. Запуск веб-сервера для Render
    Thread(target=run_server).start()
    
    # 2. Протокол очистки конфликтов (Ошибка 409)
    print("🛰️ Очистка старых сессий Telegram...")
    bot.remove_webhook()
    time.sleep(2)
    
    print("🚀 Марти 14.2 готов к дежурству!")
    
    # 3. Запуск бесконечного цикла
    # skip_pending=True не дает боту сойти с ума от старых сообщений после рестарта
    bot.infinity_polling(timeout=90, skip_pending=True, long_polling_timeout=40)
