import requests
import urllib.parse
import os

# Подхватываем ключ из Render
HF_TOKEN = os.getenv('HF_TOKEN')

def get_cascade_image(prompt, seed):
    """
    Каскадная система генерации картинок:
    Пытается получить фото из 3 разных источников по очереди.
    """
    
    # 1. ОСНОВНОЙ КАНАЛ: Pollinations (Модель FLUX - самая красивая, но тяжелая)
    try:
        url_flux = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(prompt)}?width=1024&height=1024&nologo=true&seed={seed}&model=flux"
        res = requests.get(url_flux, timeout=12) # Ждем максимум 12 секунд
        if res.status_code == 200: return res.content
    except Exception as e:
        print(f"Сбой FLUX: {e}")

    # 2. БЫСТРЫЙ КАНАЛ: Pollinations (Модель TURBO - чуть проще, но мгновенная)
    try:
        url_turbo = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(prompt)}?width=1024&height=1024&nologo=true&seed={seed}&model=turbo"
        res = requests.get(url_turbo, timeout=10)
        if res.status_code == 200: return res.content
    except Exception as e:
        print(f"Сбой TURBO: {e}")

    # 3. ЭКСТРЕННЫЙ КАНАЛ: Hugging Face (Stable Diffusion XL)
    if HF_TOKEN:
        try:
            headers = {"Authorization": f"Bearer {HF_TOKEN}"}
            api_url = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
            payload = {"inputs": prompt, "parameters": {"seed": seed}}
            res = requests.post(api_url, headers=headers, json=payload, timeout=15)
            if res.status_code == 200: return res.content
        except Exception as e:
            print(f"Сбой Hugging Face: {e}")
            
    # Если магнитная буря отключила вообще всё
    return None
