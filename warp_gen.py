import requests
import json

# ТВОЙ КЛЮЧ
LICENSE = "0I79Gb2U-6C250hoB-0y784opm"

def get_warp_plus():
    # Маскируемся под мобильное приложение, чтобы Cloudflare не ругался
    headers = {
        "User-Agent": "okhttp/3.12.1",
        "Content-Type": "application/json; charset=UTF-8"
    }

    try:
        print("Отправляю запрос на регистрацию...")
        # 1. Регистрация
        response = requests.post("https://api.cloudflareclient.com/v0i1909051800/reg", headers=headers)
        
        if response.status_code != 200:
            print(f"Ошибка регистрации! Код: {response.status_code}")
            print(f"Ответ сервера: {response.text}")
            return

        r = response.json()
        device_id = r["id"]
        token = r["token"]
        
        auth_headers = {
            "Authorization": f"Bearer {token}",
            "User-Agent": "okhttp/3.12.1",
            "Content-Type": "application/json; charset=UTF-8"
        }
        
        print(f"Устройство зарегистрировано (ID: {device_id}). Привязываю лицензию...")

        # 2. Привязка лицензии
        payload = {"license": LICENSE}
        update = requests.put(
            f"https://api.cloudflareclient.com/v0i1909051800/reg/{device_id}/account", 
            headers=auth_headers, 
            json=payload
        )
        
        if update.status_code == 200:
            # 3. Получение финального конфига
            config = requests.get(
                f"https://api.cloudflareclient.com/v0i1909051800/reg/{device_id}", 
                headers=auth_headers
            ).json()
            
            print("\n--- ПОБЕДА! ---")
            print(f"Статус: WARP+ АКТИВИРОВАН")
            print(f"Твой PrivateKey для роутера: {config['config']['interface']['addresses']['private_key']}")
            print("--- --- --- --- ---")
        else:
            print(f"Ошибка привязки ключа! Код: {update.status_code}")
            print(f"Ответ: {update.text}")

    except Exception as e:
        print(f"Произошла ошибка: {e}")

if __name__ == "__main__":
    get_warp_plus()
