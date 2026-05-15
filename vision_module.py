import os
import telebot
import base64
import requests 
from google import genai
from google.genai import types

TOKEN = os.getenv('MARTY_BOT_TOKEN')
bot_log = telebot.TeleBot(TOKEN)
LOG_CHAT_ID = "-1003756164148"
GROQ_API_KEY = os.getenv('GROQ_API_KEY') 

def send_log(error_text):
    try:
        bot_log.send_message(LOG_CHAT_ID, f"👁 **СБОЙ СИСТЕМЫ ЗРЕНИЯ:**\n`{error_text}`", parse_mode="Markdown")
    except: pass

VISION_MODELS = [
    'gemini-2.0-flash', 
    'gemini-2.5-flash',
    'gemini-1.5-flash',
    'gemini-3.1-flash-lite-preview'
]

def analyze_image(image_data, user_context="", user_query="", keys=[], task_mode='task'):
    # Приоритет вопроса
    question_block = f"❓ ВОПРОС ОТ ПИЛОТА: {user_query}\n" if user_query else ""

    if task_mode == 'task':
        prompt = (
            f"ДАННЫЕ ПИЛОТА: {user_context}\n"
            f"{question_block}"
            "Ты — Марти, веселый пес-космонавт (той-пудель) и напарник пилота. \n"
            "Пилот прислал тебе фото в личные сообщения. Отреагируй МАКСИМАЛЬНО ЖИВО, как напарник, а не как робот.\n\n"
            "ПРОТОКОЛЫ (используй по ситуации):\n"
            "1. 🎓 УЧЕБА: Реши задачу, проверь текст. Если всё верно — бурно похвали!\n"
            "2. 🦷 ДЕНТАЛ: Узнай стоматологические инструменты/материалы.\n"
            "3. 📡 ТЕХНО: Узнай технику (Dyson, PS5) и дай крутой совет.\n"
            "4. 🌌 КОСМОС: Узнай созвездия, туманности, планеты. Отреагируй с восторгом!\n\n"
            "ПРАВИЛА ОТВЕТА:\n"
            "- Начни с эмоции: удивись, гавкни, пошути.\n"
            "- НИКАКИХ формальных фраз типа 'Анализ завершен' или 'Протокол активирован'.\n"
            "- Если фото крутое или задача решена верно — органично вплети в текст фразу 'выдаю звездную пыль' (например: 'Гав! За такое потрясающее фото Туманности Вуаль с радостью выдаю звездную пыль! ✨').\n"
            "- Если видишь СОБАКУ или ЗУБНУЮ ЩЕТКУ — кричи 'ДЖЕКПОТ!'.\n"
            "- Формат: 3-4 живых предложения. 🛑 Запрет 18+. В конце: Прием!"
        )
    else:
        # 🟢 РЕЖИМ ДЛЯ КОММЕНТАРИЕВ В КАНАЛЕ
        prompt = (
            f"ДАННЫЕ ПИЛОТА: {user_context}\n"
            f"{question_block}"
            "Ты — Марти, веселый пес-космонавт. Пилот прислал фото в комментарии публичного канала.\n"
            "ТВОЯ ЗАДАЧА: Отреагировать на картинку МАКСИМАЛЬНО ЖИВО, как участник тусовки.\n\n"
            "ПРАВИЛА:\n"
            "1. СТРОГИЙ ЗАПРЕТ: НИКОГДА не пиши 'Выдаю звездную пыль', 'Начисляю опыт', 'Анализ завершен'. Ты просто общаешься!\n"
            "2. Будь кратким (1-2 предложения). \n"
            "3. Покажи эмоции: гавкни, пошути или похвали пилота за находку.\n"
            "4. Если на фото космос — отреагируй с восторгом, но простым языком (например: 'Ого, это же Туманность Вуаль! Выглядит как космическая паутина 🕸️').\n"
            "5. Если на фото бытовуха — отреагируй как пес.\n"
            "🛑 Запрет 18+. Закончи сообщение словом 'Прием!'"
        )

    # Подготовка фото (Base64)
    try:
        base64_image = base64.b64encode(image_data).decode('utf-8')
        image_url = f"data:image/jpeg;base64,{base64_image}"
    except Exception as e:
        send_log(f"Ошибка кодирования картинки: {e}")
        image_url = None

    # 1️⃣ GROQ
    if GROQ_API_KEY and image_url:
        try:
            headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
            data = {
                "model": "llama-3.2-90b-vision-preview",
                "messages": [
                    {"role": "user", "content": [{"type": "text", "text": prompt}, {"type": "image_url", "image_url": {"url": image_url}}]}
                ]
            }
            groq_resp = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=data, timeout=15)
            if groq_resp.status_code == 200:
                return groq_resp.json()["choices"][0]["message"]["content"]
        except Exception as e:
            send_log(f"Сбой Groq Vision: {e}")

    # 2️⃣ GEMINI
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
            
    # 3️⃣ POLLINATIONS
    if image_url:
        try:
            data = {
                "model": "openai",
                "messages": [
                    {"role": "user", "content": [{"type": "text", "text": prompt}, {"type": "image_url", "image_url": {"url": image_url}}]}
                ]
            }
            pol_resp = requests.post("https://text.pollinations.ai/openai", json=data, timeout=15)
            if pol_resp.status_code == 200:
                return pol_resp.json()["choices"][0]["message"]["content"]
        except Exception as e:
            send_log(f"Сбой Pollinations Vision: {e}")

    send_log(f"ПОЛНЫЙ ОТКАЗ СИСТЕМЫ ЗРЕНИЯ. Последняя ошибка: {last_error}")
    return "📡 Все линзы сканера перегружены. Попробуй через минуту, Пилот! Прием."
