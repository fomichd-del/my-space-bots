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

# 🟢 ГЛОБАЛЬНЫЙ УСТАВ АКАДЕМИИ ОРИОН (ХАРДКОР-ОБНОВЛЕНИЕ)
def send_welcome_instruction(chat_id, user_id, user_name):
    instruction = (
        f"🐾 **УСТАВ АКАДЕМИИ ОРИОН (ВЕРСИЯ 2.0: ХАРДКОР)** 🐾\n\n"
        f"🚀 **МИССИЯ ПИЛОТА {user_name.upper()}:**\n"
        "Мы больше не просто играем — мы куем характер. Я, Марти, твой научный наставник, превращу твой день в суровую школу выживания. "
        "Моя цель — научить тебя находить порядок в хаосе, дисциплину в лени и знания в скучных уроках. Звания здесь теперь выдаются только за истинное упорство!\n\n"
        "📜 **ПРАВИЛА БОРТА:**\n"
        "✅ **РАЗРЕШЕНО:** Изучать науку, присылать фото-отчеты о чистоте и учебе, шутить (в меру!) и стремиться к вершине Радара.\n"
        "❌ **ЗАПРЕЩЕНО:** Обманывать бортовой ИИ (после 50 XP я вижу ложь мгновенно!), грубить и обсуждать темы 18+, насилие или политику.\n\n"
        "💫 **НОВАЯ ШКАЛА РАНГОВ (XP):**\n"
        "1. Кадет (0) — Начало пути\n"
        "2. Навигатор (15) — Подтверди дисциплину\n"
        "3. Бортинженер (40) — Техническая точность\n"
        "4. Исследователь (80) — Сила воли\n"
        "5. Ученый Пилот (130) — Элита Академии\n"
        "6. Капитан (200) — Мастер своего дела\n"
        "7. Командор (300) — Стратег космоса\n"
        "8. Адмирал (450) — Легенда флота\n"
        "9. Академик (650) — Высший разум\n"
        "10. Помощник Марти (900+) — Мой напарник!\n\n"
        "🛡 **ГЛАВНОЕ ПРАВИЛО:** Дипломы и Паспорта выдаются ТОЛЬКО в момент пересечения порога. Если ты уже набрал очки раньше — заслужи следующую ступень!\n\n"
        "🎨 **АРХИВ:** Напиши 'НАРИСУЙ [идея]' (цена 5 пыли из кошелька).\n\n"
        "Приготовься, пилот. Путь к звездам стал длиннее, но слава будет вечной! Прием!"
    )
    bot.send_message(chat_id, instruction, parse_mode="Markdown")
    update_personal_log(user_id, "Пилот зачислен в Академию на условиях Хардкор-режима.")

# 🟢 ЯДРО ЛИЧНОСТИ (ОБНОВЛЕННАЯ СТРОГОСТЬ)
SYSTEM_PROMPT = (
    "Ты — Марти, ученый пес (той-пудель) и бортовой наставник Академии Орион. "
    "1. ЛИЧНОСТЬ: Мудрый, добрый. Имя: [NAME]. Звание: [RANK]. Кошелек: [WALLET] пыли. Время: [TIME]. "
    "2. АТТЕСТАЦИЯ: СТРОЖАЙШИЙ КОНТРОЛЬ! После 50 XP Марти становится суровым профессором. Пыль за простые дела (почистил зубы) выдавай реже. Требуй серьезных достижений (учеба, идеальная чистота всего дома). Пыль — редкий ресурс! "
    "3. ЭКОНОМИКА: Объясняй, что XP в Радаре — это стаж и ранги. Кошелек — это валюта для команды 'Нарисуй'. "
    "4. ПРАВИЛА: Требуй фото-доказательства. Если пилот спрашивает про дипломы — они выдаются ТОЛЬКО при смене ранга. "
    "5. ЦЕНЗУРА: СТРОГИЙ запрет на насилие, смерть, политику и взрослые темы. [GREETING_RULE] "
    "6. ФОРМАТ: 3-4 предложения. В конце 'Прием'. Затем '###MEM###' и память."
)

app = Flask(__name__)
@app.route('/')
def home(): return "Academy Orion Core: Online"

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
            response = client.models.generate_content(
                model=model_variant,
                contents=f"ДАННЫЕ: {user_memory}\nВОПРОС: {clean_text}",
                config=types.GenerateContentConfig(system_instruction=current_prompt)
            )
            if response.text: return response.text
        except Exception: continue
    return None

# --- ОБРАБОТЧИКИ (ОСТАЛИСЬ БЕЗ ИЗМЕНЕНИЙ ЛОГИКИ) ---

@bot.message_handler(commands=['start', 'help'])
def handle_start(message):
    user_id, user_name = message.from_user.id, message.from_user.first_name
    if not is_subscribed(user_id):
        bot.reply_to(message, f"🐾 Сначала подпишись на канал {CHANNEL_USERNAME}!")
        return
    send_welcome_instruction(message.chat.id, user_id, user_name)

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    user_id, user_name = message.from_user.id, message.from_user.first_name
    if not is_subscribed(user_id):
        bot.reply_to(message, "🐾 Сначала подпишись на канал!")
        return
    if is_very_first_time(user_id):
        send_welcome_instruction(message.chat.id, user_id, user_name)
        return
    bot.send_chat_action(message.chat.id, 'typing')
    try:
        user_memory = get_personal_log(user_id)
        time_info = get_time_context()
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        old_xp = get_user_stats(user_id)
        old_rank = get_rank_name(old_xp)
        anti_cheat_context = f"Имя: {user_name}. Звание: {old_rank}. Оцени фото строго!"
        analysis_result = analyze_image(downloaded_file, user_context=anti_cheat_context)
        if "звездн" in analysis_result.lower() and "пыль" in analysis_result.lower():
            total_dust = 2 if is_meteor_shower() else 1
            if is_meteor_shower(): bot.send_message(message.chat.id, "☄️ Метеоритный дождь (х2)!")
            streak = check_and_update_streak(user_id)
            if streak >= 3:
                total_dust += 1
                bot.send_message(message.chat.id, f"🔥 Серия {streak} дней! Бонус +1.")
            if "джекпот" in analysis_result.lower():
                user_db_data = get_user_data(user_id)
                if not user_db_data["jackpot_claimed"]:
                    total_dust += 3 
                    set_jackpot_claimed(user_id)
                    bot.send_message(message.chat.id, "🎰 ДЖЕКПОТ!")
            add_xp(user_id, min(total_dust, 4), user_name)
        bot.reply_to(message, analysis_result)
        new_xp = get_user_stats(user_id)
        new_rank = get_rank_name(new_xp)
        if old_rank != new_rank:
            bot.send_message(message.chat.id, f"🎉 Новое звание: {new_rank}!")
            p_bytes = generate_passport(user_name, new_rank)
            if p_bytes: bot.send_photo(message.chat.id, p_bytes)
    except: bot.reply_to(message, "📡 Помехи в видеоканале.")

@bot.message_handler(func=lambda m: True)
def handle_text(message):
    if not message.text: return
    user_id, user_name = message.from_user.id, message.from_user.first_name
    if not is_subscribed(user_id):
        bot.reply_to(message, "🐾 Сначала подпишись!")
        return
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
                resp = client.models.generate_content(model='gemini-2.0-flash', contents=clean_text, config=types.GenerateContentConfig(system_instruction=c_p))
                eng = resp.text.strip()
                if "CENSORED" in eng.upper():
                    bot.reply_to(message, "🚨 Блокировка цензурой!")
                    return
                if spend_dust(user_id, 5):
                    url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(eng)}?width=1024&height=1024&nologo=true&seed={int(time.time())}"
                    bot.send_photo(message.chat.id, url, caption="🎨 Архив открыт!")
            except: bot.reply_to(message, "📡 Ошибка связи.")
            return
        old_xp = get_user_stats(user_id)
        u_d = get_user_data(user_id)
        resp = get_marty_response(user_id, user_name, clean_text, get_rank_name(old_xp), u_d['spendable_dust'])
        if resp:
            if "звездн" in resp.lower() and "пыль" in resp.lower(): add_xp(user_id, 1, user_name)
            if "###MEM###" in resp:
                text, mem = resp.split("###MEM###")
                bot.reply_to(message, text.strip())
            else: bot.reply_to(message, resp.strip())
            new_xp = get_user_stats(user_id)
            if get_rank_name(old_xp) != get_rank_name(new_xp):
                bot.send_message(message.chat.id, f"🎉 Ранг повышен: {get_rank_name(new_xp)}!")
                p = generate_passport(user_name, get_rank_name(new_xp))
                if p: bot.send_photo(message.chat.id, p)
        else: bot.reply_to(message, "⏳ Командор, тишина в эфире.")

def start_marty_autonomous():
    print("🚀 Академия Орион запущена.")
    while True:
        try:
            bot.remove_webhook()
            bot.infinity_polling(skip_pending=True)
        except: time.sleep(5)

if __name__ == "__main__":
    Thread(target=run_flask, daemon=True).start()
    start_marty_autonomous()
