import time
from datetime import datetime
from telebot import types as tele_types
from database import (get_dog_data, update_dog_data, spend_dust, get_user_data, 
                      equip_dog_item, unequip_dog_item, process_dog_walk)
from neural_draw import get_cascade_image 

# 🟢 КВАНТОВЫЙ КЭШ (Сейф для бесплатных картинок)
CABIN_IMAGE_CACHE = {}

# 🛒 ГИПЕР-ХУДОЖЕСТВЕННЫЙ МАГАЗИН АКАДЕМИИ (55 ПРЕДМЕТОВ)
DOG_SHOP = {
    # --- БАЗОВАЯ КОСМИЧЕСКАЯ ЭКИПИРОВКА ---
    "space_helmet": {"name": "Стеклянный шлем", "prompt": "physically wearing a massive clear glass astronaut bubble helmet completely enclosing the dog's entire head, realistic condensation and neon reflections on glass, thick metal neck ring locked around the collar area", "price": 40},
    "star_suit": {"name": "Скафандр", "prompt": "the dog's torso is tightly fitted into a realistic heavy-duty white padded astronaut spacesuit with Orion patches, physical fabric folds and thick thermal insulation covering the body, leaving only the head and tail visible", "price": 60},
    "cool_glasses": {"name": "Кибер-очки", "prompt": "wearing high-tech glowing neon cyberpunk sunglasses physically resting on the dog's snout, the thick frames are strapped behind the ears, realistic blue glow illuminating the surrounding fur", "price": 30},
    "bandana": {"name": "Бандана Орион", "prompt": "wearing a thick bright blue fabric bandana with white stars tightly knotted around the neck, realistic textile texture with frayed edges clearly contrasting with the fluffy fur", "price": 20},
    "laser_collar": {"name": "Лазерный ошейник", "prompt": "wearing a solid glowing neon-cyan laser collar band tightly fitted around the neck, casting a strong realistic light flare onto the dog's chin and fur", "price": 25},
    "pilot_cap": {"name": "Кепка пилота", "prompt": "physically wearing a vintage weathered brown leather aviator pilot hat, ears tucked under, thick leather chin straps buckled tightly under the jaw, realistic aged leather texture", "price": 35},
    "nebula_scarf": {"name": "Шарф Небула", "prompt": "wrapped in a massive thick cosmic-purple silk scarf circling the neck multiple times, realistic fabric drapery with sparkling galaxy patterns", "price": 15},
    "cyber_paws": {"name": "Кибер-лапы", "prompt": "all four paws are encased in heavy metallic robotic mech-boots, matte steel plates with glowing joints, physically fitted over the legs", "price": 45},
    "galaxy_crown": {"name": "Корона Галактики", "prompt": "a heavy ornate golden royal crown physically sitting firmly on top of the dog's head between the ears, realistic gold reflections, surrounded by tiny floating physical stars", "price": 80},
    "steampunk_goggles": {"name": "Стимпанк-очки", "prompt": "wearing heavy brass and leather steampunk goggles with thick glass lenses, the leather strap is buckled tightly around the dog's head, realistic metal oxidation", "price": 30},
    "neon_harness": {"name": "Неоновая сбруя", "prompt": "body is strapped into a professional neon-green tactical military harness, heavy plastic buckles and nylon straps visibly sinking into the fur, realistic shadows", "price": 40},
    "comet_bowtie": {"name": "Галстук-комета", "prompt": "wearing a glowing oversized magical cosmic bowtie physically attached directly under the chin, realistic silk texture with glowing ember particles", "price": 20},
    "radar_monocle": {"name": "Монокль-радар", "prompt": "a glowing high-tech cybernetic radar monocle physically clamped onto the side of the dog's head, realistic glass lens with green holographic data UI projected in front of the eye", "price": 50},
    "alien_antenna": {"name": "Антенны пришельца", "prompt": "physically wearing a black flexible headband with two bouncy glowing green alien antennas sticking straight up from the head, realistic plastic and light glow", "price": 15},
    "astro_boots": {"name": "Астро-ботинки", "prompt": "all four paws are shoved into thick puffy white astronaut moon boots with realistic rubber soles and fabric crinkles", "price": 35},
    "heavy_gold_chain": {"name": "Золотая цепь", "prompt": "wearing an incredibly thick and heavy oversized solid gold cuban link chain around the neck, a massive shiny gold bone pendant resting heavily on the chest fur", "price": 55},
    "diamond_collar": {"name": "Бриллиантовый ошейник", "prompt": "wearing an ultra-thick luxury collar encrusted with thousands of tiny sparkling diamonds, realistic light refraction and sharp glints from the gems", "price": 90},
    "star_pendant": {"name": "Кулон Полярная звезда", "prompt": "a huge glowing blue star-shaped crystal pendant hanging from a thick silver rope chain physically resting on the chest", "price": 30},
    "warp_jetpack": {"name": "Варп-ранец", "prompt": "a heavy metallic sci-fi jetpack is physically strapped to the dog's back with industrial nylon belts, small blue plasma nozzles at the bottom with heat distortion effects", "price": 70},
    "saturn_ring": {"name": "Кольцо Сатурна", "prompt": "a physical glowing holographic golden planetary ring spinning tightly around the dog's neck like a collar, realistic light particles illuminating the fur", "price": 45},
    "plasma_cloak": {"name": "Плазменный плащ", "prompt": "wearing a long flowing superhero cape made of semi-transparent blue plasma energy, fastened with a silver brooch at the neck, realistic energy wisps", "price": 65},
    "ufo_hat": {"name": "Шапка-тарелка", "prompt": "a realistic silver metal UFO flying saucer model is sitting perfectly flat on top of the dog's head like a hat, a faint green light beam shining down from it", "price": 40},
    "vr_visor_2": {"name": "Визор VR-Орион", "prompt": "physically wearing a bulky white modern VR headset that is strapped over the eyes and upper face, realistic plastic texture and status LEDs", "price": 50},
    "dual_aura": {"name": "Аура Контроллера", "prompt": "the dog's entire physical body is enveloped in a brilliant white and neon-blue energy aura, glowing light rays radiating through the fur fibers", "price": 25},
    "brilliant_smile": {"name": "Ослепительная улыбка", "prompt": "the dog has a wide happy smile revealing perfect bright white human-like teeth with a brilliant diamond-like spark on one canine", "price": 100},
    "dentist_mirror": {"name": "Зеркало Космо-Врача", "prompt": "physically holding a long-handled stainless steel dental mirror tool firmly in its mouth, realistic chrome reflections on the metal", "price": 15},
    "detective_pipe": {"name": "Трубка Шерлока", "prompt": "physically holding a classic polished wooden tobacco pipe in its mouth, realistic wisps of smoke rising from the bowl", "price": 20},
    "dragon_wings": {"name": "Крылья Дракона", "prompt": "two massive hyper-detailed scaly black dragon wings are physically growing out from the shoulder blades on the dog's back, fully extended, realistic leathery texture", "price": 75},
    "taco_suit": {"name": "Костюм Тако", "prompt": "the dog's entire body is hilariously wearing a giant thick plush taco shell costume with realistic fabric lettuce and cheese details", "price": 35},
    "thug_beanie": {"name": "Шапка Thug Life", "prompt": "physically wearing a thick black knitted beanie hat pulled down over the ears, 'ORION' text embroidered in white 3D thread, realistic wool texture", "price": 15},
    "cosmic_boots": {"name": "Луноходы", "prompt": "all four paws are encased in thick protective glowing neon-blue space boots with heavy industrial tread", "price": 40},
    "chef_hat": {"name": "Колпак Кока", "prompt": "physically wearing a tall white pleated chef hat on its head and a thick red fabric scarf tied around its neck, realistic cotton texture", "price": 20},
    "holographic_wings": {"name": "Крылья Ангела", "prompt": "two massive glowing semi-transparent white holographic angel wings are physically attached to the dog's back, realistic light rays", "price": 85},
    "monocle_tophat": {"name": "Джентльмен", "prompt": "wearing a formal tall black felt top hat and a golden monocle physically covering the right eye, realistic victorian aesthetic", "price": 50},
    "crown_of_light": {"name": "Легендарный Венец", "prompt": "a massive crown made of pure intense white solar light is hovering exactly one inch above the head, casting strong realistic light rays onto the fur", "price": 150},

    # --- 🆕🔥 НОВЫЕ ПОСТУПЛЕНИЯ 🔥🆕 ---
    "exosuit_armor": {"name": "Экзо-броня", "prompt": "wearing a complex matte-black tactical exosuit armor fitted to the dog's body, articulated plates, glowing blue energy cables and pistons, realistic combat-worn texture", "price": 110},
    "cyberpunk_jacket": {"name": "Куртка Найт-Сити", "prompt": "wearing an oversized black leather cyberpunk jacket with a high pop-up collar glowing neon-pink, physical wires and hardware integrated into the leather", "price": 95},
    "tactical_vest": {"name": "Тактический жилет", "prompt": "wearing a realistic military tactical vest in olive drab, multi-pouch design, 'ORION-SQUAD' patch on the side, tightly buckled around the chest", "price": 80},
    "warp_robe": {"name": "Варп-мантия", "prompt": "wearing a heavy deep-purple velvet monk robe with silver embroidered star maps, the hood is down, a thick rope belt is tied around the waist", "price": 70},
    "mech_harness": {"name": "Мех-сбруя", "prompt": "a complex industrial robotic exoskeleton frame is bolted to the dog's body over the fur, made of heavy steel with visible gears and articulated hydraulic joints", "price": 130},
    "general_hat": {"name": "Фуражка Генерала", "prompt": "physically wearing a rigid black military commander's cap with a large silver Orion insignia, the brim casting a realistic shadow over the eyes", "price": 90},
    "welding_mask": {"name": "Маска Сварщика", "prompt": "wearing a realistic industrial welding mask flipped down over the face, scratched dark metal with a small glowing glass viewing slot", "price": 60},
    "santa_astro_hat": {"name": "Астро-Санта", "prompt": "wearing a thick red fuzzy Santa hat with a high-tech life-support computer module physically attached to the side, realistic white fur trim", "price": 45},
    "straw_hat": {"name": "Шляпа Фермера", "prompt": "wearing a wide-brimmed weathered straw sun hat with a blue ribbon, realistic woven texture and shadows", "price": 30},
    "crown_of_comets": {"name": "Корона Комет", "prompt": "a crown made of jagged obsidian rock is sitting on the head, with three realistic miniature comets with glowing tails physically orbiting it", "price": 180},
    "cyber_jaw": {"name": "Кибер-челюсть", "prompt": "the lower jaw area is covered by a realistic chrome robotic jaw implant with tiny pistons and red light indicators, integrated into the dog's face", "price": 100},
    "drone_companion": {"name": "Дрон-спутник", "prompt": "a small detailed spy drone is physically tethered to the dog's harness by a glowing blue power cord, hovering close to the shoulder", "price": 75},
    "laser_eye": {"name": "Лазерный глаз", "prompt": "one eye is covered by a realistic red cybernetic lens implant with rotating parts and a faint red laser beam pointing forward", "price": 85},
    "power_gloves": {"name": "Силовые лапы", "prompt": "all paws are encased in massive blue-painted industrial robotic gauntlets with glowing orange energy vents and articulated claws", "price": 115},
    "data_monocle": {"name": "Голо-монокль", "prompt": "a high-tech monocle is strapped to the head, projecting a bright blue holographic computer screen floating just inches from the dog's snout", "price": 65},
    "diamond_grillz": {"name": "Гриллзы Сириуса", "prompt": "the dog's open mouth reveals custom diamond-encrusted teeth covers (grillz), realistic sparkling light flares and gold reflections", "price": 140},
    "floating_halo": {"name": "Нимб Ангела", "prompt": "a thin golden ring of light is physically hovering above the head, emitting a soft warm glow and tiny floating light particles", "price": 90},
    "sub_bass_speakers": {"name": "Космо-Сабвуферы", "prompt": "carrying two massive wooden high-fidelity speakers on the back, held by a thick leather harness, realistic mesh and wood grain", "price": 85},
    "rocket_boots": {"name": "Ракетные лапы", "prompt": "wearing four thick metallic rocket-powered boots, small realistic flames and blue smoke trails coming from the heels", "price": 125},
    "dentist_drill": {"name": "Бормашина Академии", "prompt": "physically holding a high-tech dental drill tool in its mouth, glowing power lights and a spinning steel drill bit, realistic cables attached", "price": 70}
}

def get_dog_prompt(dog, user_id):
    if dog['status'] == 'dead':
        return "empty dog bed, abandoned futuristic spaceship cabin, lonely atmosphere, realistic photographic style", user_id

    # 1. Световой модуль (Локальное время Чернигова)
    hour = datetime.now().hour
    if 6 <= hour < 11: light = "soft morning sunrise light through the window, cool blue and orange tones"
    elif 11 <= hour < 18: light = "bright direct midday sunlight, high contrast, crisp shadows"
    elif 18 <= hour < 22: light = "warm golden hour sunset glow, long soft shadows, cozy atmosphere"
    else: light = "deep blue night atmosphere, dim interior lighting, glowing neon control panels"

    # 2. Визуализация богатства (Пыль на столе)
    u_data = get_user_data(user_id)
    dust = u_data['spendable_dust']
    if dust < 50: dust_visual = "an empty clean metallic desk near the dog"
    elif dust < 200: dust_visual = "a small glowing pile of blue stardust on the desk"
    elif dust < 1000: dust_visual = "a large heap of shimmering cosmic dust on the table"
    else: dust_visual = "a massive overflowing treasure chest filled with glowing stardust on the desk"

    # 3. Износ оборудования (Чистота)
    if dog.get('clean', 100) < 40:
        wear = "grimy metallic surfaces, faint oil stains on the walls, dusty floor, worn-out equipment"
    else:
        wear = "pristine polished chrome surfaces, sterile clean environment, high-tech gloss"

    # 4. Генетическое наследие (Шанс 10% увидеть улитку)
    import random
    crossover = ""
    if random.random() < 0.10:
        crossover = "a small realistic garden snail is slowly crawling on the window glass,"

    # 🧬 ИТОГОВЫЙ ДИНАМИЧЕСКИЙ БАЗОВЫЙ ПРОМПТ (Теперь без перезаписи!)
    base = f"macro photography of a realistic living fluffy random-colored toy poodle dog, {light}, {dust_visual}, {wear}, {crossover} in a high-tech cozy spaceship cabin with a window showing stars, 4k, cinematic lighting"
    
    # Эволюция
    if dog['level'] < 5: evo = "a tiny cute puppy poodle, sleeping on a soft pillow"
    elif dog['level'] < 12: evo = "an active adolescent poodle, sitting alert and happy"
    else: evo = "a wise adult poodle, sitting at a control panel like a co-pilot"

    # Состояние
    if dog['energy'] < 30: state = "tired look, dim lighting, dog is resting"
    else: state = "happy expression, bright warm lighting, sparkling eyes"

    # Одежда
    equipped_items = dog.get('equipped', [])
    clothes = [DOG_SHOP[k]["prompt"] for k in equipped_items if k in DOG_SHOP]
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
