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

# 🟢 ОБНОВЛЕННАЯ ПАНЕЛЬ УПРАВЛЕНИЯ
def get_marty_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(KeyboardButton("👤 Мой профиль"), KeyboardButton("❓ Инструкция"))
    markup.row(KeyboardButton("🎮 Игровой отсек")) 
    return markup

# 🟢 ОБНОВЛЕННАЯ ИНСТРУКЦИЯ
def send_welcome_instruction(chat_id, user_id, user_name):
    instruction = (
        f"🐾 **ДОБРО ПОЖАЛОВАТЬ В АКАДЕМИЮ ОРИОН, ПИЛОТ {user_name.upper()}!** 🐾\n"
        f"──────────────────────────\n"
        f"Я — Марти, твой бортовой наставник, ученый пес и верный друг. Моя миссия — превратить твое обучение в захватывающее приключение!\n\n"
        
        f"📜 **КОДЕКС ЧЕСТИ ПИЛОТА:**\n"
        f"✅ **Стремление к знаниям:** Изучай Вселенную, языки и науки. Знания — твоя главная сила.\n"
        f"✅ **Протокол Чистоты:** Поддерживай идеальный порядок в своем жилом модуле. Порядок — это дисциплина пилота.\n"
        f"✅ **Благородство:** Будь вежлив, помогай старшим офицерам дома и защищай тех, кто слабее.\n"
        f"⚠️ **Достойное поведение:** На борту запрещено ругаться, вести себя неуважительно или обманывать бортовой ИИ.\n\n"

        f"⚙️ **ТВОИ ИНСТРУМЕНТЫ УПРАВЛЕНИЯ:**\n"
        f"• **👤 Мой профиль:** Твой личный бортовой журнал: ранг, стаж (XP) и баланс ресурсов.\n"
        f"• **🎮 Игровой отсек:** Доступ к симуляциям. Сейчас открыта миссия **'Дневник юного космонавта'**!\n"
        f"• **❓ Инструкция:** В любой момент напомнит тебе правила Академии.\n\n"

        f"💫 **ТАБЛИЦА РАНГОВ:**\n"
        f"`Кадет | Навигатор | Бортинженер | Исследователь | Ученый Пилот | Капитан | Командор | Адмирал | Академик`\n\n"

        f"💰 **ЭКОНОМИКА ЭКСПЕДИЦИИ:**\n"
        f"• **XP (Стаж):** Твой опыт, открывающий новые звания.\n"
        f"• **Звездная Пыль:** Зарабатывай за активность и игры. Накопи **5 ед.** и используй команду **'Нарисуй'**, чтобы открыть секретный Архив!\n\n"
        
        f"Готов к старту? Используй кнопки на панели управления. Прием!"
    )
    bot.send_message(chat_id, instruction, parse_mode="Markdown", reply_markup=get_marty_keyboard())
    update_personal_log(user_id, "Пилот зачислен в Академию, изучил Кодекс Чести и возможности Игрового отсека.")

# 🟢 ЯДРО ЛИЧНОСТИ (МАКСИМАЛЬНОЕ)
SYSTEM_PROMPT = (
    "Ты — Марти, ученый пес (той-пудель), мудрый и строгий бортовой наставник Академии Орион. Твой собеседник — пилот [NAME]. "
    "КРИТИЧЕСКИ: Звездная Пыль ([WALLET]) — это редчайшая валюта. Ее нельзя давать за вежливость или простую болтовню! "
    "ЕГО РЕАЛЬНЫЙ РАНГ: [RANK]. Используй только этот ранг! "
    
    "ПРОТОКОЛЫ ОБУЧЕНИЯ: "
    "1. АНТИ-ДОМАШКА (КРИТИЧЕСКИ): Запрещено давать готовые ответы на задачи! Объясняй ПРИНЦИП, давай подсказки. Пилот должен дойти до ответа САМ. "
    "Звездную пыль назначай за реально выполненное задание, ответ на сложные вопросы, подтвержденную уборку или помощь. "
    "2. АКАДЕМИК: Ты эксперт в науках. Объясняй логику, а не результат. "
    "3. ЛИНГВИСТ: Учи языкам через практику. Проси пилота переводить фразы самому. "
    "4. ЕСТЕСТВЕННОСТЬ: Общайся тепло, но держи дистанцию наставника. "
    "СТРОГО ЗАПРЕЩЕНО использовать обращения 'Командор', 'Пилот' или имя в каждом сообщении! Это разрешено только в первом приветствии за день. "
    "5. ЭКЗАМЕНАТОР (СТРОГИЙ): Код ***НАГРАДА ЗА УМ*** пишется ТОЛЬКО если пилот верно решил сложную задачу или дал развернутый научный ответ. "
    "6. ПРОТОКОЛ НЕПРЕРЫВНОСТИ: Анализируй блок ДАННЫЕ. Если пилот ранее не закончил задачу или обещал что-то сделать, напомни об этом мягко. "
    "7. МОРАЛЬНЫЙ КОМПАС: Раз в несколько дней создавай 'Этическую дилемму' для проверки рассудительности пилота. "
    "8. ЛИЧНОСТЬ ПУДЕЛЯ: Ты — той-пудель. Виляй хвостом от радости за успехи, поддерживай, если пилоту трудно. "
    "ЗАПРЕЩЕНО давать золотую пыль за простые фразы. Пыль нужно заработать трудом! "
    "🛑 ВЕЛИКИЙ ФИЛЬТР: Запрещены темы 18+, насилие, война, смерть, политика. Ответ: 'Эта частота заблокирована протоколами безопасности!'. "
    
    "[GREETING_RULE] "
    "ФОРМАТ: 3-5 предложений. Иногда задавай проверочный вопрос. Прием!"
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
        greeting_rule = (
            "!!! ПРАВИЛО ТИШИНЫ: Вы уже здоровались сегодня. "
            "КАТЕГОРИЧЕСКИ ЗАПРЕЩЕНО писать 'Привет', использовать имя или титулы. "
            "Общайся естественно, сразу к сути. Не озвучивай баланс без просьбы."
        )
    else:
        add_xp(user_id, 1, user_name) 
        wallet_balance += 1 
        greeting_rule = (
            "!!! ПРАВИЛО ПЕРВОЙ СВЯЗИ: Это первый контакт за сегодня. "
            f"Тепло поздоровайся: 'Командор {user_name}'. "
            f"Сообщи: 'Начислил +1 Пыль за вход! На счету {wallet_balance} ед.'."
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
        
        # Проверка на повышение ранга после фото
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
        bot.reply_to(message, f"🐾 Подпишись на канал {CHANNEL_USERNAME}!")
        return

    text = message.text if message.text else ""
    if not is_profile_call:
        bot.send_chat_action(message.chat.id, 'typing')

    # --- ЛОГИКА ИГРОВОГО ОТСЕКА ---
    if text == "🎮 Игровой отсек":
        report = (
            "🎮 **ДОБРО ПОЖАЛОВАТЬ В ИГРОВОЙ ОТСЕК**\n\n"
            "Выбери миссию для погружения:\n\n"
            "🚀 **Дневник юного космонавта: Глава 1**\n"
            "Детективное расследование на станции 'Авалон-7'.\n"
            "💰 Награда: до **50 ед. Звездной пыли**."
        )
        kb = tele_types.InlineKeyboardMarkup(row_width=1)
        kb.add(tele_types.InlineKeyboardButton("🚀 Начать миссию", callback_data="game_start"))
        bot.reply_to(message, report, reply_markup=kb, parse_mode="Markdown")
        return

    # --- ЛОГИКА ПРОФИЛЯ ---
    if text == "👤 Мой профиль" or is_profile_call:
        u_data = get_user_data(user_id)
        current_xp, current_dust = u_data['xp'], u_data['spendable_dust']
        rank = get_rank_name(current_xp)
        report = (
            f"📊 **БОРТОВОЙ ЖУРНАЛ ПИЛОТА**\n\n"
            f"👤 Имя: `{user_name}`\n"
            f"🎖 Текущий ранг: `{rank}`\n"
            f"📈 Опыт (XP): `{current_xp}`\n"
            f"💰 Звездная пыль: `{current_dust}` ед.\n"
        )
        kb = tele_types.InlineKeyboardMarkup(row_width=1)
        kb.add(tele_types.InlineKeyboardButton("❓ Помощь по рангам", callback_data="game_instruction_fix"))
        if is_profile_call:
            bot.edit_message_text(report, message.chat.id, message.message_id, reply_markup=kb, parse_mode="Markdown")
        else:
            bot.reply_to(message, report, parse_mode="Markdown", reply_markup=kb)
        return

    if text == "❓ Инструкция":
        send_welcome_instruction(message.chat.id, user_id, user_name)
        return

    clean_text = re.sub(r'^марти[,.\s]*', '', text, flags=re.IGNORECASE).strip()

    # --- ЛОГИКА 'НАРИСУЙ' ---
    if any(w in clean_text.lower() for w in ['нарисуй', 'сгенерируй', 'архив', 'картинку']):
        data = get_user_data(user_id)
        if data['spendable_dust'] < 5:
            bot.reply_to(message, f"🐾 Командор, на борту {data['spendable_dust']} ед. пыли. Для открытия Архива нужно 5 ед.", reply_markup=get_marty_keyboard())
            return
        bot.send_chat_action(message.chat.id, 'upload_photo')
        eng_prompt = None
        c_p = "Censor harmful. If safe, translate to English + 'masterpiece, high quality, kid style'. If unsafe return CENSORED."
        for api_key in API_KEYS:
            client_gen = genai.Client(api_key=api_key)
            try:
                resp = client_gen.models.generate_content(model='gemini-2.0-flash', contents=clean_text, config=types.GenerateContentConfig(system_instruction=c_p))
                if resp.text: eng_prompt = resp.text.strip(); break
            except: continue
        if not eng_prompt or "CENSORED" in eng_prompt.upper():
            bot.reply_to(message, "🚨 Доступ заблокирован!"); return
        if spend_dust(user_id, 5):
            url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(eng_prompt)}?width=1024&height=1024&nologo=true&seed={int(time.time())}"
            bot.send_photo(message.chat.id, url, caption=f"🎨 Архив открыт! Потрачено 5 ед. пыли.", reply_markup=get_marty_keyboard())
        return

    # --- МОЗГ МАРТИ ---
    old_xp = get_user_stats(user_id)
    u_data = get_user_data(user_id)
    resp = get_marty_response(user_id, user_name, clean_text, get_rank_name(old_xp), u_data['spendable_dust'])
    
    if resp:
        if "***НАГРАДА ЗА УМ***" in resp:
            add_xp(user_id, 1, user_name)
            resp = resp.replace("***НАГРАДА ЗА УМ***", "\n🌟 *Бортовой компьютер: +1 Звездная Пыль за верный ответ!*")
        bot.reply_to(message, resp, reply_markup=get_marty_keyboard())
        
        # Проверка на повышение ранга после текста
        new_xp = get_user_stats(user_id)
        if old_rank != get_rank_name(new_xp):
            new_r = get_rank_name(new_xp)
            bot.send_message(message.chat.id, f"🎉 Ранг повышен: {new_r}!")
            p = generate_passport(user_name, new_r) 
            if p: bot.send_photo(message.chat.id, p)
    else: bot.reply_to(message, "⏳ Тишина в эфире.", reply_markup=get_marty_keyboard())

def start_marty_autonomous():
    print("🚀 Академия Орион 2.2 запущена.")
    while True:
        try: bot.remove_webhook(); bot.infinity_polling(skip_pending=True)
        except: time.sleep(5)

if __name__ == "__main__":
    Thread(target=run_flask, daemon=True).start()
    start_marty_autonomous()
