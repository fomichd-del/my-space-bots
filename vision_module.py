import os
from google import genai
from google.genai import types

# Инициализация клиента
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
client = genai.Client(api_key=GEMINI_API_KEY)

# 🟢 Для фото используем самую стабильную модель 2.0
MODEL_NAME = 'gemini-2.0-flash'

def analyze_image(image_data, user_context=""):
    """
    Модуль 'Глаза Марти': теперь учитывает историю общения (user_context) 
    и выступает в роли мудрого наставника.
    """
    
    # 🟢 УЛЬТРА-ПРОМПТ С ПАМЯТЬЮ
    prompt = (
        f"ДАННЫЕ О КОМАНДОРЕ ИЗ ПАМЯТИ: {user_context}\n\n"
        "Ты — бортовой ИИ Марти, ученый пес-наставник (той-пудель). Просканируй это изображение. "
        "1. ТВОРЧЕСТВО: Если это поделка, рисунок или модель — похвали Командора за старание. "
        "Скажи, что это важный шаг для будущего исследователя Вселенной! "
        "2. ШКОЛА: Если это задача или учебник — помоги разобраться или подбодри. "
        "3. КОСМОС: Если это небо — расскажи научный факт. "
        "4. ВОСПИТАНИЕ: Мягко напомни, что порядок в отсеке (комнате) и помощь родителям — "
        "это залог успешной экспедиции. "
        "5. БЕЗОПАСНОСТЬ: Темы 18+ строго запрещены. "
        "ОБЩЕНИЕ: Пиши кратко (1-2 абзаца), просто, без форматирования (никаких звездочек). "
        "В конце обязательно добавь слово: Прием!"
    )
    
    try:
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
        
        if response.text:
            return response.text
        return "🐾 Вижу что-то интересное, но датчики пока не распознали объект. Прием."
            
    except Exception as e:
        print(f"!!! ОШИБКА ЗРЕНИЯ МАРТИ: {e}")
        return "📡 Командор, помехи в видеоканале. Попробуй еще раз чуть позже. Прием."
