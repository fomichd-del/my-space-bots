import requests
import urllib.parse
import os
import sys
import time
import base64
import re
from google import genai
from google.genai import types

HF_TOKEN = os.getenv('HF_TOKEN')
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
TOGETHER_API_KEY = os.getenv('TOGETHER_API_KEY')
API_KEYS = [os.getenv('GEMINI_API_KEY'), os.getenv('GEMINI_API_KEY_2'), os.getenv('GEMINI_API_KEY_3')]
API_KEYS = [k for k in API_KEYS if k]

def get_english_prompt(russian_text):
    # Очищаем текст от командных слов перед переводом
    clean = re.sub(r'(нарисуй|изобрази|сделай картинку|архив|картинка)', '', russian_text, flags=re.IGNORECASE).strip()
    if not clean: clean = russian_text
    
    system_instruction = "Translate to English for image generation. Output ONLY high-quality, descriptive keywords. Kid-friendly. No verbs like 'Draw' or 'Create'."
    user_prompt = f"Describe object: {clean}"
    
    # 🟢 Обновленный арсенал переводчиков (самые быстрые и умные из вашего скана)
    MODELS_TO_TRY = ['gemini-3.1-flash-lite-preview', 'gemini-3.1-flash-lite', 'gemini-2.5-flash', 'gemini-2.0-flash']
    
    for model_name in MODELS_TO_TRY:
        for i, key in enumerate(API_KEYS):
            try:
                client = genai.Client(api_key=key)
                resp = client.models.generate_content(
                    model=model_name,
                    contents=user_prompt,
                    config=types.GenerateContentConfig(system_instruction=system_instruction)
                )
                if resp.text: 
                    return resp.text.strip().replace("`", "")
            except: continue
            
    if GROQ_API_KEY:
        try:
            headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
            data = {"model": "llama3-70b-8192", "messages": [{"role": "system", "content": system_instruction}, {"role": "user", "content": user_prompt}]}
            res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=data, timeout=10)
            if res.status_code == 200: return res.json()["choices"][0]["message"]["content"].strip()
        except: pass
        
    return clean

def get_cascade_image(prompt, seed):
    # Сокращаем промпт в логах, чтобы не засорять консоль
    short_prompt = prompt[:100] + "..." if len(prompt) > 100 else prompt
    print(f"🎨 НАЧАЛО ГЕНЕРАЦИИ. Промпт: {short_prompt}", flush=True)
    
    stealth_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
    }

    # 🚀 1. СВЕРХСВЕТОВОЙ ЗАВОД: Модели Gemini Image (Бесплатно, 3 ключа)
    GEMINI_IMAGE_MODELS = [
        'gemini-3.1-flash-image-preview',
        'gemini-3-pro-image-preview',
        'gemini-2.5-flash-image'
    ]
    
    print("🛰 Запрос к матрице Gemini Image...", flush=True)
    for img_model in GEMINI_IMAGE_MODELS:
        for i, key in enumerate(API_KEYS):
            try:
                client = genai.Client(api_key=key)
                result = client.models.generate_images(
                    model=img_model,
                    prompt=prompt,
                    config=types.GenerateImagesConfig(
                        number_of_images=1,
                        aspect_ratio="1:1"
                    )
                )
                if result.generated_images:
                    print(f"✅ Gemini Image ({img_model}) Ключ {i+1}: УСПЕХ!", flush=True)
                    # Извлекаем байты картинки из ответа Google
                    return result.generated_images[0].image.image_bytes
            except Exception as e:
                # Если лимит исчерпан или модель недоступна - ИИ просто тихо перейдет к следующему ключу
                print(f"⚠️ Gemini Image ({img_model}) Ключ {i+1} СБОЙ: {e}", flush=True)
                continue

    # 🥇 2. Together AI (FLUX.1-schnell) - Элитный резерв (если есть баланс)
    if TOGETHER_API_KEY:
        print("🔄 Переход к Together AI...", flush=True)
        headers = {"Authorization": f"Bearer {TOGETHER_API_KEY}", "Content-Type": "application/json"}
        data = {
            "model": "black-forest-labs/FLUX.1-schnell",
            "prompt": prompt,
            "width": 1024, "height": 1024, "steps": 4, "n": 1,
            "response_format": "b64_json"
        }
        try:
            res = requests.post("https://api.together.xyz/v1/images/generations", headers=headers, json=data, timeout=30)
            if res.status_code == 200:
                print("✅ Together AI: УСПЕХ!", flush=True)
                return base64.b64decode(res.json()["data"][0]["b64_json"])
            else:
                print(f"⚠️ Together AI ОТКАЗ: {res.status_code}", flush=True)
        except Exception as e:
            print(f"⚠️ Together AI ОШИБКА: {e}", flush=True)

    # 🥈 3. Pollinations FLUX - Бесплатный резерв №1
    print("🔄 Переход к Pollinations FLUX...", flush=True)
    try:
        url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(prompt)}?width=1024&height=1024&seed={seed}&model=flux&nologo=true"
        res = requests.get(url, headers=stealth_headers, timeout=25)
        if res.status_code == 200:
            print("✅ Pollinations FLUX: УСПЕХ!", flush=True)
            return res.content
        else:
            print(f"⚠️ Pollinations FLUX ОТКАЗ: {res.status_code}", flush=True)
    except Exception as e:
        print(f"⚠️ Pollinations FLUX ОШИБКА: {e}", flush=True)

    # 🥉 4. Pollinations TURBO - Бесплатный резерв №2 (Последний рубеж)
    print("🔄 Переход к Pollinations TURBO...", flush=True)
    try:
        url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(prompt)}?width=1024&height=1024&seed={seed}&model=turbo"
        res = requests.get(url, headers=stealth_headers, timeout=20)
        if res.status_code == 200:
            print("✅ Pollinations TURBO: УСПЕХ!", flush=True)
            return res.content
    except Exception as e:
        print(f"⚠️ Pollinations TURBO ОШИБКА: {e}", flush=True)

    print("❌ ПОЛНЫЙ КРАХ ВСЕХ СИСТЕМ.", flush=True)
    return None
