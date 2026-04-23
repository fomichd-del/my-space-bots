import requests
import json

# Твой ключ из приложения
LICENSE = "0I79Gb2U-6C250hoB-0y784opm"

def get_warp_plus():
    session = requests.Session()
    # 1. Регистрация нового устройства
    r = session.post("https://api.cloudflareclient.com/v0i1909051800/reg").json()
    device_id = r["id"]
    token = r["token"]
    private_key = r["config"]["interface"]["addresses"]["private_key"] # Это НЕ то, что нам нужно в итоге
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Привязка лицензии Plus
    payload = {"license": LICENSE}
    update = session.put(f"https://api.cloudflareclient.com/v0i1909051800/reg/{device_id}/account", 
                         headers=headers, json=payload)
    
    if update.status_code == 200:
        print("--- ПОБЕДА! ---")
        print(f"Account Type: PLUS")
        # Генерируем новый конфиг
        config = session.get(f"https://api.cloudflareclient.com/v0i1909051800/reg/{device_id}", headers=headers).json()
        print(f"Твой новый PrivateKey для роутера: {config['config']['interface']['addresses']['private_key']}")
    else:
        print(f"Ошибка: {update.status_code}")
        print(update.text)

if __name__ == "__main__":
    get_warp_plus()
