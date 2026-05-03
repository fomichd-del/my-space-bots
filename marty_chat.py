import os
import time
from google import genai
from google.genai import types
from database import get_personal_log, update_personal_log 

# --- НАСТРОЙКИ ИИ ---
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
client = genai.Client(api_key=GEMINI_API_KEY)
MODEL_NAME = 'gemini-1.5-flash'

SYSTEM_PROMPT = (
    "Ты — Марти, ученый пес (той-пудель) и бортовой компьютер. "
    "Твоя миссия — помогать юному Командору в изучении Вселенной. "
    "Пиши кратко (3-4 абзаца), научно и понятно 8-летнему ребенку. "
    "Используй обращения 'Командор', 'Прием'. В конце задавай вопрос."
)

# --- МОДУЛЬ ЗРЕНИЯ ---
def analyze_vision(image_data):
    try:
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
        return f"🐾 Ой! Линзы запотели. Попробуй позже."

# --- ЛОГИКА ОБРАБОТКИ ТЕКСТА ---
def handle_text_logic(bot, message):
    """
    Основная логика чата. Использует экземпляр бота, переданный из main.py
    """
    user_id = message.from_user.id
    bot.send_chat_action(message.chat.id, 'typing')
    
    try:
        # 1. Получаем память
        user_memory = get_personal_log(user_id)
        
        # 2. Генерируем ответ
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=f"ДАННЫЕ О КОМАНДОРЕ: {user_memory}\n\nВОПРОС: {message.text}",
            config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT)
        )
        
        # 3. Отвечаем пользователю
        bot.reply_to(message, response.text, parse_mode='Markdown')
        
        # 4. Фоновое обновление базы знаний
        mem_prompt = f"Выдели факты о ребенке из: '{message.text}'. Если нет — ответь 'НЕТ'."
        mem_resp = client.models.generate_content(model=MODEL_NAME, contents=mem_prompt)
        if "НЕТ" not in mem_resp.text.upper():
            update_personal_log(user_id, mem_resp.text.strip())

    except Exception as e:
        if "429" in str(e):
            bot.reply_to(message, "⏳ Командор, превышена частота запросов. Подождите 30 секунд.")
        else:
            bot.reply_to(message, "📡 Марти на связи, но помехи сильные. Попробуй еще раз через минуту!")
            print(f"Ошибка ИИ: {e}")

# Функцию run_chat_bot и создание chat_bot удаляем, 
# так как бот теперь один и он в main.py
