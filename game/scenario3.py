import telebot
from datetime import datetime
from telebot import types as tele_types
from database import get_game_status, update_game_progress, set_game_timer, add_xp

def run_scenario(bot, call):
    user_id = call.from_user.id
    username = call.from_user.first_name if call.from_user.first_name else "Пилот"
    current_node, timer_end = get_game_status(user_id)
    
    # 0. ПРОВЕРКА ЗАВЕРШЕНИЯ ГЛАВЫ
    # Если глава уже пройдена, мы игнорируем таймеры и награды
    is_finished = any(mark in current_node for mark in ["ch3_done_true", "ch3_done_bad"])

    # 1. ГЛОБАЛЬНАЯ ПРОВЕРКА ТАЙМЕРА (Только если глава не закончена)
    if timer_end and datetime.now() < timer_end and not is_finished:
        remaining = timer_end - datetime.now()
        mins = int(remaining.total_seconds() // 60)
        bot.answer_callback_query(call.id, f"⏳ Марти калибрует сенсоры. Готовность через {mins} мин.", show_alert=True)
        return

    # 2. УМНЫЙ СТАРТ (Восстановление сессии)
    if call.data == "game3_start":
        if is_finished:
            bot.answer_callback_query(call.id, "✅ Глава пройдена. Дождитесь обновления систем!", show_alert=True)
            return

        if current_node and current_node.startswith("ch3_") and current_node != "ch3_start":
            text = (f"🛰 **СЕАНС СВЯЗИ: ГЛАВА 3**\n\n"
                    f"Пилот {username}, восстанавливаем сектор: `{current_node}`.")
            kb = tele_types.InlineKeyboardMarkup(row_width=1)
            
            # ИСПРАВЛЕНО: Проверка от самого последнего этапа к первому
            if "scan_wait" in current_node:
                kb.add(tele_types.InlineKeyboardButton("🔄 Результаты сканера", callback_data="game3_check_scan"))
            elif "jump_wait" in current_node:
                kb.add(tele_types.InlineKeyboardButton("🔄 Проверить выход из гипера", callback_data="game3_check_jump"))
            elif "gate" in current_node:
                kb.add(tele_types.InlineKeyboardButton("🗿 К Двери Колыбели", callback_data="game3_node_final_gate"))
            elif "mines" in current_node:
                kb.add(tele_types.InlineKeyboardButton("⛏ В шахты астероида", callback_data="game3_node_mines"))
            else:
                kb.add(tele_types.InlineKeyboardButton("🚀 Продолжить путь", callback_data="game3_node_arrival"))
            
            kb.add(tele_types.InlineKeyboardButton("♻️ Сбросить прогресс главы", callback_data="game3_reset"))
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
            t = "⛓ **ЭТАП 1: ПУТЬ УЗНИКА**\n\nТюрьма обесточена! Бегите к ангару."
            kb.add(tele_types.InlineKeyboardButton("🏃 К ангару", callback_data="game3_node_prejump"))
        
        bot.edit_message_text(t, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        update_game_progress(user_id, "ch3_start")

    elif call.data == "game3_reset":
        update_game_progress(user_id, "ch2_done_hero") # Ставим нейтральный финал 2 главы
        bot.answer_callback_query(call.id, "Журнал главы 3 очищен.")
        run_scenario(bot, type('obj', (object,), {'from_user': call.from_user, 'data': 'game3_start', 'message': call.message}))

    # ЭТАП 2: ЗАГАДКА
    elif call.data == "game3_node_prejump":
        text = (f"⚙️ **ЭТАП 2: НЕЙРО-СТЫКОВКА**\n\nМарти: 'Нужен фиолетовый! Синий + Красный = ?'")
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("🧩 Гнездо 'Бета' (Синий+Красный)", callback_data="game3_node_jump_wait"),
            tele_types.InlineKeyboardButton("🧩 Гнездо 'Альфа' (Зеленый)", callback_data="game3_node_fail_puzzle")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    elif call.data == "game3_node_fail_puzzle":
        bot.answer_callback_query(call.id, "💥 Искры! Ошибка в схеме.", show_alert=True)
        return

    # ЭТАП 3: ТАЙМЕР 20 МИН (ПРЫЖОК)
    elif call.data == "game3_node_jump_wait":
        set_game_timer(user_id, 20)
        bot.edit_message_text("🚀 Прыжок в гипепространство (20 мин)... Марти ушел в спящий режим.", 
                               call.message.chat.id, call.message.message_id, 
                               reply_markup=tele_types.InlineKeyboardMarkup().add(tele_types.InlineKeyboardButton("🔄 Проверить", callback_data="game3_check_jump")))
        update_game_progress(user_id, "ch3_jump_wait")

    elif call.data == "game3_check_jump":
        bot.edit_message_text("✨ Станция 'Стикс-9' перед вами. Фиолетовое свечение усиливается.", 
                               call.message.chat.id, call.message.message_id, 
                               reply_markup=tele_types.InlineKeyboardMarkup().add(tele_types.InlineKeyboardButton("🚢 Стыковаться", callback_data="game3_node_arrival")))
        update_game_progress(user_id, "ch3_arrival")

    # ЭТАП 5: ОБЫСК
    elif call.data == "game3_node_arrival":
        text = "🏚 Станция заброшена. Где-то здесь должны быть улики."
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("🗄 Шкафчики (Поиск)", callback_data="game3_search_locker"),
            tele_types.InlineKeyboardButton("☕️ Столовая (Поиск)", callback_data="game3_search_canteen"),
            tele_types.InlineKeyboardButton("🚧 К терминалу", callback_data="game3_node_horrorevent")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        update_game_progress(user_id, "ch3_hub_search")

    elif call.data == "game3_search_locker":
        if "item_stars" not in current_node:
            add_xp(user_id, 1, username); update_game_progress(user_id, current_node + "_item_stars")
            msg = "✅ Найдена Карта Звезд (+1 Пыль).\n\n"
        else: msg = "Пусто.\n\n"
        kb = tele_types.InlineKeyboardMarkup().add(tele_types.InlineKeyboardButton("🔙 Назад", callback_data="game3_node_arrival"))
        bot.edit_message_text(msg + "Старые данные навигации.", call.message.chat.id, call.message.message_id, reply_markup=kb)

    elif call.data == "game3_search_canteen":
        if "item_cup" not in current_node:
            add_xp(user_id, 1, username); update_game_progress(user_id, current_node + "_item_cup")
            msg = "✅ Найдена кружка с кодом '8811' (+1 Пыль).\n\n"
        else: msg = "Ничего интересного.\n\n"
        kb = tele_types.InlineKeyboardMarkup().add(tele_types.InlineKeyboardButton("🔙 Назад", callback_data="game3_node_arrival"))
        bot.edit_message_text(msg + "Слой пыли на всём.", call.message.chat.id, call.message.message_id, reply_markup=kb)

    # ЭТАП 7: ХОРРОР
    elif call.data == "game3_node_horrorevent":
        bot.edit_message_text("😱 Ваше отражение не повторяет ваши движения. Нужно уходить к терминалу!", 
                               call.message.chat.id, call.message.message_id, 
                               reply_markup=tele_types.InlineKeyboardMarkup().add(tele_types.InlineKeyboardButton("🏃 К терминалу", callback_data="game3_node_scan_start")))

    # ЭТАП 8: ТАЙМЕР 30 МИН (СКАНЕР — С ЗАЩИТОЙ)
    elif call.data == "game3_node_scan_start":
        # Если сканирование уже было пройдено (защита от багов)
        if "ch3_scan_done" in current_node:
            run_scenario(bot, type('obj', (object,), {'from_user': call.from_user, 'data': 'game3_check_scan', 'message': call.message}))
            return
            
        set_game_timer(user_id, 30)
        bot.edit_message_text("🖥 Идет глубокое сканирование (30 мин)... Марти заблокировал шлюз.", 
                               call.message.chat.id, call.message.message_id, 
                               reply_markup=tele_types.InlineKeyboardMarkup().add(tele_types.InlineKeyboardButton("🔄 Результаты", callback_data="game3_check_scan")))
        update_game_progress(user_id, "ch3_scan_wait")

    elif call.data == "game3_check_scan":
        bot.edit_message_text("✅ Скан готов. Объект 'Колыбель' найден в шахтах астероида.", 
                               call.message.chat.id, call.message.message_id, 
                               reply_markup=tele_types.InlineKeyboardMarkup().add(tele_types.InlineKeyboardButton("🕵️ В шахты", callback_data="game3_node_mines")))
        update_game_progress(user_id, "ch3_scan_done")

    # ЭТАПЫ 9-11: ШАХТЫ
    elif call.data == "game3_node_mines":
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("🎒 Сумка (Поиск)", callback_data="game3_item_wires"),
            tele_types.InlineKeyboardButton("🚪 К Двери", callback_data="game3_node_final_gate")
        )
        bot.edit_message_text("⛏ Вы в шахтах. Мох повсюду.", call.message.chat.id, call.message.message_id, reply_markup=kb)
        update_game_progress(user_id, "ch3_mines")

    elif call.data == "game3_item_wires":
        if "item_wires" not in current_node:
            add_xp(user_id, 1, username); update_game_progress(user_id, current_node + "_item_wires")
            msg = "✅ Провода в инвентаре (+1 Пыль).\n\n"
        else: msg = "Сумка пуста.\n\n"
        kb = tele_types.InlineKeyboardMarkup().add(tele_types.InlineKeyboardButton("🔙 Назад", callback_data="game3_node_mines"))
        bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, reply_markup=kb)

    # ЭТАПЫ 12-14: ДВЕРЬ
    elif call.data == "game3_node_final_gate":
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("🔢 Ввести 8811", callback_data="game3_node_gate_open"),
            tele_types.InlineKeyboardButton("🔢 Ввести 0000", callback_data="game3_node_fail_puzzle")
        )
        bot.edit_message_text("🗿 Дверь Колыбели заперта. Нужен код.", call.message.chat.id, call.message.message_id, reply_markup=kb)
        update_game_progress(user_id, "ch3_gate")

    # ЭТАП 15: ФИНАЛ (С ЗАЩИТОЙ ОТ ПОВТОРНОЙ ВЫПЛАТЫ)
    elif call.data == "game3_node_gate_open":
        text = "🔓 Дверь открыта. В центре зала — Кристалл и ваш Двойник."
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("🤝 Поверить себе", callback_data="game3_end_twist_good"),
            tele_types.InlineKeyboardButton("🔫 Стрелять", callback_data="game3_end_twist_bad"),
            tele_types.InlineKeyboardButton("🐕 Послушать Марти", callback_data="game3_end_marty_logic")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb)
        update_game_progress(user_id, "ch3_climax")

    elif call.data == "game3_end_marty_logic":
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("🔫 Стрелять", callback_data="game3_end_twist_bad"),
            tele_types.InlineKeyboardButton("🤝 Рискнуть", callback_data="game3_end_twist_good")
        )
        bot.edit_message_text("🐕 Марти: 'Это не ты! Это ИИ корпорации в твоем облике!'", call.message.chat.id, call.message.message_id, reply_markup=kb)

    elif call.data == "game3_end_twist_bad":
        # Проверяем, не была ли награда получена ранее
        if "ch3_claimed" not in current_node:
            add_xp(user_id, 70, username)
            update_game_progress(user_id, "ch3_done_true_ch3_claimed")
            res = "💰 Награда: +70 Пыли."
        else:
            res = "✨ Награда уже в кошельке."
        bot.edit_message_text(f"🏆 **ФИНАЛ: СВОБОДА**\n\nВы разбили кристалл. Пустота затихла. Вы свободны.\n\n{res}", call.message.chat.id, call.message.message_id)

    elif call.data == "game3_end_twist_good":
        if "ch3_claimed" not in current_node:
            add_xp(user_id, 30, username)
            update_game_progress(user_id, "ch3_done_bad_ch3_claimed")
            res = "💰 Награда: +30 Пыли."
        else:
            res = "✨ Награда уже получена."
        bot.edit_message_text(f"🤝 **ФИНАЛ: МАРИОНЕТКА**\n\nВы стали частью системы. Академия довольна, но вы ли это?\n\n{res}", call.message.chat.id, call.message.message_id)
