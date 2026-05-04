import os
import telebot
from google import genai
from google.genai import types
from database import get_personal_log, update_personal_log 

# --- НАСТРОЙКИ ---
# ВАЖНО: Убедитесь, что в Render эта переменная указывает на токен @Marty_Help_Bot
TOKEN = os.getenv('MARTY_BOT_TOKEN') 
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

client = genai.Client(api_key=GEMINI_API_KEY)
bot = telebot.TeleBot(TOKEN)

SYSTEM_PROMPT = (
    "Ты — Марти, ученый пес (той-пудель) и бортовой компьютер. "
    "Твоя миссия — помогать юному Командору в изучении Вселенной. "
    "Пиши кратко (3-4 абзаца), научно и понятно 8-летнему ребенку. "
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
        response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents=[f"ДАННЫЕ О КОМАНДОРЕ: {user_memory}", f"ВОПРОС: {message.text}"],
            config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT)
        )
        bot.reply_to(message, response.text, parse_mode='Markdown')
        
        # Обновление памяти
        mem_task = f"Выдели новые факты из: '{message.text}'. Если нет — ответь 'НЕТ'."
        mem_resp = client.models.generate_content(model='gemini-1.5-flash', contents=mem_task)
        if "НЕТ" not in mem_resp.text.upper():
            update_personal_log(user_id, mem_resp.text.strip())
            
    except Exception as e:
        print(f"Ошибка: {e}")
        bot.reply_to(message, "📡 Помехи в эфире! Попробуй еще раз через минуту.")

if __name__ == "__main__":
    print("🚀 Автономный Марти-помощник запущен!")
    bot.remove_webhook()
    bot.infinity_polling(skip_pending=True)
