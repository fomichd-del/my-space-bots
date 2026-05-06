import os
import telebot
from google import genai
from google.genai import types

# --- КОНФИГУРАЦИЯ ЛОГОВ ---
TOKEN = os.getenv('MARTY_BOT_TOKEN')
bot_log = telebot.TeleBot(TOKEN)
LOG_CHAT_ID = "-1003756164148"

def send_log(error_text):
    """Отправляет отчет в Marty Logs"""
    try:
        bot_log.send_message(LOG_CHAT_ID, f"👁 **СБОЙ СИСТЕМЫ ЗРЕНИЯ:**\n`{error_text}`", parse_mode="Markdown")
    except: pass
# --------------------------

# 🟢 ОБНОВЛЕННЫЙ КАСКАД ДЛЯ ЗРЕНИЯ (НА ОСНОВЕ ТВОЕГО СКАНЕРА)
VISION_MODELS = [
    'gemini-3.1-flash-lite-preview', 
    'gemini-2.5-flash',
    'gemini-2.0-flash',
    'gemini-flash-latest'
]

def analyze_image(image_data, user_context="", keys=[]):
    """Анализ фото с ротацией API-ключей и моделей."""
    prompt = (
        f"ДАННЫЕ ПИЛОТА: {user_context}\n"
        "Ты — ученый пес Марти, мудрый наставник. Просканируй фото. "
        "Оценивай порядок и труд, но будь дружелюбен. "
        "Если всё отлично — напиши: 'выдаю звездную пыль'. "
        "Если на фото СОБАКА или ЗУБНАЯ ЩЕТКА — напиши 'ДЖЕКПОТ'. "
        "Пиши структурировано: каждая мысль с новой строки, используй эмодзи. "
        "Цензура: 18+, насилие запрещены. В конце: Прием!"
    )
    
    active_keys = [k for k in (keys if keys else [os.getenv('GEMINI_API_KEY')]) if k]
    if not active_keys:
        send_log("СИСТЕМА ЗРЕНИЯ: Ключи API не найдены!")
        return "📡 Ошибка: Отсутствуют ключи доступа."

    for i, api_key in enumerate(active_keys):
        try:
            client_gen = genai.Client(api_key=api_key)
            for model_name in VISION_MODELS:
                try:
                    response = client_gen.models.generate_content(
                        model=model_name,
                        contents=[
                            types.Content(
                                role="user",
                                parts=[
                                    types.Part.from_bytes(data=image_data, mime_type='image/jpeg'),
                                    types.Part.from_text(text=prompt)
                                ]
                            )
                        ]
                    )
                    if response.text: return response.text
                except Exception as e:
                    if "429" not in str(e):
                        send_log(f"ЗРЕНИЕ (Ключ {i+1}, {model_name}): {e}")
                    continue
        except: continue
            
    return "📡 Все линзы сканера перегружены. Попробуй через минуту, Пилот! Прием."
