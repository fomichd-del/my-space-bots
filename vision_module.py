import google.generativeai as genai
import os

# Настройка Gemini
# Ключ должен быть прописан в Environment Variables на Render
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def analyze_image(image_data):
    """Марти изучает фото и дает экспертный комментарий с помощью Gemini 2.5 Flash"""
    
    # В 2026 году используем актуальный идентификатор модели
    # Если на сервере стоит ограничение по версии, можно попробовать 'gemini-2.5-flash-latest'
    model_name = 'gemini-2.5-flash'
    
    prompt = (
        "Ты — пес Марти, эксперт-астроном и штурман. Ты помогаешь Владику (8 лет) изучать космос. "
        "Тебе прислали фото. Опиши, что на нем, в контексте науки, космоса или техники. "
        "Говори просто, весело, используй эмодзи. Если на фото собака — поздоровайся! "
        "В конце добавь один короткий интересный факт. Отвечай только на русском языке."
    )
    
    try:
        # Инициализируем модель внутри функции для гибкости
        vision_model = genai.GenerativeModel(model_name)
        
        # Формируем контент для анализа (текст + изображение)
        contents = [
            prompt,
            {"mime_type": "image/jpeg", "data": image_data}
        ]
        
        response = vision_model.generate_content(contents)
        
        if response.text:
            return response.text
        else:
            return "🐾 Хмм... Вижу что-то странное, но не могу подобрать слов. Попробуй другое фото!"
            
    except Exception as e:
        # Если 2.5 Flash недоступна, выводим подсказку, какие модели есть в списке
        return (f"🐾 Ой! Мои линзы запотели из-за системного сбоя. "
                f"Ошибка: {str(e)}. Проверь доступность модели {model_name} в твоем регионе.")

def list_available_models():
    """Вспомогательная функция для проверки доступных имен моделей"""
    print("📡 Доступные модели:")
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"🔹 {m.name}")
