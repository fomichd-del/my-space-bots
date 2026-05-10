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
    Улучшенный каскад с расширенным логированием
    """
    print(f"🎨 Запуск генерации. Промпт: {prompt[:50]}...")

    # 1. FLUX (Pollinations) - Самый красивый
    try:
        url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(prompt)}?width=1024&height=1024&nologo=true&seed={seed}&model=flux"
        res = requests.get(url, timeout=20) # Увеличили до 20 сек
        if res.status_code == 200 and len(res.content) > 5000:
            print("✅ Успех: Модель FLUX")
            return res.content
    except Exception as e:
        print(f"⚠️ FLUX недоступен: {e}")

    # 2. TURBO (Pollinations) - Самый быстрый
    try:
        url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(prompt)}?width=1024&height=1024&nologo=true&seed={seed}&model=turbo"
        res = requests.get(url, timeout=15)
        if res.status_code == 200 and len(res.content) > 5000:
            print("✅ Успех: Модель TURBO")
            return res.content
    except Exception as e:
        print(f"⚠️ TURBO недоступен: {e}")

    # 3. HUGGING FACE (Stable Diffusion XL) - Наша главная страховка
    if HF_TOKEN:
        print("🛰 Попытка через Hugging Face...")
        try:
            headers = {"Authorization": f"Bearer {HF_TOKEN}"}
            # Используем быструю модель Lightning, она реже "спит"
            api_url = "https://api-inference.huggingface.co/models/stabilityai/sdxl-turbo"
            res = requests.post(api_url, headers=headers, json={"inputs": prompt}, timeout=25)
            if res.status_code == 200:
                print("✅ Успех: Hugging Face")
                return res.content
            else:
                print(f"⚠️ HF вернул код: {res.status_code}")
        except Exception as e:
            print(f"⚠️ Hugging Face недоступен: {e}")
    else:
        print("🚨 Критическая ошибка: HF_TOKEN не найден в системе!")

    print("❌ ПОЛНЫЙ ОТКАЗ всех систем визуализации.")
    return None
