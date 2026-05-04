import os
from google import genai
from google.genai import types

# Инициализация клиента
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
client = genai.Client(api_key=GEMINI_API_KEY)

# 🟢 ОБНОВЛЕННАЯ МОДЕЛЬ ДЛЯ ИДЕАЛЬНОГО РАСПОЗНАВАНИЯ ФОТО
MODEL_NAME = 'gemini-2.5-flash'

def analyze_image(image_data):
    """
    Модуль 'Глаза Марти': анализирует фото неба и ищет созвездия.
    """
    prompt = (
        "Ты — бортовой ИИ 'Марти'. Просканируй это изображение неба. "
        "Найди на нем созвездия или интересные космические объекты. "
        "Дай краткий отчет для Командора (8-летнего ребенка) в научном, но захватывающем стиле. "
        "Не используй форматирование текста (никаких звездочек и подчеркиваний). "
        "Если на фото ничего не видно — вежливо сообщи об этом."
    )
    
    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=[
                types.Part.from_bytes(data=image_data, mime_type='image/jpeg'),
                prompt
            ]
        )
        return response.text if response.text else "🐾 Датчики зафиксировали объект, но не смогли его распознать."
    except Exception as e:
        print(f"Ошибка Vision: {e}")
        return "📡 Ой! Мои линзы запотели из-за помех в системе."
