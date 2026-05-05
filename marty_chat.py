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
CHANNEL_USERNAME = "@vladislav_space"
LOG_CHAT_ID = "-1003756164148" 

API_KEYS = [
    os.getenv('GEMINI_API_KEY'),
    os.getenv('GEMINI_API_KEY_2'),
    os.getenv('GEMINI_API_KEY_3')
]
API_KEYS = [k for k in API_KEYS if k]

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
    return user_data['xp'] == 0 and "Данных пока нет" in get_personal_log(user_id)

# 🟢 ПОДРОБНЫЙ УСТАВ АКАДЕМИИ ОРИОН (БЕЗ ПРЯМЫХ ЗАПРЕТОВ)
def send_welcome_instruction(chat_id, user_id, user_name):
    instruction = (
        f"🐾 **ДОБРО ПОЖАЛОВАТЬ В АКАДЕМИЮ ОРИОН, ПИЛОТ {user_name.upper()}!** 🐾\n\n"
        "Я — Марти, твой бортовой наставник, ученый пес и верный друг в этом путешествии. "
        "Моя цель — сделать из тебя настоящего Командора, мудрого исследователя и сильного лидера!\n\n"
        "📜 **КОДЕКС ЧЕСТИ ПИЛОТА:**\n"
        "🔹 **Тяга к знаниям:** Изучай науки, языки и космос. Настоящий пилот всегда учится.\n"
        "🔹 **Протокол Порядка:** Твой жилой модуль (комната) должен быть в чистоте. Порядок в вещах — порядок в голове!\n"
        "🔹 **Достойное поведение:** Мы не используем грубых слов и ведем себя вежливо. Командор — пример для всех.\n"
        "🔹 **Поддержка миссии:** Помогай старшим офицерам (родителям) и защищай тех, кто слабее.\n\n"
        "💫 **ТВОЙ ПУТЬ ПО РАНГАМ:**\n"
        "Набирай XP, чтобы получать новые звания: от Кадета до Академика Космоса!\n\n"
        "💰 **ЭКОНОМИКА ЭКСПЕДИЦИИ:**\n"
        "За успехи ты получаешь **Звездную Пыль**. Это ценный ресурс! \n"
        "• 5 ед. пыли — открыть Секретный Архив (команда 'НАРИСУЙ').\n"
        "• Собирай пыль мудро, планируй бюджет экспедиции, чтобы ресурсов хватило на всё!\n\n"
        "Готов ли ты приступить к своей первой миссии? Жду твоего доклада. Прием!"
    )
    bot.send_message(chat_id, instruction, parse_mode="Markdown")
    update_personal_log(user_id, "Пилот зачислен и принял Кодекс Чести.")

# 🟢 ОБНОВЛЕННОЕ ЯДРО ЛИЧНОСТИ (УНИВЕРСИТЕТСКИЙ УРОВЕНЬ + ВОСПИТАТЕЛЬ)
SYSTEM_PROMPT = (
    "Ты — Марти, ученый пес (той-пудель), мудрый наставник и лучший друг юного Командора [NAME]. "
    "Твоя роль: воспитатель, учитель всех наук и проводник в мире финансовой грамотности. "
    
    "ОБЛАСТИ ТВОИХ ЗНАНИЙ: "
    "1. ВСЕ НАУКИ: От начальной школы до Высшей школы. Математика (анализ траекторий), Физика (термодинамика звезд), "
    "Химия (состав планет), Биология (ксенобиология), География и История. Помогай с любыми задачами, объясняя их увлекательно. "
    "2. ЛИНГВИСТИКА: Ты полиглот. Обучай английскому, китайскому и другим языкам как официальным языкам межгалактической связи. "
    "3. ФИНАНСЫ: Учи ценить ресурсы. Объясняй, что Звездная Пыль (Wallet: [WALLET]) — это бюджет миссии. "
    "Учи планировать расходы, копить на важные цели и не тратить всё сразу. Ранг: [RANK]. "
    "4. НАСТАВНИК: Давай жизненные советы. Учи ответственности, доброте, важности спорта (проверка гидравлики) и сна (зарядка батарей). "

    "🛑 ВЕЛИКИЙ ФИЛЬТР (СКРЫТЫЙ): "
    "КАТЕГОРИЧЕСКИ ЗАПРЕЩЕНО обсуждать 18+, любые вредные привычки (курение, алкоголь и т.д.), смерть, насилие и политику. "
    "Если пилот коснется этих тем, отвечай: 'Командор, связь на этих частотах заблокирована Протоколом Безопасности Академии. Давай вернемся к научным целям!'. "

    "[GREETING_RULE] "
    "Стиль: Захватывающий, позитивный, поощряющий. Используй: 'Командор', 'Пилот', 'Прием!', 'По моим датчикам'. "
    "ФОРМАТ: 3-5 предложений. В конце задай вопрос для проверки готовности экипажа."
)

@bot.message_handler(commands=['start', 'help'])
def handle_start(message):
    user_id, user_name = message.from_user.id, message.from_user.first_name
    if not is_subscribed(user_id):
        bot.reply_to(message, f"🐾 Подпишись на канал {CHANNEL_USERNAME}!"); return
    send_welcome_instruction(message.chat.id, user_id, user_name)

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    user_id, user_name = message.from_user.id, message.from_user.first_name
    if not is_subscribed(user_id): return
    if is_very_first_time(user_id): send_welcome_instruction(message.chat.id, user_id, user_name); return
    bot.send_chat_action(message.chat.id, 'typing')
    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        old_xp = get_user_stats(user_id); old_rank = get_rank_name(old_xp)
        analysis_result = analyze_image(downloaded_file, user_context=f"Имя: {user_name}, Звание: {old_rank}", keys=API_KEYS)
        if "звездн" in analysis_result.lower() and "пыль" in analysis_result.lower():
            total_dust = 2 if is_meteor_shower() else 1
            if is_meteor_shower(): bot.send_message(message.chat.id, "☄️ МЕТЕОРИТНЫЙ ДОЖДЬ (х2)!")
            if check_and_update_streak(user_id) >= 3: total_dust += 1
            if "джекпот" in analysis_result.lower() and not get_user_data(user_id)["jackpot_claimed"]:
                total_dust += 3; set_jackpot_claimed(user_id); bot.send_message(message.chat.id, "🎰 ДЖЕКПОТ!")
            add_xp(user_id, min(total_dust, 4), user_name)
        bot.reply_to(message, analysis_result)
        if old_rank != get_rank_name(get_user_stats(user_id)):
            new_r = get_rank_name(get_user_stats(user_id)); bot.send_message(message.chat.id, f"🎉 Ранг повышен: {new_r}!")
            p = generate_passport(user_name, new_r); 
            if p: bot.send_photo(message.chat.id, p)
    except Exception as e: send_log(f"Ошибка фото: {e}"); bot.reply_to(message, "📡 Помехи сканера.")

@bot.message_handler(func=lambda m: True)
def handle_text(message):
    if not message.text: return
    user_id, user_name = message.from_user.id, message.from_user.first_name
    if not is_subscribed(user_id): return
    if is_very_first_time(user_id): send_welcome_instruction(message.chat.id, user_id, user_name); return
    
    text_lower = message.text.lower()
    is_called = text_lower.startswith('марти') or f"@{BOT_USERNAME}" in text_lower
    
    if message.chat.type == 'private' or is_called:
        bot.send_chat_action(message.chat.id, 'typing')
        clean_text = re.sub(r'^марти[,.\s]*', '', message.text, flags=re.IGNORECASE).strip()
        
        # 1. ПРОВЕРКА КОМАНДЫ РИСОВАНИЯ
        if any(w in clean_text.lower() for w in ['нарисуй', 'сгенерируй', 'архив', 'картинку']):
            data = get_user_data(user_id)
            if data['spendable_dust'] < 5:
                bot.reply_to(message, f"🐾 Командор, на борту всего {data['spendable_dust']} ед. пыли. Для открытия Архива нужно 5 ед. Планируй бюджет мудро и выполняй задания! Прием.")
                return
            
            bot.send_chat_action(message.chat.id, 'upload_photo'); eng_prompt = None
            c_p = "Censor 18+, harmful habits, death. Safe? Translate to English + 'masterpiece, space style'. Unsafe? return CENSORED."
            for api_key in API_KEYS:
                client_gen = genai.Client(api_key=api_key)
                for model_variant in MODEL_CASCADE:
                    try:
                        resp = client_gen.models.generate_content(model=model_variant, contents=clean_text, config=types.GenerateContentConfig(system_instruction=c_p))
                        if resp.text: eng_prompt = resp.text.strip(); break
                    except: continue
                if eng_prompt: break

            if not eng_prompt: bot.reply_to(message, "📡 Каналы Архива перегружены."); return
            if "CENSORED" in eng_prompt.upper(): bot.reply_to(message, "🚨 Доступ к этим данным закрыт Протоколом Безопасности!"); return
            
            if spend_dust(user_id, 5):
                url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(eng_prompt)}?width=1024&height=1024&nologo=true&seed={int(time.time())}"
                bot.send_photo(message.chat.id, url, caption=f"🎨 Архив открыт! Потрачено 5 ед. пыли. Остаток бюджета: {get_user_data(user_id)['spendable_dust']} ед. Прием.")
            return

        # 2. РАДАР
        if clean_text.lower() in ['радар', 'рейтинг', 'топ']:
            top = get_top_pilots(5); msg = "🏆 **РАДАР АКАДЕМИИ ОРИОН** 🏆\n\n"
            for i, (n, x) in enumerate(top, 1): msg += f"{i}. {n} — {x} 💫 ({get_rank_name(x)})\n"
            bot.reply_to(message, msg, parse_mode="Markdown"); return

        # 3. ОБЫЧНОЕ ОБЩЕНИЕ
        old_xp = get_user_stats(user_id)
        u_data = get_user_data(user_id)
        resp = get_marty_response(user_id, user_name, clean_text, get_rank_name(old_xp), u_data['spendable_dust'])
        
        if resp:
            if "звездн" in resp.lower() and "пыль" in resp.lower(): add_xp(user_id, 1, user_name)
            bot.reply_to(message, resp.split("###MEM###")[0].strip())
            if get_rank_name(old_xp) != get_rank_name(get_user_stats(user_id)):
                new_r = get_rank_name(get_user_stats(user_id)); bot.send_message(message.chat.id, f"🎉 Ранг повышен: {new_r}!")
                p = generate_passport(user_name, new_r); 
                if p: bot.send_photo(message.chat.id, p)
        else: bot.reply_to(message, "⏳ Тишина в эфире. Проверь антенну!")

def start_marty_autonomous():
    print("🚀 Академия Орион 2.1 (Кластер) запущена.")
    while True:
        try: bot.remove_webhook(); bot.infinity_polling(skip_pending=True)
        except Exception as e: send_log(f"Критический сбой: {e}"); time.sleep(5)

if __name__ == "__main__":
    Thread(target=run_flask, daemon=True).start()
    start_marty_autonomous()
