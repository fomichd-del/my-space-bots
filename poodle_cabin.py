import time
from datetime import datetime
from telebot import types as tele_types
from database import (get_dog_data, update_dog_data, spend_dust, get_user_data, 
                      equip_dog_item, unequip_dog_item, process_dog_walk)
from neural_draw import get_cascade_image 

# 🟢 КВАНТОВЫЙ КЭШ (Сейф для бесплатных картинок)
CABIN_IMAGE_CACHE = {}

# 🛒 ГИПЕР-РАСШИРЕННЫЙ МАГАЗИН АКАДЕМИИ (ТЕПЕРЬ 55 ПРЕДМЕТОВ!)
DOG_SHOP = {
    # --- БАЗОВАЯ КОСМИЧЕСКАЯ ЭКИПИРОВКА ---
    "space_helmet": {"name": "Стеклянный шлем", "prompt": "physically wearing a massive clear glass astronaut bubble helmet completely enclosing the dog's entire head, thick metal neck ring attached, bright neon visor reflections blocking the background", "price": 40},
    "star_suit": {"name": "Скафандр", "prompt": "dog body is entirely and completely covered by a thick bulky silver sci-fi astronaut spacesuit armor, no fur visible on the body, only the dog's head is visible sticking out of the heavy suit", "price": 60},
    "cool_glasses": {"name": "Кибер-очки", "prompt": "wearing prominent glowing neon cyberpunk sunglasses physically resting on the dog's snout, thick frames completely covering the eyes", "price": 30},
    "bandana": {"name": "Бандана Орион", "prompt": "wearing a massive bright blue fabric bandana with white stars tightly tied around the neck, thick cloth clearly contrasting with the red fur", "price": 20},
    "laser_collar": {"name": "Лазерный ошейник", "prompt": "wearing a blindingly bright thick glowing neon laser collar tightly strapped around the furry neck, casting colorful neon light onto the dog's chin", "price": 25},
    "pilot_cap": {"name": "Кепка пилота", "prompt": "physically wearing a vintage brown leather aviator pilot hat tightly covering the dog's ears and forehead, thick leather straps buckled under the chin", "price": 35},
    "nebula_scarf": {"name": "Шарф Небула", "prompt": "wrapped in a huge thick flowing cosmic purple fabric scarf circling the neck multiple times, long ends flying in the wind", "price": 15},
    "cyber_paws": {"name": "Кибер-лапы", "prompt": "all four paws are completely covered by heavy metallic robotic high-tech mech boots, bright glowing joints, thick armor plates on legs", "price": 45},
    "galaxy_crown": {"name": "Корона Галактики", "prompt": "wearing a massive heavy golden royal crown physically sitting firmly on top of the dog's head, embedded with glowing jewels, surrounded by floating stars", "price": 80},
    "steampunk_goggles": {"name": "Стимпанк-очки", "prompt": "wearing thick heavy brass vintage steampunk goggles with thick leather straps buckled tightly around the dog's head, resting heavily above the eyes", "price": 30},
    "neon_harness": {"name": "Неоновая сбруя", "prompt": "body tightly strapped in a thick bright neon green tactical military dog harness, heavy duty buckles and straps visibly sinking into the fur", "price": 40},
    "comet_bowtie": {"name": "Галстук-комета", "prompt": "wearing an oversized incredibly bright glowing cosmic bowtie physically attached directly under the chin, radiating magical light", "price": 20},
    "radar_monocle": {"name": "Монокль-радар", "prompt": "wearing a glowing high-tech cybernetic radar monocle physically clamped over the dog's right eye, green holographic data streaming from it", "price": 50},
    "alien_antenna": {"name": "Антенны пришельца", "prompt": "physically wearing a thick black headband over the ears with two bouncy glowing green alien antennas sticking straight up from the head", "price": 15},
    "astro_boots": {"name": "Астро-ботинки", "prompt": "all four paws shoved into incredibly thick puffy white astronaut moon boots, huge and clunky", "price": 35},
    "heavy_gold_chain": {"name": "Золотая цепь", "prompt": "wearing an absurdly thick heavy oversized gold rapper chain necklace hanging low around the neck, huge shiny gold bone pendant resting on the chest", "price": 55},
    "diamond_collar": {"name": "Бриллиантовый ошейник", "prompt": "wearing an ultra-thick luxury collar completely encrusted in massive sparkling diamonds, tightly wrapped around the neck, intense light flares", "price": 90},
    "star_pendant": {"name": "Кулон Полярная звезда", "prompt": "wearing a huge glowing blue star-shaped magical pendant hanging from a thick silver chain physically resting on the dog's chest", "price": 30},
    "warp_jetpack": {"name": "Варп-ранец", "prompt": "carrying a massive heavy metallic sci-fi jetpack physically strapped to the dog's back with thick belts, bright blue plasma thrusters firing", "price": 70},
    "saturn_ring": {"name": "Кольцо Сатурна", "prompt": "encircled by a physical bright glowing holographic golden planetary ring spinning tightly around the dog's neck, illuminating the fur", "price": 45},
    "plasma_cloak": {"name": "Плазменный плащ", "prompt": "wearing a massive flowing superhero cape made of bright blue glowing plasma energy, tied tightly around the neck and draping over the whole back", "price": 65},
    "ufo_hat": {"name": "Шапка-тарелка", "prompt": "physically wearing a glowing silver UFO flying saucer toy resting perfectly flat on top of the dog's head like a hat, beaming green light down", "price": 40},
    "vr_visor_2": {"name": "Визор VR-Орион", "prompt": "physically wearing a bulky white modern virtual reality VR headset completely strapping over and hiding the dog's eyes and upper face", "price": 50},
    "dual_aura": {"name": "Аура Контроллера", "prompt": "entire physical body completely engulfed in a blindingly bright glowing white and neon blue energy aura, intense magical light radiating directly from the fur", "price": 25},
    "brilliant_smile": {"name": "Ослепительная улыбка", "prompt": "dog face showing an impossibly wide exaggerated bright white human-like smile, huge sparkling teeth with intense diamond glints", "price": 100},
    "dentist_mirror": {"name": "Зеркало Космо-Врача", "prompt": "physically holding a shiny metallic futuristic dental mirror tool firmly clamped sideways inside the dog's mouth between the teeth", "price": 15},
    "detective_pipe": {"name": "Трубка Шерлока", "prompt": "physically holding a classic wooden smoking detective pipe firmly clamped inside the dog's mouth, smoke rising from the bowl", "price": 20},
    "dragon_wings": {"name": "Крылья Дракона", "prompt": "having two massive highly detailed scaly black dragon wings physically growing out of the dog's back, fully spread open", "price": 75},
    "taco_suit": {"name": "Костюм Тако", "prompt": "dog body entirely stuffed inside a hilarious oversized thick soft taco shell costume, physically wrapping around the dog's entire torso", "price": 35},
    "thug_beanie": {"name": "Шапка Thug Life", "prompt": "physically wearing a thick black knitted winter beanie hat pulled down tight over the dog's head and ears, 'ORION' text embroidered on it", "price": 15},
    "chef_hat": {"name": "Колпак Кока", "prompt": "physically wearing a comically tall puffy white chef hat resting perfectly on the top of the dog's head, thick red scarf tied around the neck", "price": 20},
    "holographic_wings": {"name": "Крылья Ангела", "prompt": "having two massive bright glowing semi-transparent holographic white angel wings physically attached to the dog's back", "price": 85},
    "monocle_tophat": {"name": "Джентльмен", "prompt": "physically wearing a tall formal black top hat sitting perfectly on the dog's head, a shiny golden monocle physically covering one eye", "price": 50},
    "crown_of_light": {"name": "Легендарный Венец", "prompt": "wearing a massive incredibly bright glowing crown made of pure intense solar light hovering exactly one inch above the dog's head", "price": 150},

    # --- 🆕🔥 НОВЫЕ ПОСТУПЛЕНИЯ (20 ПРЕДМЕТОВ) 🔥🆕 ---
    
    # --- ОДЕЖДА И БРОНЯ ---
    "exosuit_armor": {"name": "Экзо-броня", "prompt": "wearing a complex, bulky matte-black military exosuit armor with integrated glowing blue hydraulic pistons and heavy duty straps, fully wrapping the dog's body and legs, no fur visible", "price": 110},
    "cyberpunk_jacket": {"name": "Куртка Найт-Сити", "prompt": "wearing an oversized black leather cyberpunk jacket with an incredibly tall high collar that glows bright neon pink, physical cables and wires integrated into the fabric and plugged into the neck", "price": 95},
    "tactical_vest": {"name": "Тактический жилет", "prompt": "wearing a heavy-duty, multi-pocket olive drab military tactical vest with physical pouches, carabiners, and the text 'ORION-SQUAD' embroidered on it, tightly buckled around the torso", "price": 80},
    "warp_robe": {"name": "Варп-мантия", "prompt": "wrapped in a thick, flowing deep-purple monk robe made of textured velvet with physical silver embroidered constellations, tied with a heavy rope belt", "price": 70},
    "mech_harness": {"name": "Мех-сбруя", "prompt": "wearing a complex physical robotic exoskeleton harness made of heavy steel beams, articulated joints, and visible gears, clamped securely over the dog's back and legs, casting sharp metallic reflections", "price": 130},

    # --- ШАПКИ И ГОЛОВНЫЕ УБОРЫ ---
    "general_hat": {"name": "Фуражка Генерала", "prompt": "physically wearing a massive, formal black military general hat with a rigid brim and a large, incredibly detailed gold and silver Orion Academy emblem prominently displayed on the front", "price": 90},
    "welding_mask": {"name": "Маска Сварщика", "prompt": "wearing a heavy, flipped-down professional welding mask with a thick, dark glass visor, made of realistic scratched metal and rust, covering the entire dog's face", "price": 60},
    "santa_astro_hat": {"name": "Астро-Санта", "prompt": "physically wearing a thick, fuzzy red Santa hat that is modified with a realistic small, functional, glowing glass and metal life-support unit on the side", "price": 45},
    "straw_hat": {"name": "Шляпа Фермера", "prompt": "wearing a comically oversized, woven straw sun hat with a fraying brim, sitting perfectly on the head, with a small physical blue bandana ribbon tied around it", "price": 30},
    "crown_of_comets": {"name": "Корона Комет", "prompt": "wearing a physical crown made of sharp, dark, textured obsidian rock, with several miniature, bright, realistic comets with trails of light and dust hovering and spinning directly above it", "price": 180},

    # --- КИБЕРНЕТИКА И АКСЕССУАРЫ ---
    "cyber_jaw": {"name": "Кибер-челюсть", "prompt": "the lower jaw is completely replaced by a realistic, complex, articulated chrome metallic robotic jaw with visible gears, pistons, and glowing red optical sensors on the side", "price": 100},
    "drone_companion": {"name": "Дрон-спутник", "prompt": "a small, incredibly detailed futuristic spy drone with two physical spinning propellers and a glowing camera lens is physically tethered to the dog's harness by a glowing blue energy cable", "price": 75},
    "laser_eye": {"name": "Лазерный глаз", "prompt": "one eye is completely replaced by a complex, realistic glowing red cybernetic optical implant, made of brushed metal and glass, with holographic targeting reticles streaming from it", "price": 85},
    "power_gloves": {"name": "Силовые лапы", "prompt": "all four paws are enclosed in massive, incredibly bulky robotic power gauntlets made of thick, blue-painted steel, with visible articulated fingers and integrated orange energy emitters", "price": 115},
    "data_monocle": {"name": "Голо-монокль", "prompt": "wearing a sophisticated high-tech cybernetic monocle physically clamped over the dog's right eye,made of clear glass, emitting complex green and blue holographic data screens that float around the face", "price": 65},

    # --- ПРИКОЛЫ И УНИКАЛЬНЫЕ ПРЕДМЕТЫ ---
    "diamond_grillz": {"name": "Гриллзы Сириуса", "prompt": "the dog is showing an incredibly wide smile with physical, custom-fitted, massive diamond and gold grillz encrusting all teeth, casting intense light flares and glints", "price": 140},
    "floating_halo": {"name": "Нимб Ангела", "prompt": "a glowing golden planetary ring halo is physically hovering exactly two inches above the dog's head, radiating soft, warm light and emitting small, floating stars and constellations", "price": 90},
    "sub_bass_speakers": {"name": "Космо-Сабвуферы", "prompt": "carrying two massive, realistic, old-school wooden sub-woofer speakers with visible physical cones and metal grilles, strapped to the dog's back with a thick leather harness", "price": 85},
    "rocket_boots": {"name": "Ракетные лапы", "prompt": "all four paws are shove inside incredibly thick clunky metallic rocket boots, each boot has realistic small fiery plasma thrusters emitting bright orange light and smoke trails", "price": 125},
    "dentist_drill": {"name": "Бормашина Академии", "prompt": "physically holding a terrifying, detailed futuristic dental drill tool with a spinning tip, complex cables, and glowing power indicators, clamped sideways inside the dog's mouth", "price": 70}
}

def get_dog_prompt(dog, user_id):
    if dog['status'] == 'dead':
        return "empty dog bed, abandoned futuristic spaceship cabin, lonely atmosphere, realistic photographic style", user_id
    
    # 🧬 ГЕНЕТИЧЕСКАЯ МОДИФИКАЦИЯ: Убрали 'apricot', добавили 'living' и 'random-colored'
    base = "macro photography of a realistic living fluffy random-colored toy poodle dog, in a high-tech cozy spaceship cabin with a window showing stars, 4k, cinematic lighting"
    
    if dog['level'] < 5: evo = "a tiny cute puppy poodle, sleeping on a soft pillow"
    elif dog['level'] < 12: evo = "an active adolescent poodle, sitting alert and happy"
    else: evo = "a wise adult poodle, sitting at a control panel like a co-pilot"

    if dog['energy'] < 30: state = "tired look, dim lighting, dog is resting"
    else: state = "happy expression, bright warm lighting, sparkling eyes"

    # 👕 ТЕПЕРЬ ПРОМПТ ЗАВИСИТ ТОЛЬКО ОТ НАДЕТЫХ ВЕЩЕЙ
    equipped_items = dog.get('equipped', [])
    clothes = [DOG_SHOP[k]["prompt"] for k in equipped_items if k in DOG_SHOP]
    
    # 🧬 Акцент на реализм живой шерсти
    style_prompt = ", ".join(clothes) if clothes else "natural living fluffy fur texture"

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

        if dog['level'] >= 10 and current_prof == 'Кадет':
            kb.row(tele_types.InlineKeyboardButton(text="🎓 Выбрать специализацию", callback_data="dog_choose_prof"))
  
        # 🟢 КВАНТОВЫЙ КЭШ: ГЕНЕТИЧЕСКАЯ ПРИВЯЗКА К ПИЛОТУ
        cache_key = f"{user_id}_{prompt}"
        
        if cache_key in CABIN_IMAGE_CACHE:
            bot.send_photo(chat_id, photo=CABIN_IMAGE_CACHE[cache_key], caption=text, parse_mode="Markdown", reply_markup=kb)
        else:
            bot.send_chat_action(chat_id, 'upload_photo')
            image_bytes = get_cascade_image(prompt, seed)
            
            if image_bytes:
                msg = bot.send_photo(chat_id, photo=image_bytes, caption=text, parse_mode="Markdown", reply_markup=kb)
                CABIN_IMAGE_CACHE[cache_key] = msg.photo[-1].file_id
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
        
        energy_boost = 60 if "Медик" in prof else 40
        
        if dog['energy'] >= 100:
            bot.answer_callback_query(call.id, "Марти уже полон сил! ⚡", show_alert=True)
        else:
            dog['energy'] = min(100, dog['energy'] + energy_boost) 
            update_dog_data(user_id, dog) 
            bot.answer_callback_query(call.id, f"Марти поспал в крио-капсуле (+{energy_boost} Энергии)! 💤")

    elif action == "play":
        if spend_dust(user_id, 5):
            dog['mood'] = min(100, dog['mood'] + 30); dog['energy'] -= 20; update_dog_data(user_id, dog)
            bot.answer_callback_query(call.id, "🎾 Грави-мяч — это весело!")
        else: bot.answer_callback_query(call.id, "❌ Нужно 5 пыли!")

    elif action == "walk":
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
        return 

    elif action.startswith("setprof_"):
        prof_map = {"medic": "Космо-Медик 👨‍⚕️", "engineer": "Бортинженер 🔧", "navigator": "Астронавигатор 🔭"}
        prof_id = action.split("_")[1]
        chosen_prof = prof_map.get(prof_id, "Кадет")
        
        from database import set_dog_profession
        set_dog_profession(user_id, chosen_prof)
        bot.answer_callback_query(call.id, f"Выбрана профессия: {chosen_prof}!", show_alert=True)
  
    elif action == "wardrobe":
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

    elif action.startswith("toggle_"):
        item = action.replace("toggle_", "")
        if item in dog.get('equipped', []): unequip_dog_item(user_id, item)
        else: equip_dog_item(user_id, item)
        bot.answer_callback_query(call.id, "Стиль обновлен!")
        call.data = "dog_wardrobe"
        handle_dog_callback(bot, call)
        return

    elif action == "shop":
        from database import get_dog_profession
        prof = get_dog_profession(user_id)
        
        text = "🛒 **МАГАЗИН АКАДЕМИИ**\n\nНовые вещи появятся в гардеробе!"
        if "Инженер" in prof:
            text += "\n🛠 *Активирована скидка Бортинженера: -20%!*"

        kb = tele_types.InlineKeyboardMarkup(row_width=2)
        for k, v in DOG_SHOP.items():
            if k not in dog['items']:
                price = v['price']
                if "Инженер" in prof:
                    price = int(price * 0.8)
                
                kb.add(tele_types.InlineKeyboardButton(f"{v['name']} ({price}💰)", callback_data=f"dog_buy_{k}"))
        
        kb.add(tele_types.InlineKeyboardButton("🔙 Назад", callback_data="dog_back"))
        bot.edit_message_caption(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        return

    elif action.startswith("buy_"):
        item = action.replace("buy_", "")
        
        from database import get_dog_profession
        prof = get_dog_profession(user_id)
        
        price = DOG_SHOP[item]['price']
        if "Инженер" in prof:
            price = int(price * 0.8) 

        if spend_dust(user_id, price):
            dog['items'].append(item)
            update_dog_data(user_id, dog)
            bot.answer_callback_query(call.id, f"🎉 Куплено: {DOG_SHOP[item]['name']} (за {price} 💰)!")
            
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
