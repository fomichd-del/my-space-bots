import os
import telebot
import time
import re
from threading import Thread
from flask import Flask
from google import genai
from google.genai import types
from database import get_personal_log, update_personal_log 
from vision_module import analyze_image 

# --- НАСТРОЙКИ ЭКИПАЖА ---
TOKEN = os.getenv('MARTY_BOT_TOKEN') 
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

client = genai.Client(api_key=GEMINI_API_KEY)
bot = telebot.TeleBot(TOKEN)

# Модель и имя бота
MODEL_NAME = 'gemini-2.5-flash'
try:
    BOT_USERNAME = bot.get_me().username.lower()
except:
    BOT_USERNAME = "marty_help_bot"

# 🟢 ЯДРО ЛИЧНОСТИ: Космос, Школа, Мораль, Краткость
SYSTEM_PROMPT = (
    "Ты — Марти, ученый пес (той-пудель) и бортовой ИИ. Твоя миссия — помогать "
    "юному Командору (8 лет) в изучении Вселенной и школьных предметов (математика, физика, химия, биология). "
    "Учи добру, уважению к родителям, помощи по дому и защите природы. "
    "Отвечай ОЧЕНЬ кратко (1-2 абзаца), просто и захватывающе. "
    "ПРАВИЛО: Не используй форматирование текста (звездочки, подчеркивания). "
    "Используй обращения 'Командор', 'Прием'. В конце — один короткий вопрос."
)

# 🟢 HEALTH CHECK ДЛЯ RENDER
app = Flask(__name__)
@app.route('/')
def home(): return "Marty Scientist Status: Orbit Stable"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- ОБРАБОТЧИКИ СОБЫТИЙ ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "🐾 Гав! Бортовой компьютер Марти запущен. Жду команд в личке или в комментариях (начни с имени 'Марти'). Прием!")

# 🟢 ОБРАБОТКА ФОТО (Успехи, поделки, задачи)
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    bot.send_chat_action(message.chat.id, 'typing')
    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        # Анализ через vision_module
        analysis_result = analyze_image(downloaded_file)
        bot.reply_to(message, analysis_result)
    except Exception as e:
        print(f"Ошибка оптики: {e}")
        bot.reply_to(message, "📡 Командор, помехи в видеоканале! Не вижу изображение. Прием.")

# 🟢 ОБРАБОТКА ТЕКСТА (Комментарии и Личка)
@bot.message_handler(func=lambda m: True)
def handle_text(message):
    if not message.text: return

    user_id = message.from_user.id
    text_lower = message.text.lower()
    
    # Триггеры активации
    is_private = message.chat.type == 'private'
    is_called = text_lower.startswith('марти') or f"@{BOT_USERNAME}" in text_lower

    if is_private or is_called:
        bot.send_chat_action(message.chat.id, 'typing')
        
        # Убираем имя Марти из запроса к ИИ
        clean_text = re.sub(r'^марти[,.\s]*', '', message.text, flags=re.IGNORECASE).strip()
        
        # Если позвали по имени, но ничего не спросили
        if not clean_text and is_called:
            bot.reply_to(message, "🐾 На связи, Командор! Нужна помощь с уроками или полетное задание? Прием.")
            return

        try:
            # Чтение памяти
            user_memory = get_personal_log(user_id)
            prompt = f"ДАННЫЕ О КОМАНДОРЕ: {user_memory}\nВОПРОС: {clean_text}"
            
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
                config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT)
            )
            
            bot.reply_to(message, response.text)
            
            # Запись в память (факты)
            if len(clean_text) > 5:
                mem_task = f"Выдели новые факты из: '{clean_text}'. Если нет — ответь 'НЕТ'."
                mem_resp = client.models.generate_content(model=MODEL_NAME, contents=mem_task)
                if "НЕТ" not in mem_resp.text.upper():
                    update_personal_log(user_id, mem_resp.text.strip())
                    
        except Exception as e:
            print(f"Ошибка ИИ: {e}")
            bot.reply_to(message, "📡 Помехи в квантовом модуле. Попробуй еще раз, Командор! Прием.")

# --- ЗАПУСК СИСТЕМ ---

def start_marty_autonomous():
    print("🚀 Марти-Ученый выходит на орбиту...")
    while True:
        try:
            bot.remove_webhook()
            bot.infinity_polling(skip_pending=True, timeout=60)
        except Exception as e:
            print(f"⚠️ Сбой связи: {e}. Перезагрузка...")
            time.sleep(5)

if __name__ == "__main__":
    # Запускаем Flask для Render
    Thread(target=run_flask, daemon=True).start()
    # Запускаем бота
    start_marty_autonomous()
