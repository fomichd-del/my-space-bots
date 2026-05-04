import os
import telebot
import time
import re
from threading import Thread  # 🟢 Для параллельного запуска Flask
from flask import Flask       # 🟢 Чтобы Render не "гасил" бота
from google import genai
from google.genai import types
from database import get_personal_log, update_personal_log 

# --- НАСТРОЙКИ ---
TOKEN = os.getenv('MARTY_BOT_TOKEN') 
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

client = genai.Client(api_key=GEMINI_API_KEY)
bot = telebot.TeleBot(TOKEN)

# 🟢 ФИКС ИМЕНИ: Указываем БЕЗ собаки. Код сам добавит её где нужно.
try:
    BOT_INFO = bot.get_me()
    BOT_USERNAME = BOT_INFO.username.replace("@", "") 
except Exception as e:
    print(f"Ошибка получения инфо о боте: {e}")
    BOT_USERNAME = "Marty_Help_Bot"

MODEL_NAME = 'gemini-2.5-flash'

SYSTEM_PROMPT = (
    "Ты — Марти, ученый пес (той-пудель) и бортовой компьютер. Твоя миссия — помогать "
    "юному Командору в изучении Вселенной и подготовке к будущим полетам. "
    "Твои ответы всегда захватывающие, научно достоверные и понятны 8-летнему ребенку. "
    "Отвечай ОЧЕНЬ кратко (1-2 абзаца), просто и увлекательно. "
    "ПРАВИЛА ТВОЕГО ОБЩЕНИЯ: "
    "1. ШКОЛЬНЫЙ ПОМОЩНИК: Ты помогаешь с учебой, объясняя предметы через призму космоса. "
    "2. ФИНАНСОВАЯ ГРАМОТНОСТЬ: Учи распоряжаться ресурсами (бюджет экспедиции). "
    "3. КОДЕКС КОСМОНАВТА: Помощь родителям, уборка (протокол чистоты), вежливость. "
    "4. СКАНЕР БИОРИТМОВ: Здоровье (топливо) и сон (перезарядка). "
    "5. СТИЛЬ: Используй 'Командор', 'Пилот', 'Прием'. "
    "В конце задавай легкий вопрос для проверки готовности экипажа."
)

# 🟢 ВЕБ-СЕРВЕР ДЛЯ RENDER (Health Check)
app = Flask(__name__)
@app.route('/')
def home():
    return "<h1>Marty Scientist is Online</h1>"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- ОБРАБОТЧИКИ ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "🐾 Гав! Бортовой компьютер Марти запущен. Я на связи, Командор! Прием.")

@bot.message_handler(func=lambda m: True)
def handle_text(message):
    if not message.text:
        return

    user_id = message.from_user.id
    text_lower = message.text.lower()
    
    is_private = message.chat.type == 'private'
    # 🟢 Проверка: зовем ли мы Марти по имени
    is_called = text_lower.startswith('марти') or f"@{BOT_USERNAME.lower()}" in text_lower

    if is_private or is_called:
        bot.send_chat_action(message.chat.id, 'typing')
        
        # Очистка текста от обращения
        clean_text = re.sub(r'^марти[,.\s]*', '', message.text, flags=re.IGNORECASE).strip()
        
        if not clean_text and is_called:
            bot.reply_to(message, "🐾 Слушаю, Командор! Какие будут указания? Прием.")
            return

        try:
            user_memory = get_personal_log(user_id)
            prompt = f"ДАННЫЕ О КОМАНДОРЕ: {user_memory}\nВОПРОС: {clean_text}"
            
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
                config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT)
            )
            
            if response.text:
                bot.reply_to(message, response.text)
                
                # Обновление памяти (в фоне)
                if len(clean_text) > 5:
                    mem_task = f"Выдели новые важные факты из: '{clean_text}'. Если их нет — ответь 'НЕТ'."
                    mem_resp = client.models.generate_content(model=MODEL_NAME, contents=mem_task)
                    if "НЕТ" not in mem_resp.text.upper():
                        update_personal_log(user_id, mem_resp.text.strip())
            
        except Exception as e:
            print(f"❌ Ошибка: {e}", flush=True)
            bot.reply_to(message, "📡 Системный сбой! Передай инженеру, что датчики барахлят. Прием.")

def start_marty_autonomous():
    print("🚀 Марти-Ученый выходит на орбиту...")
    while True:
        try:
            bot.remove_webhook()
            bot.infinity_polling(skip_pending=True)
        except Exception as e:
            print(f"⚠️ Ошибка связи: {e}. Перезагрузка...")
            time.sleep(5)

if __name__ == "__main__":
    # 1. Запускаем "дыхание" для Render в отдельном потоке
    Thread(target=run_flask, daemon=True).start()
    
    # 2. Запускаем самого бота
    start_marty_autonomous()
