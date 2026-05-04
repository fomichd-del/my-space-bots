import os
from google import genai
from google.genai import types

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
client = genai.Client(api_key=GEMINI_API_KEY)

# 🟢 Каскад для зрения: пробуем лучшую 2.0, если нет — 1.5
VISION_MODELS = ['gemini-2.0-flash', 'gemini-1.5-flash']

def analyze_image(image_data, user_context=""):
    """
    Анализирует фото, учитывая личность пользователя и историю общения.
    """
    prompt = (
        f"ДАННЫЕ О КОМАНДОРЕ: {user_context}\n"
        "Ты — ученый пес Марти, бортовой ИИ и наставник. Просканируй это фото. "
        "1. ТВОРЧЕСТВО: Если это поделка или рисунок — похвали ребенка за труд и усидчивость. "
        "2. ШКОЛА: Если это задача или учебник — помоги разобраться или подбодри. "
        "3. КОСМОС: Если это небо — расскажи захватывающий научный факт. "
        "4. ВОСПИТАНИЕ: Мягко напомни, что настоящий герой всегда помогает родителям и держит вещи в порядке. "
        "Пиши кратко, простым языком, БЕЗ звездочек и форматирования. В конце: Прием!"
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
            print(f"⚠️ Вижн-каскад: {model_name} временно недоступна.")
            continue
            
    return "📡 Командор, все линзы запотели. Попробуй еще раз через минуту! Прием."
