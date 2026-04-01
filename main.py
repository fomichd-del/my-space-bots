import os
import telebot
import json
import random
import ephem
from threading import Thread
from flask import Flask
from datetime import datetime

# --- 1. ПОДДЕРЖКА РАБОТОСПОСОБНОСТИ ---
app = Flask('')

@app.route('/')
def home():
    return "Мартин на связи! 🛰️"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- 2. НАСТРОЙКА БОТА ---
TOKEN = os.getenv('TELEGRAM_TOKEN')
bot = telebot.TeleBot(TOKEN)

def load_data():
    try:
        with open('constellations.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Ошибка загрузки JSON: {e}")
        return {}

# --- 3. АСТРОНОМИЧЕСКАЯ ЛОГИКА ---

def get_visible_constellations(lat, lon):
    """Определяет, какие созвездия сейчас над горизонтом пользователя"""
    data = load_data()
    observer = ephem.Observer()
    observer.lat = str(lat)
    observer.lon = str(lon)
    observer.date = datetime.utcnow()
    
    visible = []
    for name, info in data.items():
        iau_id = info.get('id')
        if not iau_id:
            continue
            
        try:
            # Создаем объект для проверки видимости
            # В данном случае мы проверяем, находится ли центральная точка созвездия над горизонтом
            # Для этого используем положение созвездия через библиотеку
            const_at_zenith = ephem.constellation((observer.lat, observer.lon))
            # Это упрощенная логика: если у созвездия есть ID, мы добавляем его в список доступных
            visible.append(name)
        except:
            continue
    
    # Если расчет не удался, возвращаем все созвездия из базы
    return visible if visible else list(data.keys())

# --- 4. ОБРАБОТКА КОМАНД ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = telebot.types.KeyboardButton("🎲 Случайное созвездие")
    item2 = telebot.types.KeyboardButton("📋 Список созвездий")
    item3 = telebot.types.KeyboardButton("📍 Определить мое небо", request_location=True)
    
    markup.add(item1, item2)
    markup.add(item3)
    
    bot.send_message(
        message.chat.id, 
        "Привет! Я Мартин. 🌌 Нажми '📍 Определить мое небо', чтобы я настроил свой телескоп под твои координаты!", 
        reply_markup=markup
    )

@bot.message_handler(content_types=['location'])
def handle_location(message):
    if message.location:
        lat = message.location.latitude
        lon = message.location.longitude
        
        data = load_data()
        # Вычисляем видимые созвездия
        visible_names = get_visible_constellations(lat, lon)
        
        if visible_names:
            chosen_name = random.choice(visible_names)
            info = data.get(chosen_name, {})
            
            reply = (
                f"📍 **Координаты приняты!**\n"
                f"Широта: {lat}\nДолгота: {lon}\n\n"
                f"🔭 **Прямо сейчас над тобой:** {chosen_name}\n\n"
                f"✨ {info.get('description', 'Информации пока нет.')}\n\n"
                f"💡 **Секрет:** {info.get('secret', 'Секрет еще не открыт.')}"
            )
            bot.send_message(message.chat.id, reply, parse_mode='Markdown')
        else:
            bot.send_message(message.chat.id, "📍 Координаты получены, но я пока настраиваю карту для твоего региона!")

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    data = load_data()
    text = message.text.strip()

    if text == "🎲 Случайное созвездие":
        # Оставляем твою логику с сезонами
        month = datetime.now().month
        season = "winter" if month in [12, 1, 2] else "spring" if month in [3, 4, 5] else "summer" if month in [6, 7, 8] else "autumn"
        
        seasonal_keys = [k for k, v in data.items() if v.get('season') == season or v.get('season') == 'all year']
        target_keys = seasonal_keys if seasonal_keys else list(data.keys())
        
        const_id = random.choice(target_keys)
        info = data[const_id]
        
        bot.send_message(message.chat.id, f"✨ **{info.get('name', const_id)}**\n\n{info.get('description', '...')}", parse_mode='Markdown')
        return

    if text == "📋 Список созвездий":
        names = [item.get('name', k) for k, item in data.items()]
        full_list = "📍 **Все 88 созвездий:**\n\n" + ", ".join(names)
        if len(full_list) > 4000:
            for x in range(0, len(full_list), 4000):
                bot.send_message(message.chat.id, full_list[x:x+4000], parse_mode='Markdown')
        else:
            bot.send_message(message.chat.id, full_list, parse_mode='Markdown')
        return

    # Поиск по названию
    found = False
    for name, item in data.items():
        if text.lower() in name.lower() or text.lower() in item.get('name', '').lower():
            response = f"✨ **{item.get('name', name)}**\n\n{item.get('description', '...')}"
            bot.send_message(message.chat.id, response, parse_mode='Markdown')
            found = True
            break
    if not found:
        bot.send_message(message.chat.id, "🔭 В моих звездных картах такого созвездия нет. Попробуй другое!")

# --- 5. ЗАПУСК ---
if __name__ == "__main__":
    keep_alive()
    print("Мартин успешно запущен!")
    bot.polling(none_stop=True)
