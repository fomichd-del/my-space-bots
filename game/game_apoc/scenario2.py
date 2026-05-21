import telebot
from telebot import types as tele_types
from database import (
    get_game_status, set_game_node, reset_game, set_game_timer, add_xp, 
    has_completed_chapter, mark_chapter_completed, is_timer_expired
)

def run_scenario(bot, call):
    user_id = call.from_user.id
    username = call.from_user.first_name or "Док"
    
    raw_node, _ = get_game_status(user_id)
    if not raw_node: raw_node = "apoc_start"
    
    allowed_during_timer = [
        "apoc_s2_start", "resume_game_2", "game_reset_ch2", 
        "game_main_menu", "apoc_s2_craft_bio", "apoc_s2_9_done"
    ]
    
    if call.data not in allowed_during_timer:
        if not is_timer_expired(user_id):
            bot.answer_callback_query(call.id, "⌛️ Объект заблокирован. Ожидайте завершения процесса!", show_alert=True)
            return

    def get_loc(node_str): return node_str.split('|')[0]
    def has_flag(node_str, flag): return f"|{flag}" in node_str or flag in node_str.split('|')[1:]
    def add_flag(node_str, flag): return node_str if has_flag(node_str, flag) else f"{node_str}|{flag}"
    def set_loc(node_str, new_loc):
        parts = node_str.split('|')
        parts[0] = new_loc
        return '|'.join(parts)

    current_node = raw_node
    loc = get_loc(current_node)

    # --- ВХОД И ЛОГИКА ---
    if call.data == "apoc_s2_start":
        if not has_completed_chapter(user_id, "chapter_1"):
            bot.answer_callback_query(call.id, "🔒 Доступ заблокирован! Сначала завершите Главу 1.", show_alert=True)
            return
        if loc in ["apoc_ch1_completed_screen", "apoc_start", "start"]:
            call.data = "apoc_s2_scene_1"
            current_node = set_loc(current_node, "apoc_s2_scene_1")
            set_game_node(user_id, current_node)
            loc = "apoc_s2_scene_1"
        elif loc == "apoc_s2_scene_1":
            call.data = "apoc_s2_scene_1" # ФИКС: Устранение мертвой зоны
        else:
            text = "🔙 *ВОЗВРАЩЕНИЕ В ПУСТОШЬ*\nКомандор, вы остановились на пути к ТЦ 'Зенит'. Что делаем?"
            kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
                tele_types.InlineKeyboardButton("▶️ Продолжить экспедицию", callback_data="resume_game_2"),
                tele_types.InlineKeyboardButton("🔄 Начать Главу 2 заново", callback_data="game_reset_ch2"),
                tele_types.InlineKeyboardButton("🔙 В меню Хаба", callback_data="game_main_menu")
            )
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
            return

    if call.data == "resume_game_2":
        call.data = loc
        bot.answer_callback_query(call.id, "🔄 Экспедиция продолжена!")

    if call.data == "game_reset_ch2":
        all_flags = current_node.split('|')[1:]
        ch1_backbone = ["wire", "boot", "pc_done", "meds", "liquid", "mask", "generator", "truth", "radio", "secret_found", "ch1_done", "secret_entered", "files", "super_motor", "suit_fixed"]
        filtered_flags = [f for f in all_flags if f in ch1_backbone]
        current_node = ("apoc_s2_scene_1|" + "|".join(filtered_flags)) if filtered_flags else "apoc_s2_scene_1"
        set_game_timer(user_id, 0)
        set_game_node(user_id, current_node)
        call.data = "apoc_s2_scene_1"
        loc = "apoc_s2_scene_1"

    MAJOR_NODES = ["apoc_s2_scene_1", "apoc_s2_2", "apoc_s2_4", "apoc_s2_5", "apoc_s2_6", "apoc_s2_8", "apoc_s2_9_wait", "apoc_s2_9_sound", "apoc_s2_9_done", "apoc_s2_craft_start", "apoc_s2_craft_bio", "apoc_s2_11", "apoc_s2_12", "apoc_s2_13", "apoc_s2_14", "apoc_s2_15", "apoc_s2_16", "apoc_s2_17", "apoc_s2_18", "apoc_s2_19", "apoc_s2_20", "apoc_s2_21", "apoc_s2_23", "apoc_s2_24", "apoc_s2_25", "apoc_s2_26", "apoc_s2_27", "apoc_s2_28", "apoc_s2_sync", "apoc_s2_30", "apoc_ch2_completed_screen"]
    if call.data in MAJOR_NODES:
        current_node = set_loc(current_node, call.data)
        set_game_node(user_id, current_node)

    # 🏆 --- [ ЭКРАН ЗАВЕРШЕННОЙ ГЛАВЫ ] --- 🏆
    if call.data == "apoc_ch2_completed_screen":
        text = (f"🏆 **ГЛАВА 2: ПРОЙДЕНА**\n"
                f"──────────────────────────\n"
                f"Вы добрались до окраин и разгадали тайну 'Зенита'.\n\n"
                f"Марти готов к следующему броску!")
        
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("🚀 Начать Главу 3", callback_data="apoc_s3_start"),
            tele_types.InlineKeyboardButton("🔄 Пройти Главу 2 заново", callback_data="game_reset_ch2"),
            tele_types.InlineKeyboardButton("🔙 В меню Хаба", callback_data="game_main_menu")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        return

    # --- [ ПЕРВЫЙ ШАГ В ПУСТОШЬ ] ---
    if call.data == "apoc_s2_scene_1":
        text = (f"🌫 *КИСЛОТНЫЙ ТУМАН*\n"
                f"──────────────────────────\n"
                f"Гермодверь бункера за вашей спиной закрывается с тяжелым лязгом, отсекая уютный мир ламп и стопок старых журналов. "
                f"Перед вами — то, что когда-то было пригородом. Теперь это каша из разложившегося бетона и ярко-желтых испарений. \n\n"
                f"Марти делает осторожный шаг вперед, его лапы в защитных чехлах смешно хлюпают по жиже. "
                f"Его звуковой модуль выдает серию тревожных сигналов: 'Док, датчики фиксируют уровень pH почвы в районе двойки. "
                f"Если мы просто простоим здесь полчаса, ваши подошвы станут частью этой экосистемы. Нам нужно двигаться к руинам НИИ, "
                f"там должен был остаться мобильный штаб'.\n\n"
                f"В руках вы всё еще сжимаете тот странный пропуск. Ваше лицо на нем кажется немым укором из прошлого.")
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("🧭 Свериться с картой", callback_data="apoc_s2_2"),
            tele_types.InlineKeyboardButton("🐕 Попросить Марти просканировать местность", callback_data="apoc_s2_scan_start")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ОБРАБОТКА СКАНА МАРТИ (Этап 1) ] ---
    elif call.data == "apoc_s2_scan_start":
        try: bot.answer_callback_query(call.id, "📡 Радар активирован: 'Док, впереди высокая концентрация фиолетовых спор. Руины НИИ прямо по курсу!'", show_alert=True)
        except: pass
        call.data = "apoc_s2_2"
        run_scenario(bot, call)
        return
    
    # --- [ ЭТАП 2: ЗАГАДКА ОРИЕНТИРОВ ] ---
    elif call.data == "apoc_s2_2":
        text = (f"📍 *ПРИЗРАКИ УЛИЦ*\n\n"
                f"Старый планшет едва светится. Вы пытаетесь сопоставить очертания руин с картой Мариуполя из архивов. "
                f"Справа должен быть торговый центр, но на его месте — гигантская гора фиолетовых наростов, которые пульсируют в такт какому-то подземному ритму.\n\n"
                f"Марти: 'Смотрите, Док! На дорожном указателе сохранились остатки надписи. Буква 'М' и цифра '85'. "
                f"Это не случайность. Кто-то расставил эти метки уже после Сбоя. Похоже на навигацию для тех, кто знает код'.")
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("🔍 Изучить указатель поближе", callback_data="apoc_s2_3"),
            tele_types.InlineKeyboardButton("🚶 Идти в сторону пульсации", callback_data="apoc_s2_4")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 3: УЛИКА (ПЫЛЬЦА) ] ---
    elif call.data == "apoc_s2_3":
        if not has_flag(current_node, "clue_pollen"):
            current_node = add_flag(current_node, "clue_pollen")
            set_game_node(user_id, current_node)
            add_xp(user_id, 5, username)
        text = (f"🧪 *НЕИЗВЕСТНАЯ ПЫЛЬЦА*\n\n"
                f"Вы проводите перчаткой по указателю. На ней остается липкий налет, который начинает светиться слабым неоновым светом. \n\n"
                f"Марти: 'Осторожно! Это высокоактивные споры. Мой модуль подсказывает, что они реагируют на человеческий эпителий. "
                f"Если мы не соберем Био-анализатор, мы никогда не поймем, почему этот мох так 'радуется' вашему приближению. "
                f"Я сохранил образец в своей камере хранения. Теперь у нас есть первый ингредиент для теста!'.")
        kb = tele_types.InlineKeyboardMarkup().add(tele_types.InlineKeyboardButton("🚶 Двигаться дальше", callback_data="apoc_s2_4"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 4: МОБИЛЬНАЯ ЛАБОРАТОРИЯ ] ---
    elif call.data == "apoc_s2_4":
        text = (f"🚛 *ЗАБРОШЕННЫЙ ТРЕЙЛЕР*\n\n"
                f"Сквозь туман проступают очертания грузовика с логотипом Академии Орион. Он перевернут, а его бока изъедены коррозией. "
                f"Однако герметичный отсек выглядит целым. \n\n"
                f"Марти: 'Это 'Био-Трейлер 7'. В таких машины перевозили полевое оборудование для анализа мутаций. "
                f"Если нам повезет, внутри мы найдем корпус для нашего будущего гаджета. Но дверь заперта на биометрический замок. "
                f"Док, попробуйте приложить руку. У меня предчувствие, что система вас узнает... как и тот пропуск'.")
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("✋ Приложить ладонь к замку", callback_data="apoc_s2_5"),
            tele_types.InlineKeyboardButton("🛠 Попробовать взломать через Марти", callback_data="apoc_s2_hack_fail")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 5: КОРПУС АНАЛИЗАТОРА ] ---
    elif call.data == "apoc_s2_5":
        if not has_flag(current_node, "item_bio_frame"):
            current_node = add_flag(current_node, "item_bio_frame")
            set_game_node(user_id, current_node)
            
        text = (f"🔓 *ДОСТУП ПОЛУЧЕН*\n\n"
                f"Замок пискнул и окрасился зеленым. С тихим шипением дверь трейлера отошла в сторону. "
                f"Внутри царит стерильный порядок, который кажется чужим в этом хаосе. В центре на штативе закреплен прибор, "
                f"напоминающий современный стоматологический сканер, но с более сложной оптикой.\n\n"
                f"Марти: 'Бинго! Это база для **Био-анализатора**. Но посмотрите на дисплей... Там написано: "
                f"*«Ожидание авторизации: Старший сотрудник Фомиченко»*. Док, это уже не смешно. "
                f"Мы нашли корпус, но нам нужны реактивы, чтобы он ожил. Один в шкафу, другой — где-то в болотах'.\n\n"
                f"**ВЫ ПОЛУЧИЛИ:** Основа Био-анализатора.")
        kb = tele_types.InlineKeyboardMarkup().add(
            tele_types.InlineKeyboardButton("🧪 Обыскать шкафы", callback_data="apoc_s2_6")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 6: ЛАБОРАТОРНЫЙ ШКАФ ] ---
    elif call.data == "apoc_s2_6":
        text = (f"🧪 *ЗАБЫТЫЕ РЕАКТИВЫ*\n\n"
                f"Вы открываете металлический шкаф. Внутри стройными рядами стоят колбы, многие из которых лопнули от времени, "
                f"залив полки разноцветным осадком. Но в глубине, в свинцовом контейнере, вы находите запечатанный флакон с надписью 'Катализатор-D'.\n\n"
                f"Марти подпрыгивает, пытаясь заглянуть на полку: 'Док, этот запах! Это же композит, который использовали для сверхпрочных пломб в ваше время. "
                f"Похоже, Академия адаптировала стоматологические материалы для стабилизации био-чипов. "
                f"Если мы добавим это в наш корпус, Био-анализатор сможет выдержать агрессивную среду болот. "
                f"Но будьте осторожны: флакон под давлением. Нужно аккуратно стравить газ перед открытием'.")
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("⚙️ Использовать стоматологический зажим", callback_data="apoc_s2_7"),
            tele_types.InlineKeyboardButton("👊 Просто вскрыть ножом", callback_data="apoc_s2_reagent_fail")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 7: МИНИ-ИГРА: СИНТЕЗ ] ---
    elif call.data == "apoc_s2_7":
        if not has_flag(current_node, "synth_xp_given"):
            current_node = add_flag(current_node, "synth_xp_given")
            set_game_node(user_id, current_node)
            add_xp(user_id, 5, username)
            
        text = (f"⚗️ *ХИМИЧЕСКАЯ КАЛИБРОВКА*\n\n"
                f"Вы аккуратно зажимаете клапан. Теперь нужно смешать найденную пыльцу с катализатором. "
                f"На дисплее трейлера загорается инструкция: 'Для стабилизации органики выберите элемент с атомным весом 14.007'. \n\n"
                f"Марти: 'Док, я помню это! Это основа атмосферы, которую мы сейчас вдыхаем с таким трудом. "
                f"Выбирайте правильно, иначе вместо анализатора мы получим маленькую, но очень гордую дымовую шашку!'.")
        kb = tele_types.InlineKeyboardMarkup(row_width=3).add(
            tele_types.InlineKeyboardButton("🔘 Кислород", callback_data="apoc_s2_synth_fail"),
            tele_types.InlineKeyboardButton("🔘 Азот", callback_data="apoc_s2_8"),
            tele_types.InlineKeyboardButton("🔘 Углерод", callback_data="apoc_s2_synth_fail")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 8: ШОРОХ ЗА БОРТОМ ] ---
    elif call.data == "apoc_s2_8":
        if not has_flag(current_node, "item_reagent"):
            current_node = add_flag(current_node, "item_reagent")
            set_game_node(user_id, current_node)
            
        text = (f"🦗 *ГЛАЗА В ТУМАНЕ*\n\n"
                f"Смесь в колбе зашипела и окрасилась в глубокий индиго. Но внезапно корпус трейлера содрогнулся от сильного удара снаружи. "
                f"Кто-то или что-то скребется по металлу длинными когтями.\n\n"
                f"Марти мгновенно затихает, шерсть на его загривке встает дыбом. Он включает свой сканер на минимальную мощность и шепчет через модуль: "
                f"'Док... там снаружи 'Прыгун'. Это мутировавшая амфибия, размером с хорошего дога. Они слепы, но реагируют на тепло "
                f"вашей новой химической реакции. Если мы сейчас выйдем — станем десертом. Нужно либо затаиться, либо использовать звуковой модуль, чтобы увести его подальше'.")
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("🤫 Затаиться и ждать", callback_data="apoc_s2_9_wait"),
            tele_types.InlineKeyboardButton("🔊 Модуль: Имитация ультразвука", callback_data="apoc_s2_9_sound")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # ФИКС: РАЗБИЛИ ЭТАП 9 НА ЯВНЫЕ КНОПКИ БЕЗ STARTSWITH
    # --- [ ЭТАП 9-А: ОЖИДАНИЕ ] ---
    elif call.data == "apoc_s2_9_wait":
        set_game_timer(user_id, 10)
        text = (f"🤫 *ИГРА В ПРЯТКИ*\n\n"
                f"Вы отключаете всё питание в трейлере. Снаружи слышно тяжелое, хриплое дыхание. "
                f"Тварь обходит трейлер кругами, периодически царапая металл когтями. Нужно переждать.\n\n"
                f"**Ожидание: 10 минут.**")
        kb = tele_types.InlineKeyboardMarkup().add(
            tele_types.InlineKeyboardButton("🔄 Проверить обстановку", callback_data="apoc_s2_9_done")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 9-Б: ЗВУКОВОЙ УДАР ] ---
    elif call.data == "apoc_s2_9_sound":
        text = (f"🔊 *ЗВУКОВОЙ УДАР*\n\n"
                f"Звуковой импульс Марти сработал! Тварь с диким визгом бросилась в сторону болот, подальше от источника шума.\n\n"
                f"Марти: 'Отлично, Док! А теперь давайте соберем эту штуку, пока не прибежали его старшие братья!'.")
        kb = tele_types.InlineKeyboardMarkup().add(
            tele_types.InlineKeyboardButton("⚒ Перейти к столу", callback_data="apoc_s2_9_done")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 9-В: ПЕРЕХОД К СБОРКЕ ] ---
    elif call.data == "apoc_s2_9_done":
        # ФИКС: Защита от прокликивания таймера
        if not is_timer_expired(user_id):
            bot.answer_callback_query(call.id, "🤫 Тсс! Тварь еще бродит рядом. Ждем!", show_alert=True)
            return

        text = (f"🛠 *ПОСЛЕДНИЕ ШТРИХИ*\n\n"
                f"Шаги затихли. Теперь у нас есть всё: корпус, мотор и стабилизированный реагент. Вы раскладываете детали на операционном столе трейлера. "
                f"Это кропотливая работа — соединить технологию 1985 года с ИИ-модулями 2026-го.\n\n"
                f"Марти: 'Док, я буду подавать вам инструменты. Постарайтесь не перепутать полярность!'.")
        
        t = 10 if has_flag(current_node, "super_motor") else 20
        kb = tele_types.InlineKeyboardMarkup().add(
            tele_types.InlineKeyboardButton(f"⚒ Начать сборку ({t} мин)", callback_data="apoc_s2_craft_start")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ СТАРТ СБОРКИ ] ---
    elif call.data == "apoc_s2_craft_start":
        t = 10 if has_flag(current_node, "super_motor") else 20
        set_game_timer(user_id, t)
        text = (f"⚒ *ИДЕТ СБОРКА АНАЛИЗАТОРА*\n\n"
                f"Марти аккуратно подает инструменты. Вы паяете контакты. Процесс займет **{t} минут**.")
        kb = tele_types.InlineKeyboardMarkup().add(
            tele_types.InlineKeyboardButton("🔄 Проверить готовность", callback_data="apoc_s2_craft_bio")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 10: ПЕРВЫЙ СИГНАЛ ] ---
    elif call.data == "apoc_s2_craft_bio":
        # ФИКС: Защита от прокликивания сборки
        if not is_timer_expired(user_id):
            bot.answer_callback_query(call.id, "⏳ Сборка еще идет! Не торопитесь.", show_alert=True)
            return

        if not has_flag(current_node, "scanner_upgraded"):
            current_node = add_flag(current_node, "scanner_upgraded")
            set_game_node(user_id, current_node)
            add_xp(user_id, 15, username)
            
        text = (f"📡 *ОНО ЖИВОЕ!*\n\n"
                f"Прибор в ваших руках издает мелодичный писк и проецирует в воздух голограмму. \n\n"
                f"**МАРТИ:** 'Работает! Био-анализатор активен. Док, поднесите к нему тот старый пропуск... Быстрее!'.\n\n"
                f"Вы подносите пластиковую карточку к лучу. Экран вспыхивает красным, а затем выдает текст: "
                f"*«ОБЪЕКТ ИДЕНТИФИЦИРОВАН. ДНК-ПРОФИЛЬ: ФОМИЧЕНКО Д.В. СТАТУС: СОЗДАТЕЛЬ. ТЕКУЩАЯ ЦЕЛЬ: СЕКТОР 4, МАРИУПОЛЬСКИЙ УЗЕЛ»*.\n\n"
                f"Марти замирает: 'Создатель? Док... кажется, вы не просто стоматолог из прошлого. "
                f"Вы тот, кто всё это начал. И анализатор поймал слабый сигнал ответа... прямо из центра болот'.")
        kb = tele_types.InlineKeyboardMarkup().add(
            tele_types.InlineKeyboardButton("🧭 Идти на сигнал", callback_data="apoc_s2_11")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 11: ТРОПА ШЕПЧУЩИХ КОРНЕЙ ] ---
    elif call.data == "apoc_s2_11":
        text = (f"🌿 *ЖИВОЙ ЛАБИРИНТ*\n"
                f"──────────────────────────\n"
                f"Вы покидаете трейлер и углубляетесь в заросли, где деревья больше напоминают переплетенные вены гигантского существа. "
                f"Био-анализатор на вашем запястье пульсирует мягким голубым светом, указывая направление. \n\n"
                f"Марти: 'Док, вы заметили? Корни расступаются перед вами еще до того, как вы их коснетесь. "
                f"Это не инстинкт растения, это... протокол узнавания. Как будто этот лес — ваш старый пес, который наконец учуял хозяина спустя сорок лет. "
                f"Только этот пес может нас сожрать, если мы свернем с тропы. Сигнал впереди усиливается, но он становится... прерывистым, "
                f"как будто кто-то пытается его заглушить'.")
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("📡 Усилить мощность анализатора", callback_data="apoc_s2_12"),
            tele_types.InlineKeyboardButton("🕵️ Осмотреть странные плоды на корнях", callback_data="apoc_s2_clue_fruit")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 12: ЗАГАДКА ЧАСТОТ ] ---
    elif call.data == "apoc_s2_12":
        text = (f"🎼 *ГАРМОНИЯ РАСПАДА*\n\n"
                f"Вы выходите на поляну, полностью перекрытую стеной из фиолетового плюща. Анализатор пищит: 'Блокировка доступа. Требуется звуковой ключ'. \n\n"
                f"Марти: 'Док, я понял! Плющ вибрирует. Это био-акустический замок. Чтобы он открылся, нам нужно подать резонансную частоту. "
                f"В ваших старых записях была формула: «Частота покоя равна числу миллиметров в стандартном стоматологическом боре». \n\n"
                f"Вы же помните размер своего любимого инструмента? Это поможет нам раздвинуть эти сорняки!'.")
        kb = tele_types.InlineKeyboardMarkup(row_width=3).add(
            tele_types.InlineKeyboardButton("📟 15 Hz", callback_data="apoc_s2_freq_fail"),
            tele_types.InlineKeyboardButton("📟 19 Hz", callback_data="apoc_s2_13"),
            tele_types.InlineKeyboardButton("📟 25 Hz", callback_data="apoc_s2_freq_fail")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 13: ВИДЕНИЕ МАРИУПОЛЯ (Галлюцинация) ] ---
    elif call.data == "apoc_s2_13":
        if not has_flag(current_node, "hallucination_xp"):
            current_node = add_flag(current_node, "hallucination_xp")
            set_game_node(user_id, current_node)
            add_xp(user_id, 10, username)
            
        text = (f"🌀 *ПРИЗРАК 1985 ГОДА*\n\n"
                f"Плющ дрожит и медленно сползает вниз, открывая проход. Но как только вы делаете шаг, воздух вокруг сгущается. "
                f"Туман превращается в очертания домов... Вы видите улицу Мариуполя. Яркое солнце, старые автобусы, и... молодую женщину, "
                f"которая катит коляску. Она оборачивается и улыбается прямо вам. В её руках — точно такой же Био-анализатор.\n\n"
                f"Марти (встревоженно): 'Док! Очнитесь! Это не реальность! Мох выделяет галлюциногенные споры, когда чувствует вашу ДНК. "
                f"Оно пытается заманить вас в ловушку ваших же воспоминаний. Смотрите на показатели — кислород падает!'.")
        
        kb = tele_types.InlineKeyboardMarkup(row_width=1)
        # Проверка на наличие аптечки из Главы 1!
        if has_flag(current_node, "secret_found"):
            kb.add(tele_types.InlineKeyboardButton("💉 Вколоть антисептик 'Орион'", callback_data="apoc_s2_14"))
        
        kb.add(tele_types.InlineKeyboardButton("💥 Укусить себя за руку", callback_data="apoc_s2_14"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 14: СТОЯНКА ТЕНИ ] ---
    elif call.data == "apoc_s2_14":
        if not has_flag(current_node, "hallucination_cleared"):
            current_node = add_flag(current_node, "hallucination_cleared")
            set_game_node(user_id, current_node)
            
        text = (f"⛺️ *СЛЕДЫ КИБЕР-ПИЛИГРИМА*\n\n"
                f"Видение рассеивается. Вы стоите на небольшой сухой кочке посреди болота. Здесь кто-то был совсем недавно. "
                f"Маленькая горелка всё еще теплая, а рядом лежит пустая банка из-под пайка Академии Орион. \n\n"
                f"Марти: 'Смотрите, Док. На песке — отпечаток лапы. Но это не собака. Это протез. Высокотехнологичная кибер-лапа. "
                f"И посмотрите на этот лоскут ткани... это кусок лабораторного халата вашего деда. Тот, кто здесь шел, "
                f"носит вещи вашей семьи. Это либо безумный фанат, либо... нам нужно ускориться'.")
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("🔎 Изучить записи в блокноте", callback_data="apoc_s2_clue_notes"),
            tele_types.InlineKeyboardButton("🚶 Идти дальше по след", callback_data="apoc_s2_15")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 15: СТРАННЫЙ ОБЪЕКТ ] ---
    elif call.data == "apoc_s2_15":
        text = (f"🗿 *МОНУМЕНТ ИЗ ПРОШЛОГО*\n\n"
                f"След обрывается у странного строения, напоминающего бетонный обелиск, облепленный датчиками. "
                f"Из него исходит тот самый сигнал, за которым вы шли. \n\n"
                f"Марти: 'Док, это ретранслятор Академии, но он... переделан. К нему припаяны детали от старой бормашины! "
                f"Кто-то использует ваши семейные инструменты, чтобы усилить зов мха. \n\n"
                f"Смотрите! На вершине обелиска сидит дрон, но он не атакует. Он... просто смотрит на вас и издает звук, "
                f"похожий на биение сердца. И ваш Анализатор начинает светиться фиолетовым. У нас контакт!'.")
        kb = tele_types.InlineKeyboardMarkup().add(
            tele_types.InlineKeyboardButton("📻 Попробовать войти в связь", callback_data="apoc_s2_16")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 16: УСТАНОВКА СВЯЗИ С ОБЕЛИСКОМ ] ---
    elif call.data == "apoc_s2_16":
        text = (f"📻 *ПЕРВЫЙ ГУЛ*\n"
                f"──────────────────────────\n"
                f"Вы подносите Био-анализатор к основанию обелиска. Прибор вибрирует, синхронизируясь с ритмом 'биения сердца' монумента. "
                f"Внезапно дрон на вершине расправляет металлические крылья, и из его динамиков, забитых пылью десятилетий, раздается хриплый, искаженный голос.\n\n"
                f"Голос: '...идентификация... субъект 0-1-Б... Дмитрий? Если ты это слышишь, значит, мох принял твою кровь. "
                f"Не верь Навигаторам из Академии. Они ищут Семя, но они не знают, что оно — это ты'.\n\n"
                f"Марти (испуганно прижимая уши): 'Док, это же голос вашего отца! Или очень качественная подделка. "
                f"Смотрите, анализатор выдает ошибку: «Конфликт временных меток: 1985 и 2026». Нам нужно расшифровать остаток сообщения, "
                f"но дрон требует подтверждения био-кода через сканирование ближайшего нароста мха'.")
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("🧬 Сканировать пульсирующий мох", callback_data="apoc_s2_17")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 17: МЕХАНИКА БИО-АНАЛИЗАТОРА ] ---
    elif call.data == "apoc_s2_17":
        text = (f"🔍 *АНАЛИЗ ГЕНОМА*\n\n"
                f"Вы направляете луч анализатора на жирный фиолетовый нарост у подножия. Мох начинает светиться ярко-бирюзовым, "
                f"сопротивляясь сканированию. На экране бегут цепочки нуклеотидов. \n\n"
                f"Марти: 'Док, тут нужна ваша точность. Чтобы пробить защиту мха, нужно сопоставить структуру ДНК. "
                f"В вашей семейной легенде говорилось: «Корень жизни всегда имеет структуру гексагона». \n\n"
                f"Выберите правильную последовательность связей для стабилизации луча:'.")
        kb = tele_types.InlineKeyboardMarkup(row_width=3).add(
            tele_types.InlineKeyboardButton("💠 4-х звенная", callback_data="apoc_s2_dna_fail"),
            tele_types.InlineKeyboardButton("💠 6-ти звенная", callback_data="apoc_s2_18"),
            tele_types.InlineKeyboardButton("💠 8-ми звенная", callback_data="apoc_s2_dna_fail")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 18: ТАЙНИК В ОБЕЛИСКЕ ] ---
    elif call.data == "apoc_s2_18":
        if not has_flag(current_node, "diary_page"):
            current_node = add_flag(current_node, "diary_page")
            set_game_node(user_id, current_node)
            add_xp(user_id, 10, username)
            
        text = (f"📂 *СТРАНИЦА ИЗ ПРОШЛОГО*\n\n"
                f"Анализатор издает победный сигнал. В основании обелиска открывается небольшая ниша. "
                f"Внутри лежит не электронный носитель, а настоящая бумажная страница, запечатанная в вакуумный пластик. \n\n"
                f"Текст на ней написан от руки: *«Мариуполь. Клиника. 1985. Мы нашли способ кодировать память в клеточную структуру растений. "
                f"Если город падет, знания сохранятся в мхе. Дима должен стать ключом. Только его ДНК сможет пробудить Архив»*.\n\n"
                f"Марти (шокированно): 'Док... так вы не просто наследник. Вы — ходячая флешка с данными всего человечества! "
                f"И посмотрите на обратную сторону... там схема прохода к Старому ТЦ. Сигнал идет именно оттуда!'.")
        kb = tele_types.InlineKeyboardMarkup().add(
            tele_types.InlineKeyboardButton("🚶 Двигаться к ТЦ через 'Лес Вен'", callback_data="apoc_s2_19")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 19: ЮМОР И ОПАСНОСТЬ ] ---
    elif call.data == "apoc_s2_19":
        text = (f"🌳 *ЛЕС ПУЛЬСИРУЮЩИХ ВЕН*\n\n"
                f"Вы входите в зону, где деревья буквально оплетены сосудами, по которым течет светящаяся фиолетовая жидкость. "
                f"Воздух становится тяжелым и сладковатым. \n\n"
                f"Марти: 'Знаете, Док, если бы я был обычным пуделем, я бы сейчас бегал за своим хвостом от этого запаха. "
                f"Но мой модуль говорит, что это концентрированный нейротоксин. Если чихнете — активируете систему самоликвидации моих фильтров. "
                f"И посмотрите на те коконы, свисающие с ветвей... В них что-то шевелится. \n\n"
                f"Я бы предложил пошутить про 'стоматологию в лесу', но боюсь, эти штуки не оценят ваш юмор. "
                f"Нужно пройти максимально тихо, используя ваш Анализатор как маскировочный экран'.")
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("🤫 Включить режим маскировки", callback_data="apoc_s2_20"),
            tele_types.InlineKeyboardButton("🔦 Просветить коконы сканером", callback_data="apoc_s2_cocoons_fail")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 20: ЭХО МАРИУПОЛЯ ] ---
    elif call.data == "apoc_s2_20":
        text = (f"🏙 *ПОЮЩЕЕ БОЛОТО*\n\n"
                f"Вы пробираетесь сквозь заросли. Внезапно шелест листьев складывается в отчетливую мелодию. "
                f"Это популярная песня из 80-х, которую вы слышали на старых кассетах. Мох резонирует, создавая эффект объемного звука.\n\n"
                f"Марти: 'Это не галлюцинация, Док. Мох транслирует аудио-архивы города. Мы буквально идем сквозь память Мариуполя. "
                f"Впереди показались огни... Но погодите, в этом мире не может быть работающих уличных фонарей! "
                f"Там, за туманом, стоит здание, которое светится изнутри. Это ТЦ 'Зенит'. И у его входа кто-то стоит... "
                f"Тот самый кибер-паломник в халате вашего деда!'.")
        kb = tele_types.InlineKeyboardMarkup().add(
            tele_types.InlineKeyboardButton("🎯 Попробовать перехватить фигуру", callback_data="apoc_s2_21")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 21: ПОГОНЯ У ПОРОГА ] ---
    elif call.data == "apoc_s2_21":
        text = (f"🏃 *УСКОЛЬЗАЮЩАЯ ТЕНЬ*\n"
                f"──────────────────────────\n"
                f"Вы бросаетесь вперед, хлюпая по кислотной жиже, которая при каждом шаге выбрасывает в воздух облачка едкого пара. "
                f"Фигура в халате вашего деда двигается неестественно плавно, почти не касаясь земли. Она замирает у главного входа в ТЦ всего на секунду, "
                f"оборачивается, и вы видите тусклый блеск линз вместо глаз.\n\n"
                f"Марти: 'Док, я засек его тепловой след! Но это... это не тепло человека. Температура его тела — ровно 36.6 градусов, "
                f"но она держится идеально ровно, как у откалиброванного медицинского термостата. Это киборг или кто-то под очень мощным "
                f"температурным щитом. Он зашел внутрь, но оставил подарок на пороге. Смотрите под ноги!'.")
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("🔍 Осмотреть брошенный предмет", callback_data="apoc_s2_22"),
            tele_types.InlineKeyboardButton("🚪 Рвануть следом в атриум", callback_data="apoc_s2_23")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 22: УЛИКА: СТОМАТОЛОГИЧЕСКИЙ ЭКСТРАКТОР ] ---
    elif call.data == "apoc_s2_22":
        if not has_flag(current_node, "extractor"):
            current_node = add_flag(current_node, "extractor")
            set_game_node(user_id, current_node)
            add_xp(user_id, 7, username)
            
        text = (f"🦷 *СТРАННЫЙ ИНСТРУМЕНТ*\n\n"
                f"Вы поднимаете предмет. Это старый стоматологический экстрактор, но его рукоять заменена на высокотехнологичный блок питания Академии. "
                f"На металле выгравированы инициалы: *'Ф.Д.В. 1985'*.\n\n"
                f"Марти: 'Док, этот парень использует инструменты вашего деда как оружие или ключи. "
                f"Экстрактор всё еще вибрирует на ультразвуковой частоте. Кажется, им только что что-то вскрыли... "
                f"Или кого-то. В любом случае, эта деталь может усилить наш Био-анализатор, если мы найдем способ ее подключить. "
                f"Берем с собой, в хозяйстве пригодится!'.")
        kb = tele_types.InlineKeyboardMarkup().add(
            tele_types.InlineKeyboardButton("🚪 Войти в здание", callback_data="apoc_s2_23")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 23: ЗАБЛОКИРОВАННЫЙ ВХОД ] ---
    elif call.data == "apoc_s2_23":
        text = (f"🚧 *СТЕКЛЯННЫЙ БАРЬЕР*\n\n"
                f"Стеклянные двери ТЦ заблокированы огромными узлами фиолетового мха, которые проросли сквозь стальной каркас. "
                f"Обычный лом здесь не поможет — мох моментально регенерирует. Рядом на панели управления горит надпись: "
                f"*«Авторизация по индексу вязкости реагента»*.\n\n"
                f"Марти: 'Док, это проверка на вшивость. Нам нужно настроить Био-анализатор так, чтобы он выдал луч нужной плотности. "
                f"Вспомните дедовский рецепт временного цемента для коробок — он всегда говорил, что идеальное соотношение порошка "
                f"к жидкости должно давать число, равное количеству корней у верхнего первого моляра человека'.")
        kb = tele_types.InlineKeyboardMarkup(row_width=3).add(
            tele_types.InlineKeyboardButton("🧪 Индекс 2", callback_data="apoc_s2_visco_fail"),
            tele_types.InlineKeyboardButton("🧪 Индекс 3", callback_data="apoc_s2_24"),
            tele_types.InlineKeyboardButton("🧪 Индекс 4", callback_data="apoc_s2_visco_fail")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 24: ВНУТРИ ЗЕНИТА ] ---
    elif call.data == "apoc_s2_24":
        text = (f"🏛 *ДЖУНГЛИ ПОТРЕБЛЕНИЯ*\n\n"
                f"Двери медленно расходятся, выпуская облако холодного пара. Вы заходите в главный атриум 'Зенита'. "
                f"Здесь всё замерло в 2026 году: манекены в модной одежде, покрытые плесенью, эскалаторы, застывшие как скелеты древних чудовищ. "
                f"Но по центру, там где когда-то был фонтан, теперь возвышается древоподобная структура, светящаяся мягким фосфорным светом.\n\n"
                f"Марти: 'Док, тишина пугает больше, чем монстры. Мой сканер сходит с ума — здесь тысячи сигналов ДНК, и все они... ваши. "
                f"Как будто это здание — огромная чашка Петри, заполненная вашими клонированными данными. "
                f"Смотрите на второй этаж! Там, в отделе электроники, снова мелькнул халат!'.")
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("🪜 Подняться по застывшему эскалатору", callback_data="apoc_s2_25"),
            tele_types.InlineKeyboardButton("📦 Обыскать стойку информации", callback_data="apoc_s2_clue_info")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 25: ПАНЕЛЬ 'СОТРУДНИК МЕСЯЦА' ] ---
    elif call.data == "apoc_s2_25":
        if not has_flag(current_node, "board_xp"):
            current_node = add_flag(current_node, "board_xp")
            set_game_node(user_id, current_node)
            add_xp(user_id, 8, username)
            
        text = (f"🖼 *ЗЕРКАЛО ПРОШЛОГО*\n\n"
                f"Вы поднимаетесь на второй ярус. Путь преграждает упавшая рекламная вывеска. Обойдя ее, вы натыкаетесь на почетную доску ТЦ. "
                f"Среди фотографий лучших работников красуется одна рамка, защищенная бронированным стеклом. \n\n"
                f"Марти: 'Док... я сейчас перегреюсь от удивления. Посмотрите на подпись под фото...'.\n\n"
                f"На фото — вы, но в форме инженера Академии Орион. Подпись гласит: *«Дмитрий Фомиченко. Главный архитектор системы 'Зенит-1985'. "
                f"За вклад в сохранение генофонда нации»*. \n\n"
                f"В этот момент Био-анализатор издает громкий сигнал тревоги: *«ОБЪЕКТ ОБНАРУЖЕН. ДИСТАНЦИЯ 10 МЕТРОВ. НАЧАЛО ПРОТОКОЛА ОБЪЕДИНЕНИЯ»*.")
        kb = tele_types.InlineKeyboardMarkup().add(
            tele_types.InlineKeyboardButton("🔦 Пролить свет на фигуру", callback_data="apoc_s2_26")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 26: ЛИЦОМ К ЛИЦУ С ПРОШЛЫМ ] ---
    elif call.data == "apoc_s2_26":
        text = (f"👤 *ГИПЕР-ЗЕРКАЛО*\n"
                f"──────────────────────────\n"
                f"Вы направляете мощный луч фонаря вперед. Фигура медленно поворачивается. Халат вашего деда, забрызганный фиолетовым реагентом, "
                f"сидит на ней идеально. Но когда свет падает на лицо, вы едва не роняете фонарь. \n\n"
                f"Это вы. Но это не зеркало. Перед вами — андроид серии 'Архивист', чья кожа создана из искусственно выращенного коллагена по вашим ДНК-образцам. "
                f"Его глаза — линзы с лазерной гравировкой — мигают, считывая ваши параметры. \n\n"
                f"**АНДРОИД:** 'Дмитрий... вы опоздали на сорок один год. Или на пять минут, если считать по внутренним часам мха. "
                f"Я — терминал памяти вашего деда. Я хранил его последний отчет, ожидая того, чья челюстно-лицевая структура совпадет с протоколом 'Создатель'. "
                f"Вы пришли за ответами, но готовы ли вы услышать, почему 1985 год стал началом вашего конца?'.\n\n"
                f"Марти (тихо рычит): 'Док, я не чую в нем зла. Но от него пахнет смертью и... формалином. Он — это вы, "
                f"если бы вы стали частью этой чертовой лаборатории'.")
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("📜 Потребовать расшифровку архива", callback_data="apoc_s2_27"),
            tele_types.InlineKeyboardButton("🔧 Осмотреть кибер-протез андроида", callback_data="apoc_s2_clue_arm")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 27: ЗАГАДКА 'СЕМЕНИ ЖИЗНИ' ] ---
    elif call.data == "apoc_s2_27":
        text = (f"🧩 *КЛЮЧ К СПАСЕНИЮ*\n\n"
                f"Андроид протягивает руку. Его пальцы двигаются с точностью стоматологического манипулятора. \n\n"
                f"**АНДРОИД:** 'Чтобы открыть архив, подтвердите базовую константу проекта. Дед учил вас: "
                f"«Всё в природе стремится к симметрии, как здоровая улыбка». Какое количество резцов заложено в формулу идеального генофонда человека? \n\n"
                f"Это число — ваш пароль к данным о 'Семени Жизни', скрытом в центре Мариуполя'.")
        kb = tele_types.InlineKeyboardMarkup(row_width=3).add(
            tele_types.InlineKeyboardButton("🔘 4", callback_data="apoc_s2_pass_fail"),
            tele_types.InlineKeyboardButton("🔘 8", callback_data="apoc_s2_28"),
            tele_types.InlineKeyboardButton("🔘 12", callback_data="apoc_s2_pass_fail")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 28: ПЕРЕДАЧА ДАННЫХ (Таймер) ] ---
    elif call.data == "apoc_s2_28":
        if not has_flag(current_node, "data_core"):
            current_node = add_flag(current_node, "data_core")
            set_game_node(user_id, current_node)
            add_xp(user_id, 15, username)
            
        t = 12 if has_flag(current_node, "super_motor") else 18
        set_game_timer(user_id, t)
        
        text = (f"💾 *ПОГРУЖЕНИЕ В БЕЗДНУ*\n\n"
                f"При вводе числа '8' глаза андроида вспыхивают золотом. Он берет вашу руку, и Био-анализатор начинает скачивать колоссальный объем данных. \n\n"
                f"**АНДРОИД:** 'Загрузка пошла. Вы узнаете всё: про эксперименты 1985-го, про то, как Академия Орион "
                f"пыталась приручить фиолетовый мох, и про то, почему вы — единственный выживший клон из партии 'Д-85'. "
                f"Но будьте осторожны: Академия уже знает, что терминал активен. Они идут за вами. \n\n"
                f"Марти: 'Док, я вижу движение на крыше парковки! Дроны Академии Орион! Они не собираются вести переговоры. "
                f"Нам нужно уходить, пока данные не перезагрузили ваши мозги окончательно!'.\n\n"
                f"Ожидание: **{t} минут**.")
        
        kb = tele_types.InlineKeyboardMarkup().add(
            tele_types.InlineKeyboardButton(f"🔄 Завершить синхронизацию", callback_data="apoc_s2_sync")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 29: ПРОРЫВ СКВОЗЬ КИСЛОТУ ] ---
    elif call.data == "apoc_s2_sync":
        text = (f"🔥 *ОБРУШЕНИЕ ЗЕНИТА*\n\n"
                f"Как только полоса загрузки доходит до 100%, потолок атриума разлетается в щепки под ударами ракет. "
                f"Здание 'Зенита' начинает оседать в кислотное болото. Андроид отталкивает вас к пожарному выходу.\n\n"
                f"**АНДРОИД:** 'Бегите к окраинам! Ищите стоматологическую клинику на проспекте Мира. Семя там. Я задержу их'. \n\n"
                f"Вы прыгаете в темный проем, а за вашей спиной раздается грохот рушащихся металлоконструкций. "
                f"Марти лает, указывая путь через затопленные склады. Вы бежите сквозь едкий дым, ориентируясь только на пульс Био-анализатора.")
        kb = tele_types.InlineKeyboardMarkup().add(
            tele_types.InlineKeyboardButton("🏃 Вырваться из ловушки", callback_data="apoc_s2_30")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # 🏆 --- [ ЭТАП 30: ФИНАЛ ГЛАВЫ 2 ] --- 🏆
    elif call.data == "apoc_s2_30":
        is_first_time = not has_completed_chapter(user_id, "chapter_2")
        
        if is_first_time:
            xp_reward = 150
            dust_reward = 150
            mark_chapter_completed(user_id, "chapter_2")
            reward_msg = f"🎁 **ДЖЕКПОТ ЗА ПЕРВОЕ ПРОХОЖДЕНИЕ:**\n✨ Опыт: +{xp_reward} XP\n💎 Пыль: +{dust_reward} ед.\n"
        else:
            xp_reward = 20
            dust_reward = 20
            reward_msg = f"🔄 **НАГРАДА ЗА ПОВТОРНОЕ ПРОХОЖДЕНИЕ:**\n✨ Опыт: +{xp_reward} XP\n💎 Пыль: +{dust_reward} ед.\n"

        if not has_flag(current_node, "ch2_done"):
            add_xp(user_id, xp_reward, username) 
            current_node = add_flag(current_node, "ch2_done")
            
        current_node = set_loc(current_node, "apoc_ch2_completed_screen")
        set_game_node(user_id, current_node)
        loc = "apoc_ch2_completed_screen"

        text = (f"🏜 *ГРАНИЦА МАРИУПОЛЯ*\n\n"
                f"Вы выбираетесь из кислотного тумана. Сзади догорают руины ТЦ 'Зенит'. Впереди, за пеленой смога, "
                f"проступают очертания города вашего детства — Мариуполя. Но он неузнаваем. Это джунгли из бетона и пульсирующего мха.\n\n"
                f"Вы смотрите на Био-анализатор. Теперь на нем горит новая надпись: \n"
                f"*«ОБЪЕКТ: СЕМЯ ЖИЗНИ. ЛОКАЦИЯ: ПОДЗЕМНЫЙ АРХИВ КЛИНИКИ. ДИСТАНЦИЯ: 3 КМ»*.\n\n"
                f"Марти: 'Док, мы это сделали. Мы выжили в болотах и узнали правду. Вы — не просто ученый. Вы — надежда этой планеты. "
                f"Ну что, пойдем навестим ваше старое рабочее место? Кажется, там нас ждет кто-то пострашнее дронов'.\n\n"
                f"{reward_msg}\n"
                f"🚀 **ГЛАВА 2 ЗАВЕРШЕНА. Глава 3: Эхо Небоскребов разблокирована.**")
        
        kb = tele_types.InlineKeyboardMarkup().add(
            tele_types.InlineKeyboardButton("🚀 Начать Главу 3", callback_data="apoc_s3_start"),
            tele_types.InlineKeyboardButton("🏆 Вернуться в меню симуляций", callback_data="game_main_menu")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ БЛОК: ОБРАБОТКА ОШИБОК И НЕВЕРНЫХ ВЫБОРОВ ] ---
    elif call.data in ["apoc_s2_synth_fail", "apoc_s2_freq_fail", "apoc_s2_dna_fail", "apoc_s2_visco_fail", "apoc_s2_pass_fail", "apoc_s2_cocoons_fail"]:
        bot.answer_callback_query(call.id, "❌ ОШИБКА СИНХРОНИЗАЦИИ. Марти: 'Док, вы уверены? Мои датчики говорят, что это путь в никуда!'", show_alert=True)
        return

    elif call.data == "apoc_s2_hack_fail":
        bot.answer_callback_query(call.id, "🚫 ОТКАЗ В ДОСТУПЕ. Марти: 'Тут нужна ваша рука, Док. Мой хвост система не распознает!'", show_alert=True)
        return

    elif call.data == "apoc_s2_reagent_fail":
        bot.answer_callback_query(call.id, "⚠️ ОПАСНО: Флакон под давлением! Марти: 'Док, используйте зажим, не рискуйте пальцами!'", show_alert=True)
        return

    # --- [ БЛОК: ДЕТЕКТИВНЫЕ НАХОДКИ (Анти-Фарм) ] ---
    elif call.data == "apoc_s2_clue_fruit":
        if not has_flag(current_node, "clue_fruit"):
            current_node = add_flag(current_node, "clue_fruit")
            set_game_node(user_id, current_node)
            add_xp(user_id, 3, username)
        bot.answer_callback_query(call.id, "🧬 АНАЛИЗ: Плод содержит ДНК, идентичную вашей на 99.8%. Марти: 'Это не дерево, это инкубатор!'", show_alert=True)

    elif call.data == "apoc_s2_clue_notes":
        if not has_flag(current_node, "clue_notes"):
            current_node = add_flag(current_node, "clue_notes")
            set_game_node(user_id, current_node)
            add_xp(user_id, 3, username)
        bot.answer_callback_query(call.id, "📝 ЗАПИСЬ: 'Дмитрий, если читаешь это — Семя требует ключа'. Почерк деда... он знал, что вы придете'.", show_alert=True)

    elif call.data == "apoc_s2_clue_info":
        if not has_flag(current_node, "clue_info"):
            current_node = add_flag(current_node, "clue_info")
            set_game_node(user_id, current_node)
            add_xp(user_id, 3, username)
        bot.answer_callback_query(call.id, "🖥 ДАННЫЕ: ТЦ 'Зенит' был построен как колыбель для системы 'Архив'. Вы получили +3 Пыли!", show_alert=True)

    elif call.data == "apoc_s2_clue_arm":
        if not has_flag(current_node, "clue_arm"):
            current_node = add_flag(current_node, "clue_arm")
            set_game_node(user_id, current_node)
            add_xp(user_id, 3, username)
        bot.answer_callback_query(call.id, "🦾 ОСМОТР: Протез андроида собран из инструментов вашей стоматологии. Серийный номер: М-85.", show_alert=True)
