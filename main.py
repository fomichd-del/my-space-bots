import os
import telebot
import json
from datetime import datetime
from telebot import types

# 🛠 НАСТРОЙКИ (Replit возьмет их из раздела Secrets)
TOKEN = os.getenv('TELEGRAM_TOKEN')
CHANNEL_NAME = '@vladislav_space'

bot = telebot.TeleBot(TOKEN)

# 📂 Функция загрузки созвездий
def load_data():
    try:
        with open('constellations.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Ошибка загрузки JSON: {e}")
        return {}

# 🗓 Функция определения сезона
def get_current_season():
    month = datetime.now().month
    if month in [12, 1, 2]: return "winter"
    if month in [3, 4, 5]: return "spring"
    if month in [6, 7, 8]: return "summer"
    return "autumn"

# 🚀 Стартовая команда
@bot.message_handler(commands=['start'])
def start(message):
    markup = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton("🔭 Что видно сейчас?", callback_data="show_seasonal")
    markup.add(btn)
    
    bot.send_message(
        message.chat.id, 
        f"Привет! ✨ Это бот канала {CHANNEL_NAME}.\nЯ покажу тебе звезды, которые видны именно сегодня!", 
        reply_markup=markup
    )

# 📋 Показ списка по сезону
@bot.callback_query_handler(func=lambda call: call.data == "show_seasonal")
def show_list(call):
    season = get_current_season()
    data = load_data()
    
    # Оставляем только те, что подходят под текущий сезон
    seasonal_consts = {k: v for k, v in data.items() if v.get('season') == season}
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    buttons = [types.InlineKeyboardButton(text=info['name'], callback_data=f"info_{cid}") 
               for cid, info in seasonal_consts.items()]
    markup.add(*buttons)
    
    seasons_ru = {"winter": "зима ❄️", "spring": "весна 🌱", "summer": "лето ☀️", "autumn": "осень 🍂"}
    
    bot.edit_message_text(
        f"Сейчас на улице {seasons_ru[season]}. Посмотри на эти созвездия:",
        call.message.chat.id, 
        call.message.message_id, 
        reply_markup=markup
    )

# ℹ️ Подробная информация
@bot.callback_query_handler(func=lambda call: call.data.startswith('info_'))
def handle_info(call):
    const_id = call.data.split("_")[1]
    data = load_data()
    info = data.get(const_id)
    
    if info:
        text = (
            f"✨ **{info['name']}** ✨\n\n"
            f"🔭 **Описание:** {info['description']}\n"
            f"📜 **Легенда:** {info['history']}\n"
            f"📊 **Сложность:** {info['difficulty']}"
        )
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="show_seasonal"))
        
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, 
                              parse_mode='Markdown', reply_markup=markup)

# 🔥 Запуск бота
if __name__ == "__main__":
    print("Бот запущен и готов к работе! 🛰")
    bot.polling(none_stop=True)

