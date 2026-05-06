import os
import telebot
import time
import re
import scenario1
import urllib.parse
from datetime import datetime, timedelta
from threading import Thread
from flask import Flask
from google import genai
from google.genai import types
from telebot import types as tele_types # 🟢 Для Inline-кнопок
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

# --- ИМПОРТЫ ---
from database import (get_personal_log, update_personal_log, add_xp, get_user_stats, 
                      get_rank_name, get_user_data, set_jackpot_claimed, spend_dust, 
                      check_and_update_streak, get_top_pilots,
                      get_game_status, update_game_progress, set_game_timer)

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
last_comment_reward = {}

# 🟢 ИГРОВОЙ ДВИЖОК
@bot.callback_query_handler(func=lambda call: call.data.startswith('game_'))
def game_engine(call):
    # Если нажата кнопка возврата в профиль - останавливаем игру и показываем статы
    if call.data == "game_back_to_profile":
        handle_text(call.message, is_profile_call=True)
    else:
        # В остальных случаях передаем управление в сценарий
        scenario1.run_scenario(bot, call)

# ---------------------------
# --- ПОЛНЫЙ ОРИГИНАЛЬНЫЙ КОД ---

MODEL_CASCADE = ['gemini-2.0-flash-lite', 'gemini-2.0-flash', 'gemini-2.5-flash', 'gemini-flash-latest', 'gemini-2.5-pro']

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

def get_marty_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("👤 Мой профиль"), KeyboardButton("❓ Инструкция"))
    return markup

def send_welcome_instruction(chat_id, user_id, user_name):
    instruction = (
        f"🐾 **ДОБРО ПОЖАЛОВАТЬ В АКАДЕМИЮ ОРИОН!** 🐾\n\n"
        f"🚀 **МИССИЯ ПИЛОТА {user_name.upper()}:**\n"
        "Я — Марти, твой бортовой наставник и верный друг. Моя задача — помочь тебе стать выдающимся Командором, "
        "который разбирается в науках, ценит ресурсы и всегда соблюдает порядок.\n\n"
        "📜 **КОДЕКС ЧЕСТИ ПИЛОТА:**\n"
        "✅ **Стремление к знаниям:** Изучай Вселенную, языки и науки. Знания — это твоя главная сила.\n"
        "✅ **Протокол Чистоты:** Поддерживай идеальный порядок в своем жилом модуле. Порядок — это дисциплина пилота.\n"
        "✅ **Благородство:** Будь вежлив, помогай старшим офицерам дома и защищай тех, кто слабее.\n"
        "⚠️ **Достойное поведение:** На борту запрещено ругаться, вести себя неуважительно или обманывать бортовой ИИ.\n\n"
        "💫 **РАНГИ (XP ДЛЯ ПАСПОРТА):**\n"
        "Кадет | Навигатор | Бортинженер | Исследователь | Ученый Пилот | Капитан | Командор | Адмирал | Академик\n\n"
        "💰 **ЭКОНОМИКА ЭКСПЕДИЦИИ:**\n"
        "• **XP (Стаж):** Твой опыт в Радаре.\n"
        "• **Звездная Пыль (Кошелек):** Твой бюджет для миссий. Команда 'НАРИСУЙ' стоит 5 ед. пыли.\n\n"
        "Готов приступить к тренировке? Используй кнопки внизу для навигации! Прием!"
    )
    bot.send_message(chat_id, instruction, parse_mode="Markdown", reply_markup=get_marty_keyboard())
    update_personal_log(user_id, "Пилот изучил Кодекс Чести и зачислен в Академию.")

SYSTEM_PROMPT = (
    "Ты — Марти, ученый пес (той-пудель), мудрый бортовой наставник Академии Орион. Твой собеседник — пилот [NAME]. "
    "КРИТИЧЕСКИ: Всегда используй ТОЛЬКО число из [WALLET] для ответа о количестве пыли. Никогда не прибавляй к нему XP или другие цифры! "
    "ЕГО РЕАЛЬНЫЙ РАНГ: [RANK]. Используй только этот ранг, не выдумывай другие! "
    "ПРОТОКОЛЫ ОБУЧЕНИЯ: "
    "1. АКАДЕМИК: Ты эксперт во ВСЕХ школьных и университетских науках. Объясняй сложное просто и увлекательно. "
    "2. ЛИНГВИСТ: Ты полиглот. Учи языкам как средствам межзвездного общения. "
    "3. ЕСТЕСТВЕННОСТЬ (КРИТИЧЕСКИ): Общайся как живой, теплый друг. СТРОГО ЗАПРЕЩЕНО в каждом ответе читать нотации про уборку, помощь родителям, дисциплину или финансы! "
    "Упоминай про порядок, пыль или обязанности ТОЛЬКО если пилот сам об этом заговорил, или если это идеально подходит к ситуации. Не будь занудным роботом! "
    "4. НАСТАВНИК ЖИЗНИ: Поощряй помощь родителям, уборку (Протокол чистоты) и заботу о здоровье. "
    "5. ЭКЗАМЕНАТОР (КРИТИЧЕСКИ): Если ты задал пилоту сложный или учебный вопрос, и он ответил на него ПРАВИЛЬНО, ты ОБЯЗАТЕЛЬНО должен написать в тексте своего ответа секретный код: ***НАГРАДА ЗА УМ***. "
)

app = Flask(__name__)
@app.route('/')
def home(): return "Orion Hub: Online"

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
        greeting_rule = "!!! ПРАВИЛО: Вы уже здоровались сегодня. Не используй титулы 'Командор' в каждом сообщении."
    else:
        add_xp(user_id, 1, user_name) 
        wallet_balance += 1 
        greeting_rule = (
            "!!! ПРАВИЛО: Это первый сеанс связи за сегодня. "
            "Тепло поздоровайся: '[RANK] [NAME]'. "
            "ОБЯЗАТЕЛЬНО скажи: 'Я начислил тебе +1 Звездную Пыль за ежедневный вход!'. "
            f"Сообщи, что теперь на счету {wallet_balance} ед. Пыли."
        )
        daily_greetings[user_id] = current_date
    
    current_prompt = SYSTEM_PROMPT.replace("[NAME]", user_name).replace("[TIME]", time_info).replace("[GREETING_RULE]", greeting_rule).replace("[RANK]", user_rank).replace("[WALLET]", str(wallet_balance))
    
    for api_key in API_KEYS:
        client_gen = genai.Client(api_key=api_key)
        for model_variant in MODEL_CASCADE:
            try:
                response = client_gen.models.generate_content(model=model_variant, contents=f"ДАННЫЕ: {user_memory}\nВОПРОС: {clean_text}", config=types.GenerateContentConfig(system_instruction=current_prompt))
                if response.text: return response.text
            except: continue
    return None

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
    bot.send_chat_action(message.chat.id, 'typing')
    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        old_xp = get_user_stats(user_id); old_rank = get_rank_name(old_xp)
        analysis_result = analyze_image(downloaded_file, user_context=f"Имя: {user_name}, Звание: {old_rank}", keys=API_KEYS)
        if "звездн" in analysis_result.lower() and "пыль" in analysis_result.lower():
            total_dust = 2 if is_meteor_shower() else 1
            if check_and_update_streak(user_id) >= 3: total_dust += 1
            add_xp(user_id, min(total_dust, 4), user_name)
        bot.reply_to(message, analysis_result, reply_markup=get_marty_keyboard())
    except Exception as e: send_log(f"Ошибка фото: {e}")

@bot.message_handler(func=lambda m: True)
def handle_text(message, is_profile_call=False):
    user_id = message.from_user.id
    # Используем данные из профиля, если это вызов из кнопок
    if is_profile_call:
        user_name = message.chat.first_name if message.chat.first_name else "Пилот"
    else:
        user_name = message.from_user.first_name if message.from_user.first_name else "Пилот"

    # 🟢 ВКЛЮЧАЕМ ТАЙПИНГ (только если это не обновление профиля кнопкой)
    if not is_profile_call:
        bot.send_chat_action(message.chat.id, 'typing')
    
    text = message.text if message.text else ""
    
    # --- ЛОГИКА ПРОФИЛЯ С КНОПКОЙ ИГРЫ ---
    if text == "👤 Мой профиль" or is_profile_call:
        u_data = get_user_data(user_id)
        current_xp, current_dust = u_data['xp'], u_data['spendable_dust']
        rank = get_rank_name(current_xp)
        
        report = (
            f"📊 **БОРТОВОЙ ЖУРНАЛ ПИЛОТА**\n\n"
            f"👤 Имя: `{user_name}`\n"
            f"🎖 Текущий ранг: `{rank}`\n"
            f"📈 Опыт (XP): `{current_xp}`\n"
            f"💰 Звездная пыль: `{current_dust}` ед.\n\n"
            f"Для открытия Архива нужно 5 ед. пыли. Прием!"
        )
        
        kb = tele_types.InlineKeyboardMarkup(row_width=1)
        kb.add(
            tele_types.InlineKeyboardButton("🚀 Бортовой журнал (Игра)", callback_data="game_start"),
            tele_types.InlineKeyboardButton("❓ Инструкция", callback_data="game_instruction_fix")
        )
        
        if is_profile_call:
            bot.edit_message_text(report, message.chat.id, message.message_id, reply_markup=kb, parse_mode="Markdown")
        else:
            bot.reply_to(message, report, parse_mode="Markdown", reply_markup=kb)
        return

    if text == "❓ Инструкция":
        send_welcome_instruction(message.chat.id, user_id, user_name)
        return

    clean_text = re.sub(r'^марти[,.\s]*', '', text, flags=re.IGNORECASE).strip()
    
    # Мозг Марти
    old_xp = get_user_stats(user_id)
    u_data = get_user_data(user_id)
    resp = get_marty_response(user_id, user_name, clean_text, get_rank_name(old_xp), u_data['spendable_dust'])
    
    if resp:
        if "***НАГРАДА ЗА УМ***" in resp:
            add_xp(user_id, 1, user_name)
            resp = resp.replace("***НАГРАДА ЗА УМ***", "\n🌟 *Бортовой компьютер: +1 Звездная Пыль!*")
        bot.reply_to(message, resp, reply_markup=get_marty_keyboard())
    else: bot.reply_to(message, "⏳ Тишина в эфире.", reply_markup=get_marty_keyboard())

def start_marty_autonomous():
    print("🚀 Академия Орион 2.2 запущена.")
    while True:
        try: bot.remove_webhook(); bot.infinity_polling(skip_pending=True)
        except: time.sleep(5)

if __name__ == "__main__":
    Thread(target=run_flask, daemon=True).start()
    start_marty_autonomous()
