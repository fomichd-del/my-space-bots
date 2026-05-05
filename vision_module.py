import os
import telebot
from google import genai
from google.genai import types

# --- КОНФИГУРАЦИЯ ЛОГОВ ---
TOKEN = os.getenv('MARTY_BOT_TOKEN')
bot_log = telebot.TeleBot(TOKEN)
LOG_CHAT_ID = "-1003756164148"

def send_log(error_text):
    try:
        bot_log.send_message(LOG_CHAT_ID, f"👁 **СБОЙ ЗРЕНИЯ:**\n`{error_text}`", parse_mode="Markdown")
    except: pass
# --------------------------

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
client = genai.Client(api_key=GEMINI_API_KEY)

# 🟢 КАСКАД МОДЕЛЕЙ ДЛЯ ЗРЕНИЯ
VISION_MODELS = [
    'gemini-2.0-flash', 
    'gemini-2.0-flash-lite-001', 
    'gemini-flash-latest',
    'gemini-1.5-flash',
    'gemini-1.5-flash-8b'
]

def analyze_image(image_data, user_context=""):
    """
    Анализ изображений с учетом хардкорного режима Академии Орион.
    """
    prompt = (
        f"ДАННЫЕ ПИЛОТА: {user_context}\n"
        "Ты — ученый пес Марти, бортовой ИИ и строгий наставник Академии Орион. Просканируй это фото. "
        "1. АТТЕСТАЦИЯ (ХАРДКОР): Оценивай фото ПРЕДВЗЯТО и СТРОГО. "
        "Если в данных указано звание выше Кадета (Навигатор, Бортинженер и т.д.), не давай пыль за простые вещи. "
        "Только за ИДЕАЛЬНЫЙ порядок, сложные решенные задачи или по-настоящему крутое творчество. "
        "Если работа выполнена на 'отлично' — похвали и напиши: 'выдаю звездную пыль'. "
        "Если есть хоть малейший беспорядок или ошибка — пыль НЕ ДАВАЙ, а строго и четко укажи, что нужно исправить. "
        "2. СЕКРЕТНЫЙ АРТЕФАКТ (ДЖЕКПОТ): Если на фото есть СОБАКА (мой сородич!) или ЗУБНАЯ ЩЕТКА — обязательно напиши слово 'ДЖЕКПОТ'. "
        "3. ШКОЛА: Помогай с решением задач, если это необходимо. "
        "4. КОСМОС: Если видишь небо, телескоп или звезды — добавь один научный факт. "
        "5. ЦЕНЗУРА (СТРОГО): Никакого насилия, страшных тем, политики или 18+. "
        "Пиши кратко, без лишних знаков, простым языком. В конце: Прием!"
    )
    
    for model_name in VISION_MODELS:
        try:
            response = client.models.generate_content(
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
            send_log(f"Ошибка в модели {model_name}: {e}")
            continue
            
    return "📡 Линзы сканера запотели. Попробуй еще раз, Пилот! Прием."
