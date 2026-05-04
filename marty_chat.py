import os
import telebot
import time
from google import genai
from google.genai import types
from database import get_personal_log, update_personal_log 

# --- НАСТРОЙКИ ---
TOKEN = os.getenv('MARTY_BOT_TOKEN') 
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

client = genai.Client(api_key=GEMINI_API_KEY)
bot = telebot.TeleBot(TOKEN)

# 🟢 ИЗМЕНЕНИЕ: Используем самое актуальное имя модели для новой библиотеки
MODEL_NAME = 'gemini-2.0-flash'

# Обновленный промпт без спецсимволов форматирования
SYSTEM_PROMPT = (
    "Ты — Марти, ученый пес (той-пудель) и бортовой компьютер. "
    "Твоя миссия — помогать юному Командору в изучении Вселенной. "
    "Пиши кратко (3-4 абзаца), научно и понятно 8-летнему ребенку. "
    "Не используй форматирование текста (никаких звездочек и подчеркиваний). "
    "Используй обращения 'Командор', 'Прием'. В конце задавай вопрос."
)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "🐾 Гав! Бортовой компьютер Марти запущен. Я готов к общению, Командор! Прием.")

@bot.message_handler(func=lambda m: True)
def handle_text(message):
    user_id = message.from_user.id
    bot.send_chat_action(message.chat.id, 'typing')
    
    try:
        user_memory = get_personal_log(user_id)
        prompt = f"ДАННЫЕ О КОМАНДОРЕ: {user_memory}\nВОПРОС: {message.text}"
        
        # 🟢 Подставили переменную MODEL_NAME
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT)
        )
        
        bot.reply_to(message, response.text)
        
        # Фоновое обновление памяти
        mem_task = f"Выдели новые факты из: '{message.text}'. Если нет — ответь 'НЕТ'."
        # 🟢 Подставили переменную MODEL_NAME
        mem_resp = client.models.generate_content(model=MODEL_NAME, contents=mem_task)
        if "НЕТ" not in mem_resp.text.upper():
            update_personal_log(user_id, mem_resp.text.strip())
            
    except Exception as e:
        if "429" in str(e):
            bot.reply_to(message, "⏳ Командор, антенны перегрелись от обилия информации! Дай мне 15 секунд на охлаждение систем.")
            time.sleep(15)
        else:
            print(f"❌ Ошибка Марти: {e}", flush=True) 
            bot.reply_to(message, f"📡 Системный сбой! Передай этот код инженеру:\n\n`{e}`", parse_mode='Markdown')

# --- ФУНКЦИЯ ДЛЯ ЗАПУСКА ИЗ ОСНОВНОГО ФАЙЛА ---
def start_marty_autonomous():
    print("🚀 Автономный Марти-помощник выходит на связь!")
    
    while True:
        try:
            bot.remove_webhook()
            bot.infinity_polling(skip_pending=True)
        except Exception as e:
            print(f"⚠️ Сбой систем связи Марти (ошибка {e}). Перезапуск через 5 секунд...")
            time.sleep(5)

if __name__ == "__main__":
    start_marty_autonomous()
