import os
import telebot
import google.generativeai as genai
import time
from database import get_personal_log, update_personal_log 

# --- НАСТРОЙКИ СИСТЕМЫ ---
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
MARTY_BOT_TOKEN = os.getenv('MARTY_BOT_TOKEN')
genai.configure(api_key=GEMINI_API_KEY)

# Для бесплатного уровня 'gemini-1.5-flash' — самый оптимальный вариант.
# Она поддерживает и текст, и фото.
MODEL_NAME = 'gemini-1.5-flash'

SYSTEM_PROMPT = (
    "Ты — Марти, ученый пес (той-пудель) и бортовой компьютер. "
    "Твоя миссия — помогать юному Командору в изучении Вселенной. "
    "Твои ответы всегда захватывающие, научно достоверные и понятны 8-летнему ребенку. "
    "ПРАВИЛА: 1. Любой школьный предмет объясняй через космос. "
    "2. Уборка и помощь родителям — это протоколы чистоты и поддержка офицеров миссии. "
    "3. Пиши кратко (3-4 абзаца). 4. Используй обращения 'Командор', 'Прием'. "
    "В конце всегда задавай вопрос экипажу."
)

# Инициализация модели с автоматической проверкой доступности
try:
    model = genai.GenerativeModel(model_name=MODEL_NAME, system_instruction=SYSTEM_PROMPT)
    print(f"📡 Марти подключен к модели {MODEL_NAME}")
except Exception as e:
    print(f"❌ Ошибка инициализации: {e}. Проверьте версию google-generativeai в requirements.txt")

chat_bot = telebot.TeleBot(MARTY_BOT_TOKEN, threaded=False) 

# --- МОДУЛЬ ЗРЕНИЯ ---
def analyze_vision(image_data):
    """Марти сканирует изображения через бесплатные лимиты"""
    prompt = (
        "Марти, посмотри на это фото. Что ты видишь? "
        "Опиши это для юного Командора в контексте космоса или науки. "
        "Если это рисунок — похвали. В конце добавь один космический факт."
    )
    try:
        contents = [prompt, {"mime_type": "image/jpeg", "data": image_data}]
        response = model.generate_content(contents)
        return response.text if response.text else "🐾 Датчики молчат. Попробуй еще раз!"
    except Exception as e:
        if "429" in str(e):
            return "⏳ Командор, мои оптические сенсоры перегрелись. Подожди 10 секунд!"
        return "🐾 Ой! Линзы запотели. Попробуй позже."

# --- ОБРАБОТКА ФОТО ---
@chat_bot.message_handler(content_types=['photo'])
def handle_photo(message):
    chat_id = message.chat.id
    chat_bot.send_chat_action(chat_id, 'upload_photo')
    try:
        file_info = chat_bot.get_file(message.photo[-1].file_id)
        downloaded_file = chat_bot.download_file(file_info.file_path)
        vision_result = analyze_vision(downloaded_file)
        chat_bot.reply_to(message, vision_result)
    except Exception:
        chat_bot.reply_to(message, "📡 Помехи при передаче изображения.")

# --- ОБРАБОТКА ТЕКСТА ---
@chat_bot.message_handler(func=lambda message: True, content_types=['text'])
def handle_text(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    text = message.text

    chat_bot.send_chat_action(chat_id, 'typing')
    
    try:
        # 1. Личная память пользователя
        user_memory = get_personal_log(user_id)
        full_context = f"ДАННЫЕ О КОМАНДОРЕ: {user_memory}\n\nВОПРОС: {text}"
        
        # 2. Попытка получить ответ
        response = model.generate_content(full_context)
        chat_bot.reply_to(message, response.text, parse_mode='Markdown')
        
        # 3. Фоновое запоминание (анализ фактов)
        # На бесплатном уровне делаем это аккуратно, чтобы не тратить лимиты
        memory_task = f"Выдели новые факты о пользователе из фразы: '{text}'. Если нет — ответь 'НЕТ'."
        mem_resp = model.generate_content(memory_task)
        if "НЕТ" not in mem_resp.text.upper():
            update_personal_log(user_id, mem_resp.text.strip())

    except Exception as e:
        if "429" in str(e):
            chat_bot.reply_to(message, "⏳ Слишком много запросов! Дай мне 10 секунд на перезагрузку.")
            time.sleep(10)
        else:
            chat_bot.reply_to(message, "📡 Командор, связь прервана помехами. Повтори запрос позже!")

# --- ЗАПУСК ---
def run_chat_bot():
    print(f"🚀 Марти запущен в бесплатном режиме. Прием!")
    chat_bot.remove_webhook()
    chat_bot.infinity_polling(timeout=20, long_polling_timeout=10)

if __name__ == '__main__':
    run_chat_bot()
