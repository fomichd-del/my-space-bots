import requests
import urllib.parse
import os
import time
import base64  # 🟢 НОВЫЙ ИМПОРТ ДЛЯ РАСШИФРОВКИ КАРТИНОК
from google import genai
from google.genai import types

HF_TOKEN = os.getenv('HF_TOKEN')
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
TOGETHER_API_KEY = os.getenv('TOGETHER_API_KEY') # 🟢 Подключаем новый ключ
API_KEYS = [os.getenv('GEMINI_API_KEY'), os.getenv('GEMINI_API_KEY_2'), os.getenv('GEMINI_API_KEY_3')]
API_KEYS = [k for k in API_KEYS if k]

def get_english_prompt(russian_text):
    system_instruction = "Translate to English for image generation. Output ONLY high-quality, descriptive keywords. Kid-friendly."
    user_prompt = f"Describe object: {russian_text}"
    
    # 🟢 НАШ АРСЕНАЛ МОДЕЛЕЙ (Каскад)
    MODELS_TO_TRY = ['gemini-2.0-flash', 'gemini-2.5-flash', 'gemini-1.5-flash', 'gemini-3.1-flash-lite-preview']
    
    for key in API_KEYS:
        try:
            client = genai.Client(api_key=key)
            # Перебираем модели по очереди для каждого ключа
            for model_name in MODELS_TO_TRY:
                try:
                    resp = client.models.generate_content(
                        model=model_name,
                        contents=user_prompt,
                        config=types.GenerateContentConfig(system_instruction=system_instruction)
                    )
                    if resp.text: 
                        return resp.text.strip().replace("`", "")
                except: 
                    continue # Модель устала? Берем следующую!
        except: 
            continue # Ключ не работает? Берем следующий!
            
    # Если ВООБЩЕ ВСЕ Gemini на всех ключах упали, в бой вступает резервный GROQ
    if GROQ_API_KEY:
        try:
            headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
            data = {"model": "llama3-70b-8192", "messages": [{"role": "system", "content": system_instruction}, {"role": "user", "content": user_prompt}]}
            res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=data, timeout=10)
            if res.status_code == 200: return res.json()["choices"][0]["message"]["content"].strip()
        except: pass
        
    return russian_text # Если упало абсолютно всё, возвращаем русский текст

def get_cascade_image(prompt, seed):
    """
    Каскад с элитным заводом Together AI во главе
    """
    print(f"🎨 Запуск генерации. Промпт: {prompt[:50]}...")

    # 🥇 1. ЭЛИТНЫЙ ЗАВОД: Together AI (FLUX) - Самый быстрый и надежный
    if TOGETHER_API_KEY:
        print("🛰 Запрос к премиум-серверу Together AI...")
        headers = {
            "Authorization": f"Bearer {TOGETHER_API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "black-forest-labs/FLUX.1-schnell",
            "prompt": prompt,
            "width": 1024,
            "height": 1024,
            "steps": 4, # FLUX Schnell работает идеально за 4 шага
            "n": 1,
            "response_format": "b64_json" # Просим вернуть картинку кодом
        }
        try:
            res = requests.post("https://api.together.xyz/v1/images/generations", headers=headers, json=data, timeout=30)
            if res.status_code == 200:
                print("✅ Успех: Together AI сгенерировал изображение!")
                b64_img = res.json()["data"][0]["b64_json"]
                return base64.b64decode(b64_img) # Расшифровываем в картинку
            else:
                print(f"⚠️ Сбой Together AI. Код: {res.status_code}. Ошибка: {res.text[:100]}")
        except Exception as e:
            print(f"⚠️ Ошибка связи с Together AI: {e}")
    else:
        print("🚨 TOGETHER_API_KEY не найден в системе!")

    # 🥈 2. БЕСПЛАТНЫЙ ЗАВОД: FLUX (Pollinations) - Стелс-режим
    stealth_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
    }
    try:
        url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(prompt)}?width=1024&height=1024&nologo=true&seed={seed}&model=flux"
        res = requests.get(url, headers=stealth_headers, timeout=25)
        if res.status_code == 200 and 'image' in res.headers.get('Content-Type', ''):
            print("✅ Успех: Модель FLUX (Pollinations)")
            return res.content
        else:
            print(f"⚠️ Pollinations FLUX сбой. Код: {res.status_code}")
    except Exception as e:
        print(f"⚠️ Ошибка Pollinations FLUX: {e}")

    # 🥉 3. БЕСПЛАТНЫЙ ЗАВОД: TURBO (Pollinations)
    try:
        url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(prompt)}?width=1024&height=1024&nologo=true&seed={seed}&model=turbo"
        res = requests.get(url, headers=stealth_headers, timeout=20)
        if res.status_code == 200 and 'image' in res.headers.get('Content-Type', ''):
            print("✅ Успех: Модель TURBO (Pollinations)")
            return res.content
    except Exception as e:
        print(f"⚠️ Ошибка Pollinations TURBO: {e}")

    print("❌ ПОЛНЫЙ ОТКАЗ всех систем визуализации.")
    return None
