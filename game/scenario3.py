import telebot
from datetime import datetime
from telebot import types as tele_types
from database import get_game_status, update_game_progress, set_game_timer, add_xp

def run_scenario(bot, call):
    user_id = call.from_user.id
    username = call.from_user.first_name if call.from_user.first_name else "Пилот"
    current_node, timer_end = get_game_status(user_id)
    if current_node is None:
        current_node = ""
    
    # --- [ АНТИ-ФАРМ СИСТЕМА ] ---
    # Вытаскиваем "несгораемые" метки, чтобы они не стирались при смене локаций
    saved_flags = ""
    for flag in ["_ch3_claimed", "_item_stars", "_item_cup", "_item_wires"]:
        if flag in current_node:
            saved_flags += flag
            
    # 0. ПРОВЕРКА ЗАВЕРШЕНИЯ ГЛАВЫ
    is_finished = any(mark in current_node for mark in ["ch3_done_true", "ch3_done_bad"])

    # 1. ГЛОБАЛЬНАЯ ПРОВЕРКА ТАЙМЕРА
    if timer_end and datetime.now() < timer_end and not is_finished:
        remaining = timer_end - datetime.now()
        mins = int(remaining.total_seconds() // 60)
        bot.answer_callback_query(call.id, f"⏳ Марти калибрует сенсоры. Готовность через {mins} мин.", show_alert=True)
        return

    # 2. УМНЫЙ СТАРТ (Точки восстановления)
    if call.data == "game3_start":
        if current_node and current_node.startswith("ch3_") and current_node != "ch3_start":
            
            # --- [ АТМОСФЕРНЫЙ ЛОКАТОР ] ---
            if "climax" in current_node:
                location_text = "Центральный зал. Пространство и время искажены."
            elif "gate" in current_node:
                location_text = "У запертых врат Колыбели. Панель ждет ввода."
            elif "scan_wait" in current_node or "scan_done" in current_node:
                location_text = "Орбита станции. Данные сканирования."
            elif "mines" in current_node:
                location_text = "Заброшенные шахты 'Стикса'. Мох пульсирует во тьме."
            elif "jump_wait" in current_node or "arrival" in current_node:
                location_text = "Шлюз станции 'Стикс-9'. Системы жизнеобеспечения активны."
            else:
                location_text = "Неизвестный сектор. Восстановление логов..."

            text = (f"🛰 **СЕАНС СВЯЗИ: ГЛАВА 3**\n\n"
                    f"Пилот {username}, системы успешно перезагружены.\n"
                    f"📍 **Текущая геопозиция:** *{location_text}*\n\n"
                    f"Марти бодро вильнул хвостом: 'Хозяин, я сохранил все наши зацепки! Продолжаем погружение?'")
            
            kb = tele_types.InlineKeyboardMarkup(row_width=1)
            
            if "climax" in current_node:
                kb.add(tele_types.InlineKeyboardButton("🤝 К Кристаллу", callback_data="game3_node_gate_open"))
            elif "gate" in current_node:
                kb.add(tele_types.InlineKeyboardButton("🗿 К Двери Колыбели", callback_data="game3_node_final_gate"))
            elif "scan_wait" in current_node:
                kb.add(tele_types.InlineKeyboardButton("🔄 Результаты сканера", callback_data="game3_check_scan"))
            elif "mines" in current_node:
                kb.add(tele_types.InlineKeyboardButton("⛏ В шахты", callback_data="game3_node_mines"))
            elif "jump_wait" in current_node:
                kb.add(tele_types.InlineKeyboardButton("🔄 Проверить выход из гипера", callback_data="game3_check_jump"))
            else:
                kb.add(tele_types.InlineKeyboardButton("🚀 Продолжить миссию", callback_data="game3_node_arrival"))
            
            kb.add(tele_types.InlineKeyboardButton("♻️ Сбросить прогресс", callback_data="game3_reset"))
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
            return

        # ЭТАП 1: МУЛЬТИ-СТАРТ
        kb = tele_types.InlineKeyboardMarkup(row_width=1)
        if "ch2_done_hero" in current_node:
            t = "🌟 **ЭТАП 1: ПУТЬ АГЕНТА**\n\nВы — герой Академии. Ваш новый 'Стриж' готов к прыжку."
            kb.add(tele_types.InlineKeyboardButton("🛰 Лететь к маяку", callback_data="game3_node_prejump"))
        elif "ch2_done_escape" in current_node:
            t = "🏴 **ЭТАП 1: ПУТЬ ИЗГОЯ**\n\nВы скрываетесь. Нужно найти базу в астероидном поясе."
            kb.add(tele_types.InlineKeyboardButton("☄️ Искать укрытие", callback_data="game3_node_prejump"))
        else:
            t = "⛓ **ЭТАП 1: ПУТЬ УЗНИКА**\n\nТюрьма повреждена! Бегите к ангару."
            kb.add(tele_types.InlineKeyboardButton("🏃 К ангару", callback_data="game3_node_prejump"))
        
        bot.edit_message_text(t, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        update_game_progress(user_id, "ch3_start" + saved_flags)

    elif call.data == "game3_reset":
        new_start = "ch2_done_hero" + saved_flags # Награды теперь не сгорают при сбросе
        update_game_progress(user_id, new_start)
        bot.answer_callback_query(call.id, "Журнал обнулен. Награды защищены.")
        run_scenario(bot, type('obj', (object,), {'from_user': call.from_user, 'data': 'game3_start', 'message': call.message}))

    # ЭТАП 2-3: ПРЫЖОК
    elif call.data == "game3_node_prejump":
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("🧩 Гнездо 'Бета' (Фиолетовый)", callback_data="game3_node_jump_wait"),
            tele_types.InlineKeyboardButton("🧩 Гнездо 'Альфа' (Зеленый)", callback_data="game3_node_fail_puzzle")
        )
        bot.edit_message_text("⚙️ **ЭТАП 2: НЕЙРО-СТЫКОВКА**\n\nВыберите частоту прыжка.", call.message.chat.id, call.message.message_id, reply_markup=kb)

    elif call.data == "game3_node_jump_wait":
        set_game_timer(user_id, 20)
        bot.edit_message_text("🚀 Прыжок (20 мин)... Марти калибрует щиты.", 
                               call.message.chat.id, call.message.message_id, 
                               reply_markup=tele_types.InlineKeyboardMarkup().add(tele_types.InlineKeyboardButton("🔄 Проверить", callback_data="game3_check_jump")))
        update_game_progress(user_id, "ch3_jump_wait" + saved_flags)

    elif call.data == "game3_check_jump":
        bot.edit_message_text("✨ Станция 'Стикс-9' на экранах. Свечение манит.", 
                               call.message.chat.id, call.message.message_id, 
                               reply_markup=tele_types.InlineKeyboardMarkup().add(tele_types.InlineKeyboardButton("🚢 Стыковка", callback_data="game3_node_arrival")))
        update_game_progress(user_id, "ch3_arrival" + saved_flags)

    # ЭТАПЫ 4-6: ОБЫСК (ПРЕДМЕТЫ)
    elif call.data == "game3_node_arrival":
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("🗄 Шкафчики (Поиск)", callback_data="game3_search_locker"),
            tele_types.InlineKeyboardButton("☕️ Столовая (Поиск)", callback_data="game3_search_canteen"),
            tele_types.InlineKeyboardButton("🚧 К терминалу", callback_data="game3_node_horrorevent")
        )
        bot.edit_message_text("🏚 Станция пуста. Марти: 'Смотрите в оба!'", call.message.chat.id, call.message.message_id, reply_markup=kb)
        update_game_progress(user_id, "ch3_hub_search" + saved_flags)

    elif call.data == "game3_search_locker":
        if "item_stars" not in current_node:
            add_xp(user_id, 1, username)
            update_game_progress(user_id, current_node + "_item_stars")
            msg = "✅ Карта Звезд в инвентаре (+1 Пыль).\n\n"
        else: 
            msg = "Тут уже пусто.\n\n"
        kb = tele_types.InlineKeyboardMarkup().add(tele_types.InlineKeyboardButton("🔙 Назад", callback_data="game3_node_arrival"))
        bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, reply_markup=kb)

    elif call.data == "game3_search_canteen":
        if "item_cup" not in current_node:
            add_xp(user_id, 1, username)
            update_game_progress(user_id, current_node + "_item_cup")
            msg = "✅ Найдена кружка с кодом 8811 (+1 Пыль).\n\n"
        else: 
            msg = "Кофе-машина молчит.\n\n"
        kb = tele_types.InlineKeyboardMarkup().add(tele_types.InlineKeyboardButton("🔙 Назад", callback_data="game3_node_arrival"))
        bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, reply_markup=kb)

    # ЭТАП 8: СКАНЕР
    elif call.data == "game3_node_scan_start":
        if "ch3_scan_done" in current_node:
            run_scenario(bot, type('obj', (object,), {'from_user': call.from_user, 'data': 'game3_check_scan', 'message': call.message}))
            return
        set_game_timer(user_id, 30)
        bot.edit_message_text("🖥 Сканирование (30 мин)... Марти блокирует двери.", 
                               call.message.chat.id, call.message.message_id, 
                               reply_markup=tele_types.InlineKeyboardMarkup().add(tele_types.InlineKeyboardButton("🔄 Результаты", callback_data="game3_check_scan")))
        update_game_progress(user_id, "ch3_scan_wait" + saved_flags)

    elif call.data == "game3_check_scan":
        bot.edit_message_text("✅ Скан готов. Цель — в шахтах астероида.", 
                               call.message.chat.id, call.message.message_id, 
                               reply_markup=tele_types.InlineKeyboardMarkup().add(tele_types.InlineKeyboardButton("🕵️ В шахты", callback_data="game3_node_mines")))
        update_game_progress(user_id, "ch3_scan_done" + saved_flags)

    # ЭТАПЫ 9-11: ШАХТЫ
    elif call.data == "game3_node_mines":
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("🎒 Сумка (Поиск)", callback_data="game3_item_wires"),
            tele_types.InlineKeyboardButton("🚪 К Двери", callback_data="game3_node_final_gate")
        )
        bot.edit_message_text("⛏ Шахты 'Стикса'. Мох светится во тьме.", call.message.chat.id, call.message.message_id, reply_markup=kb)
        update_game_progress(user_id, "ch3_mines" + saved_flags)

    elif call.data == "game3_item_wires":
        if "item_wires" not in current_node:
            add_xp(user_id, 1, username)
            update_game_progress(user_id, current_node + "_item_wires")
            msg = "✅ Провода найдены (+1 Пыль).\n\n"
        else: 
            msg = "Тут только камни.\n\n"
        kb = tele_types.InlineKeyboardMarkup().add(tele_types.InlineKeyboardButton("🔙 Назад", callback_data="game3_node_mines"))
        bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, reply_markup=kb)

    # ЭТАП 12-14: ДВЕРЬ
    elif call.data == "game3_node_final_gate":
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("🔢 Ввести 8811", callback_data="game3_node_gate_open"),
            tele_types.InlineKeyboardButton("🔢 Ввести 0000", callback_data="game3_node_fail_puzzle")
        )
        bot.edit_message_text("🗿 Дверь Колыбели заперта. Нужен код с кружки.", call.message.chat.id, call.message.message_id, reply_markup=kb)
        update_game_progress(user_id, "ch3_gate" + saved_flags)

    # ЭТАПЫ 15-18: ФИНАЛ
    elif call.data == "game3_node_gate_open":
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("🤝 Поверить себе", callback_data="game3_end_twist_good"),
            tele_types.InlineKeyboardButton("🔫 Стрелять", callback_data="game3_end_twist_bad"),
            tele_types.InlineKeyboardButton("🐕 Слушать Марти", callback_data="game3_end_marty_logic")
        )
        bot.edit_message_text("🔓 Дверь открыта. Вы и ваш Двойник. Время замерло.", call.message.chat.id, call.message.message_id, reply_markup=kb)
        update_game_progress(user_id, "ch3_climax" + saved_flags)

    elif call.data == "game3_end_twist_bad":
        if "ch3_claimed" not in current_node:
            add_xp(user_id, 70, username)
            update_game_progress(user_id, "ch3_done_true" + saved_flags + "_ch3_claimed")
            res = "💰 Награда: +70 Пыли."
        else:
            add_xp(user_id, 5, username)
            update_game_progress(user_id, "ch3_done_true" + saved_flags)
            res = "✨ Награда за повтор: +5 Пыли."
        bot.edit_message_text(f"🏆 **ФИНАЛ: СВОБОДА**\n\nВы разбили кристалл. Петля разорвана. {res}", call.message.chat.id, call.message.message_id)

    elif call.data == "game3_end_twist_good":
        if "ch3_claimed" not in current_node:
            add_xp(user_id, 30, username)
            update_game_progress(user_id, "ch3_done_bad" + saved_flags + "_ch3_claimed")
            res = "💰 Награда: +30 Пыли."
        else:
            add_xp(user_id, 5, username)
            update_game_progress(user_id, "ch3_done_bad" + saved_flags)
            res = "✨ Награда за повтор: +5 Пыли."
        bot.edit_message_text(f"🤝 **ФИНАЛ: МАРИОНЕТКА**\n\nВы стали частью системы. {res}", call.message.chat.id, call.message.message_id)

    # Прочие переходы
    elif call.data == "game3_node_horrorevent":
        run_scenario(bot, type('obj', (object,), {'from_user': call.from_user, 'data': 'game3_node_scan_start', 'message': call.message}))
    elif call.data == "game3_end_marty_logic":
        bot.edit_message_text("🐕 Марти: 'Не верь ему! Это ИИ корпорации!'", 
                               call.message.chat.id, call.message.message_id, 
                               reply_markup=tele_types.InlineKeyboardMarkup().add(tele_types.InlineKeyboardButton("🔫 Стрелять", callback_data="game3_end_twist_bad")))
