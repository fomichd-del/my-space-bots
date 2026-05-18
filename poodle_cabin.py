import time
from datetime import datetime
from telebot import types as tele_types
from database import (get_dog_data, update_dog_data, spend_dust, get_user_data, 
                      equip_dog_item, unequip_dog_item, process_dog_walk, update_user_data)
from neural_draw import get_cascade_image 

# 🟢 КВАНТОВЫЙ КЭШ (Сейф для бесплатных картинок)
CABIN_IMAGE_CACHE = {}

# 🛒 ГИПЕР-ХУДОЖЕСТВЕННЫЙ МАГАЗИН АКАДЕМИИ (55 ПРЕДМЕТОВ)
DOG_SHOP = {
    # --- БАЗОВАЯ КОСМИЧЕСКАЯ ЭКИПИРОВКА ---
    "space_helmet": {"name": "Стеклянный шлем", "prompt": "physically wearing a massive clear glass astronaut bubble helmet completely enclosing the dog's entire head, thick metal locking ring firmly clamped around the neck, realistic condensation and neon reflections on glass", "price": 40},
    "star_suit": {"name": "Скафандр", "prompt": "the dog's entire torso and legs are physically stuffed tightly into a heavy-duty white padded astronaut spacesuit, prominent Orion patches, deep fabric folds, leaving only the head distinctively visible", "price": 60},
    "cool_glasses": {"name": "Кибер-очки", "prompt": "physically wearing high-tech glowing neon cyberpunk sunglasses resting firmly on the snout, the thick metal frames are strapped tightly behind the ears, casting a strong blue glow on the face", "price": 30},
    "bandana": {"name": "Бандана Орион", "prompt": "physically wearing a thick bright blue fabric bandana prominently and tightly knotted around the neck, realistic textile texture with frayed edges clearly contrasting with the fluffy fur", "price": 20},
    "laser_collar": {"name": "Лазерный ошейник", "prompt": "physically wearing a thick solid glowing neon-cyan laser collar tightly buckled around the neck, prominently dominating the collar area and casting strong light flares on the chin", "price": 25},
    "pilot_cap": {"name": "Кепка пилота", "prompt": "physically wearing a vintage weathered brown leather aviator pilot hat tightly strapped to the head, thick leather chin straps prominently buckled securely under the jaw", "price": 35},
    "nebula_scarf": {"name": "Шарф Небула", "prompt": "physically wearing a massive thick cosmic-purple silk scarf aggressively wrapped multiple times around the neck, realistic heavy fabric drapery hiding the collarbone", "price": 15},
    "cyber_paws": {"name": "Кибер-лапы", "prompt": "all four physical paws are inserted deep inside heavy metallic robotic mech-boots, matte steel plates strapped tightly over the legs, glowing joints", "price": 45},
    "galaxy_crown": {"name": "Корона Галактики", "prompt": "physically wearing a massive, heavy, highly detailed golden royal crown actively resting firmly on the very top of the dog's head, encrusted with prominent glowing jewels", "price": 80},
    "steampunk_goggles": {"name": "Стимпанк-очки", "prompt": "physically wearing heavy brass steampunk goggles tightly strapped right over the dog's eyes with thick, prominent leather belts buckled around the head", "price": 30},
    "neon_harness": {"name": "Неоновая сбруя", "prompt": "the dog's torso is tightly strapped into a heavy-duty neon-green tactical military harness, thick nylon straps and massive plastic buckles distinctly digging into the fur", "price": 40},
    "comet_bowtie": {"name": "Галстук-комета", "prompt": "physically wearing an oversized glowing magical cosmic bowtie prominently clipped to the front of the neck, clearly visible and casting ember particles", "price": 20},
    "radar_monocle": {"name": "Монокль-радар", "prompt": "physically wearing a high-tech glowing cybernetic monocle device clamped tightly over one eye, projecting a highly visible green holographic UI directly in front of the face", "price": 50},
    "alien_antenna": {"name": "Антенны пришельца", "prompt": "physically wearing a thick black headband strapped firmly over the head, with two large bouncy glowing green alien antennas prominently sticking straight up", "price": 15},
    "astro_boots": {"name": "Астро-ботинки", "prompt": "all four physical paws are firmly planted deep inside oversized puffy white astronaut moon boots with thick heavy rubber soles", "price": 35},
    "heavy_gold_chain": {"name": "Золотая цепь", "prompt": "physically wearing an incredibly thick, massive solid gold cuban link chain heavily draped around the neck, an oversized gold bone pendant resting prominently on the chest", "price": 55},
    "diamond_collar": {"name": "Бриллиантовый ошейник", "prompt": "physically wearing an ultra-thick luxury collar tightly strapped around the neck, heavily encrusted with thousands of prominent sparkling diamonds catching the light", "price": 90},
    "star_pendant": {"name": "Кулон Полярная звезда", "prompt": "physically wearing a huge glowing blue star-shaped crystal pendant hanging prominently from a thick silver rope chain strapped around the neck", "price": 30},
    "warp_jetpack": {"name": "Варп-ранец", "prompt": "a massive metallic sci-fi jetpack is physically strapped tightly to the dog's back with heavy industrial nylon belts crossing the chest, blue plasma nozzles firing", "price": 70},
    "saturn_ring": {"name": "Кольцо Сатурна", "prompt": "a physical mechanical collar base projecting a highly visible, glowing holographic golden planetary ring spinning tightly around the dog's neck", "price": 45},
    "plasma_cloak": {"name": "Плазменный плащ", "prompt": "physically wearing a long flowing superhero cape distinctly clasped at the neck, made of bright semi-transparent blue plasma energy billowing outwards", "price": 65},
    "ufo_hat": {"name": "Шапка-тарелка", "prompt": "physically wearing a solid silver metal UFO flying saucer toy firmly strapped to the very top of the dog's head like a hat, dominating the upper silhouette", "price": 40},
    "vr_visor_2": {"name": "Визор VR-Орион", "prompt": "physically wearing a bulky white modern VR headset tightly strapped completely over the dog's eyes and upper face, thick head straps clearly visible", "price": 50},
    "dual_aura": {"name": "Аура Контроллера", "prompt": "the dog's physical body and fur are intensely radiating a blindingly brilliant white and neon-blue energy aura, completely dominating the lighting of the scene", "price": 25},
    "brilliant_smile": {"name": "Ослепительная улыбка", "prompt": "the dog's mouth is wide open in a highly exaggerated human-like smile, physically revealing perfect bright white teeth with a prominent diamond-like spark", "price": 100},
    "dentist_mirror": {"name": "Зеркало Космо-Врача", "prompt": "the dog's jaws are firmly holding a professional stainless steel dental mirror tool horizontally in its teeth, the reflective metal mirror clearly protruding from the mouth", "price": 15},
    "detective_pipe": {"name": "Трубка Шерлока", "prompt": "the dog is firmly clenching a highly detailed, classic polished wooden detective pipe horizontally in its teeth, prominent wisps of smoke clearly rising from the bowl", "price": 20},
    "dragon_wings": {"name": "Крылья Дракона", "prompt": "physically wearing a heavy dark leather chest harness tightly buckled on the torso, with two massive, wide-open black dragon wings firmly attached to the harness, dominating the background", "price": 75},
    "taco_suit": {"name": "Костюм Тако", "prompt": "the dog's entire physical torso is aggressively stuffed inside a massive, thick plush taco shell costume, prominent fabric lettuce and cheese wrapping around the body", "price": 35},
    "thug_beanie": {"name": "Шапка Thug Life", "prompt": "physically wearing a thick black knitted beanie hat pulled aggressively down over the ears and forehead, prominent 3D white embroidered text on the front", "price": 15},
    "cosmic_boots": {"name": "Луноходы", "prompt": "all four legs are physically inserted deep into massive, thick protective neon-blue space boots with prominent heavy industrial treads", "price": 40},
    "chef_hat": {"name": "Колпак Кока", "prompt": "physically wearing a towering white pleated chef hat securely strapped to the top of the head, paired with a thick red fabric scarf knotted at the neck", "price": 20},
    "holographic_wings": {"name": "Крылья Ангела", "prompt": "physically wearing a bulky metallic high-tech backpack tightly strapped to the chest, projecting two massive, intensely glowing white holographic angel wings behind the dog", "price": 85},
    "monocle_tophat": {"name": "Джентльмен", "prompt": "physically wearing a tall formal black top hat strapped to the head, and a distinct golden monocle firmly clamped over one eye", "price": 50},
    "crown_of_light": {"name": "Легендарный Венец", "prompt": "physically wearing a solid metallic headband that projects a massive, intensely glowing crown of pure white light directly above the head", "price": 150},

    # --- 🌌 СЕКРЕТНЫЙ ЛУТ (ТОЛЬКО ИЗ ЭКСПЕДИЦИЙ) ---
    "ancient_relic": {"name": "Древний артефакт", "prompt": "firmly clenching a heavy, glowing ancient alien stone artifact horizontally in its teeth, casting intense golden light directly onto the dog's snout", "price": 0},
    "broken_android_ear": {"name": "Ухо андроида", "prompt": "a highly detailed, rusted physical metal android ear is tied directly to the dog's collar as a trophy, dangling prominently on the chest", "price": 0},
    "void_collar": {"name": "Ошейник Пустоты", "prompt": "physically wearing an incredibly thick, prominent collar made of pure light-absorbing black void material, tightly strapped around the neck", "price": 0},
    "plasma_ball": {"name": "Плазменный мяч", "prompt": "the dog is physically resting its front paws heavily on top of a glowing glass plasma ball toy, visible static electricity lifting the fur", "price": 0},
    "cyber_tail_ring": {"name": "Кольцо на хвост", "prompt": "a massive, heavy chrome robotic ring with bright glowing blue LEDs is physically clamped tightly around the very base of the dog's tail", "price": 0},
    "starlight_medal": {"name": "Медаль Звезды", "prompt": "physically wearing a massive, heavy star-shaped medal prominently hanging from a thick silver chain strapped securely around the neck", "price": 0},
    "holographic_map": {"name": "Голо-карта", "prompt": "physically wearing a high-tech collar module that projects a highly visible, glowing 3D holographic star map floating directly in front of the dog's nose", "price": 0},
    "nebula_boots": {"name": "Туманные сапоги", "prompt": "all four paws are firmly planted deep inside thick translucent boots, prominently glowing with swirling colorful nebula gas inside", "price": 0},
    "black_hole_pendant": {"name": "Кулон-Сингулярность", "prompt": "a heavy glass sphere pendant containing a tiny realistic black hole is physically attached to the dog's collar, prominently visible on the chest", "price": 0},
    "golden_asteroid_bone": {"name": "Золотая кость", "prompt": "firmly clenching a massive, heavy gold-veined asteroid fragment shaped like a bone horizontally in its teeth", "price": 0},
    "ion_cape": {"name": "Ионный плащ", "prompt": "physically wearing a flowing superhero cape distinctly clasped to the collar, made of crackling bright blue electrical ion energy", "price": 0},
    "alien_translator": {"name": "Переводчик", "prompt": "physically wearing a bulky, heavy metallic translation device tightly strapped to the throat, emitting prominent glowing blue alien runes", "price": 0},
    "comet_tail_ribbon": {"name": "Лента кометы", "prompt": "a thick, physical glowing ribbon made of comet dust and ice crystals is tied tightly in a prominent bow around the dog's tail", "price": 0},
    "zero_g_harness": {"name": "Зеро-Г сбруя", "prompt": "the dog's torso is tightly strapped into a heavy-duty metallic zero-gravity harness, with prominent floating thruster modules attached to the back", "price": 0},
    "meteorite_shades": {"name": "Метеоритные очки", "prompt": "physically wearing incredibly thick sunglasses carved from dark meteorite stone, strapped tightly over the eyes, prominently reflecting the stars", "price": 0},
    "pulsar_watch": {"name": "Пульсар-часы", "prompt": "physically wearing a bulky, glowing futuristic smartwatch tightly strapped around one of the dog's front wrists, screen clearly visible", "price": 0},
    "energy_shield_orb": {"name": "Сфера-щит", "prompt": "physically wearing a metallic chest module that strongly projects a visible, highly detailed semi-transparent blue energy shield bubble entirely enclosing the dog", "price": 0},
    "quantum_leash": {"name": "Квантовый поводок", "prompt": "a glowing purple energy leash is physically and prominently clipped to the metal ring on the dog's collar, trailing off out of frame", "price": 0},
    "ruby_mars_stone": {"name": "Марсианский рубин", "prompt": "firmly clenching a massive, glowing red Martian ruby stone horizontally in its teeth, casting strong red light on the face", "price": 0},
    "cyberspace_aura": {"name": "Аура Матрицы", "prompt": "physically wearing a bulky collar projector that casts a highly visible, dense hologram of falling green digital matrix code directly onto the dog", "price": 0},
    
    # --- 🆕🔥 НОВЫЕ ПОСТУПЛЕНИЯ 🔥🆕 ---
    "exosuit_armor": {"name": "Экзо-броня", "prompt": "the dog's entire physical body is encased in heavy, bulky matte-black mechanical exosuit armor panels, tightly strapped to the torso and legs", "price": 110},
    "cyberpunk_jacket": {"name": "Куртка Найт-Сити", "prompt": "physically wearing an oversized black leather cyberpunk jacket securely zipped around the torso, featuring a highly prominent glowing neon-pink high collar", "price": 95},
    "tactical_vest": {"name": "Тактический жилет", "prompt": "physically wearing a heavy-duty olive drab military tactical vest aggressively strapped and buckled around the entire chest, prominent pouches visible", "price": 80},
    "warp_robe": {"name": "Варп-мантия", "prompt": "physically wearing a thick, heavy deep-purple velvet monk robe entirely covering the dog's body, tightly secured around the waist with a thick rope belt", "price": 70},
    "mech_harness": {"name": "Мех-сбруя", "prompt": "a massive, highly detailed metallic robotic exoskeleton frame is physically bolted and strapped entirely around the dog's torso and back", "price": 130},
    "general_hat": {"name": "Фуражка Генерала", "prompt": "physically wearing a rigid, formal black military commander's cap securely strapped to the very top of the head, prominent silver insignia clearly visible", "price": 90},
    "welding_mask": {"name": "Маска Сварщика", "prompt": "physically wearing a massive, heavy industrial metal welding mask securely strapped over and completely covering the dog's entire face", "price": 60},
    "santa_astro_hat": {"name": "Астро-Санта", "prompt": "physically wearing a thick, fuzzy red Santa hat securely strapped to the head, with a highly visible metallic life-support module bolted to its side", "price": 45},
    "straw_hat": {"name": "Шляпа Фермера", "prompt": "physically wearing a massive, wide-brimmed woven straw sun hat firmly tied under the dog's jaw with a prominent blue ribbon", "price": 30},
    "crown_of_comets": {"name": "Корона Комет", "prompt": "physically wearing a heavy, jagged obsidian stone crown resting firmly on the head, with three distinct glowing miniature comets orbiting the crown", "price": 180},
    "cyber_jaw": {"name": "Кибер-челюсть", "prompt": "the dog's entire lower jaw is physically encased inside a heavy, highly detailed mechanical chrome prosthetic jaw with prominent pistons and glowing LEDs", "price": 100},
    "drone_companion": {"name": "Дрон-спутник", "prompt": "a highly detailed metallic spy drone is physically tethered directly to the dog's collar via a thick, visible blue power cable, hovering prominently beside the head", "price": 75},
    "laser_eye": {"name": "Лазерный глаз", "prompt": "physically wearing a heavy metallic cybernetic eye patch firmly strapped around the head, completely covering one eye with a glowing red lens", "price": 85},
    "power_gloves": {"name": "Силовые лапы", "prompt": "all four paws are completely swallowed inside massive, incredibly bulky industrial robotic steel gauntlets with glowing orange vents", "price": 115},
    "data_monocle": {"name": "Голо-монокль", "prompt": "physically wearing a high-tech glass monocle device tightly strapped to the side of the head, prominently projecting a bright blue holographic screen", "price": 65},
    "diamond_grillz": {"name": "Гриллзы Сириуса", "prompt": "the dog's mouth is wide open, physically revealing highly prominent custom diamond-encrusted teeth covers catching intense bright light", "price": 140},
    "symbiote_friend": {"name": "Симбиот-Компаньон", "prompt": "a tiny, highly detailed physical alien creature is actively grabbing and sitting securely onto the top of the dog's head, prominently visible", "price": 1},
    "mecha_tail": {"name": "Кибер-хвост", "prompt": "the dog's entire tail is physically encased inside a highly detailed, articulated chrome robotic metal sleeve with prominent glowing blue joints", "price": 3},
    "cryo_gear": {"name": "Крио-генератор", "prompt": "physically wearing a massive futuristic metal backpack tightly strapped to the back, aggressively pumping out dense freezing white fog filling the floor", "price": 7},
    "hover_board": {"name": "Антиграв-доска", "prompt": "the dog is physically standing with all four paws firmly planted on top of a highly detailed metallic sci-fi hoverboard floating visibly above the floor", "price": 5},
    "holographic_butterfly": {"name": "Голо-бабочка", "prompt": "a highly detailed, physical glowing neon blue butterfly toy is resting directly and firmly onto the very tip of the dog's wet nose", "price": 5},
    "floating_halo": {"name": "Нимб Ангела", "prompt": "physically wearing a metallic headband that projects a highly visible, solid glowing golden ring hovering rigidly just above the head", "price": 90},
    "sub_bass_speakers": {"name": "Космо-Сабвуферы", "prompt": "two massive, highly detailed wooden sub-woofer speakers are physically strapped to the dog's back with thick, prominent leather harnesses crossing the chest", "price": 85},
    "rocket_boots": {"name": "Ракетные лапы", "prompt": "all four legs are physically inserted deep into massive, heavy metallic rocket boots with highly visible thruster flames firing near the floor", "price": 125},
    "dentist_drill": {"name": "Бормашина Академии", "prompt": "the dog's jaws are firmly clenching a high-speed pneumatic dental drill handpiece horizontally in its teeth, prominent mechanical details and cables visible", "price": 70}
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

    # 3. Износ оборудования (Чистота привязана к настроению и сытости)
    if dog['mood'] < 40 or dog['hunger'] < 40:
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
            tele_types.InlineKeyboardButton("🗺 Экспедиция", callback_data="dog_map"),
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

    elif action == "map":
        kb = tele_types.InlineKeyboardMarkup()
        kb.row(tele_types.InlineKeyboardButton("🪨 Астероидный пояс (-50 🔋)", callback_data="dog_exp_belt"))
        kb.row(tele_types.InlineKeyboardButton("🛰 Заброшенная станция (-30 🔋)", callback_data="dog_exp_station"))
        kb.row(tele_types.InlineKeyboardButton("🔙 Назад", callback_data="dog_back"))
        
        bot.edit_message_caption("🗺 **ВЫБОР ЛОКАЦИИ ДЛЯ ЭКСПЕДИЦИИ**\n\n"
                              "🪨 **Астероидный пояс**: Высокий риск, но можно найти залежи Пыли.\n"
                              "🛰 **Заброшенная станция**: Шанс найти секретные артефакты и экипировку.", 
                              call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        return

    elif action == "exp_station":
        from database import get_ship_date
        today = get_ship_date()
        
        # 🛡 ПРОВЕРКА НА ОГРАНИЧЕНИЕ ПО ВРЕМЕНИ (1 раз в день в любую экспедицию)
        if dog.get('last_exp', '') == today:
            bot.answer_callback_query(call.id, "🛰 Навигатор сообщает: Гипердвигатель на перезарядке. Доступен 1 полет в день!", show_alert=True)
            return

        if dog['energy'] >= 30:
            dog['energy'] -= 30
            dog['last_exp'] = today # Фиксируем полет
            
            import random
            from datetime import datetime
            
            # 🌟 Жесткая логика шансов (10% будни, 50% воскресенье)
            is_sunday = (datetime.now().weekday() == 6)
            drop_chance = 0.50 if is_sunday else 0.10
            
            if random.random() < drop_chance:
                secret_items = [k for k, v in DOG_SHOP.items() if v['price'] == 0]
                found_item = random.choice(secret_items)
                
                if found_item not in dog['items']:
                    dog['items'].append(found_item)
                    msg = f"🛰 **УСПЕХ!** Марти обыскал заброшенные палубы и нашел: *{DOG_SHOP[found_item]['name']}*! Проверьте гардероб."
                    if is_sunday: msg = "✨ **ВОСКРЕСНЫЙ БУСТ!** " + msg
                else:
                    msg = "🛰 Марти нашел обломки старого спутника, но ничего полезного."
            else:
                msg = "🛰 Экспедиция завершена. Станция пуста, артефактов не обнаружено."
            
            update_dog_data(user_id, dog)
            bot.answer_callback_query(call.id, msg, show_alert=True)
        else:
            bot.answer_callback_query(call.id, "❌ Недостаточно энергии для прыжка!", show_alert=True)
  
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

    elif action == "exp_belt":
        from database import get_ship_date
        today = get_ship_date()
        
        # 🛡 ПРОВЕРКА НА ОГРАНИЧЕНИЕ ПО ВРЕМЕНИ (Общий кулдаун с Заброшенной станцией)
        if dog.get('last_exp', '') == today:
            bot.answer_callback_query(call.id, "🪨 Сканеры перегружены. Доступен 1 полет в день!", show_alert=True)
            return

        if dog['energy'] >= 50:
            dog['energy'] -= 50
            dog['last_exp'] = today # Фиксируем полет
            
            import random
            from datetime import datetime
            
            # 🌟 Жесткая логика шансов (10% будни, 50% воскресенье)
            is_sunday = (datetime.now().weekday() == 6)
            drop_chance = 0.50 if is_sunday else 0.10
            
            if random.random() < drop_chance:
                found_dust = random.randint(50, 150)
                if is_sunday:
                    found_dust = int(found_dust * 2) # Удваиваем пыль по воскресеньям
                
                u_data = get_user_data(user_id)
                u_data['spendable_dust'] += found_dust
                update_user_data(user_id, u_data) 
                
                msg = f"🪨 УСПЕХ! Марти пробурил астероид: +{found_dust} 💰 Пыли!"
                if is_sunday: msg = "🔥 **ВОСКРЕСНЫЙ МЕГА-КРАШ!** " + msg
            else:
                msg = "🪨 Пусто... Марти увернулся от метеорита и вернулся ни с чем."
            
            update_dog_data(user_id, dog)
            bot.answer_callback_query(call.id, msg, show_alert=True)
        else:
            bot.answer_callback_query(call.id, "❌ Для полета в пояс нужно 50 🔋 Энергии!", show_alert=True)

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
            # 🟢 ДОБАВЛЕНА ПРОВЕРКА: v['price'] > 0 (Скрываем секретный лут с витрины)
            if k not in dog['items'] and v['price'] > 0:
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
