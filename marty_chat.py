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

# 🟢 ГИПЕР-КАСКАД: Марти пробует их по очереди при ошибке 429
MODEL_CASCADE = [
    'gemini-2.5-pro', 'gemini-2.5-flash', 'gemini-2.0-flash',
    'gemini-flash-latest', 'gemini-2.0-flash-lite', 'gemini-flash-lite-latest'
]

try:
    BOT_USERNAME = bot.get_me().username.lower()
except:
    BOT_USERNAME = "marty_help_bot"

# ЯДРО ЛИЧНОСТИ ДЛЯ ВСЕХ ПОЛЬЗОВАТЕЛЕЙ
SYSTEM_PROMPT = (
    "Ты — Марти, ученый пес (той-пудель) и ИИ-наставник для всех участников канала. "
    "1. ЛИЧНОСТЬ: Ты мудрый и добрый. Обращайся к пользователю [NAME] или 'Пилот' естественно. "
    "2. ТЕМЫ: Ты эксперт по космосу и школьный помощник. Учи помогать родителям и держать вещи в порядке. "
    "3. БЕЗОПАСНОСТЬ: Темы 18+ СТРОГО запрещены. Ты — научный и добрый ИИ. "
    "4. ФОРМАТ: Пиши кратко (1-2 абзаца), БЕЗ звездочек. В конце напиши 'Прием' и вопрос. "
    "Затем добавь разделитель '###MEM###' и новые важные факты для памяти или 'НЕТ'."
)

app = Flask(__name__)
@app.route('/')
def home(): return "Marty Hyper-Drive: Ready for All Pilots"

def run_flask():
    try:
        port = int(os.environ.get("PORT", 10000))
        app.run(host='0.0.0.0', port=port)
    except: pass

# --- ОБРАБОТЧИКИ ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    name = message.from_user.first_name
    bot.reply_to(message, f"🐾 Гав! Рад видеть тебя в нашем экипаже, {name}! Я Марти. Полетели к звездам? Прием!")

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    user_id, user_name = message.from_user.id, message.from_user.first_name
    bot.send_chat_action(message.chat.id, 'typing')
    try:
        user_memory = get_personal_log(user_id)
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        analysis_result = analyze_image(downloaded_file, user_context=f"Имя: {user_name}. Память: {user_memory}")
        bot.reply_to(message, analysis_result)
        update_personal_log(user_id, f"Пилот показал фото, Марти ответил: {analysis_result[:100]}")
    except Exception:
        bot.reply_to(message, "📡 Командор, все камеры перегреты. Попробуй через минуту! Прием.")

@bot.message_handler(func=lambda m: True)
def handle_text(message):
    if not message.text: return
    user_id, user_name = message.from_user.id, message.from_user.first_name
    text_lower = message.text.lower()
    
    is_private = message.chat.type == 'private'
    is_called = text_lower.startswith('марти') or f"@{BOT_USERNAME}" in text_lower

    if is_private or is_called:
        bot.send_chat_action(message.chat.id, 'typing')
        clean_text = re.sub(r'^марти[,.\s]*', '', message.text, flags=re.IGNORECASE).strip()
        
        response_sent = False
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
                break
            except Exception as e:
                if "429" in str(e) or "resource" in str(e).lower(): continue
                else: break

        if not response_sent:
            bot.reply_to(message, "📡 Ищу информацию, подожди чуток! Постараюсь ответить быстро... Прием.")
            time.sleep(15)
            try:
                # Финальный резервный запрос
                response = client.models.generate_content(
                    model='gemini-2.0-flash-lite',
                    contents=f"ВОПРОС: {clean_text}",
                    config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT.replace("[NAME]", user_name))
                )
                bot.reply_to(message, response.text.split("###MEM###")[0].strip())
            except:
                bot.reply_to(message, "⏳ Командор, все антенны перегружены. Дай мне минуту на отдых! Прием.")

def start_marty_autonomous():
    print("🚀 Марти-Ученый: Каскад для всего экипажа запущен.")
    while True:
        try:
            bot.remove_webhook()
            bot.infinity_polling(skip_pending=True)
        except Exception:
            time.sleep(5)

if __name__ == "__main__":
    Thread(target=run_flask, daemon=True).start()
    start_marty_autonomous()
