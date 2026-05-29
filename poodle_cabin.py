import time
import hashlib
from datetime import datetime
from telebot import types as tele_types
from database import (get_dog_data, update_dog_data, spend_dust, get_user_data, 
                      equip_dog_item, unequip_dog_item, process_dog_walk, update_user_data)
from neural_draw import get_cascade_image 

# 🟢 КВАНТОВЫЙ КЭШ (Сейф для бесплатных картинок)
CABIN_IMAGE_CACHE = {}

# 📥 ВРЕМЕННЫЕ БУФЕРЫ С ЗАЩИТОЙ ОТ УТЕЧКИ ПАМЯТИ
# Структура: {user_id: {"items": [...], "last_time": timestamp}}
SHOP_CART = {}        
WARDROBE_BUFFER = {}  

def clean_dead_sessions():
    """Автоматически вычищает из ОЗУ брошенные корзины и гардеробы старше 15 минут"""
    now = time.time()
    cutoff = 15 * 60
    
    dead_shop = [uid for uid, sess in SHOP_CART.items() if now - sess.get("last_time", 0) > cutoff]
    for uid in dead_shop:
        del SHOP_CART[uid]
        
    dead_wardrobe = [uid for uid, sess in WARDROBE_BUFFER.items() if now - sess.get("last_time", 0) > cutoff]
    for uid in dead_wardrobe:
        del WARDROBE_BUFFER[uid]

DOG_SHOP = {
    # --- БАЗОВАЯ КОСМИЧЕСКАЯ ЭКИПИРОВКА ---
    "space_helmet": {"name": "Стеклянный шлем", "prompt": "Astronaut bubble helmet, clear glass, massive, metal locking ring, neon reflections", "price": 40},
    "star_suit": {"name": "Скафандр", "prompt": "White padded astronaut spacesuit, Orion patches, deep fabric folds, bulky", "price": 60},
    "cool_glasses": {"name": "Кибер-очки", "prompt": "Cyberpunk sunglasses, neon glow, thick metal frames, blue light reflection", "price": 30},
    "bandana": {"name": "Бандана Орион", "prompt": "Bright blue fabric bandana, knotted, frayed edges, textile texture", "price": 20},
    "laser_collar": {"name": "Лазерный ошейник", "prompt": "Glowing neon-cyan laser collar, thick buckle, light flares on chin", "price": 25},
    "pilot_cap": {"name": "Кепка пилота", "prompt": "Vintage aviator pilot hat, brown leather, thick buckled chin straps", "price": 35},
    "nebula_scarf": {"name": "Шарф Небула", "prompt": "Cosmic-purple silk scarf, massive thick drapery, heavy fabric", "price": 15},
    "cyber_paws": {"name": "Кибер-лапы", "prompt": "Metallic robotic mech-boots, matte steel plates, glowing joints", "price": 45},
    "galaxy_crown": {"name": "Корона Галактики", "prompt": "Golden royal crown, detailed, heavy, encrusted with glowing jewels", "price": 80},
    "steampunk_goggles": {"name": "Стимпанк-очки", "prompt": "Brass steampunk goggles, leather belts, heavy, vintage design", "price": 30},
    "neon_harness": {"name": "Неоновая сбруя", "prompt": "Neon-green tactical military harness, thick nylon straps, plastic buckles", "price": 40},
    "comet_bowtie": {"name": "Галстук-комета", "prompt": "Glowing magical cosmic bowtie, oversized, ember particles", "price": 20},
    "radar_monocle": {"name": "Монокль-радар", "prompt": "High-tech cybernetic monocle, glowing green holographic UI", "price": 50},
    "alien_antenna": {"name": "Антенны пришельца", "prompt": "Black headband, two bouncy glowing green alien antennas, sci-fi", "price": 15},
    "astro_boots": {"name": "Астро-ботинки", "prompt": "Oversized white puffy astronaut moon boots, thick rubber soles", "price": 35},
    "heavy_gold_chain": {"name": "Золотая цепь", "prompt": "Thick solid gold Cuban link chain, gold bone pendant, metallic sheen", "price": 55},
    "diamond_collar": {"name": "Бриллиантовый ошейник", "prompt": "Ultra-thick luxury collar, encrusted with thousands of diamonds, reflective", "price": 90},
    "star_pendant": {"name": "Кулон Полярная звезда", "prompt": "Glowing blue star-shaped crystal pendant, silver rope chain", "price": 30},
    "warp_jetpack": {"name": "Варп-ранец", "prompt": "Metallic sci-fi jetpack, industrial nylon belts, blue plasma nozzles", "price": 70},
    "saturn_ring": {"name": "Кольцо Сатурна", "prompt": "Mechanical collar base, glowing holographic golden planetary ring", "price": 45},
    "plasma_cloak": {"name": "Плазменный плащ", "prompt": "Superhero cape, bright semi-transparent blue plasma energy, flowing drapery", "price": 65},
    "ufo_hat": {"name": "Шапка-тарелка", "prompt": "Silver metal UFO flying saucer, hat style, metallic sheen", "price": 40},
    "vr_visor_2": {"name": "Визор VR-Орион", "prompt": "Modern white VR headset, bulky, thick head straps", "price": 50},
    "dual_aura": {"name": "Аура Контроллера", "prompt": "Intense white and neon-blue energy aura, light rays, radiating", "price": 25},
    "brilliant_smile": {"name": "Ослепительная улыбка", "prompt": "Exaggerated human-like smile, perfect white teeth, diamond spark", "price": 100},
    "dentist_mirror": {"name": "Зеркало Космо-Врача", "prompt": "Professional stainless steel dental mirror, highly reflective chrome, detailed", "price": 15},
    "detective_pipe": {"name": "Трубка Шерлока", "prompt": "Polished wooden tobacco pipe, wisps of smoke, detailed", "price": 20},
    "dragon_wings": {"name": "Крылья Дракона", "prompt": "Black leather chest harness, two massive wide-open dragon wings", "price": 75},
    "taco_suit": {"name": "Костюм Тако", "prompt": "Plush taco shell costume, fabric lettuce and cheese, food aesthetic", "price": 35},
    "thug_beanie": {"name": "Шапка Thug Life", "prompt": "Black knitted beanie hat, 3D white embroidered text, streetwear", "price": 15},
    "cosmic_boots": {"name": "Луноходы", "prompt": "Neon-blue space boots, heavy industrial treads, protective design", "price": 40},
    "chef_hat": {"name": "Колпак Кока", "prompt": "Tall white pleated chef hat, red fabric scarf", "price": 20},
    "holographic_wings": {"name": "Крылья Ангела", "prompt": "Metallic chest backpack, two massive glowing white holographic angel wings", "price": 85},
    "monocle_tophat": {"name": "Джентльмен", "prompt": "Formal black top hat, golden monocle, elegant style", "price": 50},
    "crown_of_light": {"name": "Легендарный Венец", "prompt": "Metallic headband, projected glowing crown of pure white light", "price": 150},

    # --- 🌌 СЕКРЕТНЫЙ ЛУТ ---
    "ancient_relic": {"name": "Древний артефакт", "prompt": "Glowing ancient alien stone artifact, golden light, heavy", "price": 0},
    "broken_android_ear": {"name": "Ухо андроида", "prompt": "Rusted metal android ear trophy, dangling, mechanical details", "price": 0},
    "void_collar": {"name": "Ошейник Пустоты", "prompt": "Light-absorbing black void material collar, thick, abstract", "price": 0},
    "plasma_ball": {"name": "Плазменный мяч", "prompt": "Glowing glass plasma ball toy, visible static electricity", "price": 0},
    "cyber_tail_ring": {"name": "Кольцо на хвост", "prompt": "Chrome robotic ring, bright glowing blue LEDs, articulated", "price": 0},
    "starlight_medal": {"name": "Медаль Звезды", "prompt": "Massive star-shaped medal, heavy, silver chain", "price": 0},
    "holographic_map": {"name": "Голо-карта", "prompt": "Collar module, projected 3D holographic star map, glowing", "price": 0},
    "nebula_boots": {"name": "Туманные сапоги", "prompt": "Translucent boots, swirling colorful nebula gas inside, glowing", "price": 0},
    "black_hole_pendant": {"name": "Кулон-Сингулярность", "prompt": "Glass sphere pendant, realistic tiny black hole inside", "price": 0},
    "golden_asteroid_bone": {"name": "Золотая кость", "prompt": "Gold-veined asteroid fragment, bone shape, metallic luster", "price": 0},
    "ion_cape": {"name": "Ионный плащ", "prompt": "Superhero cape, crackling blue electrical ion energy", "price": 0},
    "alien_translator": {"name": "Переводчик", "prompt": "Bulky metallic translation device, glowing blue alien runes", "price": 0},
    "comet_tail_ribbon": {"name": "Лента кометы", "prompt": "Glowing ribbon, comet dust and ice crystals, bow", "price": 0},
    "zero_g_harness": {"name": "Зеро-Г сбруя", "prompt": "Metallic zero-gravity harness, floating thruster modules", "price": 0},
    "meteorite_shades": {"name": "Метеоритные очки", "prompt": "Sunglasses carved from dark meteorite stone, reflective", "price": 0},
    "pulsar_watch": {"name": "Пульсар-часы", "prompt": "Bulky glowing futuristic smartwatch, digital screen", "price": 0},
    "energy_shield_orb": {"name": "Сфера-щит", "prompt": "Chest module, semi-transparent blue energy shield bubble", "price": 0},
    "quantum_leash": {"name": "Квантовый поводок", "prompt": "Glowing purple energy leash, trailing off frame", "price": 0},
    "ruby_mars_stone": {"name": "Марсианский рубин", "prompt": "Glowing red Martian ruby stone, brilliant, intense light", "price": 0},
    "cyberspace_aura": {"name": "Аура Матрицы", "prompt": "Collar projector, dense hologram of falling green digital matrix code", "price": 0},

    # --- 🆕🔥 НОВЫЕ ПОСТУПЛЕНИЯ 🔥🆕 ---
    "exosuit_armor": {"name": "Экзо-броня", "prompt": "Matte-black mechanical exosuit armor, industrial panels, heavy", "price": 110},
    "cyberpunk_jacket": {"name": "Куртка Найт-Сити", "prompt": "Oversized black leather cyberpunk jacket, neon-pink high collar, zip-up", "price": 95},
    "tactical_vest": {"name": "Тактический жилет", "prompt": "Olive drab military tactical vest, pouches, heavy-duty", "price": 80},
    "warp_robe": {"name": "Варп-мантия", "prompt": "Deep-purple velvet monk robe, heavy, rope belt", "price": 70},
    "mech_harness": {"name": "Мех-сбруя", "prompt": "Metallic robotic exoskeleton frame, articulated, industrial bolts", "price": 130},
    "general_hat": {"name": "Фуражка Генерала", "prompt": "Rigid black military commander's cap, silver insignia", "price": 90},
    "welding_mask": {"name": "Маска Сварщика", "prompt": "Heavy industrial metal welding mask, dark glass visor", "price": 60},
    "santa_astro_hat": {"name": "Астро-Санта", "prompt": "Fuzzy red Santa hat, bolted metallic life-support module", "price": 45},
    "straw_hat": {"name": "Шляпа Фермера", "prompt": "Wide-brimmed woven straw hat, blue ribbon tie", "price": 30},
    "crown_of_comets": {"name": "Корона Комет", "prompt": "Jagged obsidian stone crown, three orbiting miniature glowing comets", "price": 180},
    "cyber_jaw": {"name": "Кибер-челюсть", "prompt": "Mechanical chrome prosthetic jaw, pistons, glowing blue LEDs", "price": 100},
    "drone_companion": {"name": "Дрон-спутник", "prompt": "Metallic spy drone, blue power cable, hovering nearby", "price": 75},
    "laser_eye": {"name": "Лазерный глаз", "prompt": "Metallic cybernetic eye patch, glowing red lens", "price": 85},
    "power_gloves": {"name": "Силовые лапы", "prompt": "Bulky industrial robotic steel gauntlets, glowing orange vents", "price": 115},
    "data_monocle": {"name": "Голо-монокль", "prompt": "High-tech glass monocle, bright blue holographic screen projection", "price": 65},
    "diamond_grillz": {"name": "Гриллзы Сириуса", "prompt": "Custom diamond-encrusted teeth, bright light reflections", "price": 140},
    "symbiote_friend": {"name": "Симбиот-Компаньон", "prompt": "Tiny alien creature, sitting on head, detailed tentacles", "price": 1},
    "mecha_tail": {"name": "Кибер-хвост", "prompt": "Articulated chrome robotic metal tail sleeve, glowing blue joints", "price": 3},
    "cryo_gear": {"name": "Крио-генератор", "prompt": "Futuristic metal backpack, pumping freezing white fog", "price": 7},
    "hover_board": {"name": "Антиграв-доска", "prompt": "Metallic sci-fi hoverboard, glowing underside", "price": 5},
    "holographic_butterfly": {"name": "Голо-бабочка", "prompt": "Glowing neon blue butterfly toy, holographic wings", "price": 5},
    "floating_halo": {"name": "Нимб Ангела", "prompt": "Solid glowing golden ring halo, hovering, rigid", "price": 90},
    "sub_bass_speakers": {"name": "Космо-Сабвуферы", "prompt": "Two wooden sub-woofer speakers, leather harnesses, heavy", "price": 85},
    "rocket_boots": {"name": "Ракетные лапы", "prompt": "Metallic rocket boots, thruster flames, industrial treads", "price": 125},
    "dentist_drill": {"name": "Бормашина Академии", "prompt": "High-speed pneumatic dental drill, highly detailed mechanical handpiece, cables, photorealistic chrome", "price": 70},
    "leather_biker_jacket": {"name": "Байкерская косуха", "prompt": "Miniature black leather biker jacket, metal zippers, silver studs, heavy textile texture, classic punk style", "price": 85},
    "neon_hoodie": {"name": "Худи Навигатора", "prompt": "Bright neon-orange oversized streetwear hoodie with holographic cosmic strings, soft cotton fabric texture", "price": 55},
    "steampunk_vest": {"name": "Стимпанк-жилет", "prompt": "Vintage brown velvet vest, brass gears embroidery, tiny gold buttons, Victorian sci-fi aesthetic", "price": 75},
    "hawaiian_shirt": {"name": "Гавайская рубашка", "prompt": "Colorful tropical Hawaiian beach shirt, print with mini palm trees and planets, lightweight fabric", "price": 40},
    "royal_mantle": {"name": "Мантия Императора", "prompt": "Heavy royal red velvet mantle, luxury white fur edges, golden embroidery threads, majestic look", "price": 120},
    "starfleet_uniform": {"name": "Форма Звездного Флота", "prompt": "Futuristic sleek sci-fi starfleet uniform jacket, deep blue and yellow panels, metallic comm-badge on chest", "price": 90},
    "cosmic_sweater": {"name": "Вязаный свитер", "prompt": "Warm cozy knitted wool winter sweater, pixelated white and blue pixel-art UFO patterns, soft yarn texture", "price": 50},
    "samurai_armor": {"name": "Доспех Самурая", "prompt": "Traditional crimson-red samurai chest plate armor, lacquered wood plates, golden silk cords binding", "price": 140},
    "detective_trench": {"name": "Плащ Детектива", "prompt": "Classic tan-beige canvas trench coat, high popped collar, belted waist, dark noir atmosphere fabric", "price": 80},
    "matrix_coat": {"name": "Плащ Нео", "prompt": "Long floor-length glossy black leather duster coat, cybernetic matrix styling, highly reflective texture", "price": 110}
}

WARDROBE_CATEGORIES = {
    "head": ["🎩 Голова", ["head", "top of the head"]],
    "face": ["👓 Лицо", ["eyes", "face", "left eye", "right eye", "one eye"]],
    "mouth": ["👄 Пасть", ["mouth", "lower jaw", "teeth", "nose"]],
    "neck": ["🧣 Шея", ["neck"]],
    "torso": ["👕 Туловище", ["body", "chest"]],
    "back": ["🪁 Спина", ["back"]],
    "paws": ["🐾 Лапы", ["paws", "front paws", "front paw", "under the paws"]],
    "tail": ["💫 Хвост", ["tail"]]
}

def get_item_slot(item_key):
    mapping = {
        "space_helmet": "head", "pilot_cap": "head", "galaxy_crown": "head",
        "alien_antenna": "head", "ufo_hat": "head", "thug_beanie": "head",
        "chef_hat": "head", "monocle_tophat": "head", "crown_of_light": "head",
        "general_hat": "head", "santa_astro_hat": "head", "straw_hat": "head",
        "crown_of_comets": "head", "symbiote_friend": "top of the head", "floating_halo": "head",
        
        "cool_glasses": "eyes", "steampunk_goggles": "eyes", "radar_monocle": "left eye",
        "vr_visor_2": "eyes", "meteorite_shades": "eyes", "data_monocle": "right eye",
        "laser_eye": "one eye", "welding_mask": "face",
        
        "brilliant_smile": "mouth", "dentist_mirror": "mouth", "detective_pipe": "mouth",
        "ancient_relic": "mouth", "golden_asteroid_bone": "mouth", "ruby_mars_stone": "mouth",
        "cyber_jaw": "lower jaw", "diamond_grillz": "teeth", "holographic_butterfly": "nose",
        "dentist_drill": "mouth",
        
        "bandana": "neck", "laser_collar": "neck", "nebula_scarf": "neck",
        "heavy_gold_chain": "neck", "diamond_collar": "neck", "star_pendant": "neck",
        "saturn_ring": "neck", "broken_android_ear": "neck", "void_collar": "neck",
        "starlight_medal": "neck", "holographic_map": "neck", "black_hole_pendant": "neck",
        "alien_translator": "neck", "quantum_leash": "neck", "cyberspace_aura": "neck",
        
        "star_suit": "body", "neon_harness": "body", "comet_bowtie": "chest",
        "taco_suit": "body", "exosuit_armor": "body", "cyberpunk_jacket": "body",
        "tactical_vest": "body", "warp_robe": "body", "mech_harness": "body",
        "zero_g_harness": "body", "energy_shield_orb": "chest", "dual_aura": "body",
        "leather_biker_jacket": "body", "neon_hoodie": "body", "steampunk_vest": "body",
        "hawaiian_shirt": "body", "royal_mantle": "body", "starfleet_uniform": "body",
        "cosmic_sweater": "body", "samurai_armor": "body", "detective_trench": "body",
        "matrix_coat": "body",
      
        "warp_jetpack": "back", "plasma_cloak": "back", "dragon_wings": "back",
        "holographic_wings": "back", "ion_cape": "back", "drone_companion": "back",
        "cryo_gear": "back", "sub_bass_speakers": "back",
        
        "cyber_paws": "paws", "power_gloves": "front paws", "astro_boots": "paws", "cosmic_boots": "paws",
        "nebula_boots": "paws", "pulsar_watch": "front paw", "hover_board": "under the paws", "rocket_boots": "paws",
        
        "cyber_tail_ring": "tail", "comet_tail_ribbon": "tail", "mecha_tail": "tail"
    }
    return mapping.get(item_key, "body")

def get_deterministic_dna(user_id, gender=None):
    hash_obj = hashlib.md5(str(user_id).encode())
    digest = hash_obj.hexdigest()
    
    builds = ["athletic", "compact", "dainty", "sturdy"]
    ears = ["floppy long ears covered in tight curls", "characteristic long drooping poodle ears"]
    noses = ["black button nose", "distinctive small black nose"]
    eyes = ["round expressive dark eyes", "almond-shaped dark eyes"]
    fur_types = ["tightly curled hypoallergenic coat", "dense soft curly fur", "tight poodle curls", "well-groomed curly coat"]
    colors = ["snow-white", "ash-grey", "coffee-brown", "apricot", "silver-grey", "cream"]
    traits = ["brave", "shy", "clumsy", "energetic", "calm", "mischievous"]
    markings = ["a small white patch on chest", "a white tip on tail", "no special markings", "one white paw"]
    
    if not gender:
        gender = ["male", "female"][int(digest[0:3], 16) % 2]
    
    build = builds[int(digest[3:7], 16) % len(builds)]
    ear = ears[int(digest[7:11], 16) % len(ears)]
    nose = noses[int(digest[11:15], 16) % len(noses)]
    eye = eyes[int(digest[15:19], 16) % len(eyes)]
    fur = fur_types[int(digest[19:23], 16) % len(fur_types)]
    color = colors[int(digest[23:26], 16) % len(colors)]
    trait = traits[int(digest[26:29], 16) % len(traits)]
    mark = markings[int(digest[29:32], 16) % len(markings)]
    
    return {
        "desc": f"Toy Poodle, {color} {gender} with {build} build, {ear}, {nose}, {eye}, {fur}, {mark}",
        "trait": trait,
        "gender": gender
    }

def get_growth_stage(level):
    if level < 5:
        return "tiny, very small puppy, soft rounded facial features, clumsy but adorable posture, fluffy puppy-like coat with loose curls"
    elif level < 12:
        return "adolescent dog, lean and lanky, slightly longer legs, energetic and curious posture, developing tight poodle curls"
    else:
        return "adult dog, elegant and dignified, well-proportioned, signature toy poodle stature, perfectly groomed dense tight curls"

def get_cabin_style(level):
    if level < 5:
        return "rusty industrial spacecraft cabin, exposed pipes, basic metal walls"
    elif level < 12:
        return "standard sleek modern spaceship cabin, clean white panels, subtle neon trims"
    else:
        return "luxury captain's quarters, high-end futuristic mahogany textures, advanced glowing holographic displays"

def get_dog_prompt(dog, user_id):
    if dog['status'] == 'dead':
        return "empty dog bed, abandoned futuristic spaceship cabin, lonely atmosphere, realistic photographic style", 42

    gender = dog.get('gender', 'male')
    dna_data = get_deterministic_dna(user_id, gender=gender)
    dna_desc = dna_data['desc']
    
    cabin_tier = get_cabin_style(dog['level'])
    u_data = get_user_data(user_id)
    dust = u_data['spendable_dust']
    hour = datetime.now().hour
    
    dust_str = "glowing cosmic dust" if dust > 50 else "a few specks of dust"
    
    if 6 <= hour < 12: 
        time_state = "morning"
        dog_pos = "sitting on the soft dog bed"
        bg_desc = "morning light through the space window"
    elif 12 <= hour < 22: 
        time_state = "evening"
        dog_pos = "sitting on the desk right next to an open glowing laptop"
        bg_desc = "deep space view through the porthole window"
    else: 
        time_state = "night"
        dog_pos = "sleeping curled up on the dog bed"
        bg_desc = "dark room, moody night lighting, starry space outside"

    equipped = dog.get('equipped', [])
    
    # 🛡 ОБНОВЛЕННЫЙ ПРЕДОХРАНИТЕЛЬ: Лимит увеличен до 7 предметов!
    if len(equipped) > 7:
        import random as rnd
        equipped = rnd.sample(equipped, 7)

    slots_data = {}
    for k in equipped:
        if k in DOG_SHOP:
            slot = get_item_slot(k) 
            if slot not in slots_data: slots_data[slot] = []
            slots_data[slot].append(DOG_SHOP[k]["prompt"])
    
    wearables_parts = []
    for slot, prompts in slots_data.items():
        # Более жесткая привязка одежды к конкретной части тела
        wearables_parts.append(f"wearing {', '.join(prompts)} directly on its {slot}")
        
    wearables_str = f" ATTIRE: The dog is {', and '.join(wearables_parts)}." if wearables_parts else ""

    full_prompt = (
        f"RAW photo, highly detailed, 35mm lens. "
        f"SUBJECT: Purebred Toy Poodle, {dna_desc}. "
        f"ACTION: The dog is {dog_pos}. "
        f"{wearables_str} "
        f"SCENE: {cabin_tier}, {bg_desc}, {dust_str} on the surface. "
        # 🟢 ДОБАВЛЕНО В NEGATIVE: Запрет на одежду, валяющуюся рядом или висящую в воздухе
        "NEGATIVE: Yorkshire terrier, cartoon, 3d render, floating items, detached accessories, missing clothes, clothes on the floor, items in background."
    )
    
    seed_string = f"{user_id}_{cabin_tier}_{time_state}"
    static_seed = int(hashlib.md5(seed_string.encode()).hexdigest()[:8], 16) % 1000000
    
    return full_prompt, static_seed

def send_dog_menu(bot, chat_id, user_id):
    dog = get_dog_data(user_id)
    u_data = get_user_data(user_id)
    
    from database import get_ship_date
    today = get_ship_date() 
    
    if dog['date'] != today:
        dog['hunger'] -= 20; dog['energy'] -= 25; dog['mood'] -= 15
        dog['date'] = today
        if dog['hunger'] <= 0 or dog['energy'] <= 0: dog['status'] = 'dead'
        update_dog_data(user_id, dog)

    full_prompt, seed = get_dog_prompt(dog, user_id)
    
    if dog['status'] == 'dead':
        text = "🛰 **СИГНАЛ ПОТЕРЯН**\n\nКомандор, твой верный пес покинул корабль. Каюта пуста..."
        kb = tele_types.InlineKeyboardMarkup().add(tele_types.InlineKeyboardButton("🛰 Вызвать нового щенка (-100 💰)", callback_data="dog_resurrect"))
    else:
        equipped_names = [DOG_SHOP[k]['name'] for k in dog.get('equipped', []) if k in DOG_SHOP]
        style_info = ", ".join(equipped_names) if equipped_names else "Ничего не надето"

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
            tele_types.InlineKeyboardButton("🛒 Maгазин", callback_data="dog_shop") 
        )

        if dog['level'] >= 10 and current_prof == 'Кадет':
            kb.row(tele_types.InlineKeyboardButton(text="🎓 Выбрать специализацию", callback_data="dog_choose_prof"))
  
        cache_key = f"{user_id}_{full_prompt}"
        
        if cache_key in CABIN_IMAGE_CACHE:
            bot.send_photo(chat_id, photo=CABIN_IMAGE_CACHE[cache_key], caption=text, parse_mode="Markdown", reply_markup=kb)
        else:
            bot.send_chat_action(chat_id, 'upload_photo')
            image_bytes = get_cascade_image(full_prompt, seed)
            if image_bytes:
                msg = bot.send_photo(chat_id, photo=image_bytes, caption=text, parse_mode="Markdown", reply_markup=kb)
                if len(CABIN_IMAGE_CACHE) > 500:
                    CABIN_IMAGE_CACHE.clear()
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
        
        if dog.get('last_exp', '') == today:
            bot.answer_callback_query(call.id, "🛰 Навигатор сообщает: Гипердвигатель на перезарядке. Доступен 1 полет в день!", show_alert=True)
            return

        if dog['energy'] >= 30:
            dog['energy'] -= 30
            dog['last_exp'] = today
            
            import random
            from datetime import datetime
            
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
        
        if dog.get('last_exp', '') == today:
            bot.answer_callback_query(call.id, "🪨 Сканеры перегружены. Доступен 1 полет в день!", show_alert=True)
            return

        if dog['energy'] >= 50:
            dog['energy'] -= 50
            dog['last_exp'] = today
            
            import random
            from datetime import datetime
            
            is_sunday = (datetime.now().weekday() == 6)
            drop_chance = 0.50 if is_sunday else 0.10
            
            if random.random() < drop_chance:
                found_dust = random.randint(50, 150)
                if is_sunday: found_dust = int(found_dust * 2)
                
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
                              "🔧 **Бортинженер** - скидка 20% in магазине.\n"
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
  
        # === ГАРДЕРОБ ПУДЕЛЯ ===
    elif action == "wardrobe":
        clean_dead_sessions() # Скидываем старый балласт
        
        # 🟢 ИСПРАВЛЕНИЕ: Загружаем старые вещи ТОЛЬКО если юзер зашел первый раз. 
        # Если он вернулся по кнопке "Назад" из категории — сохраняем его примерку!
        if user_id not in WARDROBE_BUFFER:
            WARDROBE_BUFFER[user_id] = {
                "items": list(dog.get('equipped', [])),
                "last_time": time.time()
            }
        else:
            WARDROBE_BUFFER[user_id]["last_time"] = time.time()
            
        text = "👕 **ГАРДЕРОБ МАРТИ (РЕЖИМ ПРИМЕРКИ)**\n\nВыбирайте вещи. Нажмите 'СОХРАНИТЬ И ВЫЙТИ' для применения костюма."
        kb = tele_types.InlineKeyboardMarkup(row_width=2)
        
        for key, value in WARDROBE_CATEGORIES.items():
            kb.add(tele_types.InlineKeyboardButton(value[0], callback_data=f"dog_cat_{key}"))
            
        kb.row(tele_types.InlineKeyboardButton("❌ СНЯТЬ ВСЁ", callback_data="dog_strip_all"))
        kb.row(tele_types.InlineKeyboardButton("🔙 СОХРАНИТЬ И ВЫЙТИ", callback_data="dog_wardrobe_save"))
        bot.edit_message_caption(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        return

    elif action == "strip_all":
        if user_id not in WARDROBE_BUFFER:
            WARDROBE_BUFFER[user_id] = {"items": [], "last_time": time.time()}
        else:
            WARDROBE_BUFFER[user_id]["items"] = []
            WARDROBE_BUFFER[user_id]["last_time"] = time.time()
            
        bot.answer_callback_query(call.id, "🪐 Все вещи сняты! Нажмите Выход для сохранения.")
        
        # Отрисовываем меню вручную, чтобы не вызывать сброс буфера из основного блока wardrobe
        text = "👕 **ГАРДЕРОБ МАРТИ (РЕЖИМ ПРИМЕРКИ)**\n\nВыбирайте вещи. Нажмите 'СОХРАНИТЬ И ВЫЙТИ' для применения костюма."
        kb = tele_types.InlineKeyboardMarkup(row_width=2)
        
        for key, value in WARDROBE_CATEGORIES.items():
            kb.add(tele_types.InlineKeyboardButton(value[0], callback_data=f"dog_cat_{key}"))
            
        kb.row(tele_types.InlineKeyboardButton("❌ СНЯТЬ ВСЁ", callback_data="dog_strip_all"))
        kb.row(tele_types.InlineKeyboardButton("🔙 СОХРАНИТЬ И ВЫЙТИ", callback_data="dog_wardrobe_save"))
        bot.edit_message_caption(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        return

    elif action.startswith("cat_"):
        cat_key = action.replace("cat_", "")
        allowed_slots = WARDROBE_CATEGORIES[cat_key][1]
        cat_name = WARDROBE_CATEGORIES[cat_key][0]
        
        if user_id not in WARDROBE_BUFFER:
            WARDROBE_BUFFER[user_id] = {"items": list(dog.get('equipped', [])), "last_time": time.time()}
        else:
            WARDROBE_BUFFER[user_id]["last_time"] = time.time()
            
        text = f"👕 **{cat_name}**\nОтметьте галочками то, что хотите надеть:"
        kb = tele_types.InlineKeyboardMarkup(row_width=1)
        
        found_any = False
        for item_key in dog['items']:
            if item_key not in DOG_SHOP:
                continue
                
            if get_item_slot(item_key) in allowed_slots:
                found_any = True
                name = DOG_SHOP[item_key]['name']
                
                is_in_buffer = item_key in WARDROBE_BUFFER[user_id]["items"]
                btn_text = f"✅ {name}" if is_in_buffer else f"⬜️ {name}"
                
                kb.add(tele_types.InlineKeyboardButton(btn_text, callback_data=f"dog_togbuff_{item_key}_{cat_key}"))
                
        if not found_any:
            text = f"👕 **{cat_name}**\nУ вас нет вещей для этого слота."
            
        kb.add(tele_types.InlineKeyboardButton("🔙 Назад к категориям", callback_data="dog_wardrobe"))
        bot.edit_message_caption(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        return

    elif action.startswith("togbuff_"):
        parts = action.replace("togbuff_", "").rsplit("_", 1)
        item_key = parts[0]
        cat_key = parts[1]
        
        # Правильная инициализация словаря
        if user_id not in WARDROBE_BUFFER:
            WARDROBE_BUFFER[user_id] = {"items": list(dog.get('equipped', [])), "last_time": time.time()}
            
        WARDROBE_BUFFER[user_id]["last_time"] = time.time()
        current_items = WARDROBE_BUFFER[user_id]["items"]
        
        if item_key in current_items:
            current_items.remove(item_key)
            bot.answer_callback_query(call.id, "Предмет снят")
        else:
            target_slot = get_item_slot(item_key)
            current_items = [item for item in current_items if get_item_slot(item) != target_slot]
            current_items.append(item_key)
            bot.answer_callback_query(call.id, "Предмет надет")
            
        WARDROBE_BUFFER[user_id]["items"] = current_items
        
        call.data = f"dog_cat_{cat_key}"
        handle_dog_callback(bot, call)
        return

    elif action == "wardrobe_save":
        if user_id in WARDROBE_BUFFER:
            dog['equipped'] = WARDROBE_BUFFER[user_id]["items"]
            update_dog_data(user_id, dog)
            del WARDROBE_BUFFER[user_id] # Выгружаем сессию из ОЗУ сразу после коммита
            
        bot.answer_callback_query(call.id, "🚀 Гардероб сохранен!")
        try: bot.delete_message(call.message.chat.id, call.message.message_id)
        except: pass
        send_dog_menu(bot, call.message.chat.id, user_id)
        return

    # === МАГАЗИН ПУДЕЛЯ ===
    elif action == "shop":
        clean_dead_sessions()
        
        if user_id not in SHOP_CART:
            SHOP_CART[user_id] = {"items": [], "last_time": time.time()}
        else:
            SHOP_CART[user_id]["last_time"] = time.time()
            
        from database import get_dog_profession
        prof = get_dog_profession(user_id)
        
        text = "🛒 **МАГАЗИН АКАДЕМИИ (КОРЗИНА ПОКУПОК)**\n\nВыбирайте товары по категориям. Покупка оформится при нажатии кнопки 'ОФОРМИТЬ ПОКУПКУ'."
        if "Инженер" in prof:
            text += "\n\n🛠 *Активирована скидка Бортинженера: -20%!*"

        kb = tele_types.InlineKeyboardMarkup(row_width=2)
        
        for key, value in WARDROBE_CATEGORIES.items():
            kb.add(tele_types.InlineKeyboardButton(value[0], callback_data=f"dog_shopcat_{key}"))
        
        total_price = 0
        for item in SHOP_CART[user_id]["items"]:
            if item in DOG_SHOP:
                p = DOG_SHOP[item]['price']
                if "Инженер" in prof: p = int(p * 0.8)
                total_price += p
        
        kb.row(tele_types.InlineKeyboardButton(f"🛍 ОФОРМИТЬ ПОКУПКУ ({total_price} 💰)", callback_data="dog_shop_checkout"))
        kb.row(tele_types.InlineKeyboardButton("🔙 ОТМЕНА", callback_data="dog_shop_cancel"))
        
        bot.edit_message_caption(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        return

    elif action.startswith("shopcat_"):
        cat_key = action.replace("shopcat_", "")
        allowed_slots = WARDROBE_CATEGORIES[cat_key][1]
        cat_name = WARDROBE_CATEGORIES[cat_key][0]
        
        if user_id not in SHOP_CART:
            SHOP_CART[user_id] = {"items": [], "last_time": time.time()}
        else:
            SHOP_CART[user_id]["last_time"] = time.time()
            
        from database import get_dog_profession
        prof = get_dog_profession(user_id)
        
        text = f"🛒 **{cat_name}**\nКликните на вещь для добавления в корзину:"
        if "Инженер" in prof: 
            text += "\n🛠 *Скидка Бортинженера -20% применена!*"
            
        kb = tele_types.InlineKeyboardMarkup(row_width=1)
        found_any = False
        
        for k, v in DOG_SHOP.items():
            if get_item_slot(k) in allowed_slots and v['price'] > 0:
                found_any = True
                price = int(v['price'] * 0.8) if "Инженер" in prof else v['price']
                
                if k in dog.get('items', []):
                    btn_text = f"🔒 {v['name']} [Уже куплено]"
                elif k in SHOP_CART[user_id]["items"]:
                    btn_text = f"✅ {v['name']} ({price}💰) [В КОРЗИНЕ]"
                else:
                    btn_text = f"⬜️ {v['name']} ({price}💰)"
                    
                kb.add(tele_types.InlineKeyboardButton(btn_text, callback_data=f"dog_addcart_{k}_{cat_key}"))
        
        if not found_any:
            text = f"🛒 **{cat_name}**\nВ этой категории товаров пока нет."
            
        kb.add(tele_types.InlineKeyboardButton("🔙 К категориям", callback_data="dog_shop"))
        bot.edit_message_caption(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        return

    elif action.startswith("addcart_"):
        raw_data = action.replace("addcart_", "").rsplit("_", 1)
        item_key = raw_data[0]
        cat_key = raw_data[1]
        
        # Правильная инициализация словаря корзины
        if user_id not in SHOP_CART:
            SHOP_CART[user_id] = {"items": [], "last_time": time.time()}
            
        SHOP_CART[user_id]["last_time"] = time.time()
        current_cart = SHOP_CART[user_id]["items"]
        
        if item_key in dog.get('items', []):
            bot.answer_callback_query(call.id, "Этот предмет уже есть у вас в гардеробе!", show_alert=True)
            return

        if item_key in current_cart:
            current_cart.remove(item_key)
            bot.answer_callback_query(call.id, "Убрано из корзины")
        else:
            current_cart.append(item_key)
            bot.answer_callback_query(call.id, "Добавлено в корзину")
            
        SHOP_CART[user_id]["items"] = current_cart
        
        call.data = f"dog_shopcat_{cat_key}"
        handle_dog_callback(bot, call)
        return

    elif action == "shop_cancel":
        if user_id in SHOP_CART:
            del SHOP_CART[user_id] # Полная очистка при выходе
        bot.answer_callback_query(call.id, "Корзина очищена")
        try: bot.delete_message(call.message.chat.id, call.message.message_id)
        except: pass
        send_dog_menu(bot, call.message.chat.id, user_id)
        return

    elif action == "shop_checkout":
        if user_id not in SHOP_CART or not SHOP_CART[user_id]["items"]:
            bot.answer_callback_query(call.id, "❌ Ваша корзина пуста!", show_alert=True)
            return
            
        from database import get_dog_profession
        prof = get_dog_profession(user_id)
        
        total_price = 0
        for item in SHOP_CART[user_id]["items"]:
            if item in DOG_SHOP:
                p = DOG_SHOP[item]['price']
                # 🛠 ИСПРАВЛЕНО: было "Inter", стало "Инженер"
                if "Инженер" in prof: p = int(p * 0.8)
                total_price += p
                
        if spend_dust(user_id, total_price):
            for item in SHOP_CART[user_id]["items"]:
                if item not in dog['items']:
                    dog['items'].append(item)
                    
            update_dog_data(user_id, dog)
            del SHOP_CART[user_id] # Чистим ОЗУ
            
            bot.answer_callback_query(call.id, f"🎉 Куплено! Списано {total_price} 💰. Вещи в гардеробе!", show_alert=True)
            try: bot.delete_message(call.message.chat.id, call.message.message_id)
            except: pass
            send_dog_menu(bot, call.message.chat.id, user_id)
            return
        else:
            bot.answer_callback_query(call.id, f"❌ Не хватает пыли! Нужно {total_price} 💰", show_alert=True)
            return
    
    elif action == "resurrect":
        kb = tele_types.InlineKeyboardMarkup()
        kb.row(tele_types.InlineKeyboardButton("♂ Мальчик", callback_data="dog_resurrect_male"))
        kb.row(tele_types.InlineKeyboardButton("♀ Девочка", callback_data="dog_resurrect_female"))
        bot.edit_message_caption("🛰 **Выбор напарника**\n\nКомандор, выберите пол вашего нового щенка:", 
                                 call.message.chat.id, call.message.message_id, reply_markup=kb)
        return

    elif action.startswith("resurrect_"):
        gender = action.split("_")[1]
        if spend_dust(user_id, 100):
            update_dog_data(user_id, {"level": 1, "hunger": 80, "energy": 80, "mood": 80, 
                                      "items": [], "equipped": [], "xp": 0, "date": "", 
                                      "status": "alive", "gender": gender})
            bot.answer_callback_query(call.id, "🛰 Новый щенок на борту!")
            try: bot.delete_message(call.message.chat.id, call.message.message_id)
            except: pass
            send_dog_menu(bot, call.message.chat.id, user_id)
            return
        else: 
            bot.answer_callback_query(call.id, "❌ Нужно 100 пыли!", show_alert=True)
            return

    try: bot.delete_message(call.message.chat.id, call.message.message_id)
    except: pass
    send_dog_menu(bot, call.message.chat.id, user_id)
