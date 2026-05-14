import time
from datetime import datetime
from telebot import types as tele_types
from database import (get_dog_data, update_dog_data, spend_dust, get_user_data, 
                      equip_dog_item, unequip_dog_item, process_dog_walk) # 🟢 Добавлены новые функции
from neural_draw import get_cascade_image 

# 🛒 РАСШИРЕННЫЙ МАГАЗИН (15 ПРЕДМЕТОВ)
DOG_SHOP = {
    # --- БАЗОВАЯ КОСМИЧЕСКАЯ ЭКИПИРОВКА ---
    "space_helmet": {"name": "Стеклянный шлем", "prompt": "head completely enclosed inside a clear thick glass astronaut bubble helmet, glowing neon reflections on the glass visor", "price": 40},
    "star_suit": {"name": "Скафандр", "prompt": "explicitly wearing a full-body thick silver sci-fi astronaut spacesuit, bulky futuristic armor panels completely covering the torso and legs", "price": 60},
    "cool_glasses": {"name": "Кибер-очки", "prompt": "wearing thick neon futuristic cyberpunk sunglasses strapped tightly over the eyes, glowing lenses", "price": 30},
    "bandana": {"name": "Бандана Орион", "prompt": "wearing a thick blue cloth bandana with white stars tied tightly around the neck, clearly visible fabric", "price": 20},
    "laser_collar": {"name": "Лазерный ошейник", "prompt": "wearing a thick bright glowing neon laser collar tightly wrapped around the neck, radiating strong colorful light", "price": 25},
    "pilot_cap": {"name": "Кепка пилота", "prompt": "physically wearing a vintage brown leather aviator pilot hat covering the head, strapped tightly under the chin", "price": 35},
    "nebula_scarf": {"name": "Шарф Небула", "prompt": "wearing a thick, long, flowing cosmic purple scarf wrapped heavily around the neck and shoulders", "price": 15},
    "cyber_paws": {"name": "Кибер-лапы", "prompt": "explicitly wearing heavy robotic high-tech metallic boots on all four paws, glowing mechanical joints clearly visible", "price": 45},
    "galaxy_crown": {"name": "Корона Галактики", "prompt": "wearing a large highly detailed golden crown physically resting on top of the head, surrounded by floating glowing stars", "price": 80},
    "steampunk_goggles": {"name": "Стимпанк-очки", "prompt": "wearing heavy brass vintage steampunk goggles strapped tightly over the eyes, thick leather straps", "price": 30},
    "neon_harness": {"name": "Неоновая сбруя", "prompt": "explicitly wearing a thick bright neon green tactical military harness strapped tightly around the chest and torso", "price": 40},
    "comet_bowtie": {"name": "Галстук-комета", "prompt": "wearing a large bright glowing cosmic bowtie attached firmly to the collar under the chin, radiating light", "price": 20},
    "radar_monocle": {"name": "Монокль-радар", "prompt": "wearing a glowing high-tech cybernetic radar monocle physically attached over one eye", "price": 50},
    "alien_antenna": {"name": "Антенны пришельца", "prompt": "wearing a thick headband with two glowing green alien antennas physically sitting on top of the head", "price": 15},
    "astro_boots": {"name": "Астро-ботинки", "prompt": "explicitly wearing thick puffy white astronaut moon boots covering all four paws", "price": 35},
    
    # --- ЮВЕЛИРКА И ЦЕПОЧКИ ---
    "heavy_gold_chain": {"name": "Золотая цепь", "prompt": "wearing an extremely thick, heavy, oversized gold rapper chain necklace physically hanging around the neck, large shiny gold bone pendant", "price": 55},
    "diamond_collar": {"name": "Бриллиантовый ошейник", "prompt": "wearing a very thick, extremely shiny luxury diamond-encrusted collar wrapped tightly around the neck, sparkling heavily", "price": 90},
    "star_pendant": {"name": "Кулон Полярная звезда", "prompt": "wearing a large glowing blue star-shaped pendant on a highly visible thick silver chain hanging around the neck", "price": 30},

    # --- КОСМИЧЕСКОЕ СНАРЯЖЕНИЕ ---
    "warp_jetpack": {"name": "Варп-ранец", "prompt": "wearing a heavy metallic high-tech jetpack explicitly strapped to the back, bright blue plasma flames shooting out", "price": 70},
    "saturn_ring": {"name": "Кольцо Сатурна", "prompt": "surrounded by a bright glowing holographic golden planetary ring physically rotating tightly around the neck area", "price": 45},
    "plasma_cloak": {"name": "Плазменный плащ", "prompt": "wearing a large flowing cape made of bright blue glowing plasma and nebula energy explicitly tied around the neck and draping over the back", "price": 65},
    "ufo_hat": {"name": "Шапка-тарелка", "prompt": "wearing a glowing silver UFO flying saucer model as a hat physically resting flat on top of the head", "price": 40},

    # --- ГЕЙМЕРСКИЕ ПРИКОЛЫ (PS5 / VR) ---
    "vr_visor_2": {"name": "Визор VR-Орион", "prompt": "wearing a bulky white modern virtual reality VR headset strapped tightly covering the eyes and upper face", "price": 50},
    "dual_aura": {"name": "Аура Контроллера", "prompt": "entire body engulfed in a bright glowing white and neon blue energy aura, intense magical light radiating from the fur", "price": 25},

    # --- ПРОФЕССИОНАЛЬНЫЙ ЮМОР (СТОМАТОЛОГИЯ) ---
    "brilliant_smile": {"name": "Ослепительная улыбка", "prompt": "showing a very wide, exaggerated, extremely bright white human-like smile, sparkling teeth with bright diamond glints", "price": 100},
    "dentist_mirror": {"name": "Зеркало Космо-Врача", "prompt": "explicitly holding a shiny metallic futuristic dental mirror tool firmly clamped in its teeth", "price": 15},

    # --- ПРИКОЛЫ И КОСТЮМЫ ---
    "detective_pipe": {"name": "Трубка Шерлока", "prompt": "explicitly holding a classic wooden smoking detective pipe firmly clamped in its mouth", "price": 20},
    "dragon_wings": {"name": "Крылья Дракона", "prompt": "with two large highly detailed scaly black dragon wings explicitly attached to and extending from the back", "price": 75},
    "taco_suit": {"name": "Костюм Тако", "prompt": "explicitly wearing a full-body hilarious thick soft taco shell costume physically wrapping around the entire torso", "price": 35},
    "thug_beanie": {"name": "Шапка Thug Life", "prompt": "physically wearing a thick black knitted winter beanie hat pulled down tight over the head, 'ORION' written on it", "price": 15},
    "cosmic_boots": {"name": "Луноходы", "prompt": "explicitly wearing thick heavy protective glowing neon blue space boots covering all four paws", "price": 40},
    "chef_hat": {"name": "Колпак Кока", "prompt": "physically wearing a very tall puffy white chef hat resting on the head, thick red scarf tied around the neck", "price": 20},
    "holographic_wings": {"name": "Крылья Ангела", "prompt": "with two massive bright glowing semi-transparent holographic white angel wings explicitly attached to the back", "price": 85},
    "monocle_tophat": {"name": "Джентльмен", "prompt": "physically wearing a tall formal black top hat on the head, shiny golden monocle physically covering one eye", "price": 50},
    "crown_of_light": {"name": "Легендарный Венец", "prompt": "wearing a massive extremely bright glowing crown made of pure intense solar light hovering exactly above the head", "price": 150}
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

        # 🟢 ДОСТАЕМ ПРОФЕССИЮ ИЗ БАЗЫ
        from database import get_dog_profession
        current_prof = get_dog_profession(user_id)
        
        # 🟢 ИСПРАВЛЕНИЕ: Добавили {current_prof} в заголовок!
        text = (
            f"🐕 **КАЮТА ПИТОМЦА ({current_prof})**\n\n"
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
            tele_types.InlineKeyboardButton("🚀 Выгулять (-10 💰)", callback_data="dog_walk"), 
            tele_types.InlineKeyboardButton("👕 Гардероб", callback_data="dog_wardrobe"), 
            tele_types.InlineKeyboardButton("🛒 Магазин", callback_data="dog_shop") 
        )

        # 🟢 КНОПКА ПРОФЕССИИ, ЕСЛИ УРОВЕНЬ ПОЗВОЛЯЕТ
        if dog['level'] >= 10 and current_prof == 'Кадет':
            kb.row(tele_types.InlineKeyboardButton(text="🎓 Выбрать специализацию", callback_data="dog_choose_prof"))
  
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
        from database import get_dog_profession
        prof = get_dog_profession(user_id)
        
        # Медики спят эффективнее!
        energy_boost = 60 if "Медик" in prof else 40
        
        if dog['energy'] >= 100:
            bot.answer_callback_query(call.id, "Марти уже полон сил! ⚡", show_alert=True)
        else:
            dog['energy'] = min(100, dog['energy'] + energy_boost) # 🟢 Исправлено
            update_dog_data(user_id, dog) # 🟢 Исправлено
            bot.answer_callback_query(call.id, f"Марти поспал в крио-капсуле (+{energy_boost} Энергии)! 💤")
            chat_id = call.message.chat.id
            send_dog_menu(bot, chat_id, user_id, message_id=call.message.message_id)

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

    elif action == "choose_prof":
        kb = tele_types.InlineKeyboardMarkup()
        kb.row(tele_types.InlineKeyboardButton(text="👨‍⚕️ Космо-Медик", callback_data="dog_setprof_medic"))
        kb.row(tele_types.InlineKeyboardButton(text="🔧 Бортинженер", callback_data="dog_setprof_engineer"))
        kb.row(tele_types.InlineKeyboardButton(text="🔭 Астронавигатор", callback_data="dog_setprof_navigator"))
        bot.edit_message_caption("🎓 **АКАДЕМИЯ: ВЫБОР ПУТИ**\n\nВыберите специализацию для Марти:\n\n"
                              "👨‍⚕️ **Космо-Медик** - эффективнее спит.\n"
                              "🔧 **Бортинженер** - скидка 20% в магазине.\n"
                              "🔭 **Астронавигатор** - приносит x2 Пыли за ум.", 
                              call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        return # Важно, чтобы не сработало общее обновление меню внизу

    elif action.startswith("setprof_"):
        prof_map = {"medic": "Космо-Медик 👨‍⚕️", "engineer": "Бортинженер 🔧", "navigator": "Астронавигатор 🔭"}
        prof_id = action.split("_")[1]
        chosen_prof = prof_map.get(prof_id, "Кадет")
        
        from database import set_dog_profession
        set_dog_profession(user_id, chosen_prof)
        bot.answer_callback_query(call.id, f"Выбрана профессия: {chosen_prof}!", show_alert=True)
  
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
        # 🟢 Достаем профессию, чтобы показать скидки прямо на витрине
        from database import get_dog_profession
        prof = get_dog_profession(user_id)
        
        text = "🛒 **МАГАЗИН АКАДЕМИИ**\n\nНовые вещи появятся в гардеробе!"
        if "Инженер" in prof:
            text += "\n🛠 *Активирована скидка Бортинженера: -20%!*"

        kb = tele_types.InlineKeyboardMarkup(row_width=2)
        for k, v in DOG_SHOP.items():
            if k not in dog['items']:
                # Считаем цену со скидкой для кнопок
                price = v['price']
                if "Инженер" in prof:
                    price = int(price * 0.8)
                
                kb.add(tele_types.InlineKeyboardButton(f"{v['name']} ({price}💰)", callback_data=f"dog_buy_{k}"))
        
        kb.add(tele_types.InlineKeyboardButton("🔙 Назад", callback_data="dog_back"))
        # Добавил parse_mode="Markdown", чтобы текст скидки был красивым курсивом
        bot.edit_message_caption(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        return

    elif action.startswith("buy_"):
        item = action.replace("buy_", "")
        
        # 🟢 Снова достаем профессию для правильного списания Пыли
        from database import get_dog_profession
        prof = get_dog_profession(user_id)
        
        price = DOG_SHOP[item]['price']
        if "Инженер" in prof:
            price = int(price * 0.8) # Применяем скидку 20%

        if spend_dust(user_id, price):
            dog['items'].append(item)
            update_dog_data(user_id, dog)
            bot.answer_callback_query(call.id, f"🎉 Куплено: {DOG_SHOP[item]['name']} (за {price} 💰)!")
            
            # Возвращаем в магазин после покупки, чтобы кнопка купленной вещи пропала
            kb = tele_types.InlineKeyboardMarkup(row_width=2)
            kb.add(tele_types.InlineKeyboardButton("🔙 В каюту", callback_data="dog_back"))
            bot.edit_message_caption("✅ Покупка отправлена в Гардероб!", call.message.chat.id, call.message.message_id, reply_markup=kb)
        else: 
            bot.answer_callback_query(call.id, f"❌ Мало пыли! Нужно {price} 💰", show_alert=True)

    elif action == "resurrect":
        if spend_dust(user_id, 100):
            update_dog_data(user_id, {"level": 1, "hunger": 80, "energy": 80, "mood": 80, "items": [], "equipped": [], "xp": 0, "date": "", "status": "alive"})
            bot.answer_callback_query(call.id, "🛰 Новый щенок на борту!")
        else: bot.answer_callback_query(call.id, "❌ Нужно 100 пыли!")

    # Обновление меню
    try: bot.delete_message(call.message.chat.id, call.message.message_id)
    except: pass
    send_dog_menu(bot, call.message.chat.id, user_id)
