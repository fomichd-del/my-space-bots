import os
import telebot
import time
from google import genai
from google.genai import types
from database import get_personal_log, update_personal_log 

# --- НАСТРОЙКИ СИСТЕМЫ ---
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
MARTY_BOT_TOKEN = os.getenv('MARTY_BOT_TOKEN')

# Используем новый клиент 2026 года
client = genai.Client(api_key=GEMINI_API_KEY)
MODEL_NAME = 'gemini-1.5-flash'

SYSTEM_PROMPT = (
    "Ты — Марти, ученый пес (той-пудель) и бортовой компьютер. "
    "Твоя миссия — помогать юному Командору в изучении Вселенной. "
    "Пиши кратко (3-4 абзаца), научно и понятно 8-летнему ребенку. "
    "Используй обращения 'Командор', 'Прием'. В конце задавай вопрос."
)

chat_bot = telebot.TeleBot(MARTY_BOT_TOKEN, threaded=False) 

# --- МОДУЛЬ ЗРЕНИЯ ---
def analyze_vision(image_data):
    try:
        # В новой библиотеке работа с изображениями стала проще
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=[
                types.Part.from_bytes(data=image_data, mime_type='image/jpeg'),
                "Марти, сканируй фото! Что видишь? Опиши для Командора в стиле космоса."
            ],
            config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT)
        )
        return response.text if response.text else "🐾 Датчики не видят цель."
    except Exception as e:
        return f"🐾 Ой! Линзы запотели. Попробуй позже. (Код: {str(e)[:20]})"

# --- ОБРАБОТКА ФОТО ---
@chat_bot.message_handler(content_types=['photo'])
def handle_photo(message):
    chat_bot.send_chat_action(message.chat.id, 'upload_photo')
    try:
        file_info = chat_bot.get_file(message.photo[-1].file_id)
        downloaded_file = chat_bot.download_file(file_info.file_path)
        result = analyze_vision(downloaded_file)
        chat_bot.reply_to(message, result)
    except Exception:
        chat_bot.reply_to(message, "📡 Ошибка сканера.")

# --- ОБРАБОТКА ТЕКСТА ---
@chat_bot.message_handler(func=lambda message: True, content_types=['text'])
def handle_text(message):
    user_id = message.from_user.id
    chat_bot.send_chat_action(message.chat.id, 'typing')
    
    try:
        user_memory = get_personal_log(user_id)
        
        # Новый метод генерации ответа
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=f"ДАННЫЕ О КОМАНДОРЕ: {user_memory}\n\nВОПРОС: {message.text}",
            config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT)
        )
        
        chat_bot.reply_to(message, response.text, parse_mode='Markdown')
        
        # Фоновое запоминание (только если ответ прошел)
        mem_prompt = f"Выдели факты о ребенке из: '{message.text}'. Если нет — ответь 'НЕТ'."
        mem_resp = client.models.generate_content(model=MODEL_NAME, contents=mem_prompt)
        if "НЕТ" not in mem_resp.text.upper():
            update_personal_log(user_id, mem_resp.text.strip())

    except Exception as e:
        if "429" in str(e):
            chat_bot.reply_to(message, "⏳ Командор, превышена частота запросов. Подождите 30 секунд.")
        else:
            chat_bot.reply_to(message, "📡 Марти на связи, но помехи сильные. Попробуй еще раз через минуту!")
            print(f"Ошибка: {e}")

def run_chat_bot():
    print(f"🚀 Марти обновлен до стандарта google-genai. Летим!")
    chat_bot.remove_webhook()
    chat_bot.infinity_polling(timeout=20)

if __name__ == '__main__':
    run_chat_bot()
