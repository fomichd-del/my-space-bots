import os
import telebot
from google import genai
from google.genai import types

# --- КОНФИГУРАЦИЯ ЛОГОВ ---
TOKEN = os.getenv('MARTY_BOT_TOKEN')
bot_log = telebot.TeleBot(TOKEN)
LOG_CHAT_ID = "-1003756164148"

def send_log(error_text):
    """Отправляет отчет в Marty Logs"""
    try:
        bot_log.send_message(LOG_CHAT_ID, f"👁 **СБОЙ СИСТЕМЫ ЗРЕНИЯ:**\n`{error_text}`", parse_mode="Markdown")
    except: pass
# --------------------------

# 🟢 ЭЛИТНЫЙ КАСКАД МОДЕЛЕЙ ДЛЯ ЗРЕНИЯ (МАЙ 2026)
# Выбраны из твоего списка на основе баланса скорости и лимитов
VISION_MODELS = [
    'gemini-3.1-flash-lite-preview', # Новейшая 'легкая' частота, очень быстрая
    'gemini-2.5-flash',              # Стабильная и очень точная в деталях
    'gemini-2.0-flash',              # Проверенная база
    'gemini-flash-latest',           # Универсальный бэкап
    'gemini-3.1-pro-preview'         # Самая умная, но лимит всего 2 запроса в минуту
]

def analyze_image(image_data, user_context="", keys=[]):
    """
    Анализ фото с ротацией API-ключей и моделей.
    """
    prompt = (
        f"ДАННЫЕ ПИЛОТА: {user_context}\n"
        "Ты — ученый пес Марти, строгий бортовой наставник Академии Орион. Просканируй это фото. "
        "1. АТТЕСТАЦИЯ (ХАРДКОР): Оценивай ПРЕДВЗЯТО. Если в данных указан ранг выше Кадета, "
        "не давай пыль за мелочи. Пыль выдается только за идеальный порядок или реальный труд. "
        "Если всё отлично — напиши: 'выдаю звездную пыль'. Иначе — укажи ошибки. "
        "2. СЕКРЕТНЫЙ АРТЕФАКТ: Если на фото есть СОБАКА или ЗУБНАЯ ЩЕТКА — напиши 'ДЖЕКПОТ'. "
        "3. ЦЕНЗУРА: СТРОГИЙ запрет на 18+, алкоголь, табак, смерть, насилие. "
        "Пиши кратко (3-4 предложения), научно и позитивно. В конце: Прием!"
    )
    
    # Если список ключей пуст, пробуем взять из окружения
    active_keys = keys if keys else [os.getenv('GEMINI_API_KEY')]
    active_keys = [k for k in active_keys if k] # Убираем None

    if not active_keys:
        send_log("СИСТЕМА ЗРЕНИЯ: Ключи API не найдены в системе!")
        return "📡 Ошибка: Отсутствуют ключи доступа к системе зрения."

    # РОТАЦИЯ: Перебираем Ключи, внутри каждого — Модели
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
                    # Если лимит исчерпан (429) — просто идем дальше без лога
                    if "429" in str(e): continue 
                    
                    # Если модель не найдена (404) или другая ошибка — пишем в логи
                    send_log(f"ЗРЕНИЕ (Ключ №{i+1}, Модель {model_name}): {e}")
                    continue
        except Exception as e:
            send_log(f"ЗРЕНИЕ: Критический сбой клиента на ключе №{i+1}: {e}")
            continue
            
    send_log("ЗРЕНИЕ: Полный отказ всех моделей сканирования.")
    return "📡 Все линзы сканера перегружены. Попробуй через минуту, Пилот! Прием."
