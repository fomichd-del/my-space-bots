import telebot
from datetime import datetime
from telebot import types as tele_types
from database import get_game_status, update_game_progress, set_game_timer

def run_scenario(bot, call):
    user_id = call.from_user.id
    username = call.from_user.first_name if call.from_user.first_name else "Пилот"
    
    current_node, timer_end = get_game_status(user_id)
    
    # 1. Глобальная проверка таймера
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
            tele_types.InlineKeyboardButton("📦 Вскрыть шкафчики", callback_data="game_node_closet"),
            tele_types.InlineKeyboardButton("🛑 Сбросить прогресс", callback_data="game_reset")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        update_game_progress(user_id, "shluz_entry")

    elif call.data == "game_reset":
        update_game_progress(user_id, "start")
        bot.answer_callback_query(call.id, "Бортовой журнал очищен.")
        # Искусственно вызываем старт
        call.data = "game_start"
        run_scenario(bot, call)

    # --- ВЕТКА ШКАФЧИКОВ ---
    elif call.data == "game_node_closet":
        text = (f"📦 Внутри шкафчика стенки покрыты замерзшей фиолетовой субстанцией. "
                f"Марти внезапно оскалился и издал низкий рык. Под ворохом одежды лежит "
                f"**серебряный медальон**, пульсирующий в такт вашему сердцу.\n\n"
                f"Что сделаете?")
        
        kb = tele_types.InlineKeyboardMarkup(row_width=1)
        kb.add(
            tele_types.InlineKeyboardButton("🖐 Взять медальон (Риск)", callback_data="game_node_medalion"),
            tele_types.InlineKeyboardButton("🐕 Попросить Марти (Безопасно)", callback_data="game_node_marty_bring"),
            tele_types.InlineKeyboardButton("⬅️ Назад к панели", callback_data="game_start")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        update_game_progress(user_id, "shluz_closet")

    # --- ВЕТКА ПАНЕЛИ (ТАЙМЕР 10 МИН) ---
    elif call.data == "game_node_panel":
        set_game_timer(user_id, 10)
        text = ("⚙️ Марти подключился к панели:\n\n"
                "— Хозяин, тут протокол 'Эхо'. Мне нужно **10 минут**. "
                "Мне кажется, из вентиляции за нами кто-то наблюдает...")
        kb = tele_types.InlineKeyboardMarkup()
        kb.add(tele_types.InlineKeyboardButton("🔄 Проверить готовность", callback_data="game_start"))
        kb.add(tele_types.InlineKeyboardButton("🏠 На мостик", callback_data="game_back_to_profile"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        update_game_progress(user_id, "hacking_panel")

    # --- ВЕТКА МЕДАЛЬОНА И КООРДИНАТ ---
    elif call.data == "game_node_medalion":
        text = (f"🖐 Вы касаетесь металла. Зрение вспыхивает белым светом! \n\n"
                f"В шлеме горят координаты: **42.0081 // -19.4402**.\n"
                f"Шепот в динамиках: 'Не ищите нас... оно уже здесь'.\n\n"
                f"Медальон почернел, но данные выжжены в памяти.")
        kb = tele_types.InlineKeyboardMarkup(row_width=1)
        kb.add(
            tele_types.InlineKeyboardButton("🛰 Ввести координаты", callback_data="game_node_panel_with_coords"),
            tele_types.InlineKeyboardButton("🏠 На мостик", callback_data="game_back_to_profile")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    elif call.data == "game_node_panel_with_coords":
        set_game_timer(user_id, 30)
        text = (f"📟 Вы ввели координаты. Терминал залил рубку багровым светом.\n\n"
                f"— Хозяин, идет поиск в архивах 'Стикс'. Вычисление траектории займет **30 минут**.\n"
                f"Магнитные замки шлюза заблокированы.")
        kb = tele_types.InlineKeyboardMarkup()
        kb.add(tele_types.InlineKeyboardButton("🔄 Проверить результат", callback_data="game_check_trajectory"))
        kb.add(tele_types.InlineKeyboardButton("🏠 На мостик", callback_data="game_back_to_profile"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        update_game_progress(user_id, "calculating_trajectory")

    # --- ПРОВЕРКА РЕЗУЛЬТАТА ТРАЕКТОРИИ ---
    elif call.data == "game_check_trajectory":
        text = (f"✅ **РАСЧЕТ ЗАВЕРШЕН**\n\n"
                f"Точка ведет внутрь станции, в скрытый ярус. "
                f"За фальш-панелью открылся проход. Это Сектор Зеро. "
                f"Там нет кислорода.")
        kb = tele_types.InlineKeyboardMarkup(row_width=1)
        kb.add(tele_types.InlineKeyboardButton("🔦 Спуститься в Сектор Зеро", callback_data="game_node_sector_zero"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- СЕКТОР ЗЕРО ---
    elif call.data == "game_node_sector_zero":
        text = (f"🌑 В Секторе Зеро абсолютная темнота. Вы слышите только свое дыхание. "
                f"Марти видит тепловые следы: 'Стены пульсируют теплом'. "
                f"В конце коридора что-то движется.")
        kb = tele_types.InlineKeyboardMarkup(row_width=1)
        kb.add(
            tele_types.InlineKeyboardButton("🔦 Прожектор (Риск)", callback_data="game_node_light_trap"),
            tele_types.InlineKeyboardButton("🛰 Сенсоры Марти (Безопасно)", callback_data="game_node_marty_vision")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- СЕНСОРЫ МАРТИ И КАПИТАН ---
    elif call.data == "game_node_marty_vision":
        text = (f"🐕 Мир окрасился в синий. На потолке висит огромный фиолетовый кокон. "
                f"Внутри — капитан 'Авалона'. Его ДНК перестраивается. "
                f"Рядом стоит старый сейф.")
        kb = tele_types.InlineKeyboardMarkup(row_width=1)
        kb.add(
            tele_types.InlineKeyboardButton("🩺 Осмотреть кокон", callback_data="game_node_open_cocoon"),
            tele_types.InlineKeyboardButton("🗄 Осмотреть сейф", callback_data="game_node_safe_search")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- ДЕТЕКТИВНАЯ НАХОДКА В СЕЙФЕ ---
    elif call.data == "game_node_safe_search":
        text = (f"🗄 Сейф не заперт. Внутри вы находите детскую игрушку — модель шаттла — и "
                f"потрепанный дневник капитана. Последняя запись: \n\n"
                f"'Сектор Зеро — это не лаборатория. Это убежище. Мы пытались спрятать их здесь от того, "
                f"что пришло вместе с сигналом из Солнечной системы'. \n\n"
                f"Вы понимаете: угроза пришла не из космоса, а с Земли.")
        kb = tele_types.InlineKeyboardMarkup(row_width=1)
        kb.add(tele_types.InlineKeyboardButton("🩺 Теперь к кокону...", callback_data="game_node_open_cocoon"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- ВЕТКА: ОСМОТР КОКОНА (СБОР ОБРАЗЦА) ---
    elif call.data == "game_node_open_cocoon":
        text = (f"🩺 Вы осторожно приближаетесь к пульсирующему кокону. Марти замер, его "
                f"био-сенсоры работают на пределе. Вблизи фиолетовые нити выглядят как "
                f"тончайшие нейронные сети.\n\n"
                f"— Хозяин, — Марти (male) сканирует поверхность, — этот мох питается "
                f"остаточной энергией станции. Если мы возьмем образец, я смогу проанализировать "
                f"его в лаборатории Академии. Но это может спровоцировать защиту.\n\n"
                f"Что предпримете?")
        
        kb = tele_types.InlineKeyboardMarkup(row_width=1)
        kb.add(
            tele_types.InlineKeyboardButton("🧪 Собрать образец (Бонус +3 Пыли)", callback_data="game_node_collect_moss"),
            tele_types.InlineKeyboardButton("⚔️ Попробовать вскрыть кокон", callback_data="game_node_cut_cocoon"),
            tele_types.InlineKeyboardButton("⬅️ Назад к сейфу", callback_data="game_node_marty_vision")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        update_game_progress(user_id, "at_the_cocoon")

    # --- ВЕТКА: СБОР МХА (БОНУС) ---
    elif call.data == "game_node_collect_moss":
        # Начисляем награду (XP и Пыль в вашей базе связаны 1:1)
        add_xp(user_id, 3, username) 
        
        text = (f"✨ Марти аккуратно выдвинул медицинский манипулятор и срезал фрагмент светящегося мха. "
                f"Субстанция в контейнере зашипела, а по всей станции раздался едва слышный стон.\n\n"
                f"✅ **Бортовой компьютер:** Начислено +3 Звездной пыли за научный вклад!\n\n"
                f"— Образец изолирован, — Марти (male) спрятал контейнер в свой корпус. — Но мох "
                f"снаружи стал темнеть. Кажется, он нас... почувствовал. Нужно действовать быстрее!")
        
        kb = tele_types.InlineKeyboardMarkup(row_width=1)
        kb.add(
            tele_types.InlineKeyboardButton("⚔️ Вскрыть кокон и спасти капитана", callback_data="game_node_cut_cocoon"),
            tele_types.InlineKeyboardButton("🏃 Срочно уходить отсюда", callback_data="game_node_escape_zero")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        update_game_progress(user_id, "moss_collected")
