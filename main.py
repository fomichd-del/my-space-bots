import os
import sys
import requests
import time
from threading import Thread
from flask import Flask
from draw_map import generate_star_map

def log_print(msg):
    print(msg)
    sys.stdout.flush()

app = Flask('')
@app.route('/')
def home(): return "Система Марти: Режим Инкогнито 🕵️‍♂️"

def run_flask():
    port = int(os.environ.get("PORT", 7860))
    app.run(host='0.0.0.0', port=port)

TOKEN = os.environ.get('TELEGRAM_TOKEN', '').strip()
URL = f"https://api.telegram.org/bot{TOKEN}/"

# Маскируемся под обычный браузер
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def send_msg(chat_id, text, reply_markup=None):
    data = {'chat_id': chat_id, 'text': text, 'parse_mode': 'Markdown'}
    if reply_markup: data['reply_markup'] = reply_markup
    try: requests.post(URL + "sendMessage", json=data, headers=HEADERS, timeout=15)
    except: pass

def start_martin():
    if not TOKEN:
        log_print("❌ КРИТИЧЕСКАЯ ОШИБКА: НЕТ ТОКЕНА")
        return
    
    log_print("📡 [ИНКОГНИТО]: Марти Астроном начал глубокое сканирование...")
    offset = 0
    
    while True:
        try:
            # Пытаемся пробиться с коротким таймаутом, чтобы не висеть долго
            response = requests.get(URL + f"getUpdates?offset={offset}&timeout=10", headers=HEADERS, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("result"):
                    for update in data["result"]:
                        offset = update["update_id"] + 1
                        msg = update.get("message")
                        if not msg: continue
                        
                        chat_id = msg['chat']['id']
                        user_name = msg['from'].get('first_name', 'Космонавт')
                        text = msg.get('text', '')

                        log_print(f"✅ [КОНТАКТ]: Поймал сообщение от {user_name}!")

                        if text == "/start":
                            markup = {
                                "keyboard": [[{"text": "📍 Мое небо", "request_location": True}]],
                                "resize_keyboard": True
                            }
                            send_msg(chat_id, f"Прием, {user_name}! Я Марти. Проверка связи прошла успешно! 🐩🔭", markup)
                        elif "location" in msg:
                            send_msg(chat_id, "🛰 Вижу координаты! Запускаю обсерваторию...")
                            try:
                                path = generate_star_map(msg['location']['latitude'], msg['location']['longitude'], user_name)
                                with open(path, 'rb') as f:
                                    requests.post(URL + "sendPhoto", data={'chat_id': chat_id}, files={'photo': f}, headers=HEADERS, timeout=20)
                            except Exception as e:
                                send_msg(chat_id, "⚠️ Ошибка при отрисовке карты.")
                        else:
                            send_msg(chat_id, "Я тебя слышу! Нажми кнопку 'Мое небо' для карты.")
            else:
                if response.status_code != 409: # Игнорируем конфликты
                    log_print(f"⚠️ Статус ответа: {response.status_code}")

        except Exception as e:
            # Не спамим таймаутами в логи, просто ждем
            if "timeout" not in str(e).lower():
                log_print(f"🔄 Поиск сигнала... ({e})")
            time.sleep(5)

if __name__ == "__main__":
    Thread(target=run_flask, daemon=True).start()
    start_martin()
