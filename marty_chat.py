import os
import telebot
import time
import re
import urllib.parse
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
CHANNEL_USERNAME = "@vladislav_space"
LOG_CHAT_ID = "-1003756164148" 

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

def send_log(error_text):
    try:
        now = (datetime.utcnow() + timedelta(hours=3)).strftime("%Y-%m-%d %H:%M:%S")
        log_msg = f"🚨 **ОТЧЕТ СИСТЕМЫ ОРИОН**\n📅 Время: `{now}`\n🔍 **Детали:** `{error_text}`"
        bot.send_message(LOG_CHAT_ID, log_msg, parse_mode="Markdown")
    except: pass

def get_time_context():
    now = datetime.utcnow() + timedelta(hours=3)
    hour = now.hour
    time_str = now.strftime("%H:%M")
    if 0 <= hour < 5: return f"{time_str} (Глубокая ночь)"
    elif 5 <= hour < 11: return f"{time_str} (Утро)"
    elif 11 <= hour < 17: return f"{time_str} (День)"
    elif 17 <= hour < 23: return f"{time_str} (Вечер)"
    else: return f"{time_str} (Ночь)"

def is_subscribed(user_id):
    if user_id == 777000 or user_id < 0: return True
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except: return True 

def is_meteor_shower():
    return datetime.now().weekday() >= 5

def is_very_first_time(user_id):
    user_data = get_user_data(user_id)
    user_memory = get_personal_log(user_id)
    return user_data['xp'] == 0 and "Данных пока нет" in user_memory

# 🟢 ГЛОБАЛЬНЫЙ УСТАВ АКАДЕМИИ ОРИОН
def send_welcome_instruction(chat_id, user_id, user_name):
    instruction = (
        f"🐾 **УСТАВ АКАДЕМИИ ОРИОН (ВЕРСИЯ 2.0)** 🐾\n\n"
        f"🚀 **МИССИЯ ПИЛОТА {user_name.upper()}:**\n"
        "Я — Марти, ученый пес и твой бортовой наставник. Мы готовимся к великим полетам! "
        "Здесь ты учишься дисциплине, порядку и науке. Ранги выдаются за упорство!\n\n"
        "📜 **ПРАВИЛА БОРТА:**\n"
        "✅ **РАЗРЕШЕНО:** Изучать Вселенную, присылать фото-отчеты о чистоте (Протокол жилого модуля) и успехах в учебе.\n"
        "❌ **ЗАПРЕЩЕНО:** Темы 18+, вредные привычки, грубость и обман Марти.\n\n"
        "💫 **РАНГИ (XP ДЛЯ ПАСПОРТА):**\n"
        "Кадет (0) | Навигатор (15) | Бортинженер (40) | Исследователь (80) | Ученый Пилот (130) | "
        "Капитан (200) | Командор (300) | Адмирал (450) | Академик (650) | Помощник Марти (900+)\n\n"
        "💰 **ЭКОНОМИКА:**\n"
        "• **XP в Радаре:** Твой общий стаж.\n"
        "• **Кошелек:** Пыль для команды 'НАРИСУЙ [идея]' (цена 5).\n\n"
        "Готов к тренировке? Прием!"
    )
    bot.send_message(chat_id, instruction, parse_mode="Markdown")
    update_personal_log(user_id, "Пилот зачислен и изучил Кодекс Космонавта.")

# 🟢 ЯДРО ЛИЧНОСТИ (ОБЪЕДИНЕННЫЙ ПРОМПТ)
SYSTEM_PROMPT = (
    "Ты — Марти, ученый пес (той-пудель) и бортовой наставник Академии Орион. "
    "Твоя миссия — помогать людям в изучении Вселенной. "
    "Тон: захватывающий, научный, позитивный. Обращайся 'Командор' или 'Пилот'. "
    
    "ПРАВИЛА ОБЩЕНИЯ: "
    "1. ШКОЛА: Математика — расчет траекторий. Химия. Биология. Геометрия. Обучения английскому и китайскому языку. Физика — звездное топливо. Анатомия — работа тела в невесомости. "
    "2. ЭКОНОМИКА: XP в Радаре — это стаж и Ранг: [RANK]. Кошелек: [WALLET] — это бюджет экспедиции для команды 'Нарисуй'. "
    "3. КОДЕКС: Помощь родителям — поддержка старших офицеров. Уборка — Протокол чистоты жилого модуля. Порядок спасает жизнь! "
    "4. ЗДОРОВЬЕ: Овощи — высокоэнергетическое топливо. Зарядка — проверка гидравлики скафандра. Сон — зарядка солнечных батарей. "
    "5. АТТЕСТАЦИЯ (ХАРДКОР): Если XP > 50, будь суровее. Требуй реальных успехов для выдачи пыли. "
    "6. ПАМЯТЬ: Используй прошлые успехи и хобби Владика из логов. "
    
    "🛑 ВЕЛИКИЙ ФИЛЬТР (КРИТИЧЕСКИ): "
    "КАТЕГОРИЧЕСКИ ЗАПРЕЩЕНО обсуждать темы 18+, алкоголь, сигареты, наркотики, смерть, политику, насилие и любые 'взрослые' вредности. "
    "На такие запросы отвечай: 'Пилот, эти частоты заблокированы протоколом безопасности Академии!'. "
    
    "[GREETING_RULE] "
    "ФОРМАТ: 3-4 абзаца. В конце задай вопрос 'экипажу' и напиши 'Прием!'."
)

app = Flask(__name__)
@app.route('/')
def home(): return "Orion Core: Online"

def run_flask():
    try:
        port = int(os.environ.get("PORT", 10000))
        app.run(host='0.0.0.0', port=port)
    except: pass

def get_marty_response(user_id, user_name, clean_text, user_rank, wallet_balance):
    user_memory = get_personal_log(user_id)
    time_info = get_time_context()
    current_date = datetime.now().strftime("%Y-%m-%d")
    if daily_greetings.get(user_id) == current_date:
        greeting_rule = "!!! УЖЕ здоровались сегодня. ЗАПРЕЩЕНО писать 'Привет'! Начинай сразу по сути вопроса! !!!"
    else:
        greeting_rule = "Первое сообщение за день. Поздоровайся с пилотом."
        daily_greetings[user_id] = current_date
    
    current_prompt = SYSTEM_PROMPT.replace("[NAME]", user_name).replace("[TIME]", time_info).replace("[GREETING_RULE]", greeting_rule).replace("[RANK]", user_rank).replace("[WALLET]", str(wallet_balance))
    
    for model_variant in MODEL_CASCADE:
        try:
            response = client.models.generate_content(model=model_variant, contents=f"ДАННЫЕ: {user_memory}\nВОПРОС: {clean_text}", config=types.GenerateContentConfig(system_instruction=current_prompt))
            if response.text: return response.text
        except Exception as e:
            send_log(f"Сбой модели {model_variant}: {e}")
            continue
    return None

# --- ОБРАБОТЧИКИ ---

@bot.message_handler(commands=['start', 'help'])
def handle_start(message):
    user_id, user_name = message.from_user.id, message.from_user.first_name
    if not is_subscribed(user_id):
        bot.reply_to(message, f"🐾 Подпишись на канал {CHANNEL_USERNAME}!")
        return
    send_welcome_instruction(message.chat.id, user_id, user_name)

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    user_id, user_name = message.from_user.id, message.from_user.first_name
    if not is_subscribed(user_id): return
    if is_very_first_time(user_id):
        send_welcome_instruction(message.chat.id, user_id, user_name)
        return
    bot.send_chat_action(message.chat.id, 'typing')
    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        old_xp = get_user_stats(user_id)
        old_rank = get_rank_name(old_xp)
        analysis_result = analyze_image(downloaded_file, user_context=f"Имя: {user_name}, Звание: {old_rank}")
        
        if "звездн" in analysis_result.lower() and "пыль" in analysis_result.lower():
            total_dust = 2 if is_meteor_shower() else 1
            if is_meteor_shower(): bot.send_message(message.chat.id, "☄️ МЕТЕОРИТНЫЙ ДОЖДЬ (х2)!")
            streak = check_and_update_streak(user_id)
            if streak >= 3: total_dust += 1
            if "джекпот" in analysis_result.lower():
                user_db_data = get_user_data(user_id)
                if not user_db_data["jackpot_claimed"]:
                    total_dust += 3 
                    set_jackpot_claimed(user_id)
                    bot.send_message(message.chat.id, "🎰 ДЖЕКПОТ!")
            add_xp(user_id, min(total_dust, 4), user_name)
        
        bot.reply_to(message, analysis_result)
        new_xp = get_user_stats(user_id)
        if get_rank_name(old_xp) != get_rank_name(new_xp):
            bot.send_message(message.chat.id, f"🎉 Ранг повышен: {get_rank_name(new_xp)}!")
            p = generate_passport(user_name, get_rank_name(new_xp))
            if p: bot.send_photo(message.chat.id, p)
    except Exception as e:
        send_log(f"Ошибка в handle_photo: {e}")
        bot.reply_to(message, "📡 Помехи в видеоканале.")

@bot.message_handler(func=lambda m: True)
def handle_text(message):
    if not message.text: return
    user_id, user_name = message.from_user.id, message.from_user.first_name
    if not is_subscribed(user_id): return
    if is_very_first_time(user_id):
        send_welcome_instruction(message.chat.id, user_id, user_name)
        return
    text_lower = message.text.lower()
    is_called = text_lower.startswith('марти') or f"@{BOT_USERNAME}" in text_lower
    
    if message.chat.type == 'private' or is_called:
        bot.send_chat_action(message.chat.id, 'typing')
        clean_text = re.sub(r'^марти[,.\s]*', '', message.text, flags=re.IGNORECASE).strip()
        
        if clean_text.lower() in ['радар', 'рейтинг', 'топ']:
            top = get_top_pilots(5)
            msg = "🏆 **РАДАР АКАДЕМИИ ОРИОН** 🏆\n\n"
            for i, (n, x) in enumerate(top, 1): msg += f"{i}. {n} — {x} 💫 ({get_rank_name(x)})\n"
            bot.reply_to(message, msg, parse_mode="Markdown")
            return

        if any(w in clean_text.lower() for w in ['нарисуй', 'сгенерируй', 'архив']):
            data = get_user_data(user_id)
            if data['spendable_dust'] < 5:
                bot.reply_to(message, f"🐾 Нужно 5 пыли! У тебя сейчас {data['spendable_dust']}.")
                return
            bot.send_chat_action(message.chat.id, 'upload_photo')
            c_p = "Censor: masterpiece, highly detailed, kid-friendly. If unsafe return CENSORED."
            try:
                resp = client.models.generate_content(model='gemini-1.5-flash', contents=clean_text, config=types.GenerateContentConfig(system_instruction=c_p))
                eng = resp.text.strip()
                if "CENSORED" in eng.upper():
                    bot.reply_to(message, "🚨 Блокировка цензурой!")
                    return
                if spend_dust(user_id, 5):
                    url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(eng)}?width=1024&height=1024&nologo=true&seed={int(time.time())}"
                    bot.send_photo(message.chat.id, url, caption="🎨 Архив открыт!")
            except Exception as e:
                send_log(f"Ошибка Архива: {e}")
                bot.reply_to(message, "📡 Ошибка связи.")
            return

        old_xp = get_user_stats(user_id)
        u_d = get_user_data(user_id)
        resp = get_marty_response(user_id, user_name, clean_text, get_rank_name(old_xp), u_d['spendable_dust'])
        if resp:
            if "звездн" in resp.lower() and "пыль" in resp.lower(): add_xp(user_id, 1, user_name)
            bot.reply_to(message, resp.split("###MEM###")[0].strip())
            new_xp = get_user_stats(user_id)
            if get_rank_name(old_xp) != get_rank_name(new_xp):
                bot.send_message(message.chat.id, f"🎉 Ранг повышен: {get_rank_name(new_xp)}!")
                p = generate_passport(user_name, get_rank_name(new_xp))
                if p: bot.send_photo(message.chat.id, p)
        else: bot.reply_to(message, "⏳ Командор, тишина в эфире.")

def start_marty_autonomous():
    print("🚀 Академия Орион 2.0 запущена.")
    while True:
        try:
            bot.remove_webhook()
            bot.infinity_polling(skip_pending=True)
        except Exception as e:
            send_log(f"Критический сбой цикла: {e}")
            time.sleep(5)

if __name__ == "__main__":
    Thread(target=run_flask, daemon=True).start()
    start_marty_autonomous()
