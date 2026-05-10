import time
import urllib.parse
import requests
from datetime import datetime
from threading import Thread
from telebot import types as tele_types
from database import get_pet_data, update_pet_data, spend_dust, get_user_data, get_all_users_with_pets

# 🛒 КАТАЛОГ МАГАЗИНА
SHOP_ITEMS = {
    "neon_rocks": {"name": "Светящиеся камни", "prompt": "glowing neon cosmic rocks", "price": 10},
    "alien_castle": {"name": "Замок НЛО", "prompt": "miniature crashed UFO castle", "price": 25},
    "disco_ball": {"name": "Звездный диско-шар", "prompt": "tiny floating space disco ball", "price": 15}
}

# 📡 СЛОВАРЬ НАПОМИНАНИЙ
sent_reminders = {}

def get_dynamic_image_url(pet, user_id):
    if pet['status'] == 'dead':
        prompt = "empty dirty glass terrarium, broken glass, dried moss, dark gloomy lighting, depressing atmosphere, no life"
        return f"https://image.pollinations.ai/prompt/{urllib.parse.quote(prompt)}?width=1024&height=1024&nologo=true&seed={user_id}&nofeed=true"

    base = f"macro photography of {pet['count']} cute alien space snails, {pet['colors']} shells, high-tech glass terrarium"
    
    if pet['clean'] < 30: state = "murky green dirty water, messy environment, withered moss"
    else: state = "clean crystal clear water, glowing neon moss, bubbles"
        
    if pet['level'] < 5: evo = "baby snails"
    elif pet['level'] < 15: evo = "majestic cosmic snails with nebula patterns"
    else: evo = "god-like ancient star snails, galactic aura"
        
    decor = [SHOP_ITEMS[k]["prompt"] for k in pet['items'] if k in SHOP_ITEMS]
    decor_prompt = "decorated with " + " and ".join(decor) if decor else "minimalist glass setup"
        
    eng_prompt = f"{base}, {evo}, {state}, {decor_prompt}, 4k, cinematic lighting"
    seed = int(time.time() / 3600) + user_id
    return f"https://image.pollinations.ai/prompt/{urllib.parse.quote(eng_prompt)}?width=1024&height=1024&nologo=true&seed={seed}&nofeed=true"

def check_daily_decay(pet):
    today = datetime.now().strftime("%Y-%m-%d")
    if pet['date'] != today and pet['status'] == 'alive':
        pet['hunger'] = max(0, pet['hunger'] - 30)
        pet['clean'] = max(0, pet['clean'] - 20)
        pet['happiness'] = max(0, pet['happiness'] - 25)
        pet['feed_count'] = 0
        pet['clean_count'] = 0
        pet['play_count'] = 0
        pet['date'] = today
        if pet['hunger'] <= 0 or pet['clean'] <= 0:
            pet['status'] = 'dead'
    return pet

def send_eco_menu(bot, chat_id, user_id):
    pet = check_daily_decay(get_pet_data(user_id))
    update_pet_data(user_id, pet)
    u_data = get_user_data(user_id)
    url = get_dynamic_image_url(pet, user_id)
    
    if pet['status'] == 'dead':
        text = "💀 **ТРАГЕДИЯ В ЭКО-ОТСЕКЕ**\n\nПилот, из-за ненадлежащего ухода эко-система погибла. Террариум заброшен.\n\nНужна полная дезинфекция!"
        kb = tele_types.InlineKeyboardMarkup()
        kb.add(tele_types.InlineKeyboardButton("🧼 Дезинфекция (-50 💰)", callback_data="eco_sanitize"))
    else:
        # Умножаем стоимость на кол-во улиток
        f_cost, c_cost, p_cost = 2*pet['count'], 3*pet['count'], 2*pet['count']
        text = (
            f"🌿 **ЭКО-ОТСЕК (Жильцов: {pet['count']})**\n"
            f"🧬 Уровень: {pet['level']} | Опыт: {pet['xp']}/10\n"
            f"🔋 Сытость: {pet['hunger']}% _({pet['feed_count']}/3)_\n"
            f"💧 Чистота: {pet['clean']}% _({pet['clean_count']}/3)_\n"
            f"🎾 Радость: {pet['happiness']}% _({pet['play_count']}/3)_\n\n"
            f"💰 _Пыль: {u_data['spendable_dust']} ед._"
        )
        kb = tele_types.InlineKeyboardMarkup(row_width=2)
        kb.add(
            tele_types.InlineKeyboardButton(f"🥬 Кормить (-{f_cost} 💰)", callback_data="eco_feed"),
            tele_types.InlineKeyboardButton(f"🧽 Убрать (-{c_cost} 💰)", callback_data="eco_clean"),
            tele_types.InlineKeyboardButton(f"🎾 Играть (-{p_cost} 💰)", callback_data="eco_play"),
            tele_types.InlineKeyboardButton("🛒 Магазин", callback_data="eco_shop")
        )
        if pet['level'] >= 15:
            if pet['count'] == 1: kb.add(tele_types.InlineKeyboardButton("➕ Найти пару (-300 💰)", callback_data="eco_addpet"))
            elif pet['count'] == 2: kb.add(tele_types.InlineKeyboardButton("🥚 Вывести потомство (-500 💰)", callback_data="eco_addpet"))

    try:
        # 🟢 Скачиваем фото на наш сервер с запасом времени
        response = requests.get(url, timeout=25)
        if response.status_code == 200:
            # 🟢 Отправляем как готовый байт-файл (photo=response.content)
            bot.send_photo(chat_id, photo=response.content, caption=text, parse_mode="Markdown", reply_markup=kb)
        else:
            raise Exception(f"Pollinations вернул статус {response.status_code}")
    except Exception as e:
        print(f"Ошибка загрузки фото террариума: {e}")
        bot.send_message(chat_id, text + "\n\n⚠️ _Сбой визуализации! Нейросеть-художник сейчас перегружена, но параметры террариума сохранены._", parse_mode="Markdown", reply_markup=kb)

def send_shop_menu(bot, chat_id, user_id, message_id):
    pet = get_pet_data(user_id)
    text = f"🛒 **МАГАЗИН ЭКО-ОТСЕКА**\n\nПокупай декорации! Марти установит их, и они появятся на фото!"
    kb = tele_types.InlineKeyboardMarkup(row_width=1)
    for key, data in SHOP_ITEMS.items():
        if key in pet['items']: kb.add(tele_types.InlineKeyboardButton(f"✅ {data['name']} (Куплено)", callback_data="eco_none"))
        else: kb.add(tele_types.InlineKeyboardButton(f"📦 Купить {data['name']} (-{data['price']} 💰)", callback_data=f"eco_buy_{key}"))
    kb.add(tele_types.InlineKeyboardButton("🔙 Назад", callback_data="eco_back"))
    bot.edit_message_caption(caption=text, chat_id=chat_id, message_id=message_id, parse_mode="Markdown", reply_markup=kb)

def handle_eco_callback(bot, call):
    user_id = call.from_user.id
    action = call.data.replace("eco_", "")
    pet = check_daily_decay(get_pet_data(user_id))
    
    # --- НАВИГАЦИЯ ---
    if action == "shop": send_shop_menu(bot, call.message.chat.id, user_id, call.message.message_id); return
    elif action == "back": bot.delete_message(call.message.chat.id, call.message.message_id); send_eco_menu(bot, call.message.chat.id, user_id); return
    elif action == "none": bot.answer_callback_query(call.id, "Уже установлено!"); return

    # --- ВОЗРОЖДЕНИЕ И РАЗМНОЖЕНИЕ ---
    if action == "sanitize":
        if spend_dust(user_id, 50):
            new_pet = {"level": 1, "hunger": 100, "clean": 100, "happiness": 100, "items": [], "xp": 0, "date": datetime.now().strftime("%Y-%m-%d"), "feed_count": 0, "clean_count": 0, "play_count": 0, "count": 1, "status": "alive", "colors": "blue"}
            update_pet_data(user_id, new_pet)
            bot.answer_callback_query(call.id, "🧼 Стерилизация завершена! Заселена новая улитка.", show_alert=True)
        else: bot.answer_callback_query(call.id, "❌ Нужно 50 Пыли!", show_alert=True)
    
    elif action == "addpet":
        cost = 300 if pet['count'] == 1 else 500
        if spend_dust(user_id, cost):
            pet['count'] += 1
            new_color = "red" if pet['count'] == 2 else "purple"
            pet['colors'] += f", {new_color}"
            update_pet_data(user_id, pet)
            bot.answer_callback_query(call.id, "💖 Пополнение в семействе!", show_alert=True)
        else: bot.answer_callback_query(call.id, f"❌ Нужно {cost} Пыли!", show_alert=True)

    # --- МАГАЗИН ---
    elif action.startswith("buy_"):
        item_key = action.replace("buy_", "")
        price = SHOP_ITEMS[item_key]["price"]
        if item_key in pet['items']: bot.answer_callback_query(call.id, "Уже куплено!", show_alert=True); return
        if spend_dust(user_id, price):
            pet['items'].append(item_key)
            update_pet_data(user_id, pet)
            bot.answer_callback_query(call.id, f"🎉 Куплено: {SHOP_ITEMS[item_key]['name']}!", show_alert=True)
        else: bot.answer_callback_query(call.id, f"❌ Нужно {price} Пыли!", show_alert=True)

    # --- УХОД ЗА ПИТОМЦЕМ ---
    limits = {"feed": ("feed_count", "hunger", 30, 2, "🥬"), "clean": ("clean_count", "clean", 40, 3, "🧽"), "play": ("play_count", "happiness", 30, 2, "🎾")}
    
    if action in limits:
        count_key, stat_key, boost, base_cost, emoji = limits[action]
        total_cost = base_cost * pet['count']
        
        if pet[count_key] >= 3:
            bot.answer_callback_query(call.id, "❌ Лимит исчерпан на сегодня!", show_alert=True)
            return
            
        if spend_dust(user_id, total_cost):
            pet[stat_key] += boost
            pet[count_key] += 1
            msg = f"{emoji} Выполнено! +{boost}%"
            
            # Логика Опыта
            if action == "feed":
                if pet['clean'] >= 50 and pet['happiness'] >= 50:
                    pet['xp'] += 1
                    msg += "\n📈 +1 Опыт!"
                    if pet['xp'] >= 10 and pet['level'] < 15:
                        pet['level'] += 1
                        pet['xp'] = 0
                        msg += f"\n🌌 ЭВОЛЮЦИЯ! Уровень {pet['level']}!"
                else:
                    msg += "\n⚠️ Не растет: грязно или грустно!"
            
            update_pet_data(user_id, pet)
            bot.answer_callback_query(call.id, msg, show_alert=True)
        else:
            bot.answer_callback_query(call.id, f"❌ Не хватает Пыли (Нужно {total_cost})!", show_alert=True)
            return

    # Перерисовываем меню
    bot.delete_message(call.message.chat.id, call.message.message_id)
    send_eco_menu(bot, call.message.chat.id, user_id)

# 📡 АВТОНОМНЫЙ РАДАР (НАПОМИНАНИЯ)
def run_reminder_loop(bot):
    def loop():
        while True:
            try:
                users = get_all_users_with_pets()
                today = datetime.now().strftime("%Y-%m-%d")
                
                for user_id, pet_date, hunger, clean in users:
                    if sent_reminders.get(user_id) == today: continue
                        
                    if pet_date != today or hunger <= 40 or clean <= 40:
                        try:
                            text = "🐾 **БОРТОВОЕ НАПОМИНАНИЕ**\n\nПрием! В твоем Эко-отсеке падают показатели. Срочно зайди и наведи порядок, иначе улитка погибнет!"
                            bot.send_message(user_id, text, parse_mode="Markdown")
                            sent_reminders[user_id] = today
                        except: pass 
            except: pass
            
            time.sleep(14400) # Спим 4 часа
            
    Thread(target=loop, daemon=True).start()
