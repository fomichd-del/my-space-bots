import time
import urllib.parse
from datetime import datetime
from telebot import types as tele_types
from database import get_pet_data, update_pet_data, spend_dust, get_user_data

# 🛒 МАГАЗИН (Цена, Тег)
SHOP_ITEMS = {
    "neon_rocks": {"name": "Светящиеся камни", "prompt": "glowing neon cosmic rocks on the bottom", "price": 10},
    "alien_castle": {"name": "Замок НЛО", "prompt": "miniature crashed UFO castle decoration", "price": 25},
    "disco_ball": {"name": "Диско-шар", "prompt": "tiny floating disco ball reflecting lights", "price": 15},
    "space_coral": {"name": "Космический коралл", "prompt": "vibrant alien crystal corals", "price": 20}
}

def get_dynamic_image_url(pet, user_id):
    base = "macro photography of a cute alien space snail in a high-tech glass terrarium, 4k, cinematic lighting"
    
    # 1. Состояние (Грязь и радость)
    if pet['clean'] < 40: state = "murky green dirty water, messy environment, withered alien moss"
    elif pet['happiness'] < 40: state = "snail hiding inside shell, lonely atmosphere, dim lighting"
    else: state = "clean crystal clear water, glowing neon moss, happy active snail, floating bubbles"
        
    # 2. Эволюция (15 уровней)
    if pet['level'] < 4: evo = "tiny baby snail, cute small glowing shell"
    elif pet['level'] < 7: evo = "active young snail, bright neon shell"
    elif pet['level'] < 10: evo = "majestic adult snail, beautiful nebula patterns on shell"
    elif pet['level'] < 13: evo = "large cosmic snail, floating mini asteroids orbiting its shell"
    elif pet['level'] < 15: evo = "giant ancient space snail, starry aura, radiant energy"
    else: evo = "god-like colossal cosmic snail, entire galaxy contained inside its shell, epic sci-fi scale"
        
    # 3. Декорации
    decor = [SHOP_ITEMS[k]["prompt"] for k in pet['items'] if k in SHOP_ITEMS]
    decor_prompt = "decorated with " + " and ".join(decor) if decor else "minimalist glass setup"
        
    eng_prompt = f"{base}, {evo}, {state}, {decor_prompt}"
    seed = int(time.time() / 3600) + user_id # Обновляем раз в час
    return f"https://image.pollinations.ai/prompt/{urllib.parse.quote(eng_prompt)}?width=1024&height=1024&nologo=true&seed={seed}&nofeed=true"

def check_daily_decay(pet):
    today = datetime.now().strftime("%Y-%m-%d")
    if pet['date'] != today:
        # Наступил новый день: сбрасываем статы и лимиты
        pet['hunger'] -= 30
        pet['clean'] -= 20
        pet['happiness'] -= 25
        pet['feed_count'] = 0
        pet['clean_count'] = 0
        pet['play_count'] = 0
        pet['date'] = today
    return pet

def send_eco_menu(bot, chat_id, user_id):
    pet = check_daily_decay(get_pet_data(user_id))
    update_pet_data(user_id, pet) # Сохраняем, если был сброс дня
    u_data = get_user_data(user_id)
    
    url = get_dynamic_image_url(pet, user_id)
    status = "🟢 Счастлива" if pet['hunger'] > 50 and pet['clean'] > 50 and pet['happiness'] > 50 else "🔴 Требует ухода!"
    
    text = (
        f"🌿 **ЭКО-ОТСЕК (Террариум)**\n\n"
        f"🧬 **Уровень:** {pet['level']} (Опыт: {pet['xp']}/10)\n"
        f"📊 **Статус:** {status}\n\n"
        f"🔋 Сытость: {pet['hunger']}% _(Кормежек сегодня: {pet['feed_count']}/3)_\n"
        f"💧 Чистота: {pet['clean']}% _(Уборок сегодня: {pet['clean_count']}/3)_\n"
        f"🎾 Радость: {pet['happiness']}% _(Игр сегодня: {pet['play_count']}/3)_\n\n"
        f"💰 _Пыль: {u_data['spendable_dust']} ед._"
    )
    
    kb = tele_types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        tele_types.InlineKeyboardButton("🥬 Кормить (-2 💰)", callback_data="eco_feed"),
        tele_types.InlineKeyboardButton("🧽 Убрать (-3 💰)", callback_data="eco_clean"),
        tele_types.InlineKeyboardButton("🎾 Играть (-2 💰)", callback_data="eco_play"),
        tele_types.InlineKeyboardButton("🛒 Магазин", callback_data="eco_shop")
    )
    bot.send_photo(chat_id, url, caption=text, parse_mode="Markdown", reply_markup=kb)

def send_shop_menu(bot, chat_id, user_id, message_id):
    pet = get_pet_data(user_id)
    text = f"🛒 **МАГАЗИН ЭКО-ОТСЕКА**\n\nПокупай декорации! Марти установит их, и они появятся на фото!"
    kb = tele_types.InlineKeyboardMarkup(row_width=1)
    for key, data in SHOP_ITEMS.items():
        if key in pet['items']: kb.add(tele_types.InlineKeyboardButton(f"✅ {data['name']}", callback_data="eco_none"))
        else: kb.add(tele_types.InlineKeyboardButton(f"📦 Купить {data['name']} (-{data['price']} 💰)", callback_data=f"eco_buy_{key}"))
    kb.add(tele_types.InlineKeyboardButton("🔙 Назад", callback_data="eco_back"))
    bot.edit_message_caption(caption=text, chat_id=chat_id, message_id=message_id, parse_mode="Markdown", reply_markup=kb)

def handle_eco_callback(bot, call):
    user_id = call.from_user.id
    action = call.data.replace("eco_", "")
    pet = check_daily_decay(get_pet_data(user_id))
    
    if action == "shop": send_shop_menu(bot, call.message.chat.id, user_id, call.message.message_id); return
    elif action == "back": bot.delete_message(call.message.chat.id, call.message.message_id); send_eco_menu(bot, call.message.chat.id, user_id); return
    elif action == "none": bot.answer_callback_query(call.id, "Уже установлено!"); return

    # --- МАГАЗИН ---
    if action.startswith("buy_"):
        item_key = action.replace("buy_", "")
        price = SHOP_ITEMS[item_key]["price"]
        if item_key in pet['items']: bot.answer_callback_query(call.id, "Уже куплено!", show_alert=True); return
        if spend_dust(user_id, price):
            pet['items'].append(item_key)
            update_pet_data(user_id, pet)
            bot.answer_callback_query(call.id, f"🎉 Куплено: {SHOP_ITEMS[item_key]['name']}!", show_alert=True)
            bot.delete_message(call.message.chat.id, call.message.message_id)
            send_eco_menu(bot, call.message.chat.id, user_id) 
        else: bot.answer_callback_query(call.id, f"❌ Нужно {price} Пыли!", show_alert=True)
        return

    # --- УХОД ЗА ПИТОМЦЕМ ---
    limits = {"feed": ("feed_count", "hunger", 30, 2, "🥬"), "clean": ("clean_count", "clean", 40, 3, "🧽"), "play": ("play_count", "happiness", 30, 2, "🎾")}
    
    if action in limits:
        count_key, stat_key, boost, cost, emoji = limits[action]
        
        # 1. Проверка дневного лимита
        if pet[count_key] >= 3:
            bot.answer_callback_query(call.id, "❌ Лимит исчерпан на сегодня!", show_alert=True)
            return
            
        # 2. Проверка пыли
        if spend_dust(user_id, cost):
            pet[stat_key] += boost
            pet[count_key] += 1
            msg = f"{emoji} Выполнено! +{boost}%"
            
            # 3. Логика ОПЫТА (XP) - выдается ТОЛЬКО при кормлении в хороших условиях
            if action == "feed":
                if pet['clean'] >= 50 and pet['happiness'] >= 50:
                    pet['xp'] += 1
                    msg += "\n📈 Улитка получила +1 Опыт!"
                    if pet['xp'] >= 10 and pet['level'] < 15:
                        pet['level'] += 1
                        pet['xp'] = 0
                        msg += f"\n🌌 ЭВОЛЮЦИЯ! Уровень {pet['level']}!"
                else:
                    msg += "\n⚠️ Улитка не растет: ей грязно или грустно!"
            
            update_pet_data(user_id, pet)
            bot.answer_callback_query(call.id, msg, show_alert=True)
        else:
            bot.answer_callback_query(call.id, "❌ Не хватает Звездной Пыли!", show_alert=True)
            return

    bot.delete_message(call.message.chat.id, call.message.message_id)
    send_eco_menu(bot, call.message.chat.id, user_id)
