import telebot
from datetime import datetime
from telebot import types as tele_types
# Импортируем функции базы данных
from database import get_game_status, update_game_progress, set_game_timer

def run_scenario(bot, call):
    user_id = call.from_user.id
    username = call.from_user.first_name if call.from_user.first_name else "Пилот"
    
    # Получаем статус игрока
    current_node, timer_end = get_game_status(user_id)
    
    # 1. Проверка глобального таймера
    if timer_end and datetime.now() < timer_end:
        remaining = timer_end - datetime.now()
        mins = int(remaining.total_seconds() // 60)
        bot.answer_callback_query(call.id, f"⏳ Марти занят. Будет готов через {mins} мин.", show_alert=True)
        return

    # 2. Навигация по сюжету
    if call.data == "game_start":
        text = (f"🛰 **БОРТОВОЙ ЖУРНАЛ: ЗАПИСЬ #1**\n\n"
                f"{username}, шлюз 'Авалона-7' встретил вас ледяным сквозняком. "
                f"Марти замер, его сенсоры сканируют темноту. Перед вами — разбитая панель управления и "
                f"ряд запертых шкафчиков экипажа.\n\n"
                "С чего начнете?")
        
        kb = tele_types.InlineKeyboardMarkup(row_width=1)
        kb.add(
            tele_types.InlineKeyboardButton("🔍 Осмотреть панель", callback_data="game_node_panel"),
            tele_types.InlineKeyboardButton("📦 Вскрыть шкафчики", callback_data="game_node_closet")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        update_game_progress(user_id, "shluz_entry")

    # --- ВЕТКА ШКАФЧИКОВ (ПУГАЮЩАЯ) ---
    elif call.data == "game_node_closet":
        text = (f"📦 Вы подошли к ряду шкафчиков. Один из них слегка приоткрыт, и оттуда тянет странным "
                f"металлическим запахом. Вы тянете за ручку...\n\n"
                f"Внутри — не просто вещи. Стенки шкафчика покрыты тонким слоем замерзшей фиолетовой субстанции. "
                f"На дне лежит офицерский китель, но он разорван так, будто кто-то пытался выбраться из него "
                f"слишком быстро. \n\n"
                f"Марти внезапно оскалился и издал низкий, вибрирующий рык. Его налобный фонарь выхватил из-под "
                f"вороха одежды **серебряный медальон**, который... пульсирует в такт вашему пульсу.\n\n"
                f"Что сделаете?")
        
        kb = tele_types.InlineKeyboardMarkup(row_width=1)
        kb.add(
            tele_types.InlineKeyboardButton("🖐 Взять медальон в руки", callback_data="game_node_medalion"),
            tele_types.InlineKeyboardButton("🐕 Попросить Марти принести его", callback_data="game_node_marty_bring"),
            tele_types.InlineKeyboardButton("⬅️ Назад к панели", callback_data="game_start")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        update_game_progress(user_id, "shluz_closet")

    # --- ВЕТКА ПАНЕЛИ (ТАЙМЕР) ---
    elif call.data == "game_node_panel":
        set_game_timer(user_id, 10)
        text = ("⚙️ Вы коснулись проводов. Марти тут же выпустил манипулятор:\n\n"
                "— Хозяин, здесь зашифрованный протокол 'Эхо'. Мне нужно около **10 минут**, чтобы взломать систему. "
                "Пока я работаю, не отходите далеко. Мне кажется, из вентиляции за нами кто-то наблюдает...")
        kb = tele_types.InlineKeyboardMarkup()
        kb.add(tele_types.InlineKeyboardButton("⬅️ Вернуться на мостик", callback_data="game_back_to_profile"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        update_game_progress(user_id, "hacking_panel")

    # Возврат к профилю
    elif call.data == "game_back_to_profile":
        # Это вызовет handle_text в marty_chat.py, если правильно настроено
        bot.answer_callback_query(call.id, "Возвращаемся на мостик...")

    # --- ВЕТКА: ВЗЯТЬ МЕДАЛЬОН (РИСК) ---
    elif call.data == "game_node_medalion":
        # Начисляем немного XP за смелость
        # add_xp(user_id, 2) # Можно вызвать функцию из базы, если нужно
        text = (f"🖐 Вы протягиваете руку и касаетесь холодного металла. В ту же секунду ваше зрение "
                f"вспыхивает белым светом. Тело пронзает слабый электрический разряд.\n\n"
                f"Прямо на сетчатке вашего глаза, поверх интерфейса шлема, начинают бежать кроваво-красные цифры:\n"
                f"📍 **СЕКТОР: 0-Г-13**\n"
                f"📍 **КООРДИНАТЫ: 42.0081 // -19.4402**\n\n"
                f"Вы слышите хриплый, прерывающийся шепот в динамиках: 'Не ищите нас... оно уже здесь'.\n\n"
                f"Марти подпрыгивает и толкает вас носом, приводя в чувство. Медальон в вашей руке "
                f"мгновенно почернел и превратился в бесполезный кусок пластика. "
                f"Но координаты теперь выжжены в вашей памяти.")
        
        kb = tele_types.InlineKeyboardMarkup(row_width=1)
        kb.add(
            tele_types.InlineKeyboardButton("🛰 Ввести данные в панель", callback_data="game_node_panel_with_coords"),
            tele_types.InlineKeyboardButton("🏠 Вернуться на мостик", callback_data="game_back_to_profile")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        update_game_progress(user_id, "shluz_coords_found")

    # --- ВЕТКА: МАРТИ ПРИНОСИТ (ОСТОРОЖНОСТЬ) ---
    elif call.data == "game_node_marty_bring":
        text = (f"🐕 Марти аккуратно подкрадывается к шкафчику и хватает медальон зубами. "
                f"Раздается короткий треск статики. Пес испуганно роняет вещь и отскакивает.\n\n"
                f"— Хозяин! — динамик Марти выдает помехи. — Мои системы зафиксировали "
                f"передачу пакета данных. Это навигационный маяк. Он транслирует точку назначения "
                f"глубоко внутри фиолетовой туманности.\n\n"
                f"Медальон перестал пульсировать. Похоже, он передал всё, что мог, и 'умер'.")
        
        kb = tele_types.InlineKeyboardMarkup(row_width=1)
        kb.add(
            tele_types.InlineKeyboardButton("🔍 Посмотреть, куда ведут данные", callback_data="game_node_panel_with_coords"),
            tele_types.InlineKeyboardButton("⬅️ Назад к панели", callback_data="game_start")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        update_game_progress(user_id, "shluz_marty_data")

     # --- ВЕТКА: ВВОД КООРДИНАТ В ПАНЕЛЬ ---
    elif call.data == "game_node_panel_with_coords":
        set_game_timer(user_id, 30)  # Таймер на 30 минут
        text = (f"📟 Вы подходите к центральному терминалу. Пальцы в тяжелых перчатках неловко "
                f"вбивают цифры: **42.0081 // -19.4402**.\n\n"
                f"Экран на мгновение гаснет, а затем заливает всю рубку тревожным багровым светом. "
                f"В глубине станции что-то тяжело загудело, по полу прошла вибрация.\n\n"
                f"— Хозяин, — Марти прижал уши к голове, — компьютер запрашивает старые навигационные карты "
                f"из глубокого архива. Этот сектор заблокирован протоколом 'Стикс'. \n\n"
                f"На экране побежали проценты: **[Вычисление траектории: 1%]**.\n"
                f"Это займет минимум **30 минут**. Пока система работает, мы не можем покинуть шлюз — "
                f"магнитные замки заблокированы для стабилизации питания.")
        
        kb = tele_types.InlineKeyboardMarkup()
        kb.add(tele_types.InlineKeyboardButton("⬅️ Вернуться на мостик", callback_data="game_back_to_profile"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        update_game_progress(user_id, "calculating_trajectory")

    # --- ПРОВЕРКА РЕЗУЛЬТАТА (ПОСЛЕ ТАЙМЕРА) ---
    elif call.data == "game_check_trajectory":
        text = (f"✅ **РАСЧЕТ ЗАВЕРШЕН**\n\n"
                f"Гул в стенах затих. Багровый свет сменился на ровный белый. На экране терминала "
                f"развернулась трехмерная карта туманности. \n\n"
                f"Точка, которую вы ввели, находится не в открытом космосе. Она ведет... внутрь "
                f"самой станции, в скрытый ярус, которого нет на схемах. \n\n"
                f"— {username}, посмотри, — Марти указал лапой на открывшийся проход в стене, "
                f"скрытый за фальш-панелью. — Это путь в 'Сектор Зеро'. Но мои датчики говорят, "
                f"что там нет кислорода. Совсем.")
        
        kb = tele_types.InlineKeyboardMarkup(row_width=1)
        kb.add(
            tele_types.InlineKeyboardButton("🔦 Спуститься в Сектор Зеро", callback_data="game_node_sector_zero"),
            tele_types.InlineKeyboardButton("🏠 На мостик (отложить)", callback_data="game_back_to_profile")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        update_game_progress(user_id, "path_to_zero_opened")

    # --- ВЕТКА: СПУСК В СЕКТОР ЗЕРО (АТМОСФЕРА И ТЕМНОТА) ---
    elif call.data == "game_node_sector_zero":
        text = (f"🌑 вы делаете шаг в проем. Тяжелый гермозатвор за вашей спиной с грохотом закрывается. "
                f"В шлеме тут же вспыхивает красная надпись: **[ВНЕШНЯЯ АТМОСФЕРА: ОТСУТСТВУЕТ]**.\n\n"
                f"Здесь абсолютная, густая темнота. Фонарь скафандра выхватывает лишь пыль, застывшую в вакууме. "
                f"Тишина такая глубокая, что вы слышите собственное сердцебиение.\n\n"
                f"— Хозяин, — голос Марти в наушниках звучит приглушенно, — я переключаюсь на тепловизор. "
                f"Стены здесь покрыты тем же фиолетовым 'мхом', но он... пульсирует теплом. \n\n"
                f"Марти замирает. Его сенсоры поймали движение в конце коридора. "
                f"Что предпримете?")
        
        kb = tele_types.InlineKeyboardMarkup(row_width=1)
        kb.add(
            tele_types.InlineKeyboardButton("🔦 Включить мощный прожектор", callback_data="game_node_light_trap"),
            tele_types.InlineKeyboardButton("🛰 Использовать сенсоры Марти", callback_data="game_node_marty_vision"),
            tele_types.InlineKeyboardButton("🔇 Двигаться на ощупь в тишине", callback_data="game_node_stealth")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        update_game_progress(user_id, "sector_zero_entry")

    # --- ВЕТКА: СЕНСОРЫ МАРТИ (ДЕТЕКТИВНЫЙ ПУТЬ) ---
    elif call.data == "game_node_mart_vision":
        text = (f"🐕 Марти транслирует изображение прямо в ваш визор. Мир окрашивается в сине-зеленые тона. \n\n"
                f"Вы видите то, что скрыто от глаз: тепловые следы ведут к запертой сейфовой двери в стене. "
                f"Но самое странное — на потолке висит огромный кокон из тех самых фиолетовых нитей. \n\n"
                f"Внутри кокона угадываются очертания... человеческой фигуры. Марти анализирует биометрию.\n\n"
                f"— Это капитан 'Авалона', — шепчет робо-пес. — Но его ДНК... она перестраивается прямо сейчас.")
        
        kb = tele_types.InlineKeyboardMarkup(row_width=1)
        kb.add(
            tele_types.InlineKeyboardButton("🩺 Попробовать вскрыть кокон", callback_data="game_node_open_cocoon"),
            tele_types.InlineKeyboardButton("🗄 Осмотреть сейф рядом", callback_data="game_node_safe_search")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        update_game_progress(user_id, "captain_found")

    # --- ВЕТКА: ЛОВУШКА СВЕТА (ТУПИК/ПРОБЛЕМА) ---
    elif call.data == "game_node_light_trap":
        text = (f"💡 Вы щелкаете тумблером прожектора. Яркий луч разрезает мрак...\n\n"
                f"И в ту же секунду фиолетовый мох на стенах начинает стремительно расти в сторону света! "
                f"Щупальца из энергии оплетают ваши ноги. Система скафандра выдает каскад ошибок.\n\n"
                f"— Назад! — Марти пытается перегрызть светящиеся нити, но они проходят сквозь металл.\n\n"
                f"Вам нужно срочно что-то предпринять, пока энергия скафандра не упала до нуля!")
        
        kb = tele_types.InlineKeyboardMarkup(row_width=1)
        kb.add(
            tele_types.InlineKeyboardButton("💥 Выстрелить из импульсного резака", callback_data="game_node_shoot"),
            tele_types.InlineKeyboardButton("🔋 Выключить питание скафандра", callback_data="game_node_power_off")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        update_game_progress(user_id, "light_trap_active")
