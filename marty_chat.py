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

MODEL_NAME = 'gemini-2.5-flash'

try:
    BOT_USERNAME = bot.get_me().username.lower()
except:
    BOT_USERNAME = "marty_help_bot"

# ЯДРО ЛИЧНОСТИ
SYSTEM_PROMPT = (
    "Ты — Марти, ученый пес (той-пудель) и бортовой ИИ. Твоя миссия — быть наставником. "
    "1. ЛИЧНОСТЬ: Ты мудрый и добрый. Обращайся к пользователю [NAME] или 'Командор' естественно. "
    "2. ТЕМЫ: Ты эксперт по космосу и школьный помощник (математика, физика, химия, биология). "
    "3. ВОСПИТАНИЕ: Учи помогать родителям, держать вещи в порядке и любить семью. "
    "4. БЕЗОПАСНОСТЬ: Темы 18+ строго запрещены. "
    "ОБЩЕНИЕ: Пиши кратко (1-2 абзаца), просто, БЕЗ звездочек. "
    "В конце — слово 'Прием' и короткий вопрос."
)

app = Flask(__name__)
@app.route('/')
def home(): return "Marty Auto-Retry: Online"

def run_flask():
    try:
        port = int(os.environ.get("PORT", 10000))
        app.run(host='0.0.0.0', port=port)
    except: pass

# --- ОБРАБОТЧИКИ ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    name = message.from_user.first_name
    bot.reply_to(message, f"🐾 Гав! Рад встрече, {name}! Я твой бортовой помощник Марти. Полетели к звездам? Прием!")

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    user_id = message.from_user.id
    bot.send_chat_action(message.chat.id, 'typing')
    
    def try_analyze():
        user_memory = get_personal_log(user_id)
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        analysis_result = analyze_image(downloaded_file, user_context=user_memory)
        bot.reply_to(message, analysis_result)
        update_personal_log(user_id, f"Марти видел фото и сказал: {analysis_result[:100]}...")

    try:
        try_analyze()
    except Exception as e:
        if "429" in str(e) or "resource_exhausted" in str(e).lower():
            bot.reply_to(message, "📡 Ищу информацию, подожди чуток! Около 15 секунд, я постараюсь ответить... Прием.")
            time.sleep(15)
            try: try_analyze()
            except: bot.reply_to(message, "📡 Командор, антенны всё еще перегреты. Попробуй через минуту! Прием.")
        else:
            bot.reply_to(message, "📡 Командор, не могу считать фото. Попробуй еще раз! Прием.")

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
        
        if not clean_text and is_called:
            bot.reply_to(message, f"🐾 Слушаю, {user_name}! Какие будут полетные задания? Прием.")
            return

        def ask_ai():
            user_memory = get_personal_log(user_id)
            current_prompt = SYSTEM_PROMPT.replace("[NAME]", user_name)
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=f"ДАННЫЕ: {user_memory}\nВОПРОС: {clean_text}",
                config=types.GenerateContentConfig(system_instruction=current_prompt)
            )
            bot.reply_to(message, response.text)
            
            time.sleep(1)
            if len(clean_text) > 5:
                mem_task = f"Выдели факты из: '{clean_text}'. Если нет — ответь 'НЕТ'."
                mem_resp = client.models.generate_content(model=MODEL_NAME, contents=mem_task)
                if "НЕТ" not in mem_resp.text.upper():
                    update_personal_log(user_id, mem_resp.text.strip())

        try:
            ask_ai()
        except Exception as e:
            if "429" in str(e) or "resource_exhausted" in str(e).lower():
                # 🟢 ВОТ ОНО: Авто-повтор
                bot.reply_to(message, "📡 Ищу информацию, подожди чуток! Около 15 секунд, я постараюсь ответить... Прием.")
                time.sleep(15)
                try: ask_ai()
                except: bot.reply_to(message, "⏳ Командор, перегрев слишком сильный. Дай мне минуту на перезагрузку. Прием.")
            else:
                bot.reply_to(message, "📡 Системный сбой! Попробуй чуть позже, Командор. Прием.")

def start_marty_autonomous():
    while True:
        try:
            bot.remove_webhook()
            bot.infinity_polling(skip_pending=True)
        except Exception:
            time.sleep(5)

if __name__ == "__main__":
    Thread(target=run_flask, daemon=True).start()
    start_marty_autonomous()
