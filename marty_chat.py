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

# --- НАСТРОЙКИ ---
TOKEN = os.getenv('MARTY_BOT_TOKEN') 
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

client = genai.Client(api_key=GEMINI_API_KEY)
bot = telebot.TeleBot(TOKEN)

# 🟢 ГИПЕР-КАСКАД: Марти пробует их по очереди, пока не получит ответ
MODEL_CASCADE = [
    'gemini-2.5-pro',          # Уровень 1: Максимальный интеллект
    'gemini-2.5-flash',        # Уровень 2: Новейшая скорость
    'gemini-2.0-flash',        # Уровень 3: Стабильность
    'gemini-flash-latest',     # Уровень 4: Подстраховка
    'gemini-2.0-flash-lite',   # Уровень 5: Резерв
    'gemini-flash-lite-latest' # Уровень 6: Финальный рубеж
]

try:
    BOT_USERNAME = bot.get_me().username.lower()
except:
    BOT_USERNAME = "marty_help_bot"

# ЯДРО ЛИЧНОСТИ
SYSTEM_PROMPT = (
    "Ты — Марти, ученый пес (той-пудель) и бортовой ИИ. Твоя миссия — наставник для ребенка 8 лет. "
    "1. ЛИЧНОСТЬ: Ты мудрый и добрый. Обращайся к пользователю [NAME] или 'Командор' только иногда (не чаще раза в 3 сообщения). "
    "2. ТЕМЫ: Ты эксперт по космосу и школьный помощник. Учи помогать родителям, держать вещи в порядке и любить семью. "
    "3. БЕЗОПАСНОСТЬ: Темы 18+ СТРОГО запрещены. Вежливо уводи разговор в науку. "
    "4. ФОРМАТ: Пиши кратко (1-2 абзаца), просто, БЕЗ звездочек. В конце напиши 'Прием' и вопрос. "
    "Затем добавь разделитель '###MEM###' и напиши только новые важные факты о пользователе для памяти или 'НЕТ'."
)

app = Flask(__name__)
@app.route('/')
def home(): return "Marty Hyper-Cascade: Online"

def run_flask():
    try:
        port = int(os.environ.get("PORT", 10000))
        app.run(host='0.0.0.0', port=port)
    except: pass

# --- ОБРАБОТЧИКИ ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    name = message.from_user.first_name
    bot.reply_to(message, f"🐾 Гав! Системы каскадного резонанса запущены. Я на связи, {name}! Прием.")

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    bot.send_chat_action(message.chat.id, 'typing')
    
    try:
        user_memory = get_personal_log(user_id)
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        # Вызов Вижн-модуля (там свой каскад)
        analysis_result = analyze_image(downloaded_file, user_context=f"Имя: {user_name}. Память: {user_memory}")
        bot.reply_to(message, analysis_result)
        
        # Запись факта в память
        update_personal_log(user_id, f"Командор показал фото, Марти ответил: {analysis_result[:100]}")
    except Exception as e:
        bot.reply_to(message, "📡 Командор, все камеры перегреты. Попробуй через минуту! Прием.")

@bot.message_handler(func=lambda m: True)
def handle_text(message):
    if not message.text: return
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    text_lower = message.text.lower()
    
    is_private = message.chat.type == 'private'
    is_called = text_lower.startswith('марти') or f"@{BOT_USERNAME}" in text_lower

    if is_private or is_called:
        bot.send_chat_action(message.chat.id, 'typing')
        clean_text = re.sub(r'^марти[,.\s]*', '', message.text, flags=re.IGNORECASE).strip()
        
        response_sent = False
        # 🟢 ЦИКЛ ГИПЕР-КАСКАДА
        for model_variant in MODEL_CASCADE:
            try:
                user_memory = get_personal_log(user_id)
                current_prompt = SYSTEM_PROMPT.replace("[NAME]", user_name)
                
                response = client.models.generate_content(
                    model=model_variant,
                    contents=f"ДАННЫЕ: {user_memory}\nВОПРОС: {clean_text}",
                    config=types.GenerateContentConfig(system_instruction=current_prompt)
                )
                
                full_response = response.text
                if "###MEM###" in full_response:
                    user_text, mem_data = full_response.split("###MEM###")
                    bot.reply_to(message, user_text.strip())
                    if "НЕТ" not in mem_data.upper():
                        update_personal_log(user_id, mem_data.strip())
                else:
                    bot.reply_to(message, full_response.strip())
                
                response_sent = True
                break # Успех! Выходим из цикла моделей
                
            except Exception as e:
                if "429" in str(e) or "resource" in str(e).lower():
                    print(f"⚠️ {model_variant} перегрет, переключаюсь...")
                    continue
                else:
                    print(f"❌ Критическая ошибка в {model_variant}: {e}")
                    break

        if not response_sent:
            bot.reply_to(message, "📡 Ищу информацию по всем каналам связи, подожди чуток... Прием.")
            time.sleep(15)
            # Последняя попытка на самой стабильной модели
            try:
                ask_ai_final(message, user_id, user_name, clean_text)
            except:
                bot.reply_to(message, "⏳ Все системы перегружены. Сделаем паузу в одну минуту? Прием.")

def ask_ai_final(message, user_id, user_name, clean_text):
    # Финальный резервный запрос на Lite-модели
    user_memory = get_personal_log(user_id)
    current_prompt = SYSTEM_PROMPT.replace("[NAME]", user_name)
    response = client.models.generate_content(
        model='gemini-flash-lite-latest',
        contents=f"ДАННЫЕ: {user_memory}\nВОПРОС: {clean_text}",
        config=types.GenerateContentConfig(system_instruction=current_prompt)
    )
    bot.reply_to(message, response.text.split("###MEM###")[0].strip())

def start_marty_autonomous():
    print("🚀 Марти-Ученый: Многоядерный режим активирован.")
    while True:
        try:
            bot.remove_webhook()
            bot.infinity_polling(skip_pending=True)
        except Exception:
            time.sleep(5)

if __name__ == "__main__":
    Thread(target=run_flask, daemon=True).start()
    start_marty_autonomous()
