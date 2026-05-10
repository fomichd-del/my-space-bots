import time
from datetime import datetime
from threading import Thread
from telebot import types as tele_types
from database import get_pet_data, update_pet_data, spend_dust, get_user_data, get_all_users_with_pets
from neural_draw import get_cascade_image # 🟢 Подключаем наш новый каскадный модуль

SHOP_ITEMS = {
    "natural_pebbles": {"name": "Речные камешки", "prompt": "small smooth river pebbles on the bottom", "price": 10},
    "castle_ruin": {"name": "Руины замка", "prompt": "ancient miniature castle ruin decoration", "price": 25},
    "dark_driftwood": {"name": "Темная коряга", "prompt": "natural looking piece of dark driftwood", "price": 15},
    "live_plants": {"name": "Живые растения", "prompt": "vibrant natural freshwater aquatic plants (Java moss, Anubias)", "price": 20}
}

sent_reminders = {}

def get_dynamic_prompt(pet, user_id):
    if pet['status'] == 'dead':
        prompt = "macro photography of an empty dirty glass terrarium, broken glass, dried grey moss, murky water, gloomy dim lighting, depressing realistic look, no life, photorealistic"
        return prompt, user_id

    base = "macro photography of a realistic freshwater aquarium tank, 4k, natural realistic photographic style, cinematic lighting"
    shells_style = "natural realistic brown and beige shells with intricate dark stripes"
    
    if pet['count'] == 1:
        if pet['level'] < 3: evo_details = "tiny newborn size,semi-translucent shell"
        elif pet['level'] < 7: evo_details = "growing adolescent size,clear spiral shell"
        elif pet['level'] < 11: evo_details = "large adult size,detailed patterns"
        elif pet['level'] < 14: evo_details = "mature old size,massive heavy shell"
        else: evo_details = "colossal ancient matriarch size, incredibly complex shell"
        snails_prompt = f"exactly one realistic garden snail (Cornu aspersum), {evo_details}, {shells_style}"
        if pet['clean'] < 30: state_modifier = "murky green dirty water, messy environment"
        elif pet['happiness'] < 30: state_modifier = "snail hiding inside shell, lonely atmosphere"
        else: state_modifier = "crystal clear water, vibrant active snail, floating bubbles"

    elif pet['count'] == 2:
        snails_prompt = f"exactly two realistic garden snails (Cornu aspersum) interacting, both with {shells_style}"
        if pet['clean'] < 30: state_modifier = "murky green dirty water, messy environment"
        elif pet['happiness'] < 30: state_modifier = "snails hiding inside shells, lonely atmosphere"
        else: state_modifier = "crystal clear water, vibrant active snails, floating bubbles"

    else:
        snails_prompt = f"a diverse family of realistic garden snails (Cornu aspersum) (multiple individuals of different sizes), {shells_style}"
        if pet['clean'] < 30: state_modifier = "murky green dirty water, messy environment"
        else: state_modifier = "crystal clear water, vibrant active snails, floating bubbles"

    decor = [SHOP_ITEMS[k]["prompt"] for k in pet['items'] if k in SHOP_ITEMS]
    decor_prompt = "decorated with " + " and ".join(decor) if decor else "minimalist glass setup with only a few river pebbles on the bottom"
        
    full_prompt = f"{base}, {snails_prompt}, {state_modifier}, {decor_prompt}, photorealistic"
    seed = int(time.time() / 3600) + user_id 
    
    return full_prompt, seed # Возвращаем текст промпта и зерно, а не готовую ссылку

def check_daily_decay(pet):
    today = datetime.now().strftime("%Y-%m-%d")
    if pet['date'] != today and pet['status'] == 'alive':
        pet['hunger'] = max(0, pet['hunger'] - 30)
        pet['clean'] = max(0, pet['clean'] - 20)
        pet['happiness'] = max(0, pet['happiness'] - 25)
        pet['feed_count'] = 0; pet['clean_count'] = 0; pet['play_count'] = 0
        pet['date'] = today
        if pet['hunger'] <= 0 or pet['clean'] <= 0: pet['status'] = 'dead'
    return pet

def send_eco_menu(bot, chat_id, user_id):
    pet = check_daily_decay(get_pet_data(user_id))
    update_pet_data(user_id, pet)
    u_data = get_user_data(user_id)
    
    prompt, seed = get_dynamic_prompt(pet, user_id)
    
    if pet['status'] == 'dead':
        text = "💀 **ТРАГЕДИЯ В ЭКО-ОТСЕКЕ**\n\nПилот, из-за ненадлежащего ухода эко-система погибла. Террариум заброшен.\n\nНужна полная дезинфекция!"
        kb = tele_types.InlineKeyboardMarkup().add(tele_types.InlineKeyboardButton("🧼 Дезинфекция (-50 💰)", callback_data="eco_sanitize"))
    else:
        f_cost, c_cost, p_cost = 2*pet['count'], 3*pet['count'], 2*pet['count']
        status = "🟢 Счастлива" if pet['hunger'] > 50 and pet['clean'] > 50 and pet['happiness'] > 50 else "🔴 Требует ухода!"
        family_status = "Одинокая улитка"
        if pet['count'] == 2: family_status = "Пара улиток"
        elif pet['count'] >= 3: family_status = "Семья улиток"

        text = (
            f"🌿 **ЭКО-ОТСЕК (Уровень: {pet['level']})**\n\n"
            f"Опыт: {pet['xp']}/10 | Статус: {status}\n"
            f"🐌 Жильцы: **{family_status}**\n\n"
            f"🔋 Сытость: {pet['hunger']}% _({pet['feed_count']}/3)_\n"
            f"💧 Чистота: {pet['clean']}% _({pet['clean_count']}/3)_\n"
            f"🎾 Радость: {pet['happiness']}% _({pet['play_count']}/3)_\n\n"
            f"💰 _Твой баланс: {u_data['spendable_dust']} пыли._"
        )
        kb = tele_types.InlineKeyboardMarkup(row_width=2)
        kb.add(
            tele_types.InlineKeyboardButton(f"🥬 Кормить (-{f_cost} 💰)", callback_data="eco_feed"),
            tele_types.InlineKeyboardButton(f"🧽 Убрать (-{c_cost} 💰)", callback_data="eco_clean"),
            tele_types.InlineKeyboardButton(f"🎾 Играть (-{p_cost} 💰)", callback_data="eco_play"),
            tele_types.InlineKeyboardButton("🛒 Магазин", callback_data="eco_shop")
        )
        if pet['level'] >= 15:
            if pet['count'] == 1: kb.add(tele_types.InlineKeyboardButton("➕ Найти пару (-200 💰)", callback_data="eco_addpet"))
            elif pet['count'] == 2: kb.add(tele_types.InlineKeyboardButton("🥚 Создать семью (-300 💰)", callback_data="eco_addpet"))

    # 🟢 ВЫЗЫВАЕМ КАСКАДНЫЙ ГЕНЕРАТОР
    image_bytes = get_cascade_image(prompt, seed)
    
    if image_bytes:
        bot.send_photo(chat_id, photo=image_bytes, caption=text, parse_mode="Markdown", reply_markup=kb)
    else:
        bot.send_message(chat_id, text + "\n\n⚠️ _Сбой визуализации! Все резервные нейросети перегружены._", parse_mode="Markdown", reply_markup=kb)

def send_shop_menu(bot, chat_id, user_id, message_id):
    pet = get_pet_data(user_id)
    text = f"🛒 **МАГАЗИН ЭКО-ОТСЕКА**\n\n💰 Твоя пыль: {get_user_data(user_id)['spendable_dust']}\nПокупай натуральные декорации! Они появятся на фото аквариума!"
    kb = tele_types.InlineKeyboardMarkup(row_width=1)
    for key, data in SHOP_ITEMS.items():
        if key in pet['items']: kb.add(tele_types.InlineKeyboardButton(f"✅ {data['name']} (Установлено)", callback_data="eco_none"))
        else: kb.add(tele_types.InlineKeyboardButton(f"📦 Купить {data['name']} (-{data['price']} 💰)", callback_data=f"eco_buy_{key}"))
    kb.add(tele_types.InlineKeyboardButton("🔙 Назад к террариуму", callback_data="eco_back"))
    bot.edit_message_caption(caption=text, chat_id=chat_id, message_id=message_id, parse_mode="Markdown", reply_markup=kb)

def handle_eco_callback(bot, call):
    user_id = call.from_user.id
    action = call.data.replace("eco_", "")
    pet = check_daily_decay(get_pet_data(user_id))
    
    if action == "shop": send_shop_menu(bot, call.message.chat.id, user_id, call.message.message_id); return
    elif action == "back": bot.delete_message(call.message.chat.id, call.message.message_id); send_eco_menu(bot, call.message.chat.id, user_id); return
    elif action == "none": bot.answer_callback_query(call.id, "Уже установлено в террариум!"); return
    elif action == "sanitize":
        if spend_dust(user_id, 50):
            update_pet_data(user_id, {"level": 1, "hunger": 100, "clean": 100, "happiness": 100, "items": [], "xp": 0, "date": datetime.now().strftime("%Y-%m-%d"), "feed_count": 0, "clean_count": 0, "play_count": 0, "count": 1, "status": "alive", "colors": "blue"})
            bot.answer_callback_query(call.id, "🧼 Стерилизация завершена!", show_alert=True)
        else: bot.answer_callback_query(call.id, "❌ Нужно 50 Пыли!", show_alert=True)
    elif action == "addpet":
        if pet['level'] < 15: bot.answer_callback_query(call.id, "❌ Доступно с 15 уровня!", show_alert=True); return
        cost = 200 if pet['count'] == 1 else 300
        if spend_dust(user_id, cost):
            pet['count'] += 1
            update_pet_data(user_id, pet)
            bot.answer_callback_query(call.id, "💖 Пополнение в семействе!", show_alert=True)
        else: bot.answer_callback_query(call.id, f"❌ Нужно {cost} Пыли!", show_alert=True); return
    elif action.startswith("buy_"):
        item_key = action.replace("buy_", "")
        if item_key not in SHOP_ITEMS: return
        price = SHOP_ITEMS[item_key]["price"]
        if item_key in pet['items']: bot.answer_callback_query(call.id, "Уже куплено!", show_alert=True); return
        if spend_dust(user_id, price):
            pet['items'].append(item_key)
            update_pet_data(user_id, pet)
            bot.answer_callback_query(call.id, f"🎉 Куплено: {SHOP_ITEMS[item_key]['name']}!", show_alert=True)
        else: bot.answer_callback_query(call.id, f"❌ Не хватает Пыли!", show_alert=True); return

    limits = {"feed": ("feed_count", "hunger", 30, 2, "🥬"), "clean": ("clean_count", "clean", 40, 3, "🧽"), "play": ("play_count", "happiness", 30, 2, "🎾")}
    if action in limits:
        count_key, stat_key, boost, base_cost, emoji = limits[action]
        total_cost = base_cost * pet['count']
        if pet[count_key] >= 3: bot.answer_callback_query(call.id, "❌ Лимит на сегодня!", show_alert=True); return
        if spend_dust(user_id, total_cost):
            pet[stat_key] += boost; pet[count_key] += 1
            msg = f"{emoji} Выполнено! +{boost}%"
            if action == "feed":
                if pet['clean'] >= 50 and pet['happiness'] >= 50:
                    pet['xp'] += 1; msg += "\n📈 +1 Опыт!"
                    if pet['xp'] >= 10: pet['level'] += 1; pet['xp'] = 0; msg += f"\n🌌 Уровень {pet['level']}!"
                else: msg += "\n⚠️ Не растет: грязно или грустно!"
            update_pet_data(user_id, pet)
            bot.answer_callback_query(call.id, msg, show_alert=True)
        else: bot.answer_callback_query(call.id, f"❌ Не хватает Пыли!", show_alert=True); return

    bot.delete_message(call.message.chat.id, call.message.message_id)
    send_eco_menu(bot, call.message.chat.id, user_id)

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
                            bot.send_message(user_id, "🐾 **БОРТОВОЕ НАПОМИНАНИЕ**\n\nПрием! В твоем Эко-отсеке падают показатели. Срочно наводи порядок!", parse_mode="Markdown")
                            sent_reminders[user_id] = today
                        except: pass 
            except: pass
            time.sleep(14400)
    Thread(target=loop, daemon=True).start()
