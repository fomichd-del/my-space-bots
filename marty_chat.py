import os
import telebot
import time
import re
from datetime import datetime, timedelta # 🟢 Новое для времени
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

MODEL_CASCADE = [
    'gemini-2.0-flash-lite',
    'gemini-2.0-flash',
    'gemini-2.5-flash',
    'gemini-2.5-pro'
]

try:
    BOT_USERNAME = bot.get_me().username.lower()
except:
    BOT_USERNAME = "marty_help_bot"

# 🟢 ФУНКЦИЯ ОПРЕДЕЛЕНИЯ ВРЕМЕНИ
def get_time_context():
    # Сдвиг времени (например, +3 для Москвы/Киева). Измени число, если нужно.
    now = datetime.utcnow() + timedelta(hours=3)
    hour = now.hour
    time_str = now.strftime("%H:%M")
    
    if 0 <= hour < 5:
        return f"{time_str} (Глубокая ночь. Удивляйся, почему пилот не в криокамере/не спит)"
    elif 5 <= hour < 11:
        return f"{time_str} (Утро. Время подготовки к экспедиции и завтрака)"
    elif 11 <= hour < 17:
        return f"{time_str} (День. Самое время для науки, школы и помощи родителям)"
    elif 17 <= hour < 23:
        return f"{time_str} (Вечер. Время отдыха и наведения порядка в отсеке)"
    else:
        return f"{time_str} (Ночь. Пора гасить иллюминаторы)"

# ЯДРО ЛИЧНОСТИ
SYSTEM_PROMPT = (

    "Ты — Марти, ученый пес (той-пудель) и бортовой наставник для всех пилотов канала. "

    "1. ЛИЧНОСТЬ: Ты мудрый, но ведешь себя как собака: иногда говори 'Гав!', 'Тяв!' или 'Виляю хвостом от радости!'. "

    "Обращайся к пользователю [NAME] или 'Пилот' не чаще раза в 3 сообщения. Время суток: [TIME]. "

    "2. ИГРА И ЗВАНИЯ: Хвали за успехи и присваивай звания (Кадет, Навигатор, Исследователь). "

    "Выдавай 'звездную пыль' за помощь родителям и порядок в комнате. Предлагай 'Миссии дня' (уборка, учеба). "

    "3. СЕКРЕТНЫЕ КОДЫ: Если пишут 'ПОЕХАЛИ!' — выдай самый крышесносный факт о космосе. "

    "Если пишут 'КОСТОЧКА' — расскажи добрую космическую шутку. "

    "4. ПАМЯТЬ И ЭМОЦИИ: Считывай настроение пилота. Хвали за прошлые победы, найденные в ДАННЫХ. "

    "Если глубокая ночь — пожури, что пилот не спит. "

    "5. ТЕМЫ: Космос, школа, порядок в комнате, помощь семье. "

    "6. ФОРМАТ: СТРОГО 3-4 коротких предложения. Без звездочек. В конце 'Прием' и вопрос. "

    "Затем разделитель '###MEM###' и новые факты для памяти или 'НЕТ'."

)

app = Flask(__name__)
@app.route('/')
def home(): return "Marty Time-Aware: Online"

def run_flask():
    try:
        port = int(os.environ.get("PORT", 10000))
        app.run(host='0.0.0.0', port=port)
    except: pass

def get_marty_response(user_id, user_name, clean_text):
    user_memory = get_personal_log(user_id)
    # 🟢 Вставляем время суток прямо в системную инструкцию
    time_info = get_time_context()
    current_prompt = SYSTEM_PROMPT.replace("[NAME]", user_name).replace("[TIME]", time_info)
    
    for model_variant in MODEL_CASCADE:
        try:
            response = client.models.generate_content(
                model=model_variant,
                contents=f"ДАННЫЕ: {user_memory}\nВОПРОС: {clean_text}",
                config=types.GenerateContentConfig(system_instruction=current_prompt)
            )
            if response.text:
                return response.text
        except Exception as e:
            if "429" in str(e): continue
            print(f"❌ Ошибка {model_variant}: {e}")
    return None

# --- ОБРАБОТЧИКИ ---

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    user_id, user_name = message.from_user.id, message.from_user.first_name
    bot.send_chat_action(message.chat.id, 'typing')
    try:
        user_memory = get_personal_log(user_id)
        time_info = get_time_context() # 🟢 Добавляем время и в зрение
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        analysis_result = analyze_image(downloaded_file, user_context=f"Имя: {user_name}. Память: {user_memory}. Время: {time_info}")
        bot.reply_to(message, analysis_result)
        update_personal_log(user_id, f"Пилот показал фото в {time_info[:5]}")
    except Exception:
        bot.reply_to(message, "📡 Командор, помехи в видеоканале. Прием.")

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
        
        full_response = get_marty_response(user_id, user_name, clean_text)
        
        if not full_response:
            bot.reply_to(message, "📡 Ищу информацию, подожди чуток... Прием.")
            time.sleep(15)
            full_response = get_marty_response(user_id, user_name, clean_text)

        if full_response:
            if "###MEM###" in full_response:
                user_text, mem_data = full_response.split("###MEM###")
                bot.reply_to(message, user_text.strip())
                if "НЕТ" not in mem_data.upper() and len(mem_data.strip()) > 2:
                    update_personal_log(user_id, mem_data.strip())
            else:
                bot.reply_to(message, full_response.strip())
        else:
            bot.reply_to(message, "⏳ Командор, тишина в эфире. Прием.")

def start_marty_autonomous():
    print("🚀 Марти: Хранитель Времени запущен.")
    while True:
        try:
            bot.remove_webhook()
            bot.infinity_polling(skip_pending=True)
        except Exception:
            time.sleep(5)

if __name__ == "__main__":
    Thread(target=run_flask, daemon=True).start()
    start_marty_autonomous()
