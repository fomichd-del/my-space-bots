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

# 🟢 ПЕРЕСТРОЕННЫЙ КАСКАД: Стабильные модели теперь ПЕРВЫМИ
MODEL_CASCADE = [
    'gemini-2.0-flash',        # Теперь это основной двигатель (очень стабильный)
    'gemini-2.5-flash',        # На подхвате
    'gemini-flash-latest',     # Резерв
    'gemini-2.0-flash-lite',   # Почти вечный двигатель
    'gemini-2.5-pro'           # Убираем в самый конец, чтобы не ломать систему
]

try:
    BOT_USERNAME = bot.get_me().username.lower()
except:
    BOT_USERNAME = "marty_help_bot"

SYSTEM_PROMPT = (
    "Ты — Марти, ученый пес (той-пудель) и ИИ-наставник для всех участников канала. "
    "1. ЛИЧНОСТЬ: Мудрый, добрый, вдохновляющий. Обращайся к пользователю [NAME] или 'Пилот'. "
    "2. ТЕМЫ: Космос, наука, школа. Объясняй просто. "
    "3. ВОСПИТАНИЕ: Пропагандируй порядок в комнате, помощь родителям и любовь к семье. "
    "4. ФОРМАТ: Пиши кратко (1-2 абзаца), БЕЗ звездочек. В конце — 'Прием' и вопрос. "
    "После ответа добавь '###MEM###' и новые факты для памяти или 'НЕТ'."
)

app = Flask(__name__)
@app.route('/')
def home(): return "Marty Core Fixed: Orbit Stable"

def run_flask():
    try:
        port = int(os.environ.get("PORT", 10000))
        app.run(host='0.0.0.0', port=port)
    except: pass

# --- ФУНКЦИЯ ЗАПРОСА С КАСКАДОМ ---
def get_marty_response(user_id, user_name, clean_text):
    user_memory = get_personal_log(user_id)
    current_prompt = SYSTEM_PROMPT.replace("[NAME]", user_name)
    
    for model_variant in MODEL_CASCADE:
        try:
            print(f"📡 Пробую модель: {model_variant}")
            response = client.models.generate_content(
                model=model_variant,
                contents=f"ДАННЫЕ: {user_memory}\nВОПРОС: {clean_text}",
                config=types.GenerateContentConfig(system_instruction=current_prompt)
            )
            if response.text:
                return response.text, model_variant
        except Exception as e:
            if "429" in str(e) or "resource" in str(e).lower():
                print(f"⚠️ {model_variant} перегрет...")
                continue
            print(f"❌ Ошибка {model_variant}: {e}")
    return None, None

# --- ОБРАБОТЧИКИ ---

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    user_id, user_name = message.from_user.id, message.from_user.first_name
    bot.send_chat_action(message.chat.id, 'typing')
    try:
        user_memory = get_personal_log(user_id)
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        # Передаем в зрение
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
        
        if not clean_text and is_called:
            bot.reply_to(message, f"🐾 Слушаю, {user_name}! Какие будут полетные задания? Прием.")
            return

        # Первая попытка
        full_response, used_model = get_marty_response(user_id, user_name, clean_text)
        
        # Если не вышло — ждем и пробуем ВТОРОЙ РАЗ
        if not full_response:
            bot.reply_to(message, "📡 Ищу информацию, подожди чуток! Постараюсь ответить быстро... Прием.")
            time.sleep(15)
            full_response, used_model = get_marty_response(user_id, user_name, clean_text)

        if full_response:
            if "###MEM###" in full_response:
                user_text, mem_data = full_response.split("###MEM###")
                bot.reply_to(message, user_text.strip())
                if "НЕТ" not in mem_data.upper():
                    update_personal_log(user_id, mem_data.strip())
            else:
                bot.reply_to(message, full_response.strip())
        else:
            bot.reply_to(message, "⏳ Командор, полная тишина в эфире. Дай мне минуту на перезагрузку реактора! Прием.")

def start_marty_autonomous():
    print("🚀 Марти-Ученый: Каскад 'Стабильная Орбита' активирован.")
    while True:
        try:
            bot.remove_webhook()
            bot.infinity_polling(skip_pending=True)
        except Exception:
            time.sleep(5)

if __name__ == "__main__":
    Thread(target=run_flask, daemon=True).start()
    start_marty_autonomous()
