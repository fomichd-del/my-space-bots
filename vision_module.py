import os
import telebot
from google import genai
from google.genai import types

TOKEN = os.getenv('MARTY_BOT_TOKEN')
bot_log = telebot.TeleBot(TOKEN)
LOG_CHAT_ID = "-1003756164148"

def send_log(error_text):
    try:
        bot_log.send_message(LOG_CHAT_ID, f"👁 **СБОЙ СИСТЕМЫ ЗРЕНИЯ:**\n`{error_text}`", parse_mode="Markdown")
    except: pass

# Используем только те частоты, что подтвердил сканер
VISION_MODELS = [
    'gemini-2.0-flash', 
    'gemini-1.5-flash',
    'gemini-3.1-flash-lite-preview'
]

def analyze_image(image_data, user_context="", keys=[]):
    prompt = (
        f"ДАННЫЕ ПИЛОТА: {user_context}\n"
        "Ты — ученый пес Марти. Просканируй фото.\n"
        "Пиши структурировано: каждое предложение с новой строки.\n"
        "Используй эмодзи 🐾, 🚀, 🔬.\n"
        "Если на фото идеальный порядок — напиши: 'выдаю звездную пыль'.\n"
        "Если есть СОБАКА или ЗУБНАЯ ЩЕТКА — напиши 'ДЖЕКПОТ'.\n"
        "Запрет 18+, алкоголь. В конце: Прием!"
    )
    
    active_keys = [k for k in (keys if keys else [os.getenv('GEMINI_API_KEY')]) if k]
    
    for i, api_key in enumerate(active_keys):
        try:
            client_gen = genai.Client(api_key=api_key)
            for model_name in VISION_MODELS:
                try:
                    response = client_gen.models.generate_content(
                        model=model_name,
                        contents=[
                            types.Content(role="user", parts=[
                                types.Part.from_bytes(data=image_data, mime_type='image/jpeg'),
                                types.Part.from_text(text=prompt)
                            ])
                        ]
                    )
                    if response.text: return response.text
                except Exception as e:
                    if "429" not in str(e): send_log(f"Зрение ошибка: {e}")
                    continue
        except: continue
    return "📡 Линзы перегружены. Прием."
