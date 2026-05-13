import time
from datetime import datetime
from telebot import types as tele_types
from database import (get_dog_data, update_dog_data, spend_dust, get_user_data, 
                      equip_dog_item, unequip_dog_item, process_dog_walk) # 🟢 Добавлены новые функции
from neural_draw import get_cascade_image 

# 🛒 РАСШИРЕННЫЙ МАГАЗИН (15 ПРЕДМЕТОВ)
DOG_SHOP = {
    "space_helmet": {"name": "Стеклянный шлем", "prompt": "wearing a transparent glowing space helmet", "price": 40},
    "star_suit": {"name": "Скафандр", "prompt": "wearing a stylish miniature silver astronaut suit", "price": 60},
    "cool_glasses": {"name": "Кибер-очки", "prompt": "wearing cool neon futuristic sunglasses", "price": 30},
    "bandana": {"name": "Бандана Орион", "prompt": "wearing a blue silk bandana with white stars", "price": 20},
    "laser_collar": {"name": "Лазерный ошейник", "prompt": "wearing a glowing laser-neon collar", "price": 25},
    "pilot_cap": {"name": "Кепка пилота", "prompt": "wearing a small leather pilot aviator hat", "price": 35},
    "nebula_scarf": {"name": "Шарф Небула", "prompt": "wearing a cosmic purple flowing scarf", "price": 15},
    "cyber_paws": {"name": "Кибер-лапы", "prompt": "having robotic high-tech boots on paws", "price": 45},
    "galaxy_crown": {"name": "Корона Галактики", "prompt": "wearing a floating golden crown of tiny stars", "price": 80},
    "steampunk_goggles": {"name": "Стимпанк-очки", "prompt": "wearing vintage brass steampunk goggles", "price": 30},
    "neon_harness": {"name": "Неоновая сбруя", "prompt": "wearing a bright neon green tactical harness", "price": 40},
    "comet_bowtie": {"name": "Галстук-комета", "prompt": "wearing a glowing cosmic bowtie", "price": 20},
    "radar_monocle": {"name": "Монокль-радар", "prompt": "wearing a high-tech glowing radar monocle", "price": 50},
    "alien_antenna": {"name": "Антенны пришельца", "prompt": "having funny green alien head antennas", "price": 15},
    "astro_boots": {"name": "Астро-ботинки", "prompt": "wearing miniature white moon boots", "price": 35},
      # --- ЮВЕЛИРКА И ЦЕПОЧКИ ---
    "heavy_gold_chain": {"name": "Золотая цепь", "prompt": "wearing a thick heavy gold rapper chain with a bone pendant", "price": 55},
    "diamond_collar": {"name": "Бриллиантовый ошейник", "prompt": "wearing a sparkling luxury diamond-encrusted collar", "price": 90},
    "star_pendant": {"name": "Кулон Полярная звезда", "prompt": "wearing a glowing blue star-shaped pendant on a silver chain", "price": 30},

    # --- КОСМИЧЕСКОЕ СНАРЯЖЕНИЕ ---
    "warp_jetpack": {"name": "Варп-ранец", "prompt": "having a small high-tech jetpack with blue plasma flames on the back", "price": 70},
    "saturn_ring": {"name": "Кольцо Сатурна", "prompt": "having a holographic golden planetary ring glowing around the neck", "price": 45},
    "plasma_cloak": {"name": "Плазменный плащ", "prompt": "wearing a translucent flowing cape made of blue nebula energy", "price": 65},
    "ufo_hat": {"name": "Шапка-тарелка", "prompt": "wearing a tiny funny glowing UFO flying saucer as a hat", "price": 40},

    # --- ГЕЙМЕРСКИЕ ПРИКОЛЫ (PS5 / VR) ---
    "vr_visor_2": {"name": "Визор VR-Орион", "prompt": "wearing a miniature white PSVR2-style virtual reality headset", "price": 50},
    "dual_aura": {"name": "Аура Контроллера", "prompt": "surrounded by a white and blue glowing aura like a DualSense", "price": 25},

    # --- ПРОФЕССИОНАЛЬНЫЙ ЮМОР (СТОМАТОЛОГИЯ) ---
    "brilliant_smile": {"name": "Ослепительная улыбка", "prompt": "showing a funny wide sparkling white smile with diamond glints", "price": 100},
    "dentist_mirror": {"name": "Зеркало Космо-Врача", "prompt": "holding a small futuristic dental mirror in its mouth", "price": 15},

    # --- ПРИКОЛЫ И КОСТЮМЫ ---
    "detective_pipe": {"name": "Трубка Шерлока", "prompt": "holding a classic wooden detective pipe in its mouth", "price": 20},
    "dragon_wings": {"name": "Крылья Дракона", "prompt": "having small scaly black dragon wings on the back", "price": 75},
    "taco_suit": {"name": "Костюм Тако", "prompt": "wearing a hilarious soft taco shell costume around the body", "price": 35},
    "thug_beanie": {"name": "Шапка Thug Life", "prompt": "wearing a black knitted beanie with 'ORION' text", "price": 15},
    "cosmic_boots": {"name": "Луноходы", "prompt": "wearing four glowing neon blue protective space boots on paws", "price": 40},
    "chef_hat": {"name": "Колпак Кока", "prompt": "wearing a tall white chef hat and a small red scarf", "price": 20},
    "holographic_wings": {"name": "Крылья Ангела", "prompt": "having large glowing holographic white angel wings", "price": 85},
    "monocle_tophat": {"name": "Джентльмен", "prompt": "wearing a small black top hat and a golden monocle over one eye", "price": 50},
    "crown_of_light": {"name": "Легендарный Венец", "prompt": "wearing a majestic floating crown made of pure solar light", "price": 150}

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

    # 👕 ТЕПЕРЬ ПРОМПТ ЗАВИСИТ ТОЛЬКО ОТ НАДЕТЫХ ВЕЩЕЙ (EQUIPPED)
    equipped_items = dog.get('equipped', [])
    clothes = [DOG_SHOP[k]["prompt"] for k in equipped_items if k in DOG_SHOP]
    style_prompt = ", ".join(clothes) if clothes else "natural fluffy fur"

    full_prompt = f"{base}, {evo}, {state}, {style_prompt}, photorealistic"
    return full_prompt, user_id

def send_dog_menu(bot, chat_id, user_id):
    dog = get_dog_data(user_id)
    u_data = get_user_data(user_id)
    
    # Синхронизация по времени Чернигова
    from database import get_ship_date
    today = get_ship_date() 
    
    if dog['date'] != today:
        dog['hunger'] -= 20; dog['energy'] -= 25; dog['mood'] -= 15
        dog['date'] = today
        if dog['hunger'] <= 0 or dog['energy'] <= 0: dog['status'] = 'dead'
        update_dog_data(user_id, dog)

    prompt, seed = get_dog_prompt(dog, user_id)
    
    if dog['status'] == 'dead':
        text = "🛰 **СИГНАЛ ПОТЕРЯН**\n\nКомандор, твой верный пес покинул корабль. Каюта пуста..."
        kb = tele_types.InlineKeyboardMarkup().add(tele_types.InlineKeyboardButton("🛰 Вызвать нового щенка (-100 💰)", callback_data="dog_resurrect"))
    else:
        # Список надетых вещей для текста
        equipped_names = [DOG_SHOP[k]['name'] for k in dog.get('equipped', []) if k in DOG_SHOP]
        style_info = ", ".join(equipped_names) if equipped_names else "Ничего не надето"
        
        text = (
            f"🐕 **КАЮТА ПИТОМЦА**\n\n"
            f"Уровень: {dog['level']} | Опыт: {dog['xp']}/15\n"
            f"🍖 Сытость: {dog['hunger']}% | 🔋 Энергия: {dog['energy']}%\n"
            f"🎾 Настроение: {dog['mood']}%\n"
            f"👕 Надето: {style_info}\n\n"
            f"💰 Пыль: {u_data['spendable_dust']} ед."
        )
        kb = tele_types.InlineKeyboardMarkup(row_width=2)
        kb.add(
            tele_types.InlineKeyboardButton("🍖 Кормить (-5 💰)", callback_data="dog_feed"),
            tele_types.InlineKeyboardButton("💤 Спать (+40 🔋)", callback_data="dog_sleep"),
            tele_types.InlineKeyboardButton("🎾 Играть (-5 💰)", callback_data="dog_play"),
            tele_types.InlineKeyboardButton("🚀 Выгулять (-10 💰)", callback_data="dog_walk"), # 🆕
            tele_types.InlineKeyboardButton("👕 Гардероб", callback_data="dog_wardrobe"), # 🆕
            tele_types.InlineKeyboardButton("🛒 Магазин", callback_data="dog_shop") # 🆕
        )

    image_bytes = get_cascade_image(prompt, seed)
    if image_bytes:
        bot.send_photo(chat_id, photo=image_bytes, caption=text, parse_mode="Markdown", reply_markup=kb)
    else:
        bot.send_message(chat_id, text + "\n\n⚠️ _Сбой визуализации!_", parse_mode="Markdown", reply_markup=kb)

def handle_dog_callback(bot, call):
    user_id = call.from_user.id
    action = call.data.replace("dog_", "")
    dog = get_dog_data(user_id)

    if action == "feed":
        if spend_dust(user_id, 5):
            dog['hunger'] = min(100, dog['hunger'] + 30); dog['xp'] += 1
            if dog['xp'] >= 15: dog['level'] += 1; dog['xp'] = 0
            update_dog_data(user_id, dog)
            bot.answer_callback_query(call.id, "🍖 Вкусно! Сытость +30, Опыт +1")
        else: bot.answer_callback_query(call.id, "❌ Нужно 5 пыли!")

    elif action == "sleep":
        dog['energy'] = 100; update_dog_data(user_id, dog)
        bot.answer_callback_query(call.id, "💤 Пес спит в капсуле...")

    elif action == "play":
        if spend_dust(user_id, 5):
            dog['mood'] = min(100, dog['mood'] + 30); dog['energy'] -= 20; update_dog_data(user_id, dog)
            bot.answer_callback_query(call.id, "🎾 Грави-мяч — это весело!")
        else: bot.answer_callback_query(call.id, "❌ Нужно 5 пыли!")

    elif action == "walk": # 🆕 Выгул
        res = process_dog_walk(user_id)
        if res == "low_dust": bot.answer_callback_query(call.id, "❌ Нужно 10 пыли!")
        elif res == "error": bot.answer_callback_query(call.id, "❌ Ошибка систем.")
        else:
            bonus = f" Найдено {res} XP!" if isinstance(res, int) else ""
            bot.answer_callback_query(call.id, f"🚀 Прогулка завершена! Счастье и Энергия в норме.{bonus}", show_alert=True)

    elif action == "wardrobe": # 🆕 Гардероб
        text = "👕 **ГАРДЕРОБ МАРТИ**\n\nЗдесь можно надеть или снять купленные вещи:"
        kb = tele_types.InlineKeyboardMarkup(row_width=1)
        for item_key in dog['items']:
            name = DOG_SHOP[item_key]['name']
            is_equipped = item_key in dog.get('equipped', [])
            btn_text = f"❌ Снять {name}" if is_equipped else f"✅ Надеть {name}"
            kb.add(tele_types.InlineKeyboardButton(btn_text, callback_data=f"dog_toggle_{item_key}"))
        kb.add(tele_types.InlineKeyboardButton("🔙 Назад", callback_data="dog_back"))
        bot.edit_message_caption(text, call.message.chat.id, call.message.message_id, reply_markup=kb)
        return

    elif action.startswith("toggle_"): # 🆕 Переключатель
        item = action.replace("toggle_", "")
        if item in dog.get('equipped', []): unequip_dog_item(user_id, item)
        else: equip_dog_item(user_id, item)
        bot.answer_callback_query(call.id, "Стиль обновлен!")
        # Возвращаемся в гардероб для удобства
        call.data = "dog_wardrobe"
        handle_dog_callback(bot, call)
        return

    elif action == "shop":
        text = "🛒 **МАГАЗИН АКАДЕМИИ**\n\nНовые вещи появятся в гардеробе!"
        kb = tele_types.InlineKeyboardMarkup(row_width=2)
        for k, v in DOG_SHOP.items():
            if k not in dog['items']:
                kb.add(tele_types.InlineKeyboardButton(f"{v['name']} ({v['price']}💰)", callback_data=f"dog_buy_{k}"))
        kb.add(tele_types.InlineKeyboardButton("🔙 Назад", callback_data="dog_back"))
        bot.edit_message_caption(text, call.message.chat.id, call.message.message_id, reply_markup=kb)
        return

    elif action.startswith("buy_"):
        item = action.replace("buy_", "")
        if spend_dust(user_id, DOG_SHOP[item]['price']):
            dog['items'].append(item); update_dog_data(user_id, dog)
            bot.answer_callback_query(call.id, f"🎉 Куплено: {DOG_SHOP[item]['name']}!")
        else: bot.answer_callback_query(call.id, "❌ Мало пыли!")

    elif action == "resurrect":
        if spend_dust(user_id, 100):
            update_dog_data(user_id, {"level": 1, "hunger": 80, "energy": 80, "mood": 80, "items": [], "equipped": [], "xp": 0, "date": "", "status": "alive"})
            bot.answer_callback_query(call.id, "🛰 Новый щенок на борту!")
        else: bot.answer_callback_query(call.id, "❌ Нужно 100 пыли!")

    # Обновление меню
    try: bot.delete_message(call.message.chat.id, call.message.message_id)
    except: pass
    send_dog_menu(bot, call.message.chat.id, user_id)
