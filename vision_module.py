import os
from google import genai
from google.genai import types

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
client = genai.Client(api_key=GEMINI_API_KEY)

# Каскад для зрения
VISION_MODELS = ['gemini-2.0-flash', 'gemini-1.5-flash']

def analyze_image(image_data, user_context=""):
    prompt = (
        f"ДАННЫЕ О КОМАНДОРЕ: {user_context}\n"
        "Ты — ученый пес Марти. Просканируй это фото. "
        "Похвали за труд, помоги с учебой или расскажи факт о космосе. "
        "Напомни про порядок в комнате и помощь родителям. "
        "Пиши кратко, без звездочек. В конце: Прием!"
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
            return response.text
        except:
            continue
    return "📡 Командор, все линзы запотели. Попробуй еще раз через минуту! Прием."
