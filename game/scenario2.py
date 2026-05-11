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
    saved_flags = ""
    for flag in ["_ch2_claimed", "_item_chip", "_item_tape", "_item_token", "_item_diary"]:
        if flag in current_node:
            saved_flags += flag

    # 0. ПРОВЕРКА ЗАВЕРШЕНИЯ ГЛАВЫ
    is_finished = any(mark in current_node for mark in ["ch2_done_hero", "ch2_done_escape", "ch2_done_normal"])

    # 1. ГЛОБАЛЬНАЯ ПРОВЕРКА ТАЙМЕРА
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
            
            # --- [ АТМОСФЕРНЫЙ ЛОКАТОР ГЛАВЫ 2 ] ---
            if "hangar" in current_node:
                location_text = "Ангар. Экранирование артефактов в процессе."
            elif "interrogation" in current_node or "ready_to_talk" in current_node:
                location_text = "Допросная комната СБ 'Ориона'. Свет бьет в глаза."
            elif "vent" in current_node or "horror" in current_node:
                location_text = "Вентиляционная шахта. Холодно и пыльно."
            elif "server" in current_node or "puzzle" in current_node:
                location_text = "Серверная СБ. Ищем питание для систем."
            elif "reboot" in current_node or "path_clear" in current_node:
                location_text = "Технический узел. Восстановление систем связи."
            elif "wounded" in current_node:
                location_text = "Путь к челноку. Веклер ранен."
            else:
                location_text = "База СБ. Вычисление маршрута..."

            text = (f"🛰 **БОРТОВОЙ ЖУРНАЛ: ГЛАВА 2**\n\n"
                    f"Пилот {username}, восстанавливаем данные.\n"
                    f"📍 **Текущая позиция:** *{location_text}*\n\n"
                    f"Марти готов продолжать операцию.")
            
            kb = tele_types.InlineKeyboardMarkup(row_width=1)
            
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
        update_game_progress(user_id, "ch2_start" + saved_flags)

    elif call.data == "game2_reset":
        update_game_progress(user_id, "chapter1_finished" + saved_flags) # Возврат к началу, сохраняя награды
        run_scenario(bot, type('obj', (object,), {'from_user': call.from_user, 'data': 'game2_start', 'message': call.message}))

    # ЭТАП 2: Маскировка (Таймер 1)
    elif call.data == "game2_hide_evidence":
        if "ready_to_talk" in current_node:
            run_scenario(bot, type('obj', (object,), {'from_user': call.from_user, 'data': 'game2_check_hack', 'message': call.message}))
            return
            
        set_game_timer(user_id, 15)
        bot.edit_message_text("🛠 Марти прячет артефакты (15 мин)... Идите на допрос, он догонит.", 
                               call.message.chat.id, call.message.message_id, 
                               reply_markup=tele_types.InlineKeyboardMarkup().add(tele_types.InlineKeyboardButton("🔄 Проверить готовность", callback_data="game2_check_hack")))
        update_game_progress(user_id, "ch2_hangar_hack" + saved_flags)

    elif call.data == "game2_check_hack":
        bot.edit_message_text("✅ Марти готов. Вы у входа в СБ.", 
                               call.message.chat.id, call.message.message_id, 
                               reply_markup=tele_types.InlineKeyboardMarkup().add(tele_types.InlineKeyboardButton("🚪 Войти", callback_data="game2_interrogation_room")))
        update_game_progress(user_id, "ch2_ready_to_talk" + saved_flags)

    # ЭТАП 3: Допрос
    elif call.data == "game2_interrogation_room":
        text = f"🔦 Веклер ждет ответов. — Пилот {username}, что вы скрываете?"
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("📜 Рассказать правду", callback_data="game2_talk_horror"),
            tele_types.InlineKeyboardButton("🐕 Отвлечь его", callback_data="game2_search_mode")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        update_game_progress(user_id, "ch2_interrogation" + saved_flags)

    # ЭТАП 4: Сбор улик
    elif call.data == "game2_search_mode":
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("🔍 Стол", callback_data="game2_item_chip"),
            tele_types.InlineKeyboardButton("📂 Сейф", callback_data="game2_item_tape"),
            tele_types.InlineKeyboardButton("🪑 На место", callback_data="game2_talk_horror")
        )
        bot.edit_message_text("🐕 Марти отвлекает офицера. Действуйте!", call.message.chat.id, call.message.message_id, reply_markup=kb)

    elif call.data == "game2_item_chip":
        if "_item_chip" not in current_node:
            add_xp(user_id, 1, username)
            update_game_progress(user_id, current_node + "_item_chip")
            msg = "✅ **НОВЫЙ ПРЕДМЕТ:** Чип СБ (+1 Пыль).\n\n"
        else: msg = "📦 Этот предмет уже есть в вашей коллекции.\n\n"
        kb = tele_types.InlineKeyboardMarkup().add(tele_types.InlineKeyboardButton("🔙 Назад", callback_data="game2_search_mode"))
        bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, reply_markup=kb)

    elif call.data == "game2_item_tape":
        if "_item_tape" not in current_node:
            add_xp(user_id, 1, username)
            update_game_progress(user_id, current_node + "_item_tape")
            msg = "✅ Кассета у вас (+1 Пыль).\n\n"
        else: msg = "Пусто.\n\n"
        kb = tele_types.InlineKeyboardMarkup().add(tele_types.InlineKeyboardButton("🔙 Назад", callback_data="game2_search_mode"))
        bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, reply_markup=kb)

    # ЭТАП 5: Побег
    elif call.data == "game2_talk_horror":
        bot.edit_message_text("🚨 Блэкаут! Веклер исчез. Единственный путь — вентиляция.", 
                               call.message.chat.id, call.message.message_id, 
                               reply_markup=tele_types.InlineKeyboardMarkup().add(tele_types.InlineKeyboardButton("💨 Лезть", callback_data="game2_vent_shaft")))
        update_game_progress(user_id, "ch2_horror" + saved_flags)

    elif call.data == "game2_vent_shaft":
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("🪪 Жетон (+1 Пыль)", callback_data="game2_item_token"),
            tele_types.InlineKeyboardButton("🚶 Вперед", callback_data="game2_server_room")
        )
        bot.edit_message_text("💨 Вы в трубах. Марти нашел жетон.", call.message.chat.id, call.message.message_id, reply_markup=kb)

    elif call.data == "game2_item_token":
        if "_item_token" not in current_node:
            add_xp(user_id, 1, username)
            update_game_progress(user_id, current_node + "_item_token")
            bot.answer_callback_query(call.id, "✅ Жетон найден (+1 Пыль).", show_alert=False)
        else:
            bot.answer_callback_query(call.id, "📦 Жетон уже найден.", show_alert=False)
        run_scenario(bot, type('obj', (object,), {'from_user': call.from_user, 'data': 'game2_server_room', 'message': call.message}))

    # ЭТАП 7: Серверная и щиток
    elif call.data == "game2_server_room":
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("💾 Взлом (Нужен Чип)", callback_data="game2_lab_hack"),
            tele_types.InlineKeyboardButton("🚪 К питанию", callback_data="game2_power_puzzle")
        )
        bot.edit_message_text("🖥 Проект 'Стикс'. Академия знала всё.", call.message.chat.id, call.message.message_id, reply_markup=kb)

    elif call.data == "game2_lab_hack":
        if "_item_chip" in current_node:
            add_xp(user_id, 5, username)
            update_game_progress(user_id, current_node + "_data") # _data - не предмет, просто флаг, что взломали
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
        update_game_progress(user_id, "ch2_reboot_wait" + saved_flags)

    elif call.data == "game2_check_reboot":
        bot.edit_message_text("✅ Связь восстановлена. Путь к ангару чист.", 
                               call.message.chat.id, call.message.message_id, 
                               reply_markup=tele_types.InlineKeyboardMarkup().add(tele_types.InlineKeyboardButton("🏃 К ангару", callback_data="game2_wounded_officer")))
        update_game_progress(user_id, "ch2_path_clear" + saved_flags)

    # ЭТАП 10: Финал
    elif call.data == "game2_wounded_officer":
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("📕 Взять дневник", callback_data="game2_item_diary"),
            tele_types.InlineKeyboardButton("🚀 К челноку", callback_data="game2_final_choice")
        )
        bot.edit_message_text("🩸 Вы нашли дневник Веклера. Пора улетать.", call.message.chat.id, call.message.message_id, reply_markup=kb)

    elif call.data == "game2_item_diary":
        if "_item_diary" not in current_node:
            add_xp(user_id, 1, username)
            update_game_progress(user_id, current_node + "_item_diary")
            bot.answer_callback_query(call.id, "📕 Дневник Веклера получен (+1 Пыль)", show_alert=False)
        else:
            bot.answer_callback_query(call.id, "📦 Дневник уже у вас.", show_alert=False)
        run_scenario(bot, type('obj', (object,), {'from_user': call.from_user, 'data': 'game2_final_choice', 'message': call.message}))

    elif call.data == "game2_final_choice":
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("🛡 Герой", callback_data="game2_end_hero"),
            tele_types.InlineKeyboardButton("🚀 Беглец", callback_data="game2_end_escape"),
            tele_types.InlineKeyboardButton("🏳 Сдаться", callback_data="game2_end_normal") # (Normal не был полностью прописан в тексте, но я оставлю логику)
        )
        bot.edit_message_text("🚢 Вы в кресле пилота. Какой финал выберете?", call.message.chat.id, call.message.message_id, reply_markup=kb)

   # --- ФИНАЛЫ С УМНОЙ ВЫПЛАТНОЙ ---
    elif call.data == "game2_end_hero":
        if "_ch2_claimed" not in current_node:
            add_xp(user_id, 50, username)
            update_game_progress(user_id, "ch2_done_hero" + saved_flags + "_ch2_claimed")
            res = "💰 Вы получили основной гонорар: **50 Пыли**!"
        else:
            add_xp(user_id, 5, username)
            update_game_progress(user_id, "ch2_done_hero" + saved_flags)
            res = "✨ Вы прошли эту главу снова. Награда за повтор: **5 Пыли**."
            
        bot.edit_message_text(f"🏆 **ФИНАЛ: ГЕРОЙ**\n\nВы спасли станцию 'Орион'.\n\n{res}", 
                               call.message.chat.id, call.message.message_id, parse_mode="Markdown")

    elif call.data == "game2_end_escape":
        if "_ch2_claimed" not in current_node:
            add_xp(user_id, 25, username)
            update_game_progress(user_id, "ch2_done_escape" + saved_flags + "_ch2_claimed")
            res = "💰 Ваша награда: **25 Пыли**."
        else:
            add_xp(user_id, 5, username)
            update_game_progress(user_id, "ch2_done_escape" + saved_flags)
            res = "✨ Награда за повторный полет: **5 Пыли**."
            
        bot.edit_message_text(f"🥈 **ФИНАЛ: БЕГЛЕЦ**\n\nПустота приняла вас.\n\n{res}", 
                               call.message.chat.id, call.message.message_id, parse_mode="Markdown")
        
    elif call.data == "game2_end_normal":
        if "_ch2_claimed" not in current_node:
            add_xp(user_id, 10, username)
            update_game_progress(user_id, "ch2_done_normal" + saved_flags + "_ch2_claimed")
            res = "💰 Ваша награда: **10 Пыли**."
        else:
            add_xp(user_id, 5, username)
            update_game_progress(user_id, "ch2_done_normal" + saved_flags)
            res = "✨ Награда за повтор: **5 Пыли**."
            
        bot.edit_message_text(f"🏳 **ФИНАЛ: КАПИТУЛЯЦИЯ**\n\nВы сдались силам СБ.\n\n{res}", 
                               call.message.chat.id, call.message.message_id, parse_mode="Markdown")
