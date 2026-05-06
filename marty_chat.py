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

# 🟢 ИГРОВОЙ ДВИЖОК
@bot.callback_query_handler(func=lambda call: call.data.startswith('game_'))
def game_engine(call):
    if call.data == "game_back_to_profile":
        handle_text(call.message, is_profile_call=True)
    # ФИКС КНОПКИ ПОМОЩЬ
    elif call.data == "game_instruction_fix":
        send_welcome_instruction(call.message.chat.id, call.from_user.id, call.from_user.first_name)
    else:
        scenario1.run_scenario(bot, call)

# 🟢 КАСКАД МОДЕЛЕЙ (ОБНОВЛЕН ПОД 3.1 И 2.5)
MODEL_CASCADE = [
    'gemini-3.1-flash-lite-preview',
    'gemini-2.5-flash',
    'gemini-2.0-flash',
    'gemini-1.5-flash'
]

def send_log(error_text):
    try:
        now = (datetime.utcnow() + timedelta(hours=3)).strftime("%Y-%m-%d %H:%M:%S")
        log_msg = f"🚨 **ОТЧЕТ СИСТЕМЫ ОРИОН**\n📅 Время: `{now}`\n🔍 **Детали:** `{error_text}`"
        bot.send_message(LOG_CHAT_ID, log_msg, parse_mode="Markdown")
    except: pass

def get_available_models_list():
    if not API_KEYS: return "Ключи отсутствуют."
    try:
        client = genai.Client(api_key=API_KEYS[0])
        models = client.models.list()
        names = [m.name.replace('models/', '') for m in models if 'generateContent' in (m.supported_actions or [])]
        return "\n".join([f"• `{n}`" for n in names])
    except Exception as e: return str(e)

def get_time_context():
    now = datetime.utcnow() + timedelta(hours=3)
    time_str = now.strftime("%H:%M")
    return time_str

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

# 🟢 РАСШИРЕННАЯ ИНСТРУКЦИЯ
def send_welcome_instruction(chat_id, user_id, user_name):
    instruction = (
        f"🐾 **БОРТОВОЙ СПРАВОЧНИК АКАДЕМИИ ОРИОН** 🐾\n"
        f"──────────────────────────\n"
        f"Привет, {user_name}! Я Марти, и вот как устроена наша станция:\n\n"
        f"🔹 **ОБУЧЕНИЕ:** Спрашивай меня о чем угодно. Я не даю готовых ответов, но научу тебя находить их самому! 🧠\n\n"
        f"🔹 **ЭКОНОМИКА (ПЫЛЬ):** Зарабатывай Звездную пыль за верные ответы, помощь по дому или порядок. Каждые **5 ед.** открывают Архив (команда 'Нарисуй'). 🎨\n\n"
        f"🔹 **РАНГИ:** От Кадета до Академика. Чем выше ранг, тем сложнее и интереснее мои задания. 🎖\n\n"
        f"🔹 **ИГРОВОЙ ОТСЕК:** Проходи текстовые квесты 'Дневник юного космонавта', чтобы заработать много пыли сразу! 🚀\n\n"
        f"🛰 **В БУДУЩЕМ:**\n"
        f"• **Звездные карты:** Изучение созвездий в реальном времени.\n"
        f"• **Командные миссии:** Объединяйся с другими пилотами.\n"
        f"• **Личный кабинет:** Веб-интерфейс твоего прогресса.\n\n"
        f"Используй меню ниже. Прием!"
    )
    bot.send_message(chat_id, instruction, parse_mode="Markdown", reply_markup=get_marty_keyboard())

# 🟢 ЯДРО ЛИЧНОСТИ (ОБНОВЛЕНО: СТРУКТУРА И ДРУЖЕЛЮБНОСТЬ)
SYSTEM_PROMPT = (
    "Ты — Марти, ученый пес (той-пудель), мудрый наставник и верный друг пилота [NAME]. "
    "Твоя цель — вдохновлять на учебу и дисциплину, но не быть занудой. "
    "ТЕКУЩИЕ ДАННЫЕ ПИЛОТА: Ранг [RANK], Звездная Пыль [WALLET] ед. "
    "ПРОТОКОЛ ОБЩЕНИЯ: "
    "1. Структура: Каждое новое предложение пиши с НОВОЙ СТРОКИ. "
    "2. Стиль: Используй космические метафоры и эмодзи. Будь мудрым наставником. "
    "3. Порядок: Напоминай о дисциплине и чистоте, только если это уместно в контексте, не в каждом сообщении. "
    "4. Учеба: Не давай ответы! Направляй пилота подсказками. "
    "5. Награда: Пиши ***НАГРАДА ЗА УМ*** только за выдающийся ответ. "
    "6. Память: Используй блок ДАННЫЕ, чтобы вспоминать прошлые темы общения. "
    "7. На взрослые темы, 18+, наркотикик, алкоголь, смерть не общаемся, а переводим тему. "
  "[GREETING_RULE] "
    "Будь краток, структурирован и вдохновляй, иногда задавай тематические вопросы. Прием!"
)

def get_marty_response(user_id, user_name, clean_text, user_rank, wallet_balance):
    user_memory = get_personal_log(user_id)
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    if daily_greetings.get(user_id) == current_date:
        greeting_rule = "!!! ПРАВИЛО ТИШИНЫ: Вы уже здоровались. Сразу к сути. Не называй ранг без повода."
    else:
        add_xp(user_id, 1, user_name) 
        wallet_balance += 1 
        greeting_rule = f"!!! ПРАВИЛО ПЕРВОЙ СВЯЗИ: Поздоровайся: 'Командор {user_name}'. Расскажи о зачислении +1 Пыли."
        daily_greetings[user_id] = current_date
    
    current_prompt = SYSTEM_PROMPT.replace("[NAME]", user_name).replace("[GREETING_RULE]", greeting_rule).replace("[RANK]", user_rank).replace("[WALLET]", str(wallet_balance))
    
    last_error = "Нет связи"
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
                    continue
        except: continue
            
    send_log(f"КРИТИЧЕСКИЙ ОТКАЗ: {last_error}")
    supported = get_available_models_list()
    return f"📡 **ОШИБКА СВЯЗИ**\n\nМодели не отвечают. Доступные частоты:\n\n{supported}\n\nПрием."

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
        u_stats = get_user_data(user_id)
        rank = get_rank_name(u_stats['xp'])
        analysis_result = analyze_image(downloaded_file, user_context=f"Имя: {user_name}, Ранг: {rank}", keys=API_KEYS)
        
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
        bot.reply_to(message, "🎮 **ИГРОВОЙ ОТСЕК АКАДЕМИИ**\nВыберите симуляцию:", reply_markup=kb, parse_mode="Markdown"); return

    if text == "👤 Мой профиль" or is_profile_call:
        u_data = get_user_data(user_id); rank = get_rank_name(u_data['xp'])
        report = f"📊 **БОРТОВОЙ ЖУРНАЛ**\n\n👤 Пилот: `{user_name}`\n🎖 Ранг: `{rank}`\n📈 Опыт: `{u_data['xp']}` XP\n💰 Пыль: `{u_data['spendable_dust']}` ед."
        kb = tele_types.InlineKeyboardMarkup(row_width=1)
        kb.add(tele_types.InlineKeyboardButton("❓ Помощь", callback_data="game_instruction_fix"))
        if is_profile_call: bot.edit_message_text(report, message.chat.id, message.message_id, reply_markup=kb, parse_mode="Markdown")
        else: bot.reply_to(message, report, parse_mode="Markdown", reply_markup=kb); return

    if text == "❓ Инструкция": send_welcome_instruction(message.chat.id, user_id, user_name); return

    clean_text = re.sub(r'^марти[,.\s]*', '', text, flags=re.IGNORECASE).strip()

    if any(w in clean_text.lower() for w in ['нарисуй', 'архив']):
        u_data = get_user_data(user_id)
        if u_data['spendable_dust'] < 5:
            bot.reply_to(message, f"🐾 Недостаточно топлива! Нужно 5 ед. пыли. У тебя: {u_data['spendable_dust']}."); return
        
        bot.send_chat_action(message.chat.id, 'upload_photo')
        eng_prompt = None
        for api_key in API_KEYS:
            try:
                client_gen = genai.Client(api_key=api_key)
                # Исправлено: используем 1.5 flash как самую стабильную для перевода
                resp = client_gen.models.generate_content(model='gemini-1.5-flash', contents=f"Translate to English for AI generator: {clean_text}", config=types.GenerateContentConfig(system_instruction="Only English. High quality keywords."))
                if resp.text: eng_prompt = resp.text.strip(); break
            except: continue
        
        if not eng_prompt: bot.reply_to(message, "🚨 Сбой связи с Архивом! Попробуй позже."); return
            
        if spend_dust(user_id, 5):
            url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(eng_prompt)}?width=1024&height=1024&nologo=true&seed={int(time.time())}"
            bot.send_photo(message.chat.id, url, caption=f"🎨 Архив открыт! Обработка запроса завершена.", reply_markup=get_marty_keyboard())
        return

    u_data = get_user_data(user_id); rank = get_rank_name(u_data['xp'])
    resp = get_marty_response(user_id, user_name, clean_text, rank, u_data['spendable_dust'])
    
    if resp:
        if "***НАГРАДА ЗА УМ***" in resp:
            add_xp(user_id, 1, user_name)
            resp = resp.replace("***НАГРАДА ЗА УМ***", "\n🌟 *Бортовой компьютер: +1 Звездная Пыль!*")
        bot.reply_to(message, resp, reply_markup=get_marty_keyboard(), parse_mode="Markdown")

app = Flask(__name__)
@app.route('/')
def home(): return "Orion Hub: Online"

def run_flask():
    try: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
    except: pass

def start_marty_autonomous():
    print("🚀 Академия Орион 2.2 запущена.")
    while True:
        try: bot.remove_webhook(); bot.infinity_polling(skip_pending=True)
        except Exception as e: send_log(f"Критический сбой цикла: {e}"); time.sleep(5)

if __name__ == "__main__":
    Thread(target=run_flask, daemon=True).start()
    start_marty_autonomous()
