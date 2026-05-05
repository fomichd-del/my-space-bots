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

# 🟢 КАСКАД МОДЕЛЕЙ ДЛЯ ЗРЕНИЯ
VISION_MODELS = [
    'gemini-2.0-flash', 
    'gemini-2.0-flash-lite-001', 
    'gemini-flash-latest',
    'gemini-1.5-flash'
]

def analyze_image(image_data, user_context="", keys=[]):
    """
    Анализ фото с ротацией API-ключей и моделей.
    """
    prompt = (
        f"ДАННЫЕ ПИЛОТА: {user_context}\n"
        "Ты — ученый пес Марти, строгий бортовой наставник Академии Орион. Просканируй это фото. "
        "1. АТТЕСТАЦИЯ (ХАРДКОР): Оценивай ПРЕДВЗЯТО. Если в данных указан ранг выше Кадета, "
        "не давай пыль за мелочи. Пыль выдается только за идеальный порядок или реальный труд. "
        "Если всё отлично — напиши: 'выдаю звездную пыль'. Иначе — укажи ошибки. "
        "2. СЕКРЕТНЫЙ АРТЕФАКТ: Если на фото есть СОБАКА или ЗУБНАЯ ЩЕТКА — напиши 'ДЖЕКПОТ'. "
        "3. ЦЕНЗУРА: СТРОГИЙ запрет на 18+, алкоголь, табак, смерть, насилие. "
        "Пиши кратко (3-4 предложения), научно и позитивно. В конце: Прием!"
    )
    
    # Если список ключей пуст, пробуем взять хотя бы основной из окружения
    if not keys:
        keys = [os.getenv('GEMINI_API_KEY')]

    # РОТАЦИЯ: Сначала перебираем Ключи, внутри каждого — Модели
    for i, api_key in enumerate(keys):
        if not api_key: continue
        
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
                if response.text:
                    return response.text
            except Exception as e:
                # Если лимит исчерпан — просто идем к следующему ключу/модели
                if "429" in str(e):
                    continue 
                
                # О других ошибках докладываем в логи
                send_log(f"Ключ №{i+1}, Модель {model_name}: {e}")
                continue
            
    return "📡 Все линзы сканера перегружены. Попробуй через минуту, Пилот! Прием."
