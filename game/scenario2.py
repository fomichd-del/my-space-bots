import telebot
from datetime import datetime
from telebot import types as tele_types
from database import get_game_status, update_game_progress, set_game_timer, add_xp

def run_scenario(bot, call):
    user_id = call.from_user.id
    username = call.from_user.first_name if call.from_user.first_name else "Пилот"
    current_node, timer_end = get_game_status(user_id)
    
    # 0. ПРОВЕРКА ЗАВЕРШЕНИЯ ГЛАВЫ
    # Если в истории есть любая метка финала — глава считается пройденной
    is_finished = any(mark in current_node for mark in ["ch2_done_hero", "ch2_done_escape", "ch2_done_normal"])

    # 1. ГЛОБАЛЬНАЯ ПРОВЕРКА ТАЙМЕРА (Блокировка только если глава не завершена)
    if timer_end and datetime.now() < timer_end and not is_finished:
        remaining = timer_end - datetime.now()
        mins = int(remaining.total_seconds() // 60)
        bot.answer_callback_query(call.id, f"⏳ Марти занят системами. Осталось {mins} мин.", show_alert=True)
        return

    # 2. УМНЫЙ СТАРТ (Восстановление сессии)
    if call.data == "game2_start":
        if is_finished:
            bot.answer_callback_query(call.id, "✅ Эта миссия уже в архиве!", show_alert=True)
            return

        if current_node and current_node.startswith("ch2_") and current_node != "ch2_start":
            text = (f"🛰 **БОРТОВОЙ ЖУРНАЛ: ГЛАВА 2**\n\n"
                    f"Пилот {username}, восстанавливаем данные: `{current_node}`.")
            kb = tele_types.InlineKeyboardMarkup(row_width=1)
            
            # Приоритетная проверка специфических статусов
            if "reboot_wait" in current_node:
                kb.add(tele_types.InlineKeyboardButton("🔄 Проверить системы связи", callback_data="game2_check_reboot"))
            elif "hangar_hack" in current_node:
                kb.add(tele_types.InlineKeyboardButton("🔄 Проверить готовность Марти", callback_data="game2_check_hack"))
            elif "vent" in current_node:
                kb.add(tele_types.InlineKeyboardButton("💨 Продолжить побег", callback_data="game2_vent_shaft"))
            elif "interrogation" in current_node:
                kb.add(tele_types.InlineKeyboardButton("🚪 Вернуться в допросную", callback_data="game2_interrogation_room"))
            else:
                kb.add(tele_types.InlineKeyboardButton("🚀 Продолжить", callback_data="game2_interrogation_room"))
            
            kb.add(tele_types.InlineKeyboardButton("♻️ Начать Главу 2 заново", callback_data="game2_reset"))
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
            return

        # ЭТАП 1: Прибытие
        text = (f"🛰 **ЭТАП 1: ПРИЗЕМЛЕНИЕ**\n\n"
                f"— Хозяин, — Марти настороже. — СБ 'Ориона' уже сканирует челнок. "
                f"Нам нужно экранировать артефакты, иначе это конец.")
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("🧳 Спрятать улики в Марти (15 мин)", callback_data="game2_hide_evidence"),
            tele_types.InlineKeyboardButton("🚶 Идти открыто", callback_data="game2_interrogation_room")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        update_game_progress(user_id, "ch2_start")

    elif call.data == "game2_reset":
        update_game_progress(user_id, "ch1_finished") # Возврат к метке конца 1 главы
        run_scenario(bot, type('obj', (object,), {'from_user': call.from_user, 'data': 'game2_start', 'message': call.message}))

    # ЭТАП 2: Маскировка (Таймер 1)
    elif call.data == "game2_hide_evidence":
        # Если маскировка уже была (защита от повторного клика)
        if "ready_to_talk" in current_node:
            run_scenario(bot, type('obj', (object,), {'from_user': call.from_user, 'data': 'game2_check_hack', 'message': call.message}))
            return
            
        set_game_timer(user_id, 15)
        bot.edit_message_text("🛠 Марти прячет артефакты (15 мин)... Идите на допрос, он догонит.", 
                               call.message.chat.id, call.message.message_id, 
                               reply_markup=tele_types.InlineKeyboardMarkup().add(tele_types.InlineKeyboardButton("🔄 Проверить готовность", callback_data="game2_check_hack")))
        update_game_progress(user_id, "ch2_hangar_hack")

    elif call.data == "game2_check_hack":
        bot.edit_message_text("✅ Марти готов. Вы у входа в СБ.", 
                               call.message.chat.id, call.message.message_id, 
                               reply_markup=tele_types.InlineKeyboardMarkup().add(tele_types.InlineKeyboardButton("🚪 Войти", callback_data="game2_interrogation_room")))
        update_game_progress(user_id, "ch2_ready_to_talk")

    # ЭТАП 3: Допрос
    elif call.data == "game2_interrogation_room":
        text = f"🔦 Веклер ждет ответов. — Пилот {username}, что вы скрываете?"
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("📜 Рассказать правду", callback_data="game2_talk_horror"),
            tele_types.InlineKeyboardButton("🐕 Отвлечь его", callback_data="game2_search_mode")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        update_game_progress(user_id, "ch2_interrogation")

    # ЭТАП 4: Сбор улик
    elif call.data == "game2_search_mode":
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("🔍 Стол", callback_data="game2_item_chip"),
            tele_types.InlineKeyboardButton("📂 Сейф", callback_data="game2_item_tape"),
            tele_types.InlineKeyboardButton("🪑 На место", callback_data="game2_talk_horror")
        )
        bot.edit_message_text("🐕 Марти отвлекает офицера. Действуйте!", call.message.chat.id, call.message.message_id, reply_markup=kb)

    elif call.data == "game2_item_chip":
        if "chip" not in current_node:
            add_xp(user_id, 1, username); update_game_progress(user_id, current_node + "_chip")
            msg = "✅ Чип СБ у вас (+1 Пыль).\n\n"
        else: msg = "Уже взято.\n\n"
        kb = tele_types.InlineKeyboardMarkup().add(tele_types.InlineKeyboardButton("🔙 Назад", callback_data="game2_search_mode"))
        bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, reply_markup=kb)

    elif call.data == "game2_item_tape":
        if "tape" not in current_node:
            add_xp(user_id, 1, username); update_game_progress(user_id, current_node + "_tape")
            msg = "✅ Кассета у вас (+1 Пыль).\n\n"
        else: msg = "Пусто.\n\n"
        kb = tele_types.InlineKeyboardMarkup().add(tele_types.InlineKeyboardButton("🔙 Назад", callback_data="game2_search_mode"))
        bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, reply_markup=kb)

    # ЭТАП 5: Побег
    elif call.data == "game2_talk_horror":
        bot.edit_message_text("🚨 Блэкаут! Веклер исчез. Единственный путь — вентиляция.", 
                               call.message.chat.id, call.message.message_id, 
                               reply_markup=tele_types.InlineKeyboardMarkup().add(tele_types.InlineKeyboardButton("💨 Лезть", callback_data="game2_vent_shaft")))
        update_game_progress(user_id, "ch2_horror")

    elif call.data == "game2_vent_shaft":
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("🪪 Жетон (+1 Пыль)", callback_data="game2_item_token"),
            tele_types.InlineKeyboardButton("🚶 Вперед", callback_data="game2_server_room")
        )
        bot.edit_message_text("💨 Вы в трубах. Марти нашел жетон.", call.message.chat.id, call.message.message_id, reply_markup=kb)

    elif call.data == "game2_item_token":
        if "token" not in current_node:
            add_xp(user_id, 1, username); update_game_progress(user_id, current_node + "_token")
        run_scenario(bot, type('obj', (object,), {'from_user': call.from_user, 'data': 'game2_server_room', 'message': call.message}))

    # ЭТАП 7: Серверная и щиток
    elif call.data == "game2_server_room":
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("💾 Взлом (Нужен Чип)", callback_data="game2_lab_hack"),
            tele_types.InlineKeyboardButton("🚪 К питанию", callback_data="game2_power_puzzle")
        )
        bot.edit_message_text("🖥 Проект 'Стикс'. Академия знала всё.", call.message.chat.id, call.message.message_id, reply_markup=kb)

    elif call.data == "game2_lab_hack":
        if "chip" in current_node:
            add_xp(user_id, 5, username); update_game_progress(user_id, current_node + "_data")
            msg = "🔓 Секреты Академии раскрыты (+5 Пыли)."
        else: msg = "❌ Нет чипа."
        bot.answer_callback_query(call.id, msg, show_alert=True)
        run_scenario(bot, type('obj', (object,), {'from_user': call.from_user, 'data': 'game2_power_puzzle', 'message': call.message}))

    elif call.data == "game2_power_puzzle":
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("🎚 Рычаг 2", callback_data="game2_puzzle_fail"),
            tele_types.InlineKeyboardButton("🎚 Рычаг 6", callback_data="game2_reboot_start")
        )
        bot.edit_message_text("⚡️ Нужно подать питание. Марти: '2+4=?'", call.message.chat.id, call.message.message_id, reply_markup=kb)

    elif call.data == "game2_puzzle_fail":
        bot.answer_callback_query(call.id, "💥 Замыкание!", show_alert=True)
        return

    # ЭТАП 9: Перезагрузка (Таймер 2)
    elif call.data == "game2_reboot_start":
        if "path_clear" in current_node:
            run_scenario(bot, type('obj', (object,), {'from_user': call.from_user, 'data': 'game2_check_reboot', 'message': call.message}))
            return
            
        set_game_timer(user_id, 30)
        bot.edit_message_text("🌌 Идет очистка связи (30 мин)... Ждите.", 
                               call.message.chat.id, call.message.message_id, 
                               reply_markup=tele_types.InlineKeyboardMarkup().add(tele_types.InlineKeyboardButton("🔄 Проверить", callback_data="game2_check_reboot")))
        update_game_progress(user_id, "ch2_reboot_wait")

    elif call.data == "game2_check_reboot":
        bot.edit_message_text("✅ Связь восстановлена. Путь к ангару чист.", 
                               call.message.chat.id, call.message.message_id, 
                               reply_markup=tele_types.InlineKeyboardMarkup().add(tele_types.InlineKeyboardButton("🏃 К ангару", callback_data="game2_wounded_officer")))
        update_game_progress(user_id, "ch2_path_clear")

    # ЭТАП 10: Финал
    elif call.data == "game2_wounded_officer":
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("📕 Взять дневник", callback_data="game2_item_diary"),
            tele_types.InlineKeyboardButton("🚀 К челноку", callback_data="game2_final_choice")
        )
        bot.edit_message_text("🩸 Вы нашли дневник Веклера. Пора улетать.", call.message.chat.id, call.message.message_id, reply_markup=kb)

    elif call.data == "game2_item_diary":
        if "diary" not in current_node:
            add_xp(user_id, 1, username); update_game_progress(user_id, current_node + "_diary")
        run_scenario(bot, type('obj', (object,), {'from_user': call.from_user, 'data': 'game2_final_choice', 'message': call.message}))

    elif call.data == "game2_final_choice":
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("🛡 Герой", callback_data="game2_end_hero"),
            tele_types.InlineKeyboardButton("🚀 Беглец", callback_data="game2_end_escape"),
            tele_types.InlineKeyboardButton("🏳 Сдаться", callback_data="game2_end_normal")
        )
        bot.edit_message_text("🚢 Вы в кресле пилота. Какой финал выберете?", call.message.chat.id, call.message.message_id, reply_markup=kb)

    # --- ФИНАЛЫ С ЗАЩИТОЙ ОТ ПОВТОРНОЙ ВЫПЛАТЫ ---
    elif call.data == "game2_end_hero":
        if "ch2_claimed" not in current_node:
            add_xp(user_id, 50, username)
            update_game_progress(user_id, "ch2_done_hero_ch2_claimed")
            res = "💰 Награда: +50 Пыли."
        else: res = "✨ Награда получена."
        bot.edit_message_text(f"🏆 **ГЕРОЙ**\n\nВы спасли станцию. {res}", call.message.chat.id, call.message.message_id)

    elif call.data == "game2_end_escape":
        if "ch2_claimed" not in current_node:
            add_xp(user_id, 25, username)
            update_game_progress(user_id, "ch2_done_escape_ch2_claimed")
            res = "💰 Награда: +25 Пыли."
        else: res = "✨ Награда получена."
        bot.edit_message_text(f"🥈 **БЕГЛЕЦ**\n\nСвобода в пустоте. {res}", call.message.chat.id, call.message.message_id)

    elif call.data == "game2_end_normal":
        if "ch2_claimed" not in current_node:
            add_xp(user_id, 5, username)
            update_game_progress(user_id, "ch2_done_normal_ch2_claimed")
            res = "💰 Награда: +5 Пыли."
        else: res = "✨ Награда получена."
        bot.edit_message_text(f"🥉 **ПОДОЗРЕВАЕМЫЙ**\n\nЗакон суров. {res}", call.message.chat.id, call.message.message_id)
