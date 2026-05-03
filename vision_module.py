import google.generativeai as genai
import os

# Настройка Gemini
# Используем ваш рабочий API ключ
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def analyze_image(image_data):
    """Марти изучает фото через проверенную модель 2.5 Flash"""
    
    # Тот самый идентификатор, который у вас работал
    model_name = 'gemini-2.5-flash'
    
    prompt = (
        "Ты — пес Марти, эксперт-астроном и штурман. Ты помогаешь Владику (8 лет) изучать космос. "
        "Тебе прислали фото. Опиши, что на нем, в контексте науки, космоса или техники. "
        "Говори просто, весело, используй эмодзи. Если на фото собака — поздоровайся! "
        "В конце добавь один короткий интересный факт. Отвечай только на русском языке."
    )
    
    try:
        # Инициализируем рабочую модель
        vision_model = genai.GenerativeModel(model_name)
        
        # Подготовка данных: текст-инструкция и сама картинка
        contents = [
            prompt,
            {"mime_type": "image/jpeg", "data": image_data}
        ]
        
        response = vision_model.generate_content(contents)
        
        if response.text:
            return response.text
        else:
            return "🐾 Хмм... Вижу что-то интересное, но мои речевые модули забарахлили. Попробуй ещё раз!"
            
    except Exception as e:
        # Если вдруг база или сеть выдадут сбой, Марти сообщит об этом
        return f"🐾 Ой! Мои линзы запотели из-за системного сбоя. Ошибка: {str(e)}"
