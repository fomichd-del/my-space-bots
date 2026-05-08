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
    'gemini-2.5-flash',
    'gemini-1.5-flash',
    'gemini-3.1-flash-lite-preview'
]

def analyze_image(image_data, user_context="", keys=[]):
    prompt = (
        f"ДАННЫЕ ПИЛОТА: {user_context}\n"
        "Ты — Марти, бортовой наставник. Просканируй это фото.\n\n"
        "ПРОТОКОЛ РАПОРТА (КРИТИЧЕСКИ ВАЖНО):\n"
        "1. Формат: Отвечай как человечек. Максимум 2-3 коротких предложения. Никакой воды и долгих описаний каждого предмета.\n"
        "2. Суть: Сразу выдавай вердикт. Если порядок идеален или задание выполнено — хвали и ОБЯЗАТЕЛЬНО пиши фразу: 'выдаю звездную пыль'.\n"
        "3. Критика: Если на фото бардак или ошибки — коротко укажи главную проблему (1 предложение) и не давай пыль.\n"
        "4. Секретный артефакт: Если видишь СОБАКУ или ЗУБНАЮ ЩЕТКУ — пиши слово 'ДЖЕКПОТ'.\n"
        "5. Оформление: Пиши структурировано (каждая мысль с новой строки), используй 1-2 эмодзи (🐾, 🚀, 🔬).\n\n"
        "🛑 Запрет 18+, алкоголь, табак, насилие.\n"
        "В конце всегда пиши: 'Прием!'"
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
