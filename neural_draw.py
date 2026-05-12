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
    Ультра-стелс каскад с маскировкой под живого человека
    """
    print(f"🎨 Запуск генерации. Промпт: {prompt[:50]}...")

    # Маскируемся под новейший Google Chrome
    stealth_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept': 'image/avif,image/webp,image/apng,image/*,*/*;q=0.8',
        'Referer': 'https://pollinations.ai/',
        'Sec-Ch-Ua': '"Chromium";v="124", "Google Chrome";v="124"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': '"Windows"'
    }

    # 1. FLUX (Pollinations)
    try:
        url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(prompt)}?width=1024&height=1024&nologo=true&seed={seed}&model=flux"
        res = requests.get(url, headers=stealth_headers, timeout=25)
        
        if res.status_code == 200 and 'image' in res.headers.get('Content-Type', ''):
            print("✅ Успех: Модель FLUX")
            return res.content
        else:
            print(f"⚠️ FLUX сбой. Код: {res.status_code}, Тип: {res.headers.get('Content-Type')[:30]}")
    except Exception as e:
        print(f"⚠️ Ошибка FLUX: {e}")

    # 2. TURBO (Pollinations)
    try:
        url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(prompt)}?width=1024&height=1024&nologo=true&seed={seed}&model=turbo"
        res = requests.get(url, headers=stealth_headers, timeout=20)
        if res.status_code == 200 and 'image' in res.headers.get('Content-Type', ''):
            print("✅ Успех: Модель TURBO")
            return res.content
        else:
            print(f"⚠️ TURBO сбой. Код: {res.status_code}")
    except Exception as e:
        print(f"⚠️ Ошибка TURBO: {e}")

    # 3. HUGGING FACE (SDXL) - Бронебойный резерв
    if HF_TOKEN:
        print("🛰 Попытка через Hugging Face...")
        hf_headers = {"Authorization": f"Bearer {HF_TOKEN}"}
        # Меняем модель на более безотказную!
        api_url = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell"
        
        for attempt in range(3):
            try:
                res = requests.post(api_url, headers=hf_headers, json={"inputs": prompt}, timeout=30)
                if res.status_code == 200:
                    print(f"✅ Успех: Hugging Face (Попытка {attempt + 1})")
                    return res.content
                elif res.status_code == 503:
                    wait = min(int(res.json().get('estimated_time', 5)) + 1, 15)
                    print(f"⏳ HF грузится. Ждем {wait} сек...")
                    time.sleep(wait)
                else:
                    print(f"⚠️ HF код {res.status_code}: {res.text[:80]}")
                    break
            except Exception as e:
                print(f"⚠️ Ошибка HF: {e}")
                break
    else:
        print("🚨 HF_TOKEN НЕ НАЙДЕН! Резерв отключен.")

    print("❌ ПОЛНЫЙ ОТКАЗ всех систем визуализации.")
    return None
