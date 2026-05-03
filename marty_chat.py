import os
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

# --- ЛОГИКА ОБРАБОТКИ ТЕКСТА ---
def handle_text_logic(bot, message):
    """Центральная логика общения, вызываемая из main.py"""
    user_id = message.from_user.id
    bot.send_chat_action(message.chat.id, 'typing')
    
    try:
        user_memory = get_personal_log(user_id)
        
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=f"ДАННЫЕ О КОМАНДОРЕ: {user_memory}\n\nВОПРОС: {message.text}",
            config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT)
        )
        
        bot.reply_to(message, response.text, parse_mode='Markdown')
        
        # Обновление памяти в фоне
        mem_prompt = f"Выдели факты о ребенке из: '{message.text}'. Если нет — ответь 'НЕТ'."
        mem_resp = client.models.generate_content(model=MODEL_NAME, contents=mem_prompt)
        if "НЕТ" not in mem_resp.text.upper():
            update_personal_log(user_id, mem_resp.text.strip())

    except Exception as e:
        if "429" in str(e):
            bot.reply_to(message, "⏳ Командор, датчики перегрелись. Подожди 30 секунд!")
        else:
            bot.reply_to(message, "📡 Связь прервана космическим шумом. Повтори попытку!")
            print(f"Ошибка ИИ: {e}")
