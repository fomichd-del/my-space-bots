import time
from datetime import datetime
from telebot import types as tele_types
from database import get_dog_data, update_dog_data, spend_dust, get_user_data
from neural_draw import get_cascade_image # 🟢 Наш новый модуль

DOG_SHOP = {
    "space_helmet": {"name": "Стеклянный шлем", "prompt": "wearing a transparent glowing space helmet", "price": 40},
    "star_suit": {"name": "Скафандр", "prompt": "wearing a stylish miniature silver astronaut suit", "price": 60},
    "cool_glasses": {"name": "Кибер-очки", "prompt": "wearing cool neon futuristic sunglasses", "price": 30},
    "bandana": {"name": "Бандана Орион", "prompt": "wearing a blue silk bandana with white stars", "price": 20}
}

def get_dog_prompt(dog, user_id):
    if dog['status'] == 'dead':
        return "empty dog bed, abandoned futuristic spaceship cabin, lonely atmosphere, realistic photographic style", user_id
    
    base = "macro photography of a realistic fluffy apricot toy poodle dog, in a high-tech cozy spaceship cabin with a window showing stars, 4k, cinematic lighting"
    if dog['level'] < 5: evo = "a tiny cute puppy poodle, sleeping on a soft pillow"
    elif dog['level'] < 12: evo = "an active adolescent poodle, sitting alert and happy"
    else: evo = "a wise adult poodle, sitting at a control panel like a co-pilot"

    if dog['energy'] < 30: state = "tired look, dim lighting, dog is resting"
    else: state = "happy expression, bright warm lighting, sparkling eyes"

    clothes = [DOG_SHOP[k]["prompt"] for k in dog['items'] if k in DOG_SHOP]
    style_prompt = ", ".join(clothes) if clothes else "natural fluffy fur"

    full_prompt = f"{base}, {evo}, {state}, {style_prompt}, photorealistic"
    seed = user_id
    
    return full_prompt, seed

def send_dog_menu(bot, chat_id, user_id):
    dog = get_dog_data(user_id)
    u_data = get_user_data(user_id)
    
    today = datetime.now().strftime("%Y-%m-%d")
    if dog['date'] != today:
        dog['hunger'] -= 20; dog['energy'] -= 25; dog['mood'] -= 15
        dog['date'] = today
        if dog['hunger'] <= 0 or dog['energy'] <= 0: dog['status'] = 'dead'
        update_dog_data(user_id, dog)

    prompt, seed = get_dog_prompt(dog, user_id)
    
    if dog['status'] == 'dead':
        text = "🛰 **СИГНАЛ ПОТЕРЯН**\n\nКомандор, твой верный пес покинул корабль из-за плохого ухода. Каюта пуста..."
        kb = tele_types.InlineKeyboardMarkup().add(tele_types.InlineKeyboardButton("🛰 Вызвать нового щенка (-100 💰)", callback_data="dog_resurrect"))
    else:
        text = (
            f"🐕 **КАЮТА ПИТОМЦА**\n\n"
            f"Уровень: {dog['level']} | Опыт: {dog['xp']}/15\n"
            f"🍖 Сытость: {dog['hunger']}% | 🔋 Энергия: {dog['energy']}%\n"
            f"🎾 Настроение: {dog['mood']}%\n\n"
            f"💰 Пыль: {u_data['spendable_dust']} ед."
        )
        kb = tele_types.InlineKeyboardMarkup(row_width=2)
        kb.add(
            tele_types.InlineKeyboardButton("🍖 Кормить (-5 💰)", callback_data="dog_feed"),
            tele_types.InlineKeyboardButton("💤 Спать (+40 🔋)", callback_data="dog_sleep"),
            tele_types.InlineKeyboardButton("🎾 Играть (-5 💰)", callback_data="dog_play"),
            tele_types.InlineKeyboardButton("👕 Гардероб", callback_data="dog_shop")
        )

    # 🟢 ВЫЗЫВАЕМ КАСКАДНЫЙ ГЕНЕРАТОР
    image_bytes = get_cascade_image(prompt, seed)
    
    if image_bytes:
        bot.send_photo(chat_id, photo=image_bytes, caption=text, parse_mode="Markdown", reply_markup=kb)
    else:
        bot.send_message(chat_id, text + "\n\n⚠️ _Сбой визуализации! Резервные серверы перегружены._", parse_mode="Markdown", reply_markup=kb)

def handle_dog_callback(bot, call):
    user_id = call.from_user.id
    action = call.data.replace("dog_", "")
    dog = get_dog_data(user_id)

    if action == "feed":
        if spend_dust(user_id, 5):
            dog['hunger'] += 30; dog['xp'] += 1
            if dog['xp'] >= 15: dog['level'] += 1; dog['xp'] = 0
            update_dog_data(user_id, dog)
            bot.answer_callback_query(call.id, "🍖 Вкусно! Сытость +30, Опыт +1")
        else: bot.answer_callback_query(call.id, "❌ Нужно 5 пыли!")
    elif action == "sleep":
        dog['energy'] = 100; update_dog_data(user_id, dog)
        bot.answer_callback_query(call.id, "💤 Пес спит в капсуле...")
    elif action == "play":
        if spend_dust(user_id, 5):
            dog['mood'] += 30; dog['energy'] -= 20; update_dog_data(user_id, dog)
            bot.answer_callback_query(call.id, "🎾 Грави-мяч — это весело!")
        else: bot.answer_callback_query(call.id, "❌ Нужно 5 пыли!")
    elif action == "shop":
        text = "🛒 **ГАРДЕРОБ**\n\nКупленные вещи пудель наденет сразу!"
        kb = tele_types.InlineKeyboardMarkup(row_width=1)
        for k, v in DOG_SHOP.items():
            status = "✅" if k in dog['items'] else f"-{v['price']} 💰"
            kb.add(tele_types.InlineKeyboardButton(f"{v['name']} ({status})", callback_data=f"dog_buy_{k}"))
        kb.add(tele_types.InlineKeyboardButton("🔙 Назад", callback_data="dog_back"))
        bot.edit_message_caption(text, call.message.chat.id, call.message.message_id, reply_markup=kb)
        return
    elif action.startswith("buy_"):
        item = action.replace("buy_", "")
        if item in dog['items']: bot.answer_callback_query(call.id, "Уже есть!"); return
        if spend_dust(user_id, DOG_SHOP[item]['price']):
            dog['items'].append(item); update_dog_data(user_id, dog)
            bot.answer_callback_query(call.id, f"🎉 Куплено: {DOG_SHOP[item]['name']}!")
        else: bot.answer_callback_query(call.id, "❌ Мало пыли!")
    elif action == "resurrect":
        if spend_dust(user_id, 100):
            update_dog_data(user_id, {"level": 1, "hunger": 80, "energy": 80, "mood": 80, "items": [], "xp": 0, "date": "", "status": "alive"})
            bot.answer_callback_query(call.id, "🛰 Новый щенок на борту!")
        else: bot.answer_callback_query(call.id, "❌ Нужно 100 пыли!")

    bot.delete_message(call.message.chat.id, call.message.message_id)
    send_dog_menu(bot, call.message.chat.id, user_id)
