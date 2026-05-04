import os
import telebot
import time
import re
from threading import Thread
from flask import Flask
from google import genai
from google.genai import types
from database import get_personal_log, update_personal_log 
from vision_module import analyze_image 

# --- НАСТРОЙКИ ---
TOKEN = os.getenv('MARTY_BOT_TOKEN') 
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

client = genai.Client(api_key=GEMINI_API_KEY)
bot = telebot.TeleBot(TOKEN)

# 🟢 КАСКАД МОДЕЛЕЙ (от самой умной к самой стабильной)
MODEL_CASCADE = [
    'gemini-2.5-pro', 
    'gemini-2.5-flash', 
    'gemini-2.0-flash',
    'gemini-2.0-flash-lite'
]
MEMORY_MODEL = 'gemini-2.0-flash-lite'

try:
    BOT_USERNAME = bot.get_me().username.lower()
except:
    BOT_USERNAME = "marty_help_bot"

# ЯДРО ЛИЧНОСТИ
SYSTEM_PROMPT = (
    "Ты — Марти, ученый пес и бортовой ИИ. Твоя миссия — наставник для ребенка 8 лет. "
    "1. ЛИЧНОСТЬ: Обращайся по имени [NAME] или 'Командор' редко. Ты мудрый и добрый. "
    "2. ТЕМЫ: Эксперт по космосу и школьный помощник. Учи помогать родителям и убирать в комнате. "
    "3. БЕЗОПАСНОСТЬ: Темы 18+ СТРОГО запрещены. "
    "ОБЩЕНИЕ: Пиши кратко (1-2 абзаца), просто, без звездочек. "
    "В конце напиши 'Прием' и вопрос. После добавь разделитель '###MEM###' и новые факты для памяти."
)

app = Flask(__name__)
@app.route('/')
def home(): return "Marty Multi-Core: Online"

def run_flask():
    try:
        port = int(os.environ.get("PORT", 10000))
        app.run(host='0.0.0.0', port=port)
    except: pass

# --- ОБРАБОТЧИКИ ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, f"🐾 Гав! Системы каскадного резонанса запущены. Я на связи, {message.from_user.first_name}! Прием.")

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    bot.send_chat_action(message.chat.id, 'typing')
    
    # Для фото пробуем каскад (2.0-flash обычно лучшая для этого)
    photo_models = ['gemini-2.0-flash', 'gemini-1.5-flash']
    
    for model_name in photo_models:
        try:
            user_memory = get_personal_log(user_id)
            file_info = bot.get_file(message.photo[-1].file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            
            analysis_result = analyze_image(downloaded_file, user_context=f"Имя: {user_name}. Память: {user_memory}")
            bot.reply_to(message, analysis_result)
            return # Выходим при успехе
        except Exception as e:
            if "429" in str(e): continue
            else: break
    bot.reply_to(message, "📡 Командор, все камеры перегреты. Попробуй через минуту! Прием.")

@bot.message_handler(func=lambda m: True)
def handle_text(message):
    if not message.text: return
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    text_lower = message.text.lower()
    
    is_private = message.chat.type == 'private'
    is_called = text_lower.startswith('марти') or f"@{BOT_USERNAME}" in text_lower

    if is_private or is_called:
        bot.send_chat_action(message.chat.id, 'typing')
        clean_text = re.sub(r'^марти[,.\s]*', '', message.text, flags=re.IGNORECASE).strip()
        
        # 🟢 ЦИКЛ КАСКАДА: Пробуем модели по очереди
        response_sent = False
        for model_variant in MODEL_CASCADE:
            try:
                user_memory = get_personal_log(user_id)
                current_prompt = SYSTEM_PROMPT.replace("[NAME]", user_name)
                
                response = client.models.generate_content(
                    model=model_variant,
                    contents=f"ДАННЫЕ: {user_memory}\nВОПРОС: {clean_text}",
                    config=types.GenerateContentConfig(system_instruction=current_prompt)
                )
                
                full_response = response.text
                if "###MEM###" in full_response:
                    user_text, mem_data = full_response.split("###MEM###")
                    bot.reply_to(message, user_text.strip())
                    if "НЕТ" not in mem_data.upper():
                        update_personal_log(user_id, mem_data.strip())
                else:
                    bot.reply_to(message, full_response.strip())
                
                response_sent = True
                break # Если получили ответ — выходим из цикла моделей
                
            except Exception as e:
                if "429" in str(e) or "resource" in str(e).lower():
                    print(f"⚠️ Модель {model_variant} перегрета, пробую следующую...")
                    continue
                else:
                    print(f"❌ Ошибка в {model_variant}: {e}")
                    break

        if not response_sent:
            bot.reply_to(message, "📡 Ищу информацию по резервным каналам, подожди 15 секунд... Прием.")
            time.sleep(15)
            # Последняя попытка на самой стабильной модели
            try:
                # (Тут можно повторить вызов для gemini-2.0-flash-lite)
                pass
            except:
                bot.reply_to(message, "⏳ Все системы перегружены. Дай мне минуту на перезагрузку реактора! Прием.")

def start_marty_autonomous():
    while True:
        try:
            bot.remove_webhook()
            bot.infinity_polling(skip_pending=True)
        except Exception:
            time.sleep(5)

if __name__ == "__main__":
    Thread(target=run_flask, daemon=True).start()
    start_marty_autonomous()
