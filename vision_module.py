import os
from google import genai
from google.genai import types

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
client = genai.Client(api_key=GEMINI_API_KEY)

# 🟢 РАСШИРЕННЫЙ КАСКАД ДЛЯ ЗРЕНИЯ
VISION_MODELS = [
    'gemini-2.0-flash', 
    'gemini-2.0-flash-lite-001', 
    'gemini-flash-latest',
    'gemini-1.5-flash',
    'gemini-1.5-flash-8b' # Самая легкая и быстрая модель для фото
]


def analyze_image(image_data, user_context=""):
    """
    Анализ изображений с учетом личности пилота и его истории.
    """
    prompt = (
        f"ДАННЫЕ: {user_context}\n"
        "Ты — ученый пес Марти, бортовой ИИ и наставник для всех участников канала. Просканируй это фото. "
        "1. ТВОРЧЕСТВО: Если это поделка или рисунок — похвали пилота за талант и труд. "
        "2. ШКОЛА: Если это задача — помоги найти решение или подбодри. "
        "3. КОСМОС: Если это небо — расскажи удивительный научный факт. "
        "4. ВОСПИТАНИЕ: Напомни, что путь к звездам начинается с порядка в своем отсеке (комнате) и помощи близким. "
        "Пиши кратко, простым языком, БЕЗ звездочек. В конце добавь: Прием!"
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
        except Exception:
            continue
            
    return "📡 Командор, все линзы запотели из-за космической пыли. Попробуй еще раз! Прием."
