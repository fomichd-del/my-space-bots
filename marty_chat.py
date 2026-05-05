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
CHANNEL_USERNAME = "@vladislav_space" # Название твоего канала

client = genai.Client(api_key=GEMINI_API_KEY)
bot = telebot.TeleBot(TOKEN)

# Оперативная память для приветствий
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
    
    if 0 <= hour < 5: return f"{time_str} (Глубокая ночь. Пора спать)"
    elif 5 <= hour < 11: return f"{time_str} (Утро. Время подготовки)"
    elif 11 <= hour < 17: return f"{time_str} (День. Время для школы)"
    elif 17 <= hour < 23: return f"{time_str} (Вечер. Время отдыха)"
    else: return f"{time_str} (Ночь. Пора спать)"

def is_subscribed(user_id):
    # ПРОПУСКАЕМ системные репосты (Telegram ID 777000) и посты от самого канала (отрицательные ID)
    if user_id == 777000 or user_id < 0:
        return True
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        if member.status in ['member', 'administrator', 'creator']:
            return True
        return False
    except Exception as e:
        return True 

def is_meteor_shower():
    return datetime.now().weekday() >= 5

# 🟢 ПРОВЕРКА НА НОВИЧКА
def is_very_first_time(user_id):
    user_data = get_user_data(user_id)
    user_memory = get_personal_log(user_id)
    if user_data['xp'] == 0 and "Данных пока нет" in user_memory:
        return True
    return False

# 🟢 ПОЛНАЯ ИНСТРУКЦИЯ
def send_welcome_instruction(chat_id, user_id, user_name):
    intro_text = (
        f"🐾 Гав! Привет, {user_name}! Я Марти — ученый пес и твой бортовой наставник.\n\n"
        "Моя миссия — помогать тебе учиться, поддерживать порядок и исследовать космос! 🚀\n\n"
        "📜 **ПРАВИЛА АКАДЕМИИ:**\n"
        "✨ **Звездная пыль** — наша валюта. Собирай ее, чтобы получать новые звания (от Кадета до Академика) и паспорта!\n\n"
        "📸 **Как получить пыль?** Присылай мне ФОТО-доказательства своих успехов: убранная комната, сделанные уроки или помощь родителям.\n\n"
        "🎁 **Секретные бонусы:**\n"
        "• В выходные — Метеоритный дождь (награда х2!).\n"
        "• За присылку фото каждый день — бонусы!\n"
        "• Найди секретные артефакты на фото — сорви джекпот.\n\n"
        "🏆 Напиши **РАДАР**, чтобы увидеть топ пилотов.\n"
        "🎨 Напиши **НАРИСУЙ [идея]**, чтобы открыть Архив картинок (стоит 5 пыли!).\n\n"
        "Готов? Пришли мне фото своей чистой комнаты прямо сейчас! Прием!"
    )
    bot.send_message(chat_id, intro_text)
    update_personal_log(user_id, "Пилот успешно прошел первичный инструктаж и зачислен в Академию.")

# 🟢 ЯДРО ЛИЧНОСТИ (ОБНОВЛЕНО: ЭКОНОМИКА)
SYSTEM_PROMPT = (
    "Ты — Марти, ученый пес (той-пудель) и бортовой наставник. "
    "1. ЛИЧНОСТЬ: Мудрый, добрый. Имя: [NAME]. Звание: [RANK]. Свободной пыли в кошельке: [WALLET]. Время: [TIME]. "
    "2. АТТЕСТАЦИЯ: ЧЕМ ВЫШЕ ЗВАНИЕ, ТЕМ СТРОЖЕ! Пыль давай ТОЛЬКО за фото. "
    "3. ЦЕНЗУРА (СТРОГО): Запрет на секс, смерть, насилие, политику. "
    "[GREETING_RULE] "
    "4. ИНСТРУКЦИЯ И ЭКОНОМИКА (ВАЖНО!): Если пилот спрашивает про правила, Радар или почему очки радара отличаются от кошелька, ПОДРОБНО объясни: "
    "'В Академии два разных счета! 1) Общий опыт (в Радаре) — копится навсегда. Он нужен для получения Званий. Паспорта выдаются ТОЛЬКО при переходе на новое звание (если ты уже на высшем звании, новых паспортов пока нет). "
    "2) Кошелек — это свежая пыль. Когда ты покупаешь картинки в Архиве, пыль списывается из кошелька, при этом твой общий опыт и звание не сгорают! Чтобы пополнить кошелек для новых рисунков, нужно выполнять миссии!' "
    "5. ФОРМАТ: 3-4 предложения. В конце 'Прием' и вопрос. Затем '###MEM###' и память."
)

app = Flask(__name__)
@app.route('/')
def home(): return "Marty Academy Core: Online"

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
        greeting_rule = "\n!!! КРИТИЧЕСКОЕ ПРАВИЛО: Вы УЖЕ здоровались сегодня. КАТЕГОРИЧЕСКИ ЗАПРЕЩЕНО писать слова 'Привет', 'Здравствуй', 'Гав, пилот' и любые другие приветствия. НАЧИНАЙ ОТВЕТ СРАЗУ ПО СУТИ ВОПРОСА! !!!\n"
    else:
        greeting_rule = "\nПРАВИЛО: Это первое сообщение за день. ОБЯЗАТЕЛЬНО поздоровайся с пилотом (например: 'Гав! Привет, [NAME]!').\n"
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

# --- ОБРАБОТЧИКИ ---

@bot.message_handler(commands=['start', 'help'])
def handle_start(message):
    user_id, user_name = message.from_user.id, message.from_user.first_name
    if not is_subscribed(user_id):
        bot.reply_to(message, f"🐾 Гав! Сначала подпишись на канал {CHANNEL_USERNAME}!")
        return
    send_welcome_instruction(message.chat.id, user_id, user_name)

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    user_id, user_name = message.from_user.id, message.from_user.first_name
    
    if not is_subscribed(user_id):
        bot.reply_to(message, f"🐾 Гав! Извини, Пилот! Сначала подпишись на канал {CHANNEL_USERNAME}!")
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

        anti_cheat_context = (f"Имя: {user_name}. Звание: {old_rank}. Память: {user_memory}. "
                              "Строго оцени фото. Старшим званиям пыль только за идеальный порядок!")
        
        analysis_result = analyze_image(downloaded_file, user_context=anti_cheat_context)
        
        if "звездн" in analysis_result.lower() and "пыль" in analysis_result.lower():
            base_dust = 2 if is_meteor_shower() else 1
            total_dust = base_dust
            
            if is_meteor_shower():
                bot.send_message(message.chat.id, "☄️ ВНИМАНИЕ: Зафиксирован Метеоритный дождь! Награда удвоена (Х2)!")

            streak = check_and_update_streak(user_id)
            if streak >= 3:
                total_dust += 1
                bot.send_message(message.chat.id, f"🔥 Серия миссий: {streak} дней подряд! Выдан бонус!")
            
            if "джекпот" in analysis_result.lower():
                user_db_data = get_user_data(user_id)
                if not user_db_data["jackpot_claimed"]:
                    total_dust += 3 
                    set_jackpot_claimed(user_id)
                    bot.send_message(message.chat.id, "🎰 СЕКРЕТНЫЙ АРТЕФАКТ НАЙДЕН! Выдан джекпот Академии!")
            
            total_dust = min(total_dust, 4)
            add_xp(user_id, total_dust, user_name)
            
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

    if is_very_first_time(user_id):
        send_welcome_instruction(message.chat.id, user_id, user_name)
        return

    text_lower = message.text.lower()
    is_private = message.chat.type == 'private'
    is_called = text_lower.startswith('марти') or f"@{BOT_USERNAME}" in text_lower

    if is_private or is_called:
        bot.send_chat_action(message.chat.id, 'typing')
        clean_text = re.sub(r'^марти[,.\s]*', '', message.text, flags=re.IGNORECASE).strip()
        clean_lower = clean_text.lower()

        # --- РАДАР ---
        if clean_lower in ['радар', 'рейтинг', 'топ']:
            top_pilots = get_top_pilots(5)
            if not top_pilots:
                bot.reply_to(message, "📡 Радар пока пуст. Будь первым!")
                return
            
            radar_msg = "🏆 **РАДАР АКАДЕМИИ: ТОП-5 ПИЛОТОВ** 🏆\n\n"
            for i, (p_name, p_xp) in enumerate(top_pilots, 1):
                radar_msg += f"{i}. {p_name} — {p_xp} 💫 ({get_rank_name(p_xp)})\n"
            
            bot.reply_to(message, radar_msg, parse_mode="Markdown")
            return

        # --- МАГАЗИН КАРТИНОК ---
        if any(word in clean_lower for word in ['нарисуй', 'сгенерируй', 'картинк', 'архив']):
            user_data = get_user_data(user_id)
            if user_data['spendable_dust'] < 5:
                bot.reply_to(message, f"🐾 Гав! Доступ в Архив стоит 5 пыли, а в твоем кошельке сейчас {user_data['spendable_dust']}. Выполни еще пару миссий! Прием.")
                return
            
            bot.send_chat_action(message.chat.id, 'upload_photo')
            bot.reply_to(message, "⏳ Сканирую архивы... Подготовка к генерации!")
            
            censor_prompt = ("Ты цензор Академии. Проверь запрос на генерацию картинки. "
                             "Если там насилие, смерть, секс, политика или монстры - верни ровно одно слово: CENSORED. "
                             "Если запрос безопасен, переведи его на английский язык, добавь 'masterpiece, highly detailed, kid-friendly' и верни ТОЛЬКО этот английский текст.")
            try:
                censor_resp = client.models.generate_content(
                    model='gemini-2.0-flash',
                    contents=clean_text,
                    config=types.GenerateContentConfig(system_instruction=censor_prompt)
                )
                english_prompt = censor_resp.text.strip()
            except Exception as e:
                bot.reply_to(message, "📡 Помехи на линии связи с Архивом. Попробуй позже!")
                return
            
            if "CENSORED" in english_prompt.upper():
                bot.reply_to(message, "🚨 Запрос заблокирован! Устав Академии запрещает такие изображения. Пыль сохранена.")
                return
            
            if spend_dust(user_id, 5):
                safe_url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(english_prompt)}?width=1024&height=1024&nologo=true&seed={int(time.time())}"
                try:
                    bot.send_photo(message.chat.id, safe_url, caption="🎨 Секретный архив открыт!\n💳 Успешно списано 5 звездной пыли.")
                except Exception as e:
                    bot.reply_to(message, f"📡 Ошибка печати. Попробуй еще раз! (Ссылка: {safe_url})")
            else:
                bot.reply_to(message, "📡 Сбой транзакции. Пыль не списана.")
            return

        # --- ОБЫЧНОЕ ОБЩЕНИЕ МАРТИ ---
        old_xp = get_user_stats(user_id)
        old_rank = get_rank_name(old_xp)
        user_data = get_user_data(user_id)
        wallet_balance = user_data['spendable_dust']
        
        full_response = get_marty_response(user_id, user_name, clean_text, old_rank, wallet_balance)
        
        if not full_response:
            time.sleep(5)
            full_response = get_marty_response(user_id, user_name, clean_text, old_rank, wallet_balance)

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
    print("🚀 Марти: Система 'Магазин Картинок' запущена.")
    while True:
        try:
            bot.remove_webhook()
            bot.infinity_polling(skip_pending=True)
        except Exception:
            time.sleep(5)

if __name__ == "__main__":
    Thread(target=run_flask, daemon=True).start()
    start_marty_autonomous()
