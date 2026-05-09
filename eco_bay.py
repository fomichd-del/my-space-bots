import time
import urllib.parse
from telebot import types as tele_types
from database import get_pet_data, update_pet_data, spend_dust, get_user_data

# 🛒 КАТАЛОГ МАГАЗИНА (Название вещи, Тег для нейросети, Цена)
SHOP_ITEMS = {
    "neon_rocks": {"name": "Светящиеся камни", "prompt": "glowing neon cosmic rocks on the bottom", "price": 10},
    "alien_castle": {"name": "Замок НЛО", "prompt": "miniature crashed UFO castle decoration", "price": 25},
    "disco_ball": {"name": "Звездный диско-шар", "prompt": "tiny floating disco ball reflecting galaxy lights", "price": 15},
    "space_coral": {"name": "Космический коралл", "prompt": "vibrant alien crystal corals", "price": 20}
}

def get_dynamic_image_url(pet_data, user_id):
    """Генерирует промпт на основе состояния террариума и купленных вещей"""
    base = "macro photography of a cute alien space snail in a high-tech glass terrarium, 4k, cinematic lighting"
    
    # 1. Состояние эко-системы
    if pet_data['hunger'] < 40 or pet_data['clean'] < 40:
        state = "dirty water, messy environment, gloomy dim lighting, withered alien moss"
    elif pet_data['happiness'] < 40:
        state = "snail hiding inside shell, lonely atmosphere, dim lighting"
    else:
        state = "clean crystal clear water, glowing neon moss, happy active snail, floating bubbles"
        
    # 2. Эволюция (Уровень)
    if pet_data['level'] < 3: evo = "small baby snail, tiny glowing shell"
    elif pet_data['level'] < 6: evo = "majestic adult snail, bright nebula shell"
    else: evo = "giant god-like cosmic snail, entire galaxy inside its shell"
        
    # 3. Декорации из Магазина
    decor = []
    for item_key in pet_data['items']:
        if item_key in SHOP_ITEMS:
            decor.append(SHOP_ITEMS[item_key]["prompt"])
            
    decor_prompt = "decorated with " + " and ".join(decor) if decor else "minimalist glass setup"
        
    eng_prompt = f"{base}, {evo}, {state}, {decor_prompt}"
    seed = int(time.time() / 3600) + user_id # Обновляем картинку раз в час или при покупке
    url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(eng_prompt)}?width=1024&height=1024&nologo=true&seed={seed}&nofeed=true"
    return url

def send_eco_menu(bot, chat_id, user_id):
    pet = get_pet_data(user_id)
    u_data = get_user_data(user_id)
    
    # Имитация жизни: параметры падают
    new_hunger = max(0, pet['hunger'] - 5)
    new_clean = max(0, pet['clean'] - 5)
    new_happiness = max(0, pet['happiness'] - 5)
    update_pet_data(user_id, pet['level'], new_hunger, new_clean, new_happiness, pet['items'])
    
    url = get_dynamic_image_url({'level': pet['level'], 'hunger': new_hunger, 'clean': new_clean, 'happiness': new_happiness, 'items': pet['items']}, user_id)
    
    status = "🟢 Счастлива" if new_hunger > 50 and new_clean > 50 and new_happiness > 50 else "🔴 Требует ухода!"
    text = (
        f"🌿 **ЭКО-ОТСЕК (Террариум)**\n\n"
        f"🧬 Уровень: {pet['level']} | 📊 Статус: {status}\n\n"
        f"🔋 Сытость: {new_hunger}%\n"
        f"💧 Чистота: {new_clean}%\n"
        f"🎾 Радость: {new_happiness}%\n\n"
        f"💰 _На борту: {u_data['spendable_dust']} Пыли._"
    )
    
    kb = tele_types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        tele_types.InlineKeyboardButton("🥬 Кормить (-2 💰)", callback_data="eco_feed"),
        tele_types.InlineKeyboardButton("🧽 Убрать (-3 💰)", callback_data="eco_clean"),
        tele_types.InlineKeyboardButton("🎾 Играть (-2 💰)", callback_data="eco_play"),
        tele_types.InlineKeyboardButton("🛒 Магазин", callback_data="eco_shop")
    )
    kb.add(tele_types.InlineKeyboardButton("✨ Погладить (Бесплатно)", callback_data="eco_pet"))
    
    bot.send_photo(chat_id, url, caption=text, parse_mode="Markdown", reply_markup=kb)

def send_shop_menu(bot, chat_id, user_id, message_id):
    pet = get_pet_data(user_id)
    u_data = get_user_data(user_id)
    
    text = f"🛒 **МАГАЗИН ЭКО-ОТСЕКА**\n\n💰 Твоя пыль: {u_data['spendable_dust']}\nПокупай декорации! Марти установит их, и они появятся на фото!"
    
    kb = tele_types.InlineKeyboardMarkup(row_width=1)
    for key, data in SHOP_ITEMS.items():
        if key in pet['items']:
            kb.add(tele_types.InlineKeyboardButton(f"✅ {data['name']} (Установлено)", callback_data="eco_none"))
        else:
            kb.add(tele_types.InlineKeyboardButton(f"📦 Купить {data['name']} (-{data['price']} 💰)", callback_data=f"eco_buy_{key}"))
            
    kb.add(tele_types.InlineKeyboardButton("🔙 Назад к террариуму", callback_data="eco_back"))
    
    # Меняем только текст и кнопки, фото не перерисовываем, чтобы не тратить трафик
    bot.edit_message_caption(caption=text, chat_id=chat_id, message_id=message_id, parse_mode="Markdown", reply_markup=kb)

def handle_eco_callback(bot, call):
    user_id = call.from_user.id
    action = call.data.replace("eco_", "")
    pet = get_pet_data(user_id)
    
    # --- НАВИГАЦИЯ ---
    if action == "shop":
        send_shop_menu(bot, call.message.chat.id, user_id, call.message.message_id)
        return
    elif action == "back":
        bot.delete_message(call.message.chat.id, call.message.message_id)
        send_eco_menu(bot, call.message.chat.id, user_id)
        return
    elif action == "none":
        bot.answer_callback_query(call.id, "Уже установлено в террариум!")
        return

    # --- ПОКУПКА В МАГАЗИНЕ ---
    if action.startswith("buy_"):
        item_key = action.replace("buy_", "")
        price = SHOP_ITEMS[item_key]["price"]
        
        if item_key in pet['items']:
            bot.answer_callback_query(call.id, "Уже куплено!", show_alert=True)
            return
            
        if spend_dust(user_id, price):
            pet['items'].append(item_key)
            update_pet_data(user_id, pet['level'], pet['hunger'], pet['clean'], pet['happiness'], pet['items'])
            bot.answer_callback_query(call.id, f"🎉 Куплено: {SHOP_ITEMS[item_key]['name']}! Подожди, террариум обновляется...", show_alert=True)
            bot.delete_message(call.message.chat.id, call.message.message_id)
            send_eco_menu(bot, call.message.chat.id, user_id) # Перерисовываем с новой картинкой!
        else:
            bot.answer_callback_query(call.id, f"❌ Нужно {price} Звездной Пыли!", show_alert=True)
        return

    # --- УХОД ЗА ПИТОМЦЕМ ---
    msgs = {"feed": ("🥬", "Сытость", 30, 2), "clean": ("🧽", "Чистота", 40, 3), "play": ("🎾", "Радость", 30, 2)}
    
    if action == "pet":
        update_pet_data(user_id, pet['level'], pet['hunger'], pet['clean'], pet['happiness'] + 10, pet['items'])
        bot.answer_callback_query(call.id, "✨ Ты погладил улитку. Ей приятно! Радость +10%")
    elif action in msgs:
        emoji, stat_name, boost, cost = msgs[action]
        if spend_dust(user_id, cost):
            h = pet['hunger'] + boost if action == "feed" else pet['hunger']
            c = pet['clean'] + boost if action == "clean" else pet['clean']
            hap = pet['happiness'] + boost if action == "play" else pet['happiness']
            update_pet_data(user_id, pet['level'], h, c, hap, pet['items'])
            bot.answer_callback_query(call.id, f"{emoji} {stat_name} +{boost}%", show_alert=True)
        else:
            bot.answer_callback_query(call.id, "❌ Не хватает Звездной Пыли!", show_alert=True)
            return

    # Перерисовываем меню
    bot.delete_message(call.message.chat.id, call.message.message_id)
    send_eco_menu(bot, call.message.chat.id, user_id)
