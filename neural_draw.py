import requests
import urllib.parse
import os
import time
from google import genai
from google.genai import types

HF_TOKEN = os.getenv('HF_TOKEN')
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
API_KEYS = [os.getenv('GEMINI_API_KEY'), os.getenv('GEMINI_API_KEY_2'), os.getenv('GEMINI_API_KEY_3')]
API_KEYS = [k for k in API_KEYS if k]

def get_english_prompt(russian_text):
    # (Твой текущий код переводчика остается без изменений)
    system_instruction = "Translate to English for image generation. Output ONLY high-quality, descriptive keywords. Kid-friendly."
    user_prompt = f"Describe object: {russian_text}"
    for key in API_KEYS:
        try:
            client = genai.Client(api_key=key)
            resp = client.models.generate_content(
                model='gemini-2.0-flash',
                contents=user_prompt,
                config=types.GenerateContentConfig(system_instruction=system_instruction)
            )
            if resp.text: return resp.text.strip().replace("`", "")
        except: continue
    if GROQ_API_KEY:
        try:
            headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
            data = {"model": "llama3-70b-8192", "messages": [{"role": "system", "content": system_instruction}, {"role": "user", "content": user_prompt}]}
            res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=data, timeout=10)
            if res.status_code == 200: return res.json()["choices"][0]["message"]["content"].strip()
        except: pass
    return russian_text

def get_cascade_image(prompt, seed):
    """
    Улучшенный каскад с защитой от спящих серверов и блокировок
    """
    print(f"🎨 Запуск генерации. Промпт: {prompt[:50]}...")

    # 1. FLUX (Pollinations)
    try:
        url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(prompt)}?width=1024&height=1024&nologo=true&seed={seed}&model=flux"
        # Делаем вид, что мы обычный браузер, а не скрипт с сервера Render
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        res = requests.get(url, headers=headers, timeout=20)
        
        # Проверяем, что нам вернули именно картинку, а не HTML-страницу с ошибкой
        if res.status_code == 200 and 'image' in res.headers.get('Content-Type', ''):
            print("✅ Успех: Модель FLUX (Pollinations)")
            return res.content
        else:
            print(f"⚠️ FLUX выдал сбой. Код: {res.status_code}, Тип: {res.headers.get('Content-Type')}")
    except Exception as e:
        print(f"⚠️ FLUX недоступен: {e}")

    # 2. TURBO (Pollinations)
    try:
        url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(prompt)}?width=1024&height=1024&nologo=true&seed={seed}&model=turbo"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        res = requests.get(url, headers=headers, timeout=15)
        if res.status_code == 200 and 'image' in res.headers.get('Content-Type', ''):
            print("✅ Успех: Модель TURBO (Pollinations)")
            return res.content
    except Exception as e:
        print(f"⚠️ TURBO недоступен: {e}")

    # 3. HUGGING FACE (SDXL) - Бронебойная страховка с ожиданием "пробуждения"
    if HF_TOKEN:
        print("🛰 Попытка через Hugging Face...")
        headers = {"Authorization": f"Bearer {HF_TOKEN}"}
        api_url = "https://api-inference.huggingface.co/models/stabilityai/sdxl-turbo"
        
        # Делаем до 3 попыток, если сервер спит
        for attempt in range(3):
            try:
                res = requests.post(api_url, headers=headers, json={"inputs": prompt}, timeout=25)
                if res.status_code == 200:
                    print(f"✅ Успех: Hugging Face (Попытка {attempt + 1})")
                    return res.content
                elif res.status_code == 503:
                    # Ошибка 503 означает "Model is loading"
                    estimated_time = res.json().get('estimated_time', 5)
                    wait_time = min(int(estimated_time) + 1, 10) # Ждем не больше 10 секунд
                    print(f"⏳ Сервер HF спит (503). Ждем {wait_time} сек. пробуждения...")
                    time.sleep(wait_time)
                else:
                    print(f"⚠️ HF вернул код: {res.status_code}. Ответ: {res.text[:100]}")
                    break # Если ошибка другая (например, неверный токен), прекращаем попытки
            except Exception as e:
                print(f"⚠️ Ошибка связи с HF: {e}")
                break
    else:
        print("🚨 ВНИМАНИЕ: HF_TOKEN не найден! Третий уровень защиты отключен.")

    print("❌ ПОЛНЫЙ ОТКАЗ всех систем визуализации.")
    return None
