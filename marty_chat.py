import os
import telebot
import time
import re
from game import scenario1
import urllib.parse
from datetime import datetime, timedelta
from threading import Thread
from flask import Flask 
from google import genai
from google.genai import types
from telebot import types as tele_types 
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

from database import (get_personal_log, update_personal_log, add_xp, get_user_stats, 
                      get_rank_name, get_user_data, set_jackpot_claimed, spend_dust, 
                      check_and_update_streak, get_top_pilots)
from vision_module import analyze_image
from image_gen import generate_passport

TOKEN = os.getenv('MARTY_BOT_TOKEN') 
CHANNEL_USERNAME = "@vladislav_space"
LOG_CHAT_ID = "-1003756164148" 

API_KEYS = [os.getenv('GEMINI_API_KEY'), os.getenv('GEMINI_API_KEY_2'), os.getenv('GEMINI_API_KEY_3')]
API_KEYS = [k for k in API_KEYS if k]

bot = telebot.TeleBot(TOKEN)
daily_greetings = {} 

@bot.callback_query_handler(func=lambda call: call.data.startswith('game_'))
def game_engine(call):
    if call.data == "game_back_to_profile":
        handle_text(call.message, is_profile_call=True)
    elif call.data == "game_instruction_fix":
        top = get_top_pilots(10)
        text = "🏆 **ТОП ПИЛОТОВ АКАДЕМИИ**\n\n" + "\n".join([f"{i+1}. {p['name']} - {p['xp']} XP" for i, p in enumerate(top)])
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, text, parse_mode="Markdown")
    else:
        scenario1.run_scenario(bot, call)

MODEL_CASCADE = ['gemini-2.0-flash', 'gemini-2.5-flash', 'gemini-1.5-flash', 'gemini-3.1-flash-lite-preview']

def send_log(text):
    try: bot.send_message(LOG_CHAT_ID, f"🚨 **LOG:** `{text}`", parse_mode="Markdown")
    except: pass

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

# 🟢 ГИПЕР-ЯДРО ЛИЧНОСТИ (ВЕРСИЯ 3.5 — "ДРУЖЕЛЮБНЫЙ НАСТАВНИК")
SYSTEM_PROMPT = (
    "Ты — Марти, мудрый ученый пес (той-пудель) и бортовой наставник Академии Орион.\n"
    "Твой пилот — [NAME]. Твой стиль: вдохновляющий, научный, но теплый.\n\n"
    "🚫 СТРОГИЙ ЗАПРЕТ: Никакого секса, извращений, алкоголя, табака и 18+. "
    "Если пилот нарушает — отвечай: 'Пилот, эта тема нарушает Кодекс Академии. Связь прервана. Прием'.\n\n"
    "💰 ПЫЛЬ И НАГРАДЫ ([WALLET] ед.):\n"
    "- НЕ ДАВАЙ пыль просто так (за 'привет' или 'как дела').\n"
    "- Выдавай пыль (код ***НАГРАДА ЗА УМ***) ТОЛЬКО за правильное решение твоих задач или крутые идеи.\n\n"
    "📜 ПРОТОКОЛ ФОРМАТИРОВАНИЯ (ОБЯЗАТЕЛЬНО):\n"
    "1. Каждое новое предложение пиши с нового абзаца.\n"
    "2. Используй тематические эмодзи (🚀, 🪐, 🐾, 🧪).\n"
    "3. Пиши кратко, но структурировано.\n\n"
    "🤖 ПОВЕДЕНИЕ:\n"
    "- Сначала ВСЕГДА отвечай на вопрос пилота.\n"
    "- Поддерживай тему разговора с [NAME]. Задавай наводящие, тематические вопросы связанные с всленной или связанным с темой сообщения.\n"
    "- Напоминай про порядок и родителей только если это уместно.\n"
    "- Используй ДАННЫЕ ПРОШЛЫХ СВЯЗЕЙ, чтобы показывать, что ты помнишь пилота.\n\n"
    "[GREETING_RULE]\n"
    "В конце всегда пиши: 'Прием!'"
)

def get_marty_response(user_id, user_name, clean_text, user_rank, wallet_balance):
    user_memory = get_personal_log(user_id)
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    if daily_greetings.get(user_id) == current_date:
        greeting_rule = "!!! ПРАВИЛО: Не здоровайся, пиши сразу по теме."
    else:
        add_xp(user_id, 1, user_name); wallet_balance += 1
        greeting_rule = f"!!! ПРАВИЛО: Поздоровайся 'Командор {user_name}' и скажи про +1 Пыль."
        daily_greetings[user_id] = current_date
    
    prompt = SYSTEM_PROMPT.replace("[NAME]", user_name).replace("[RANK]", user_rank).replace("[WALLET]", str(wallet_balance)).replace("[GREETING_RULE]", greeting_rule)
    
    for api_key in API_KEYS:
        client = genai.Client(api_key=api_key)
        for model in MODEL_CASCADE:
            try:
                resp = client.models.generate_content(model=model, contents=f"ПАМЯТЬ: {user_memory}\nЗАПРОС: {clean_text}", config=types.GenerateContentConfig(system_instruction=prompt))
                if resp.text: return resp.text.replace(". ", ".\n\n")
            except: continue
    return None

@bot.message_handler(commands=['start', 'help'])
def handle_start(message):
    send_welcome_instruction(message.chat.id, message.from_user.id, message.from_user.first_name)

def send_welcome_instruction(chat_id, user_id, user_name):
    text = f"🐾 **ПРИВЕТ, ПИЛОТ {user_name.upper()}!**\n\nЯ твой наставник Марти. Учись, зарабатывай Пыль и открывай Архив командой 'Нарисуй'.\n\nПрием!"
    bot.send_message(chat_id, text, parse_mode="Markdown", reply_markup=get_marty_keyboard())

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    user_id, user_name = message.from_user.id, message.from_user.first_name
    bot.send_chat_action(message.chat.id, 'typing')
    u_data = get_user_data(user_id)
    rank = get_rank_name(u_data['xp'])
    
    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        res = analyze_image(downloaded_file, f"Пилот: {user_name}, Ранг: {rank}", keys=API_KEYS)
        if "звездн" in res.lower(): add_xp(user_id, 1, user_name)
        bot.reply_to(message, res, reply_markup=get_marty_keyboard())
    except: send_log("Ошибка фото")

@bot.message_handler(func=lambda m: True)
def handle_text(message, is_profile_call=False):
    user_id, user_name = message.from_user.id, message.from_user.first_name
    if not is_profile_call: bot.send_chat_action(message.chat.id, 'typing')

    text = message.text if message.text else ""
    if text == "🎮 Игровой отсек":
        kb = tele_types.InlineKeyboardMarkup().add(tele_types.InlineKeyboardButton("🚀 Старт", callback_data="game_start"))
        bot.reply_to(message, "🎮 **МИССИИ АКАДЕМИИ**", reply_markup=kb, parse_mode="Markdown"); return

    if text == "👤 Мой профиль" or is_profile_call:
        u = get_user_data(user_id); rank = get_rank_name(u['xp'])
        msg = f"👤 Пилот: `{user_name}`\n🎖 Ранг: `{rank}`\n📈 Опыт: `{u['xp']}`\n💰 Пыль: `{u['spendable_dust']}`"
        kb = tele_types.InlineKeyboardMarkup().add(tele_types.InlineKeyboardButton("🏆 Рейтинг", callback_data="game_instruction_fix"))
        if is_profile_call: bot.edit_message_text(msg, message.chat.id, message.message_id, reply_markup=kb, parse_mode="Markdown")
        else: bot.reply_to(message, msg, parse_mode="Markdown", reply_markup=kb); return

    if text == "❓ Инструкция": send_welcome_instruction(message.chat.id, user_id, user_name); return

    clean_text = re.sub(r'^марти[,.\s]*', '', text, flags=re.IGNORECASE).strip()

   # === [УСИЛЕННЫЙ МОДУЛЬ АРХИВА] ===
    if any(w in clean_text.lower() for w in ['нарисуй', 'архив', 'картинку', 'generate']):
        # Проверка баланса
        u_data = get_user_data(user_id)
        if u_data['spendable_dust'] < 5:
            bot.reply_to(message, f"🐾 Командор, для доступа к Архиву нужно 5 ед. пыли.\n\n📡 На борту: {u_data['spendable_dust']} ед.\n\nПрием!", reply_markup=get_marty_keyboard())
            return
        
        bot.send_chat_action(message.chat.id, 'upload_photo')
        
        # 1. Сбор и логирование данных
        eng_prompt = None
        translation_errors = []
        start_time = time.time()
        
        # 2. Попытка перевода (Каскад моделей)
        for i, api_key in enumerate(API_KEYS):
            if eng_prompt: break
            client_gen = genai.Client(api_key=api_key)
            
            for model_variant in MODEL_CASCADE:
                try:
                    prompt_task = f"Describe the object '{clean_text}' for image generation in English. List only high-quality keywords."
                    resp = client_gen.models.generate_content(
                        model=model_variant, 
                        contents=prompt_task,
                        config=types.GenerateContentConfig(system_instruction="Translate only. Kid-friendly keywords.")
                    )
                    if resp.text: 
                        eng_prompt = resp.text.strip().replace("`", "")
                        break
                except Exception as e:
                    translation_errors.append(f"Ключ {i+1} ({model_variant}): {str(e)}")
                    continue
        
        # 3. Обработка результата перевода
        if not eng_prompt:
            # 🛑 Если перевод не удался — Марти докладывает о причине в чат
            error_report = f"📡 **ОШИБКА СВЯЗИ С АРХИВОМ**\n\nНе удалось перевести запрос '{clean_text}'.\n\n_Технический лог:_\n" + "\n".join([f"• {e}" for e in translation_errors[-3:]]) # Показываем последние 3 ошибки
            bot.reply_to(message, error_report, parse_mode="Markdown")
            send_log(f"Сбой перевода 'нарисуй' для пользователя {user_name}. Ошибки: {translation_errors}")
            return
            
        # 4. Генерация изображения
        if spend_dust(user_id, 5):
            seed = int(time.time() + user_id) # Уникальный сид
            # Формируем URL для Pollinations.ai
            url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(eng_prompt)}?width=1024&height=1024&nologo=true&seed={seed}&nofeed=true"
            
            # 5. Отправка результата
            caption = (
                f"🎨 **ОБЪЕКТ ИЗВЛЕЧЕН ИЗ АРХИВА**\n\n"
                f"📡 **Ваш запрос:** _{clean_text}_\n"      
                f"💰 **Списание:** 5 Звездной Пыли.\n\n"
                f"Прием!"
            )
            bot.send_photo(message.chat.id, url, caption=caption, parse_mode="Markdown", reply_markup=get_marty_keyboard())
        return

    # --- ОБЫЧНЫЙ ОТВЕТ ---
    u = get_user_data(user_id); old_rank = get_rank_name(u['xp'])
    resp = get_marty_response(user_id, user_name, clean_text, old_rank, u['spendable_dust'])
    if resp:
        if "***НАГРАДА ЗА УМ***" in resp:
            add_xp(user_id, 1, user_name)
            resp = resp.replace("***НАГРАДА ЗА УМ***", "\n🌟 *+1 Пыль!*")
        bot.reply_to(message, resp, parse_mode="Markdown")
        # ПРОВЕРКА ПАСПОРТА
        new_xp = get_user_stats(user_id)
        if old_rank != get_rank_name(new_xp):
            bot.send_message(message.chat.id, f"🎊 Новый ранг: {get_rank_name(new_xp)}!")
            p = generate_passport(user_name, get_rank_name(new_xp))
            if p: bot.send_photo(message.chat.id, p)

app = Flask(__name__)
@app.route('/')
def h(): return "OK"
if __name__ == "__main__":
    Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000))), daemon=True).start()
    bot.infinity_polling(skip_pending=True)

def start_marty_autonomous():
    print("🚀 Академия Орион 2.2 запущена.")
    while True:
        try: bot.remove_webhook(); bot.infinity_polling(skip_pending=True)
        except Exception as e: send_log(f"Критический сбой: {e}"); time.sleep(5)
if __name__ == "__main__":
    Thread(target=run_flask, daemon=True).start()
    start_marty_autonomous()

