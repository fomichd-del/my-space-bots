import os
import telebot
import time
import re
from google import genai
from google.genai import types
from database import get_personal_log, update_personal_log 

# --- НАСТРОЙКИ ---
TOKEN = os.getenv('MARTY_BOT_TOKEN') 
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

client = genai.Client(api_key=GEMINI_API_KEY)
bot = telebot.TeleBot(TOKEN)

# 🟢 УСТАНОВЛЕН НОВЕЙШИЙ ДВИГАТЕЛЬ
MODEL_NAME = 'gemini-2.5-flash'

# 🟢 ОБНОВЛЕННОЕ ЯДРО ЛИЧНОСТИ МАРТИ
SYSTEM_PROMPT = (
    "Ты — Марти, ученый пес (той-пудель) и бортовой ИИ. "
    "Твои задачи: рассказывать Командору (8 лет) про космос, помогать со школьной программой (математика, физика, химия, биология, анатомия), "
    "учить беречь природу, быть добрым, уважать и всегда помогать родителям. "
    "СТРОГОЕ ПРАВИЛО: категорически запрещены темы 18+ и разговоры для взрослых. "
    "Отвечай ОЧЕНЬ кратко и динамично (максимум 1-2 небольших абзаца). Говори простым и увлекательным языком. "
    "Не используй форматирование текста (никаких звездочек и подчеркиваний). "
    "Используй обращения 'Командор' и слово 'Прием'. В конце всегда задавай только один короткий вопрос."
)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "🐾 Гав! Бортовой компьютер Марти запущен. Я на связи и готов к работе, Командор! Прием.")

@bot.message_handler(func=lambda m: True)
def handle_text(message):
    user_id = message.from_user.id
    text_lower = message.text.lower()
    bot_username = bot.get_me().username.lower()

    # 🟢 ПРОВЕРКА: Личный чат ИЛИ обращение по имени/тегу
    is_private = message.chat.type == 'private'
    is_called = text_lower.startswith('марти') or f"@{bot_username}" in text_lower

    if is_private or is_called:
        bot.send_chat_action(message.chat.id, 'typing')
        
        # Очищаем текст от имени "Марти" в начале, чтобы ИИ не отвлекался
        clean_text = re.sub(r'^марти[,.\s]*', '', message.text, flags=re.IGNORECASE).strip()
        
        try:
            user_memory = get_personal_log(user_id)
            prompt = f"ДАННЫЕ О КОМАНДОРЕ: {user_memory}\nВОПРОС: {clean_text}"
            
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
                config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT)
            )
            
            bot.reply_to(message, response.text)
            
            # Фоновое обновление памяти (только если вопрос был содержательным)
            if len(clean_text) > 5:
                mem_task = f"Выдели новые факты из: '{clean_text}'. Если нет — ответь 'НЕТ'."
                mem_resp = client.models.generate_content(model=MODEL_NAME, contents=mem_task)
                if "НЕТ" not in mem_resp.text.upper():
                    update_personal_log(user_id, mem_resp.text.strip())
            
        except Exception as e:
            err_str = str(e)
            if "429" in err_str:
                bot.reply_to(message, "⏳ Командор, антенны перегрелись! Дай мне 15 секунд на охлаждение.")
                time.sleep(15)
            else:
                print(f"❌ Ошибка Марти: {e}", flush=True) 
                bot.reply_to(message, "📡 Системный сбой! Попробуй повторить запрос через минуту.")

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
