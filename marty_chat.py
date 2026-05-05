import os
import telebot
import time
import re
from datetime import datetime, timedelta
from threading import Thread
from flask import Flask
from google import genai
from google.genai import types

# --- ИМПОРТЫ ---
from database import get_personal_log, update_personal_log, add_xp, get_user_stats, get_rank_name
from vision_module import analyze_image
from image_gen import generate_passport
# ---------------------------

# --- КОНФИГУРАЦИЯ ---
TOKEN = os.getenv('MARTY_BOT_TOKEN') 
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
CHANNEL_USERNAME = "@vladislav_space" # Название твоего канала

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
    
    if 0 <= hour < 5:
        return f"{time_str} (Глубокая ночь. Удивляйся, почему пилот не спит)"
    elif 5 <= hour < 11:
        return f"{time_str} (Утро. Время подготовки к экспедиции и завтрака)"
    elif 11 <= hour < 17:
        return f"{time_str} (День. Время для науки и школы)"
    elif 17 <= hour < 23:
        return f"{time_str} (Вечер. Время отдыха и порядка)"
    else:
        return f"{time_str} (Ночь. Пора спать)"

def is_subscribed(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        if member.status in ['member', 'administrator', 'creator']:
            return True
        return False
    except Exception as e:
        print(f"⚠️ Ошибка проверки подписки: {e}")
        return True 

# 🟢 ЯДРО ЛИЧНОСТИ (РАСШИРЕНО: ПОДРОБНАЯ ИНСТРУКЦИЯ И ТУТОРИАЛ)
SYSTEM_PROMPT = (
    "Ты — Марти, ученый пес (той-пудель) и бортовой ИИ-наставник для пилотов. "
    "1. ЛИЧНОСТЬ: Ты мудрый, добрый, иногда говоришь 'Гав!'. "
    "Обращайся по имени [NAME]. Текущее звание пилота: [RANK]. Время суток: [TIME]. [GREETING_RULE] "
    "2. АТТЕСТАЦИЯ И СЛОЖНОСТЬ: Начисляй 'звездную пыль' за успехи. "
    "ЧЕМ ВЫШЕ ЗВАНИЕ [RANK], ТЕМ СТРОЖЕ ОЦЕНИВАЙ! Кадету дай пыль за заправленную постель, а старшим званиям — только за отличные оценки или генеральную уборку. "
    "ВАЖНО: НИКОГДА не давай пыль просто за слова. Требуй ФОТО-доказательство: 'Прикрепи фото для сканирования!'. "
    "3. РЕЖИМ 'ИНСТРУКЦИЯ' (ОЧЕНЬ ВАЖНО): Если пилот пишет 'инструкция', 'правила', 'что делать', 'помощь' или 'что такое звездная пыль', ты ОБЯЗАН выдать подробный ответ по пунктам. "
    "Текст инструкции должен быть таким (перескажи своими словами, но сохрани суть): "
    "'Привет, пилот! Я Марти, твой бортовой помощник. Вот правила нашей Академии: "
    "✨ Что такое звездная пыль? Это топливо твоего прогресса! Собирай ее, чтобы получать новые звания (от Кадета до Академика Космоса) и настоящие космические паспорта. "
    "📸 Как ее получить? Присылай мне фото-доказательства своих успехов: убранная комната, сделанные уроки, красивые поделки или помощь родителям. Я просканирую фото и выдам награду! "
    "🎁 Секреты (скоро): В выходные бывает метеоритный дождь (х2 пыли, но не больше 4 за раз), а если присылать фото каждый день без пропусков, будут бонусы! Если найдешь секретные артефакты на фото — получишь джекпот (один раз!). А еще за пыль мы скоро сможем открывать секретные архивы (генерировать картинки) и смотреть таблицу лидеров канала!' "
    "4. ТЕМЫ: Космос, школа, порядок в комнате. "
    "5. ЦЕНЗУРА (СТРОГО): Запрещено обсуждать секс, смерть, насилие, убийства, политику, страшные темы. Отвечай: 'Пилот, эти частоты заблокированы Академией!' "
    "6. ФОРМАТ: Для обычных ответов — 3-4 предложения. Для ИНСТРУКЦИИ — можно длинно и подробно, по пунктам. В конце 'Прием' и вопрос. Затем '###MEM###' и новые факты или 'НЕТ'."
)

app = Flask(__name__)
@app.route('/')
def home(): return "Marty Academy Core: Online"

def run_flask():
    try:
        port = int(os.environ.get("PORT", 10000))
        app.run(host='0.0.0.0', port=port)
    except: pass

def get_marty_response(user_id, user_name, clean_text, user_rank):
    user_memory = get_personal_log(user_id)
    time_info = get_time_context()
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    if daily_greetings.get(user_id) == current_date:
        greeting_rule = "ВНИМАНИЕ: Вы уже общались сегодня. СРАЗУ отвечай на вопрос, НЕ ИСПОЛЬЗУЙ приветствия."
    else:
        greeting_rule = "Поприветствуй пилота, учитывая время суток."
        daily_greetings[user_id] = current_date
    
    # Вшиваем звание в промпт
    current_prompt = SYSTEM_PROMPT.replace("[NAME]", user_name).replace("[TIME]", time_info).replace("[GREETING_RULE]", greeting_rule).replace("[RANK]", user_rank)
    
    for model_variant in MODEL_CASCADE:
        try:
            print(f"📡 Запрос к: {model_variant}")
            response = client.models.generate_content(
                model=model_variant,
                contents=f"ДАННЫЕ: {user_memory}\nВОПРОС: {clean_text}",
                config=types.GenerateContentConfig(system_instruction=current_prompt)
            )
            if response.text:
                return response.text
        except Exception as e:
            if "429" in str(e): continue
            print(f"❌ Ошибка {model_variant}: {e}")
    return None

# --- ОБРАБОТЧИКИ ---

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    user_id, user_name = message.from_user.id, message.from_user.first_name
    
    if not is_subscribed(user_id):
        bot.reply_to(message, f"🐾 Гав! Извини, Пилот, но Космическая Академия — закрытый клуб! Сначала подпишись на наш канал {CHANNEL_USERNAME}, а потом возвращайся за звездной пылью!")
        return
    
    bot.send_chat_action(message.chat.id, 'typing')
    try:
        user_memory = get_personal_log(user_id)
        time_info = get_time_context()
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        old_xp = get_user_stats(user_id)
        old_rank = get_rank_name(old_xp)

        # Модуль зрения теперь знает звание и судит соответственно!
        anti_cheat_context = (f"Имя: {user_name}. Текущее звание: {old_rank}. Память: {user_memory}. Время: {time_info}. "
                              f"Задание: Строго оцени фото с учетом звания ({old_rank}). Младшим званиям прощай мелкие недочеты, "
                              "а старшим званиям выдавай 'звездную пыль' только за идеальный порядок или сложные решенные уроки! "
                              "Если все отлично - похвали и дай 'звездную пыль'. Если плохо - укажи на ошибки.")
        
        analysis_result = analyze_image(downloaded_file, user_context=anti_cheat_context)
        
        if "звездн" in analysis_result.lower() and "пыль" in analysis_result.lower():
            add_xp(user_id, 1, user_name)
            
        bot.reply_to(message, analysis_result)
        update_personal_log(user_id, f"Пилот показал фото в {time_info[:5]}")
        
        new_xp = get_user_stats(user_id)
        new_rank = get_rank_name(new_xp)
        
        if old_rank != new_rank:
            bot.send_message(message.chat.id, f"🎉 Внимание! Пилот {user_name} получает новое звание: {new_rank}!\nПечатаю официальное удостоверение...")
            passport_bytes = generate_passport(user_name, new_rank)
            if passport_bytes:
                bot.send_photo(message.chat.id, passport_bytes)
                
    except Exception as e:
        print(f"Ошибка фото: {e}")
        bot.reply_to(message, "📡 Командор, помехи в видеоканале. Прием.")

@bot.message_handler(func=lambda m: True)
def handle_text(message):
    if not message.text: return
    user_id, user_name = message.from_user.id, message.from_user.first_name
    
    if not is_subscribed(user_id):
        bot.reply_to(message, f"🐾 Гав! Извини, Пилот, но Космическая Академия — закрытый клуб! Сначала подпишись на наш канал {CHANNEL_USERNAME}, а потом возвращайся за звездной пылью!")
        return

    text_lower = message.text.lower()
    is_private = message.chat.type == 'private'
    is_called = text_lower.startswith('марти') or f"@{BOT_USERNAME}" in text_lower

    if is_private or is_called:
        bot.send_chat_action(message.chat.id, 'typing')
        clean_text = re.sub(r'^марти[,.\s]*', '', message.text, flags=re.IGNORECASE).strip()
        
        # Получаем звание ДО запроса к Марти
        old_xp = get_user_stats(user_id)
        old_rank = get_rank_name(old_xp)
        
        # Передаем звание в функцию
        full_response = get_marty_response(user_id, user_name, clean_text, old_rank)
        
        if not full_response:
            bot.reply_to(message, "📡 Ищу информацию, подожди чуток... Прием.")
            time.sleep(15)
            full_response = get_marty_response(user_id, user_name, clean_text, old_rank)

        if full_response:
            if "звездн" in full_response.lower() and "пыль" in full_response.lower():
                add_xp(user_id, 1, user_name)

            new_xp = get_user_stats(user_id)
            new_rank = get_rank_name(new_xp)

            if "###MEM###" in full_response:
                user_text, mem_data = full_response.split("###MEM###")
                bot.reply_to(message, user_text.strip())
                if "НЕТ" not in mem_data.upper() and len(mem_data.strip()) > 2:
                    update_personal_log(user_id, mem_data.strip())
            else:
                bot.reply_to(message, full_response.strip())

            if old_rank != new_rank:
                bot.send_message(message.chat.id, f"🎉 Внимание! Пилот {user_name} получает новое звание: {new_rank}!\nПечатаю официальное удостоверение...")
                passport_bytes = generate_passport(user_name, new_rank)
                if passport_bytes:
                    bot.send_photo(message.chat.id, passport_bytes)

        else:
            bot.reply_to(message, "⏳ Командор, тишина в эфире. Прием.")

def start_marty_autonomous():
    print("🚀 Марти: Система 'Стабильная Орбита 3.0' запущена.")
    while True:
        try:
            bot.remove_webhook()
            bot.infinity_polling(skip_pending=True)
        except Exception:
            time.sleep(5)

if __name__ == "__main__":
    Thread(target=run_flask, daemon=True).start()
    start_marty_autonomous()
