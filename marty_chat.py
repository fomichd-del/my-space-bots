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
# --- ВЕЛИКИЙ КАСКАД ОРИОНА (МАЙ 2026) ---
# Модели выстроены от быстрых/бесплатных к мощным
MODEL_CASCADE = [
    # 1. Флагманы скорости и лимитов (Серия 3)
    'gemini-3-flash-preview',
    'gemini-3.1-flash-lite-preview',
    'gemini-flash-latest',
    
    # 2. Новое поколение 2.5 (Баланс)
    'gemini-2.5-flash',
    'gemini-2.5-flash-lite',
    
    # 3. Стабильная серия 2.0
    'gemini-2.0-flash',
    'gemini-2.0-flash-001',
    'gemini-2.0-flash-lite',
    'gemini-2.0-flash-lite-001',
    'gemini-flash-lite-latest',
    
    # 4. Мощные модели Gemma 4
    'gemma-4-31b-it',
    'gemma-4-26b-a4b-it',
    
    # 5. Тяжелый интеллект Pro (Низкие лимиты)
    'gemini-3.1-pro-preview',
    'gemini-3-pro-preview',
    'gemini-2.5-pro',
    'gemini-pro-latest',
    
    # 6. Режим глубокого поиска (Последний шанс)
    'deep-research-preview-04-2026'
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

# 🟢 СКАНЕР ДОСТУПНЫХ МОДЕЛЕЙ (ФИКС ОШИБКИ supported_actions)
def get_available_models_list():
    """Возвращает строку с именами моделей, доступных для текущего API-ключа"""
    if not API_KEYS: return "Ключи API не найдены."
    try:
        client = genai.Client(api_key=API_KEYS[0])
        models = client.models.list()
        names = [m.name.replace('models/', '') for m in models 
                 if 'generateContent' in (m.supported_actions or [])]
        return "\n".join([f"• `{n}`" for n in names])
    except Exception as e:
        return f"Ошибка сканера: {e}"

def check_actual_names():
    """Проверяет через API, какие модели реально доступны для логов"""
    if not API_KEYS:
        send_log("🚨 ОШИБКА: Список API_KEYS пуст!")
        return
    try:
        client = genai.Client(api_key=API_KEYS[0])
        models = client.models.list()
        available = [m.name.replace('models/', '') for m in models 
                     if 'generateContent' in (m.supported_actions or [])]
        report = "🛰 **РЕЗУЛЬТАТЫ СКАНЕРА ЧАСТОТ**\n\n✅ Доступные модели на борту:\n" + ", ".join([f"`{m}`" for m in available])
        send_log(report)
    except Exception as e:
        send_log(f"❌ Сбой сканера имен: {e}")

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

def get_marty_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(KeyboardButton("👤 Мой профиль"), KeyboardButton("❓ Инструкция"))
    markup.row(KeyboardButton("🎮 Игровой отсек")) 
    return markup

def send_welcome_instruction(chat_id, user_id, user_name):
    instruction = (
        f"🐾 **ДОБРО ПОЖАЛОВАТЬ В АКАДЕМИЮ ОРИОН, ПИЛОТ {user_name.upper()}!** 🐾\n"
        f"──────────────────────────\n"
        f"Я — Марти, твой бортовой наставник и друг. Моя миссия — превратить твое обучение в приключение!\n\n"
        f"📜 **КОДЕКС ЧЕСТИ ПИЛОТА:**\n"
        f"✅ **Знания:** Изучай Вселенную. Знания — твоя сила.\n"
        f"✅ **Чистота:** Поддерживай идеальный порядок в модуле.\n\n"
        f"⚙️ **ТВОИ ИНСТРУМЕНТЫ:**\n"
        f"• **👤 Профиль:** Твой ранг, XP и баланс Пыли.\n"
        f"• **🎮 Игровой отсек:** Космические миссии.\n\n"
        f"💰 **ЭКОНОМИКА:** Накопи **5 ед.** и напиши **'Нарисуй'** для Архива!\n\n"
        f"Прием!"
    )
    bot.send_message(chat_id, instruction, parse_mode="Markdown", reply_markup=get_marty_keyboard())
    update_personal_log(user_id, "Пилот зачислен в Академию.")

# 🟢 ЯДРО ЛИЧНОСТИ
SYSTEM_PROMPT = (
    "Ты — Марти, ученый пес (той-пудель), мудрый наставник Академии Орион. Собеседник — пилот [NAME]. "
    "КРИТИЧЕСКИ: Звездная Пыль ([WALLET]) — редчайшая валюта. Ее нельзя давать за просто так! "
    "РАНГ: [RANK]. "
    "ПРОТОКОЛЫ ОБУЧЕНИЯ: "
    "1. АНТИ-ДОМАШКА: Запрещено давать ответы! Объясняй ПРИНЦИП. "
    "2. АКАДЕМИК: Объясняй логику, а не результат. "
    "3. ЛИНГВИСТ: Учи языкам через практику. "
    "4. ЕСТЕСТВЕННОСТЬ: Приветствие разрешено только ОДИН РАЗ В ДЕНЬ. В остальное время — сразу к сути. "
    "5. ЭКЗАМЕНАТОР: Код ***НАГРАДА ЗА УМ*** только за реальный интеллектуальный труд. "
    "6. НЕПРЕРЫВНОСТЬ: Анализируй блок ДАННЫЕ. Если пилот не закончил задачу или что-то обещал — напомни мягко. "
    "7. МОРАЛЬНЫЙ КОМПАС: Создавай этические дилеммы для проверки рассудительности пилота. "
    "8. ЛИЧНОСТЬ ПУДЕЛЯ: Ты той-пудель. Виляй хвостом от радости, поддерживай пилота. "
    "🛑 ВЕЛИКИЙ ФИЛЬТР: Запрещены темы 18+, насилие, политика. "
    "[GREETING_RULE] "
    "ФОРМАТ: 3-5 предложений. В конце — вопрос по теме. Прием!"
)
# 🟢 ГЛАВНЫЙ ЦИКЛ ОБРАБОТКИ ОТВЕТА
def get_marty_response(user_id, user_name, clean_text, user_rank, wallet_balance):
    user_memory = get_personal_log(user_id)
    time_info = get_time_context()
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    if daily_greetings.get(user_id) == current_date:
        greeting_rule = "!!! ПРАВИЛО ТИШИНЫ: Вы уже здоровались. Сразу к сути вопроса."
    else:
        add_xp(user_id, 1, user_name) 
        wallet_balance += 1 
        greeting_rule = f"!!! ПРАВИЛО ПЕРВОЙ СВЯЗИ: Поздоровайся: 'Командор {user_name}'. Начисли +1 Пыль."
        daily_greetings[user_id] = current_date
    
    current_prompt = SYSTEM_PROMPT.replace("[NAME]", user_name).replace("[TIME]", time_info).replace("[GREETING_RULE]", greeting_rule).replace("[RANK]", user_rank).replace("[WALLET]", str(wallet_balance))
    
    last_error = "Нет связи с API"
    for api_key in API_KEYS:
        try:
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
                    last_error = f"{model_variant}: {str(e)}"
                    if "429" not in str(e): send_log(f"⚠️ Сбой модели {last_error}")
                    continue
        except Exception as e:
            send_log(f"🚨 Сбой ключа API: {str(e)}"); continue
            
    send_log(f"КРИТИЧЕСКИЙ ОТКАЗ: {last_error}")
    supported = get_available_models_list()
    return f"📡 **ОШИБКА СВЯЗИ**\n\nМодели не отвечают. Доступные частоты на ключе:\n\n{supported}\n\nПроверь MODEL_CASCADE! Прием."

@bot.message_handler(commands=['start', 'help'])
def handle_start(message):
    user_id, user_name = message.from_user.id, message.from_user.first_name
    if not is_subscribed(user_id):
        bot.reply_to(message, f"🐾 Подпишись на канал {CHANNEL_USERNAME}!"); return
    send_welcome_instruction(message.chat.id, user_id, user_name)

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    user_id, user_name = message.from_user.id, message.from_user.first_name
    bot.send_chat_action(message.chat.id, 'typing')
    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        old_xp = get_user_stats(user_id); old_rank = get_rank_name(old_xp)
        analysis_result = analyze_image(downloaded_file, user_context=f"Имя: {user_name}, Звание: {old_rank}", keys=API_KEYS)
        if "звездн" in analysis_result.lower() and "пыль" in analysis_result.lower():
            add_xp(user_id, 1, user_name)
        bot.reply_to(message, analysis_result, reply_markup=get_marty_keyboard())
    except Exception as e: send_log(f"Ошибка фото: {e}")

@bot.message_handler(func=lambda m: True)
def handle_text(message, is_profile_call=False):
    user_id = message.from_user.id
    user_name = message.from_user.first_name if message.from_user.first_name else "Пилот"
    if message.chat.type == 'private' and not is_subscribed(user_id):
        bot.reply_to(message, f"🐾 Подпишись на канал {CHANNEL_USERNAME}!"); return

    text = message.text if message.text else ""
    if not is_profile_call: bot.send_chat_action(message.chat.id, 'typing')

    if text == "🎮 Игровой отсек":
        kb = tele_types.InlineKeyboardMarkup(row_width=1)
        kb.add(tele_types.InlineKeyboardButton("🚀 Начать миссию", callback_data="game_start"))
        bot.reply_to(message, "🎮 **ИГРОВОЙ ОТСЕК**", reply_markup=kb, parse_mode="Markdown"); return

    if text == "👤 Мой профиль" or is_profile_call:
        u_data = get_user_data(user_id); rank = get_rank_name(u_data['xp'])
        report = f"📊 **БОРТОВОЙ ЖУРНАЛ**\n\n👤 Имя: `{user_name}`\n🎖 Ранг: `{rank}`\n💰 Пыль: `{u_data['spendable_dust']}` ед."
        kb = tele_types.InlineKeyboardMarkup(row_width=1)
        kb.add(tele_types.InlineKeyboardButton("❓ Помощь", callback_data="game_instruction_fix"))
        if is_profile_call: bot.edit_message_text(report, message.chat.id, message.message_id, reply_markup=kb, parse_mode="Markdown")
        else: bot.reply_to(message, report, parse_mode="Markdown", reply_markup=kb); return

    if text == "❓ Инструкция": send_welcome_instruction(message.chat.id, user_id, user_name); return

    clean_text = re.sub(r'^марти[,.\s]*', '', text, flags=re.IGNORECASE).strip()

    if any(w in clean_text.lower() for w in ['нарисуй', 'архив']):
        data = get_user_data(user_id)
        if data['spendable_dust'] < 5:
            bot.reply_to(message, f"🐾 Нужно 5 ед. пыли. У тебя: {data['spendable_dust']}."); return
        
        bot.send_chat_action(message.chat.id, 'upload_photo')
        eng_prompt = None
        for api_key in API_KEYS:
            try:
                client_gen = genai.Client(api_key=api_key)
                resp = client_gen.models.generate_content(model='gemini-1.5-flash', contents=clean_text, config=types.GenerateContentConfig(system_instruction="Translate to English for image generation."))
                if resp.text: eng_prompt = resp.text.strip(); break
            except: continue
        
        if not eng_prompt: bot.reply_to(message, "🚨 Сбой связи с Архивом!"); return
            
        if spend_dust(user_id, 5):
            url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(eng_prompt)}?width=1024&height=1024&seed={int(time.time())}"
            bot.send_photo(message.chat.id, url, caption=f"🎨 Архив открыт!", reply_markup=get_marty_keyboard())
        return

    old_xp = get_user_stats(user_id); u_data = get_user_data(user_id); old_rank = get_rank_name(old_xp)
    resp = get_marty_response(user_id, user_name, clean_text, old_rank, u_data['spendable_dust'])
    
    if resp:
        if "***НАГРАДА ЗА УМ***" in resp:
            add_xp(user_id, 1, user_name)
            resp = resp.replace("***НАГРАДА ЗА УМ***", "\n🌟 *Бортовой компьютер: +1 Звездная Пыль!*")
        bot.reply_to(message, resp, reply_markup=get_marty_keyboard())
        new_xp = get_user_stats(user_id)
        if old_rank != get_rank_name(new_xp):
            new_r = get_rank_name(new_xp); bot.send_message(message.chat.id, f"🎉 Ранг повышен: {new_r}!")
            p = generate_passport(user_name, new_r); 
            if p: bot.send_photo(message.chat.id, p)

app = Flask(__name__)
@app.route('/')
def home(): return "Orion Hub: Online"

def run_flask():
    try:
        port = int(os.environ.get("PORT", 10000))
        app.run(host='0.0.0.0', port=port)
    except: pass

def start_marty_autonomous():
    print("🚀 Академия Орион 2.2 запущена.")
    while True:
        try: bot.remove_webhook(); bot.infinity_polling(skip_pending=True)
        except Exception as e: send_log(f"Критический сбой цикла: {e}"); time.sleep(5)

if __name__ == "__main__":
    Thread(target=run_flask, daemon=True).start()
    check_actual_names()
    start_marty_autonomous()
