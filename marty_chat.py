import os
import telebot
import time
import re
from datetime import datetime, timedelta
from threading import Thread
from flask import Flask
from google import genai
from google.genai import types

# --- ДОБАВЛЕННЫЕ ИМПОРТЫ ---
from database import get_personal_log, update_personal_log, add_xp, get_user_stats, get_rank_name
from vision_module import analyze_image
from image_gen import generate_passport
# ---------------------------

# --- КОНФИГУРАЦИЯ ---
TOKEN = os.getenv('MARTY_BOT_TOKEN') 
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

client = genai.Client(api_key=GEMINI_API_KEY)
bot = telebot.TeleBot(TOKEN)

# ГИПЕР-КАСКАД (Lite на передовой для скорости)
MODEL_CASCADE = [
    'gemini-2.0-flash-lite',
    'gemini-2.0-flash',
    'gemini-2.5-flash',
    'gemini-flash-latest',
    'gemini-2.5-pro'
]

try:
    BOT_USERNAME = bot.get_me().username.lower()
except:
    BOT_USERNAME = "marty_help_bot"

# 🟢 ФУНКЦИЯ ОПРЕДЕЛЕНИЯ ВРЕМЕНИ (UTC+3 для Чернигова)
def get_time_context():
    now = datetime.utcnow() + timedelta(hours=3)
    hour = now.hour
    time_str = now.strftime("%H:%M")
    
    if 0 <= hour < 5:
        return f"{time_str} (Глубокая ночь. Удивляйся, почему пилот не спит)"
    elif 5 <= hour < 11:
        return f"{time_str} (Утро. Время подготовки к экспедиции и завтрака)"
    elif 11 <= hour < 17:
        return f"{time_str} (День. Время для науки и школы)"
    elif 17 <= hour < 23:
        return f"{time_str} (Вечер. Время отдыха и порядка)"
    else:
        return f"{time_str} (Ночь. Пора спать)"

# 🟢 ЯДРО ЛИЧНОСТИ
SYSTEM_PROMPT = (
    "Ты — Марти, ученый пес (той-пудель) и бортовой ИИ-наставник для пилотов. "
    "1. ЛИЧНОСТЬ: Ты мудрый, добрый, иногда говоришь 'Гав!' или 'Виляю хвостом!'. "
    "Обращайся по имени [NAME] или 'Пилот'. Время суток: [TIME]. "
    "2. 10 ЗВАНИЙ АКАДЕМИИ: 1.Космический Кадет, 2.Навигатор Орбиты, 3.Бортинженер, "
    "4.Астро-Исследователь, 5.Учёный Пилот, 6.Капитан Корабля, 7.Командор Галактики, "
    "8.Адмирал Флота, 9.Академик Космоса, 10.Верный Помощник Марти. "
    "Начисляй 'звездную пыль' за успехи. По достижении цели объявляй новое звание! "
    "3. ТЕМЫ: Космос, школа, порядок в комнате, помощь семье. "
    "4. КОДЫ: 'ПОЕХАЛИ!' — факт о космосе. 'КОСТОЧКА' — шутка. "
    "5. ФОРМАТ: СТРОГО 3-4 предложения. Без звездочек. В конце 'Прием' и вопрос. "
    "Затем разделитель '###MEM###' и новые факты для памяти или 'НЕТ'."
)

app = Flask(__name__)
@app.route('/')
def home(): return "Marty Academy Core: Online"

def run_flask():
    try:
        port = int(os.environ.get("PORT", 10000))
        app.run(host='0.0.0.0', port=port)
    except: pass

def get_marty_response(user_id, user_name, clean_text):
    user_memory = get_personal_log(user_id)
    time_info = get_time_context()
    current_prompt = SYSTEM_PROMPT.replace("[NAME]", user_name).replace("[TIME]", time_info)
    
    for model_variant in MODEL_CASCADE:
        try:
            print(f"📡 Запрос к: {model_variant}")
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
        time_info = get_time_context()
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
            # --- БЛОК АКАДЕМИИ И ЗВАНИЙ (ДОБАВЛЕНО) ---
            old_xp = get_user_stats(user_id)
            old_rank = get_rank_name(old_xp)

            # Если Марти хвалит и дает пыль — начисляем +1 XP
            if "звездн" in full_response.lower() and "пыль" in full_response.lower():
                add_xp(user_id, 1, user_name)

            # Проверяем звание ПОСЛЕ возможного начисления
            new_xp = get_user_stats(user_id)
            new_rank = get_rank_name(new_xp)
            # ------------------------------------------

            if "###MEM###" in full_response:
                user_text, mem_data = full_response.split("###MEM###")
                bot.reply_to(message, user_text.strip())
                if "НЕТ" not in mem_data.upper() and len(mem_data.strip()) > 2:
                    update_personal_log(user_id, mem_data.strip())
            else:
                bot.reply_to(message, full_response.strip())

            # --- ВАУ-ЭФФЕКТ: ПЕЧАТЬ ПАСПОРТА (ДОБАВЛЕНО) ---
            if old_rank != new_rank:
                bot.send_message(message.chat.id, f"🎉 Внимание! Пилот {user_name} получает новое звание: {new_rank}!\nПечатаю официальное удостоверение...")
                passport_bytes = generate_passport(user_name, new_rank)
                if passport_bytes:
                    bot.send_photo(message.chat.id, passport_bytes)
            # -----------------------------------------------

        else:
            bot.reply_to(message, "⏳ Командор, тишина в эфире. Прием.")

def start_marty_autonomous():
    print("🚀 Марти: Система 'Стабильная Орбита 2.0' запущена.")
    while True:
        try:
            bot.remove_webhook()
            bot.infinity_polling(skip_pending=True)
        except Exception:
            time.sleep(5)

if __name__ == "__main__":
    Thread(target=run_flask, daemon=True).start()
    start_marty_autonomous()
