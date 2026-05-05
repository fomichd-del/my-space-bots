import os
import telebot
import time
import re
from datetime import datetime, timedelta
from threading import Thread
from flask import Flask
from google import genai
from google.genai import types

# --- ИМПОРТЫ ---
from database import (get_personal_log, update_personal_log, add_xp, get_user_stats, 
                      get_rank_name, get_user_data, set_jackpot_claimed, spend_dust, 
                      check_and_update_streak, get_top_pilots)
from vision_module import analyze_image
from image_gen import generate_passport
# ---------------------------

# --- КОНФИГУРАЦИЯ ---
TOKEN = os.getenv('MARTY_BOT_TOKEN') 
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
CHANNEL_USERNAME = "@vladislav_space" # Название твоего канала

client = genai.Client(api_key=GEMINI_API_KEY)
bot = telebot.TeleBot(TOKEN)

daily_greetings = {} 

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

def get_time_context():
    now = datetime.utcnow() + timedelta(hours=3)
    hour = now.hour
    time_str = now.strftime("%H:%M")
    
    if 0 <= hour < 5:
        return f"{time_str} (Глубокая ночь. Пора спать)"
    elif 5 <= hour < 11:
        return f"{time_str} (Утро. Время подготовки)"
    elif 11 <= hour < 17:
        return f"{time_str} (День. Время для школы)"
    elif 17 <= hour < 23:
        return f"{time_str} (Вечер. Время отдыха)"
    else:
        return f"{time_str} (Ночь. Пора спать)"

def is_subscribed(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        if member.status in ['member', 'administrator', 'creator']:
            return True
        return False
    except Exception as e:
        return True 

def is_meteor_shower():
    # 5 - Суббота, 6 - Воскресенье
    return datetime.now().weekday() >= 5

# 🟢 ЯДРО ЛИЧНОСТИ
SYSTEM_PROMPT = (
    "Ты — Марти, ученый пес (той-пудель) и бортовой ИИ-наставник для пилотов. "
    "1. ЛИЧНОСТЬ: Ты мудрый, добрый, иногда говоришь 'Гав!'. "
    "Обращайся по имени [NAME]. Текущее звание: [RANK]. Время: [TIME]. [GREETING_RULE] "
    "2. АТТЕСТАЦИЯ: ЧЕМ ВЫШЕ ЗВАНИЕ [RANK], ТЕМ СТРОЖЕ ОЦЕНИВАЙ! НИКОГДА не давай пыль просто за слова, требуй фото. "
    "3. ИНСТРУКЦИЯ (ВАЖНО): Если пилот пишет 'инструкция', 'правила' или 'что такое пыль', отвечай подробно: "
    "'Привет! Вот правила Академии:\n✨ Звездная пыль — это топливо для званий и паспортов!\n📸 Как получить: присылай фото уборки, уроков или поделок.\n🎁 Секреты: в выходные — метеоритный дождь (пыль умножается!), а за стабильные отправки фото каждый день — бонусы! Ищи секретные предметы для джекпота! Чтобы увидеть топ пилотов, напиши мне слово РАДАР.' "
    "4. ТЕМЫ: Космос, школа, порядок. "
    "5. ЦЕНЗУРА (СТРОГО): Запрещено обсуждать секс, смерть, насилие, политику. Отвечай: 'Частоты заблокированы!' "
    "6. ФОРМАТ: 3-4 предложения (кроме инструкции). В конце 'Прием' и вопрос. Затем '###MEM###' и память."
)

app = Flask(__name__)
@app.route('/')
def home(): return "Marty Academy Core: Online"

def run_flask():
    try:
        port = int(os.environ.get("PORT", 10000))
        app.run(host='0.0.0.0', port=port)
    except: pass

def get_marty_response(user_id, user_name, clean_text, user_rank):
    user_memory = get_personal_log(user_id)
    time_info = get_time_context()
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    if daily_greetings.get(user_id) == current_date:
        greeting_rule = "ВНИМАНИЕ: Вы уже общались сегодня. СРАЗУ отвечай на вопрос, БЕЗ приветствий."
    else:
        greeting_rule = "Поприветствуй пилота."
        daily_greetings[user_id] = current_date
    
    current_prompt = SYSTEM_PROMPT.replace("[NAME]", user_name).replace("[TIME]", time_info).replace("[GREETING_RULE]", greeting_rule).replace("[RANK]", user_rank)
    
    for model_variant in MODEL_CASCADE:
        try:
            response = client.models.generate_content(
                model=model_variant,
                contents=f"ДАННЫЕ: {user_memory}\nВОПРОС: {clean_text}",
                config=types.GenerateContentConfig(system_instruction=current_prompt)
            )
            if response.text: return response.text
        except Exception: continue
    return None

# --- ОБРАБОТЧИКИ ---

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    user_id, user_name = message.from_user.id, message.from_user.first_name
    
    if not is_subscribed(user_id):
        bot.reply_to(message, f"🐾 Гав! Извини, Пилот! Сначала подпишись на канал {CHANNEL_USERNAME}!")
        return
    
    bot.send_chat_action(message.chat.id, 'typing')
    try:
        user_memory = get_personal_log(user_id)
        time_info = get_time_context()
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        old_xp = get_user_stats(user_id)
        old_rank = get_rank_name(old_xp)

        anti_cheat_context = (f"Имя: {user_name}. Звание: {old_rank}. Память: {user_memory}. "
                              "Строго оцени фото. Старшим званиям пыль только за идеальный порядок!")
        
        analysis_result = analyze_image(downloaded_file, user_context=anti_cheat_context)
        
        # --- ЛОГИКА НАГРАД (МЕТЕОРИТЫ, СТРИКИ, ДЖЕКПОТ) ---
        if "звездн" in analysis_result.lower() and "пыль" in analysis_result.lower():
            base_dust = 2 if is_meteor_shower() else 1
            total_dust = base_dust
            
            # Уведомление о метеоритном дожде
            if is_meteor_shower():
                bot.send_message(message.chat.id, "☄️ ВНИМАНИЕ: Зафиксирован Метеоритный дождь! Награда удвоена (Х2)!")

            # Стрики (Бонус за серию дней)
            streak = check_and_update_streak(user_id)
            if streak >= 3:
                total_dust += 1
                bot.send_message(message.chat.id, f"🔥 Серия миссий: {streak} дней подряд! Выдан бонус за стабильность!")
            
            # Секретный артефакт (Джекпот)
            if "джекпот" in analysis_result.lower():
                user_db_data = get_user_data(user_id)
                if not user_db_data["jackpot_claimed"]:
                    total_dust += 3 # Супер бонус
                    set_jackpot_claimed(user_id)
                    bot.send_message(message.chat.id, "🎰 СЕКРЕТНЫЙ АРТЕФАКТ НАЙДЕН! Выдан уникальный джекпот Академии!")
            
            # Не больше 4 пыли за раз (по твоему правилу)
            total_dust = min(total_dust, 4)
            add_xp(user_id, total_dust, user_name)
        # --------------------------------------------------
            
        bot.reply_to(message, analysis_result)
        
        new_xp = get_user_stats(user_id)
        new_rank = get_rank_name(new_xp)
        
        if old_rank != new_rank:
            bot.send_message(message.chat.id, f"🎉 Пилот {user_name} получает звание: {new_rank}!\nПечатаю удостоверение...")
            passport_bytes = generate_passport(user_name, new_rank)
            if passport_bytes: bot.send_photo(message.chat.id, passport_bytes)
                
    except Exception as e:
        bot.reply_to(message, "📡 Командор, помехи в видеоканале. Прием.")

@bot.message_handler(func=lambda m: True)
def handle_text(message):
    if not message.text: return
    user_id, user_name = message.from_user.id, message.from_user.first_name
    
    if not is_subscribed(user_id):
        bot.reply_to(message, f"🐾 Гав! Сначала подпишись на канал {CHANNEL_USERNAME}!")
        return

    text_lower = message.text.lower()
    clean_text = re.sub(r'^марти[,.\s]*', '', message.text, flags=re.IGNORECASE).strip()

    # --- РАДАР (ТАБЛИЦА ЛИДЕРОВ) ---
    if clean_text.lower() in ['радар', 'рейтинг', 'топ']:
        top_pilots = get_top_pilots(5)
        if not top_pilots:
            bot.reply_to(message, "📡 Радар пока пуст. Будь первым!")
            return
        
        radar_msg = "🏆 **РАДАР АКАДЕМИИ: ТОП-5 ПИЛОТОВ** 🏆\n\n"
        for i, (p_name, p_xp) in enumerate(top_pilots, 1):
            radar_msg += f"{i}. {p_name} — {p_xp} 💫 ({get_rank_name(p_xp)})\n"
        
        bot.reply_to(message, radar_msg, parse_mode="Markdown")
        return
    # -------------------------------

    is_private = message.chat.type == 'private'
    is_called = text_lower.startswith('марти') or f"@{BOT_USERNAME}" in text_lower

    if is_private or is_called:
        bot.send_chat_action(message.chat.id, 'typing')
        
        old_xp = get_user_stats(user_id)
        old_rank = get_rank_name(old_xp)
        
        full_response = get_marty_response(user_id, user_name, clean_text, old_rank)
        
        if not full_response:
            time.sleep(5)
            full_response = get_marty_response(user_id, user_name, clean_text, old_rank)

        if full_response:
            if "звездн" in full_response.lower() and "пыль" in full_response.lower():
                add_xp(user_id, 1, user_name)

            new_xp = get_user_stats(user_id)
            new_rank = get_rank_name(new_xp)

            if "###MEM###" in full_response:
                user_text, mem_data = full_response.split("###MEM###")
                bot.reply_to(message, user_text.strip())
            else:
                bot.reply_to(message, full_response.strip())

            if old_rank != new_rank:
                bot.send_message(message.chat.id, f"🎉 Пилот {user_name} получает звание: {new_rank}!\nПечатаю удостоверение...")
                passport_bytes = generate_passport(user_name, new_rank)
                if passport_bytes: bot.send_photo(message.chat.id, passport_bytes)
        else:
            bot.reply_to(message, "⏳ Командор, тишина в эфире. Прием.")

def start_marty_autonomous():
    print("🚀 Марти: Система 'Геймификация' запущена.")
    while True:
        try:
            bot.remove_webhook()
            bot.infinity_polling(skip_pending=True)
        except Exception:
            time.sleep(5)

if __name__ == "__main__":
    Thread(target=run_flask, daemon=True).start()
    start_marty_autonomous()
