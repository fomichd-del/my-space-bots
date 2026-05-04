import os
import telebot
import time
import re
from threading import Thread
from flask import Flask
from google import genai
from google.genai import types
from database import get_personal_log, update_personal_log 
from vision_module import analyze_image  # 🟢 ВАЖНО: Подключаем зрение!

# --- НАСТРОЙКИ ---
TOKEN = os.getenv('MARTY_BOT_TOKEN') 
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

client = genai.Client(api_key=GEMINI_API_KEY)
bot = telebot.TeleBot(TOKEN)

# Получаем имя бота один раз при запуске
try:
    BOT_USERNAME = bot.get_me().username.replace("@", "") 
except:
    BOT_USERNAME = "Marty_Help_Bot"

MODEL_NAME = 'gemini-2.5-flash'

# 🟢 ФИКС: Вернул запрет на форматирование и объединил все задачи
SYSTEM_PROMPT = (
    "Ты — Марти, ученый пес (той-пудель) и бортовой компьютер. "
    "Помогай Командору (8 лет) с учебой, учи добру, уважению к родителям и экологии. "
    "Отвечай ОЧЕНЬ кратко (1-2 абзаца), просто и увлекательно. "
    "ПРАВИЛО: Не используй форматирование текста (никаких звездочек и подчеркиваний). "
    "Используй 'Командор', 'Прием'. В конце задавай короткий вопрос."
)

# 🟢 Flask оставляем только если запускаем файл ОТДЕЛЬНО
app = Flask(__name__)
@app.route('/')
def home(): return "Marty is Online"

def run_flask():
    try:
        port = int(os.environ.get("PORT", 10000))
        app.run(host='0.0.0.0', port=port)
    except: pass # Защита от конфликта портов

# --- ОБРАБОТЧИКИ ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "🐾 Гав! Бортовой компьютер Марти на связи, Командор! Прием.")

# 🟢 НОВЫЙ БЛОК: Обработка ФОТО (то, что потерялось)
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    user_id = message.from_user.id
    bot.send_chat_action(message.chat.id, 'typing')
    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        # Вызываем наш vision_module
        analysis_result = analyze_image(downloaded_file)
        bot.reply_to(message, analysis_result)
    except Exception as e:
        print(f"Ошибка фото: {e}")
        bot.reply_to(message, "📡 Командор, линзы запотели! Не вижу фото. Прием.")

# Обработка текста
@bot.message_handler(func=lambda m: True)
def handle_text(message):
    if not message.text: return
    user_id = message.from_user.id
    text_lower = message.text.lower()
    
    is_private = message.chat.type == 'private'
    is_called = text_lower.startswith('марти') or f"@{BOT_USERNAME.lower()}" in text_lower

    if is_private or is_called:
        bot.send_chat_action(message.chat.id, 'typing')
        clean_text = re.sub(r'^марти[,.\s]*', '', message.text, flags=re.IGNORECASE).strip()
        
        if not clean_text and is_called:
            bot.reply_to(message, "🐾 Слушаю, Командор! Жду твоих указаний. Прием.")
            return

        try:
            user_memory = get_personal_log(user_id)
            prompt = f"ДАННЫЕ О КОМАНДОРЕ: {user_memory}\nВОПРОС: {clean_text}"
            
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
                config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT)
            )
            
            bot.reply_to(message, response.text)
            
            # Память
            if len(clean_text) > 5:
                mem_task = f"Выдели факты из: '{clean_text}'. Если нет — ответь 'НЕТ'."
                mem_resp = client.models.generate_content(model=MODEL_NAME, contents=mem_task)
                if "НЕТ" not in mem_resp.text.upper():
                    update_personal_log(user_id, mem_resp.text.strip())
        except Exception as e:
            bot.reply_to(message, "📡 Системный сбой! Передай инженеру, что датчики барахлят.")

def start_marty_autonomous():
    print("🚀 Марти-Ученый выходит на орбиту...")
    while True:
        try:
            bot.remove_webhook()
            bot.infinity_polling(skip_pending=True)
        except Exception as e:
            time.sleep(5)

if __name__ == "__main__":
    Thread(target=run_flask, daemon=True).start()
    start_marty_autonomous()
