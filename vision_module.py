import os
from google import genai
from google.genai import types

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
client = genai.Client(api_key=GEMINI_API_KEY)

# 🟢 Пробуем 2.0-flash для зрения, она самая стабильная для фото сейчас
MODEL_NAME = 'gemini-2.0-flash'

def analyze_image(image_data):
    prompt = (
        "Ты — ученый пес Марти. Просканируй это фото. "
        "Определи, что на нем: космос, поделка, школа или природа. "
        "Похвали Командора (8 лет) и напиши отчет в 1-2 абзаца без звездочек. Прием!"
    )
    
    try:
        # 🟢 Улучшенный формат отправки контента
        response = client.models.generate_content(
            model=MODEL_NAME,
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
        return response.text if response.text else "🐾 Вижу что-то интересное, но не могу разобрать. Давай еще раз!"
    except Exception as e:
        # Печатаем РЕАЛЬНУЮ ошибку в логи Render, чтобы ты мог её увидеть
        print(f"!!! ОШИБКА ЗРЕНИЯ МАРТИ: {e}")
        return "📡 Командор, помехи на линии связи с телескопом. Попробуй через минуту, когда сигнал станет чище. Прием."
