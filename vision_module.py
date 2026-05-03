import google.generativeai as genai
import os

# Настройка Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash') # Самая быстрая модель для анализа фото

def analyze_image(image_data):
    """Марти изучает фото и дает экспертный комментарий"""
    prompt = (
        "Ты — пес Марти, эксперт-астроном и штурман. Ты помогаешь Владику (8 лет) изучать космос. "
        "Тебе прислали фото. Опиши, что на нем, в контексте науки, космоса или техники. "
        "Говори просто, весело, используй эмодзи. Если на фото собака — поздоровайся! "
        "В конце добавь один короткий интересный факт. Отвечай только на русском."
    )
    
    try:
        response = model.generate_content([prompt, {"mime_type": "image/jpeg", "data": image_data}])
        return response.text
    except Exception as e:
        return f"🐾 Ой! Мои линзы запотели. Не могу разобрать изображение... (Ошибка: {e})"
