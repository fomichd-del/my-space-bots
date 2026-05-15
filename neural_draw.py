import requests
import urllib.parse
import os
import sys
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
    
    # 🟢 НАШ АРСЕНАЛ МОДЕЛЕЙ (Убрали 1.5-flash)
    MODELS_TO_TRY = ['gemini-3.1-flash-lite', 'gemini-2.5-flash', 'gemini-2.0-flash', 'gemini-flash-lite-latest']
    
    # 🟢 ГОРИЗОНТАЛЬНАЯ МАТРИЦА: Сначала модель, потом ключи
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
            except Exception as e: 
                if "429" in str(e):
                    print(f"⚠️ Лимит (429): {model_name} на Ключе {i+1} перегрет (перевод).")
                continue # Идем к следующему ключу/модели
            
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
    # Принудительно выводим в консоль, чтобы Render показал это сразу
    print(f"🎨 НАЧАЛО ГЕНЕРАЦИИ. Промпт: {prompt}", flush=True)

    if not prompt or len(prompt) < 2:
        print("❌ ОШИБКА: Пустой промпт!", flush=True)
        return None

    # 🥇 1. Together AI (FLUX)
    if TOGETHER_API_KEY:
        print("🛰 Запрос к Together AI...", flush=True)
        headers = {
            "Authorization": f"Bearer {TOGETHER_API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "black-forest-labs/FLUX.1-schnell",
            "prompt": prompt,
            "width": 1024,
            "height": 1024,
            "steps": 4, 
            "n": 1,
            "response_format": "b64_json" 
        }
        try:
            # Увеличим таймаут для надежности
            res = requests.post("https://api.together.xyz/v1/images/generations", headers=headers, json=data, timeout=40)
            if res.status_code == 200:
                print("✅ Together AI: УСПЕХ!", flush=True)
                b64_img = res.json()["data"][0]["b64_json"]
                return base64.b64decode(b64_img)
            else:
                # ВЫВОДИМ ТОЧНУЮ ОШИБКУ СЕРВЕРА
                print(f"⚠️ Together AI ОТКАЗ: {res.status_code} - {res.text}", flush=True)
        except Exception as e:
            print(f"⚠️ Ошибка связи с Together: {e}", flush=True)

    # 🥈 2. Fallback: Pollinations (FLUX)
    print("🔄 Пробую Pollinations FLUX...", flush=True)
    try:
        # Убираем nologo=true (иногда из-за него 403 ошибка)
        url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(prompt)}?width=1024&height=1024&seed={seed}&model=flux"
        res = requests.get(url, timeout=30)
        if res.status_code == 200:
            print("✅ Pollinations FLUX: УСПЕХ!", flush=True)
            return res.content
        else:
            print(f"⚠️ Pollinations сбой: {res.status_code}", flush=True)
    except Exception as e:
        print(f"⚠️ Ошибка Pollinations: {e}", flush=True)

    print("❌ ПОЛНЫЙ КРАХ всех систем визуализации.", flush=True)
    return None

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
