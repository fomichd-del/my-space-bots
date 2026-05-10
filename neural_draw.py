import requests
import urllib.parse
import os
from google import genai
from google.genai import types

# Ключи из переменных окружения
HF_TOKEN = os.getenv('HF_TOKEN')
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
API_KEYS = [os.getenv('GEMINI_API_KEY'), os.getenv('GEMINI_API_KEY_2'), os.getenv('GEMINI_API_KEY_3')]
API_KEYS = [k for k in API_KEYS if k]

def get_english_prompt(russian_text):
    """
    КАСКАДНЫЙ ПЕРЕВОДЧИК: Превращает 'нарисуй кота' в крутой английский промпт.
    """
    system_instruction = "Translate to English for image generation. Output ONLY high-quality, descriptive keywords. Kid-friendly."
    user_prompt = f"Describe object: {russian_text}"

    # 1. Сначала пробуем GEMINI
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

    # 2. Резерв: GROQ
    if GROQ_API_KEY:
        try:
            headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
            data = {
                "model": "llama3-70b-8192",
                "messages": [
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": user_prompt}
                ]
            }
            res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=data, timeout=10)
            if res.status_code == 200:
                return res.json()["choices"][0]["message"]["content"].strip()
        except: pass

    # 3. Крайний случай: POLLINATIONS TEXT
    try:
        url = f"https://text.pollinations.ai/{urllib.parse.quote(system_instruction + ' ' + user_prompt)}"
        res = requests.get(url, timeout=10)
        if res.status_code == 200: return res.text.strip()
    except: pass

    return russian_text # Если всё упало, отдаем как есть

def get_cascade_image(prompt, seed):
    """Каскадная генерация самой картинки (уже знакомая нам логика)"""
    # ... (код из прошлого сообщения: Flux -> Turbo -> HF)
    try:
        url_flux = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(prompt)}?width=1024&height=1024&nologo=true&seed={seed}&model=flux"
        res = requests.get(url_flux, timeout=15)
        if res.status_code == 200: return res.content
    except: pass
    
    # Резерв Turbo
    try:
        url_turbo = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(prompt)}?width=1024&height=1024&nologo=true&seed={seed}&model=turbo"
        res = requests.get(url_turbo, timeout=10)
        if res.status_code == 200: return res.content
    except: pass
    
    return None
