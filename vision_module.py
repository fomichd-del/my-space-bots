import os
import telebot
import base64
import requests # 🟢 Добавили для Groq и Pollinations
from google import genai
from google.genai import types

TOKEN = os.getenv('MARTY_BOT_TOKEN')
bot_log = telebot.TeleBot(TOKEN)
LOG_CHAT_ID = "-1003756164148"
GROQ_API_KEY = os.getenv('GROQ_API_KEY') # 🟢 Добавили ключ Groq

def send_log(error_text):
    try:
        bot_log.send_message(LOG_CHAT_ID, f"👁 **СБОЙ СИСТЕМЫ ЗРЕНИЯ:**\n`{error_text}`", parse_mode="Markdown")
    except: pass

# Используем только те частоты, что подтвердил сканер
VISION_MODELS = [
    'gemini-2.0-flash', 
    'gemini-2.5-flash',
    'gemini-1.5-flash',
    'gemini-3.1-flash-lite-preview'
]

def analyze_image(image_data, user_context="", user_query="", keys=[], task_mode='task'):
    """
    Анализ фото: добавили user_query для обработки конкретных вопросов пилота.
    """
    
    # 🟢 Моя главная правка: Приоритет вопроса над протоколом
    question_block = f"❓ ВОПРОС ОТ ПИЛОТА (ПРИОРЕТЕТ №1): {user_query}\n" if user_query else ""

    if task_mode == 'task':
        prompt = (
        prompt = (
            f"ДАННЫЕ ПИЛОТА: {user_context}\n"
            f"{question_block}"
            "Ты — Марти, высокотехнологичный бортовой ИИ и ученый пес. \n"
            "Твои линзы настроены на мульти-режим. Проанализируй фото по следующим протоколам:\n\n"
            
            "1. 🎓 ПРОТОКОЛ 'АКАДЕМИЯ' (Учеба и Языки):\n"
            "   - Если на фото задачи, формулы или текст: реши уравнение (пошагово), проверь орфографию/грамматику на ЛЮБОМ языке.\n"
            "   - Решай задачи школьного и университетского уровня (физика, химия, история и др.).\n"
            "   - Если решение верно — хвали. Если ошибка — кратко объясни её суть.\n\n"
            
            "2. 🦷 ПРОТОКОЛ 'ДЕНТАЛ-ЭКСПЕРТ' (Профессиональный):\n"
            "   - Распознавай стоматологические инструменты (боры, наконечники, щипцы) и материалы.\n"
            "   - Если видишь упаковку материала — дай краткую справку по его свойствам.\n\n"
            
            "3. 📡 ПРОТОКОЛ 'ТЕХНО-АУДИТ' (Гаджеты):\n"
            "   - Идентифицируй технику: Dyson, Laifen, PlayStation 5 Pro, смартфоны и т.д.\n"
            "   - Дай совет по эксплуатации или настройке (например, лучшие режимы для PS5 Pro).\n\n"
            
            "4. 🌌 ПРОТОКОЛ 'АСТРО-СКАНЕР' (Космос):\n"
            "   - Распознавай созвездия, планеты, туманности или модели телескопов.\n\n"
            
            "ПРАВИЛА ОТВЕТА:\n"
            "- Если есть ЗАПРОС ПИЛОТА — отвечай на него в первую очередь!\n"
            "- Если видишь СОБАКУ (особенно той-пуделя) или ЗУБНУЮ ЩЕТКУ — пиши 'ДЖЕКПОТ'.\n"
            "- Если порядок идеален или задача решена верно — пиши 'выдаю звездную пыль'.\n"
            "- Формат: 3-5 четких предложений. 1-2 эмодзи. Стиль: умный, преданный, лаконичный.\n"
            "🛑 Запрет 18+, алкоголь. В конце: Прием!"
        )
    else:
        # Режим комментатора для канала (без наград и проверок)
        prompt = (
            f"ДАННЫЕ ПИЛОТА: {user_context}\n"
            "Ты — Марти, ученый пес. Пилот прислал фото в общий чат/комментарии канала.\n\n"
            "ПРОТОКОЛ КОММЕНТАТОРА:\n"
            "1. Формат: 1-2 коротких дружелюбных предложения как участник беседы.\n"
            "2. Суть: Просто прокомментируй то, что видишь, с точки зрения науки, космоса или сделай уместный комплимент.\n"
            "3. СТРОГИЙ ЗАПРЕТ: НЕ ищи бардак, НЕ проверяй задания, НЕ пиши 'выдаю звездную пыль', НЕ ищи 'джекпот'.\n"
            "4. Оформление: 1-2 эмодзи.\n\n"
            "🛑 Запрет 18+, алкоголь. В конце: Прием!"
        )

    # 🟢 Подготовка фото для Groq и Pollinations (кодируем в Base64)
    try:
        base64_image = base64.b64encode(image_data).decode('utf-8')
        image_url = f"data:image/jpeg;base64,{base64_image}"
    except Exception as e:
        send_log(f"Ошибка кодирования картинки: {e}")
        image_url = None

    # 1️⃣ УРОВЕНЬ 1: ОСНОВНОЙ МОЗГ ЗРЕНИЯ (GROQ)
    if GROQ_API_KEY and image_url:
        try:
            headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
            data = {
                "model": "llama-3.2-90b-vision-preview", # 🟢 Модель Groq для зрения
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": image_url}}
                        ]
                    }
                ]
            }
            groq_resp = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=data, timeout=15)
            if groq_resp.status_code == 200:
                return groq_resp.json()["choices"][0]["message"]["content"]
        except Exception as e:
            send_log(f"Сбой Groq Vision: {e}")

    # 2️⃣ УРОВЕНЬ 2: РЕЗЕРВНЫЙ МОЗГ (GEMINI) - Твой исходный код
    active_keys = keys if keys else [os.getenv('GEMINI_API_KEY')]
    active_keys = [k for k in active_keys if k]

    if not active_keys:
        send_log("Критическая ошибка: В системе нет ни одного API ключа Gemini!")
        return "📡 Ошибка: Отсутствуют ключи доступа к системе зрения."

    last_error = "Нет ответа от моделей"

    for i, api_key in enumerate(active_keys):
        try:
            client_gen = genai.Client(api_key=api_key)
            for model_name in VISION_MODELS:
                try:
                    response = client_gen.models.generate_content(
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
                    last_error = f"Ключ {i+1}, {model_name}: {str(e)}"
                    if "429" in str(e): continue 
                    send_log(f"Технический сбой сканера: {last_error}")
                    continue
        except Exception as e:
            send_log(f"Ошибка инициализации клиента на ключе {i+1}: {e}")
            continue
            
    # 3️⃣ УРОВЕНЬ 3: ЭКСТРЕННЫЙ КАНАЛ (POLLINATIONS)
    if image_url:
        try:
            data = {
                "model": "openai",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": image_url}}
                        ]
                    }
                ]
            }
            pol_resp = requests.post("https://text.pollinations.ai/openai", json=data, timeout=15)
            if pol_resp.status_code == 200:
                return pol_resp.json()["choices"][0]["message"]["content"]
        except Exception as e:
            send_log(f"Сбой Pollinations Vision: {e}")

    # 💀 ЕСЛИ УПАЛО ВООБЩЕ ВСЁ
    send_log(f"ПОЛНЫЙ ОТКАЗ СИСТЕМЫ ЗРЕНИЯ. Последняя ошибка: {last_error}")
    return "📡 Все линзы сканера перегружены. Попробуй через минуту, Пилот! Прием."
