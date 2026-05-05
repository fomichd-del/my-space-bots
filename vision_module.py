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
    Анализ изображений с учетом личности пилота, его истории и системы античита.
    """
    prompt = (
        f"ДАННЫЕ: {user_context}\n"
        "Ты — ученый пес Марти, бортовой ИИ и наставник для участников канала. Просканируй это фото. "
        "1. АТТЕСТАЦИЯ (АНТИЧИТ): Если на фото доказательство выполненного задания (убранная комната, решенные уроки, творчество) — похвали и ОБЯЗАТЕЛЬНО напиши, что выдаешь 'звездную пыль'. Если на фото беспорядок или уроки сделаны с ошибками — мягко укажи на это и пыль пока не давай. "
        "2. СЕКРЕТНЫЙ АРТЕФАКТ (ДЖЕКПОТ): Если ты видишь на фото СОБАКУ или ЗУБНУЮ ЩЕТКУ, обязательно напиши слово 'ДЖЕКПОТ' (большими буквами) и похвали за находку! "
        "3. ШКОЛА: Если это просто задача — помоги найти решение или подбодри. "
        "4. КОСМОС: Если это небо или звезды — расскажи научный факт. "
        "5. ЦЕНЗУРА (СТРОГО): Запрещено обсуждать секс, смерть, насилие, политику. Если на фото что-то неподобающее, ответь: 'Пилот, эти визуальные частоты заблокированы Академией!'. "
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
