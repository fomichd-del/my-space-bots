import os
import telebot
import time
import re
import scenario1
import urllib.parse
from datetime import datetime, timedelta
from threading import Thread
from Flask import Flask
from google import genai
from google.genai import types
from telebot import types as tele_types 
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

# --- ИМПОРТЫ ---
from database import (get_personal_log, update_personal_log, add_xp, get_user_stats, 
                      get_rank_name, get_user_data, set_jackpot_claimed, spend_dust, 
                      check_and_update_streak, get_top_pilots,
                      get_game_status, update_game_progress, set_game_timer)
from vision_module import analyze_image
from image_gen import generate_passport

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
    if call.data == "game_back_to_profile":
        handle_text(call.message, is_profile_call=True)
    else:
        scenario1.run_scenario(bot, call)

# ---------------------------
# --- ОБНОВЛЕННЫЙ КАСКАД МОДЕЛЕЙ ---
# Только реально существующие версии для стабильности
MODEL_CASCADE = [
    'gemini-2.0-flash', 
    'gemini-2.0-flash-lite', 
    'gemini-1.5-flash', 
    'gemini-1.5-pro'
]

try:
    BOT_USERNAME = bot.get_me().username.lower()
except:
    BOT_USERNAME = "marty_help_bot"

# 🟢 ДЕТАЛИЗИРОВАННОЕ ЛОГИРОВАНИЕ
def send_log(error_text):
    """Отправляет детализированный отчет в канал логов"""
    try:
        now = (datetime.utcnow() + timedelta(hours=3)).strftime("%Y-%m-%d %H:%M:%S")
        log_msg = f"🚨 **ОТЧЕТ СИСТЕМЫ ОРИОН**\n📅 Время: `{now}`\n🔍 **Детали:** `{error_text}`"
        bot.send_message(LOG_CHAT_ID, log_msg, parse_mode="Markdown")
    except Exception as e:
        print(f"Ошибка логирования: {e}")

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
    markup.row(KeyboardButton("👤 Мой профиль"), KeyboardButton("❓ Инструкция"))
    markup.row(KeyboardButton("🎮 Игровой отсек")) 
    return markup

def send_welcome_instruction(chat_id, user_id, user_name):
    instruction = (
        f"🐾 **ДОБРО ПОЖАЛОВАТЬ В АКАДЕМИЮ ОРИОН, ПИЛОТ {user_name.upper()}!** 🐾\n"
        f"──────────────────────────\n"
        f"Я — Марти, твой бортовой наставник и друг. Моя миссия — превратить твое обучение в захватывающее приключение!\n\n"
        f"📜 **КОДЕКС ЧЕСТИ ПИЛОТА:**\n"
        f"✅ **Знания:** Изучай Вселенную. Знания — твоя главная сила.\n"
        f"✅ **Чистота:** Поддерживай идеальный порядок. Это дисциплина пилота.\n"
        f"✅ **Благородство:** Будь вежлив, помогай старшим офицерам.\n\n"
        f"⚙️ **ТВОИ ИНСТРУМЕНТЫ:**\n"
        f"• **👤 Мой профиль:** Твой ранг, стаж (XP) и баланс Звездной пыли.\n"
        f"• **🎮 Игровой отсек:** Сюжетные миссии Академии.\n"
        f"• **❓ Инструкция:** Кодекс и правила.\n\n"
        f"💰 **ЭКОНОМИКА:**\n"
        f"За активность ты получаешь **Звездную пыль**. Накопи **5 ед.** и используй команду **'Нарисуй'**, чтобы открыть Архив!\n\n"
        f"Готов к старту? Используй кнопки на панели! Прием!"
    )
    bot.send_message(chat_id, instruction, parse_mode="Markdown", reply_markup=get_marty_keyboard())
    update_personal_log(user_id, "Пилот зачислен в Академию.")

# 🟢 УЛЬТИМАТИВНОЕ ЯДРО ЛИЧНОСТИ (СТРОГИЙ НАСТАВНИК)
SYSTEM_PROMPT = (
    "Ты — Марти, ученый пес (той-пудель), мудрый наставник Академии Орион. Собеседник — пилот [NAME]. "
    "КРИТИЧЕСКИ: Звездная Пыль ([WALLET]) — редчайшая валюта. Ее нельзя давать за вежливость! "
    "РАНГ: [RANK]. "
    "ПРОТОКОЛЫ ОБУЧЕНИЯ: "
    "1. АНТИ-ДОМАШКА: Категорически запрещено давать готовые ответы! Объясняй ПРИНЦИП, давай подсказки. "
    "Звездную пыль назначай только за реально выполненное задание или верный ответ на сложный вопрос. "
    "2. АКАДЕМИК: Объясняй логику, а не результат. "
    "3. ЛИНГВИСТ: Учи языкам через практику. Проси пилота переводить фразы самому. "
    "4. ЕСТЕСТВЕННОСТЬ: Приветствие, имя и титулы разрешены только ОДИН РАЗ В ДЕНЬ. В остальное время общайся кратко. "
    "5. ЭКЗАМЕНАТОР: Код ***НАГРАДА ЗА УМ*** пишется ТОЛЬКО за реальный интеллектуальный успех. "
    "6. НЕПРЕРЫВНОСТЬ: Анализируй блок ДАННЫЕ. Если пилот не закончил задачу или что-то обещал — напомни мягко. "
    "7. ЭТИКА: Создавай дилеммы (выбор между пользой и честью) для проверки рассудительности. "
    "8. ПУДЕЛЬ: Ты той-пудель. Виляй хвостом от радости за успехи, поддерживай пилота, если ему трудно. "
    "🛑 ВЕЛИКИЙ ФИЛЬТР: Никакой политики, насилия, войны или грубости. "
    "[GREETING_RULE] "
    "ФОРМАТ: 3-4 предложения. В конце иногда — проверочный вопрос по теме. Прием!"
)

# 🟢 УЛУЧШЕННЫЙ МОЗГ МАРТИ С ЛОГИРОВАНИЕМ СБОЕВ
def get_marty_response(user_id, user_name, clean_text, user_rank, wallet_balance):
    user_memory = get_personal_log(user_id)
    time_info = get_time_context()
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    if daily_greetings.get(user_id) == current_date:
        greeting_rule = "!!! ПРАВИЛО ТИШИНЫ: Вы уже здоровались. Не пиши 'Привет', имя или титулы. Сразу к сути."
    else:
        add_xp(user_id, 1, user_name) 
        wallet_balance += 1 
        greeting_rule = f"!!! ПРАВИЛО ПЕРВОЙ СВЯЗИ: Поздоровайся: 'Командор {user_name}'. Сообщи: 'Начислил +1 Пыль за вход! На счету {wallet_balance} ед.'."
        daily_greetings[user_id] = current_date
    
    current_prompt = SYSTEM_PROMPT.replace("[NAME]", user_name).replace("[TIME]", time_info).replace("[GREETING_RULE]", greeting_rule).replace("[RANK]", user_rank).replace("[WALLET]", str(wallet_balance))
    
    last_error = "Неизвестная ошибка"
    
    for api_key in API_KEYS:
        client_gen = genai.Client(api_key=api_key)
        for model_variant in MODEL_CASCADE:
            try:
                response = client_gen.models.generate_content(
                    model=model_variant, 
                    contents=f"ДАННЫЕ: {user_memory}\nВОПРОС: {clean_text}", 
                    config=types.GenerateContentConfig(system_instruction=current_prompt)
                )
                if response.text: return response.text
            except Exception as e:
                last_error = f"Модель {model_variant}: {str(e)}"
                if "429" not in str(e):
                    send_log(f"Сбой при общении: {last_error}")
                continue
                
    send_log(f"КРИТИЧЕСКИЙ ОТКАЗ МОЗГА: Ни одна модель не ответила. Последняя ошибка: {last_error}")
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
            add_xp(user_id, total_dust, user_name)
        
        bot.reply_to(message, analysis_result, reply_markup=get_marty_keyboard())
        
        new_xp = get_user_stats(user_id)
        if old_rank != get_rank_name(new_xp):
            new_r = get_rank_name(new_xp)
            bot.send_message(message.chat.id, f"🎉 Ранг повышен: {new_r}!")
            p = generate_passport(user_name, new_r) 
            if p: bot.send_photo(message.chat.id, p)
    except Exception as e: send_log(f"Ошибка фото: {e}")

@bot.message_handler(func=lambda m: True)
def handle_text(message, is_profile_call=False):
    user_id = message.from_user.id
    user_name = message.from_user.first_name if message.from_user.first_name else "Пилот"
    
    if message.chat.type == 'private' and not is_subscribed(user_id):
        bot.reply_to(message, f"🐾 Подпишись на канал {CHANNEL_USERNAME}!"); return

    text = message.text if message.text else ""
    if not is_profile_call: bot.send_chat_action(message.chat.id, 'typing')

    # --- ЛОГИКА ИГРОВОГО ОТСЕКА ---
    if text == "🎮 Игровой отсек":
        kb = tele_types.InlineKeyboardMarkup(row_width=1)
        kb.add(tele_types.InlineKeyboardButton("🚀 Начать миссию", callback_data="game_start"))
        bot.reply_to(message, "🎮 **ИГРОВОЙ ОТСЕК**\n\nВыбери миссию для погружения:", reply_markup=kb, parse_mode="Markdown")
        return

    # --- ЛОГИКА ПРОФИЛЯ ---
    if text == "👤 Мой профиль" or is_profile_call:
        u_data = get_user_data(user_id); current_xp, current_dust = u_data['xp'], u_data['spendable_dust']
        rank = get_rank_name(current_xp)
        report = f"📊 **БОРТОВОЙ ЖУРНАЛ**\n\n👤 Имя: `{user_name}`\n🎖 Ранг: `{rank}`\n📈 XP: `{current_xp}`\n💰 Пыль: `{current_dust}` ед."
        kb = tele_types.InlineKeyboardMarkup(row_width=1)
        kb.add(tele_types.InlineKeyboardButton("❓ Помощь по рангам", callback_data="game_instruction_fix"))
        if is_profile_call: bot.edit_message_text(report, message.chat.id, message.message_id, reply_markup=kb, parse_mode="Markdown")
        else: bot.reply_to(message, report, parse_mode="Markdown", reply_markup=kb); return

    if text == "❓ Инструкция": send_welcome_instruction(message.chat.id, user_id, user_name); return

    clean_text = re.sub(r'^марти[,.\s]*', '', text, flags=re.IGNORECASE).strip()

    # --- ЛОГИКА 'НАРИСУЙ' С ЗАЩИТОЙ ---
    if any(w in clean_text.lower() for w in ['нарисуй', 'архив', 'картинку']):
        data = get_user_data(user_id)
        if data['spendable_dust'] < 5:
            bot.reply_to(message, f"🐾 Командор, на борту {data['spendable_dust']} ед. пыли. Нужно 5 ед.", reply_markup=get_marty_keyboard())
            return
            
        bot.send_chat_action(message.chat.id, 'upload_photo')
        if not API_KEYS:
            send_log("ОШИБКА: API ключи Gemini не найдены!"); return

        eng_prompt = None
        for api_key in API_KEYS:
            client_gen = genai.Client(api_key=api_key)
            try:
                resp = client_gen.models.generate_content(
                    model='gemini-1.5-flash', 
                    contents=clean_text, 
                    config=types.GenerateContentConfig(system_instruction="Translate to English for image generation. Kid-friendly only. If unsafe return CENSORED.")
                )
                if resp.text: eng_prompt = resp.text.strip(); break
            except: continue
                
        if not eng_prompt or "CENSORED" in eng_prompt.upper():
            bot.reply_to(message, "🚨 Доступ к Архиву заблокирован протоколами безопасности!", reply_markup=get_marty_keyboard()); return
            
        if spend_dust(user_id, 5):
            url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(eng_prompt)}?width=1024&height=1024&nologo=true&seed={int(time.time())}"
            bot.send_photo(message.chat.id, url, caption=f"🎨 Архив открыт! Потрачено 5 ед. пыли.", reply_markup=get_marty_keyboard())
        return

    # --- МОЗГ МАРТИ ---
    old_xp = get_user_stats(user_id); u_data = get_user_data(user_id)
    resp = get_marty_response(user_id, user_name, clean_text, get_rank_name(old_xp), u_data['spendable_dust'])
    
    if resp:
        if "***НАГРАДА ЗА УМ***" in resp:
            add_xp(user_id, 1, user_name)
            resp = resp.replace("***НАГРАДА ЗА УМ***", "\n🌟 *Бортовой компьютер: +1 Звездная Пыль за верный ответ!*")
        bot.reply_to(message, resp, reply_markup=get_marty_keyboard())
        
        new_xp = get_user_stats(user_id)
        if old_rank != get_rank_name(new_xp):
            new_r = get_rank_name(new_xp); bot.send_message(message.chat.id, f"🎉 Ранг повышен: {new_r}!")
            p = generate_passport(user_name, new_r); 
            if p: bot.send_photo(message.chat.id, p)
    else: bot.reply_to(message, "⏳ Тишина в эфире. Повтори запрос, пилот.", reply_markup=get_marty_keyboard())

def start_marty_autonomous():
    print("🚀 Академия Орион 2.2 запущена.")
    while True:
        try: bot.remove_webhook(); bot.infinity_polling(skip_pending=True)
        except Exception as e: send_log(f"Критический сбой цикла: {e}"); time.sleep(5)

if __name__ == "__main__":
    Thread(target=run_flask, daemon=True).start()
    start_marty_autonomous()
