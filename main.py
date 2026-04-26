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
def home(): return "Марти Астроном: Партизанский режим активен! 🐩"

def run_flask():
    port = int(os.environ.get("PORT", 7860))
    app.run(host='0.0.0.0', port=port)

TOKEN = os.environ.get('TELEGRAM_TOKEN', '').strip()
URL = f"https://api.telegram.org/bot{TOKEN}/"

def send_msg(chat_id, text, reply_markup=None):
    data = {'chat_id': chat_id, 'text': text, 'parse_mode': 'Markdown'}
    if reply_markup: data['reply_markup'] = reply_markup
    try: requests.post(URL + "sendMessage", json=data, timeout=10)
    except: pass

def start_martin():
    if not TOKEN:
        log_print("❌ НЕТ ТОКЕНА")
        return
    
    log_print("🚀 [ПАРТИЗАН]: Марти вышел на связь без посредников!")
    offset = 0
    
    while True:
        try:
            # Запрашиваем обновления напрямую через requests (это сложнее заблокировать)
            response = requests.get(URL + f"getUpdates?offset={offset}&timeout=20", timeout=30)
            data = response.json()
            
            if data.get("result"):
                for update in data["result"]:
                    offset = update["update_id"] + 1
                    msg = update.get("message")
                    if not msg: continue
                    
                    chat_id = msg['chat']['id']
                    user_name = msg['from'].get('first_name', 'Космонавт')
                    text = msg.get('text', '')

                    log_print(f"💬 [КОНТАКТ]: Сообщение от {user_name}")

                    if text == "/start":
                        markup = {
                            "keyboard": [[{"text": "📍 Мое небо", "request_location": True}]],
                            "resize_keyboard": True
                        }
                        send_msg(chat_id, f"Привет, {user_name}! Я Марти. Нажми кнопку для карты!", markup)
                    
                    elif "location" in msg:
                        lat = msg['location']['latitude']
                        lon = msg['location']['longitude']
                        log_print(f"📍 [ЛОКАЦИЯ]: Рисую для {user_name}")
                        send_msg(chat_id, "🛰 Секунду, навожу телескопы...")
                        try:
                            path = generate_star_map(lat, lon, user_name)
                            with open(path, 'rb') as f:
                                requests.post(URL + "sendPhoto", data={'chat_id': chat_id}, files={'photo': f}, timeout=20)
                        except Exception as e:
                            log_print(f"❌ ОШИБКА КАРТЫ: {e}")
                            send_msg(chat_id, "⚠️ Ошибка телескопа.")
                    else:
                        send_msg(chat_id, "Прием! Нажми кнопку 'Мое небо' (если нет кнопки — введи /start).")

        except Exception as e:
            if "timeout" not in str(e).lower():
                log_print(f"📡 [СВЯЗЬ]: Поиск сигнала... ({e})")
            time.sleep(2)

if __name__ == "__main__":
    Thread(target=run_flask, daemon=True).start()
    start_martin()
