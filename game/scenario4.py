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
    for flag in ["_ch4_claimed", "_item_photo", "_item_module"]:
        if flag in current_node:
            saved_flags += flag

    # 0. ГЛОБАЛЬНЫЙ ФЛАГ ЗАВЕРШЕНИЯ
    is_finished = any(mark in current_node for mark in ["ch4_done_hero", "ch4_done_escape", "ch4_done_dark"])

    # 1. СИСТЕМА УМНЫХ ТАЙМЕРОВ (Без петель)
    if timer_end and datetime.now() < timer_end and not is_finished:
        remaining = timer_end - datetime.now()
        mins = int(remaining.total_seconds() // 60)
        bot.answer_callback_query(call.id, f"⏳ Марти занят делом. Потерпи еще {mins} мин. Прием!", show_alert=True)
        return

    # 2. УМНЫЙ СТАРТ (Приоритет: от Финала к Началу)
    if call.data == "game4_start":
        if is_finished:
            bot.answer_callback_query(call.id, "🛰 Глава 4 пройдена. Доступ к архивам открыт!", show_alert=True)
            return

        if current_node and current_node.startswith("ch4_") and current_node != "ch4_start":
            text = (f"🛰 **БОРТОВОЙ ЖУРНАЛ: ГЛАВА 4**\n\n"
                    f"Пилот {username}, системы зафиксировали статус: `{current_node}`.\n"
                    f"Марти: 'Хозяин, я нашел лазейку в коде Объекта Зеро. Продолжим?'")
            kb = tele_types.InlineKeyboardMarkup(row_width=1)
            
            # Строгая проверка статусов
            if "core_diag_wait" in current_node:
                kb.add(tele_types.InlineKeyboardButton("🔄 Проверить Ядро", callback_data="game4_check_core"))
            elif "stealth_dock_wait" in current_node:
                kb.add(tele_types.InlineKeyboardButton("🔄 Завершить стыковку", callback_data="game4_check_dock"))
            elif "lab_search" in current_node:
                kb.add(tele_types.InlineKeyboardButton("🔍 Вернуться к обыску", callback_data="game4_node_lab"))
            elif "puzzle" in current_node:
                kb.add(tele_types.InlineKeyboardButton("⚡️ К консоли управления", callback_data="game4_node_console"))
            else:
                kb.add(tele_types.InlineKeyboardButton("🚀 Продолжить", callback_data="game4_node_dock_success"))
            
            kb.add(tele_types.InlineKeyboardButton("♻️ Перезагрузить Главу 4", callback_data="game4_reset"))
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
            return

        # --- ЭТАП 1: ПРОЛОГ ---
        text = (f"🛰 **ЭТАП 1: ТИШИНА ПЕРЕД БУРЕЙ**\n\n"
                f"Вы стоите на пороге астероида 'Объект Зеро'. Глава 3 осталась позади, но настоящие тайны только начинаются. "
                f"Перед вами — огромные шлюзы, покрытые живым фиолетовым мхом. \n\n"
                f"Марти: 'Хозяин, мои сенсоры зашкаливают! Внутри этого астероида не просто руда, там целая экосистема. "
                f"Мы можем вломиться силой или использовать режим Стелса, чтобы системы безопасности нас не заметили'.")
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("🐱 Режим Стелса (20 мин)", callback_data="game4_stealth_dock"),
            tele_types.InlineKeyboardButton("💥 Лобовая атака (Опасно!)", callback_data="game4_node_dock_success")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        update_game_progress(user_id, "ch4_start" + saved_flags)

    elif call.data == "game4_reset":
        new_status = "ch3_done_true" + saved_flags # Награды сохранены
        update_game_progress(user_id, new_status)
        bot.answer_callback_query(call.id, "Журнал обнулен. Ранги сохранены.")
        run_scenario(bot, type('obj', (object,), {'from_user': call.from_user, 'data': 'game4_start', 'message': call.message}))

    # --- ЭТАП 2: ТАЙМЕР 1 (20 мин) ---
    elif call.data == "game4_stealth_dock":
        set_game_timer(user_id, 20)
        text = ("🛠 **ЭТАП 2: ТИХАЯ ГАВАНЬ**\n\n"
                "— Понял! Гашу двигатели, — Марти перешел на шепот. — Нам нужно **20 минут**, чтобы "
                "медленно подойти к техническому шлюзу и не разбудить турели Академии. "
                "Замрите и не дышите!")
        kb = tele_types.InlineKeyboardMarkup().add(tele_types.InlineKeyboardButton("🔄 Проверить радары", callback_data="game4_check_dock"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        update_game_progress(user_id, "ch4_stealth_dock_wait" + saved_flags)

    elif call.data == "game4_check_dock":
        text = ("✅ **УСПЕХ**\n\nВы внутри. Коридоры пахнут древностью и чем-то органическим. Мох здесь светится ярче.")
        kb = tele_types.InlineKeyboardMarkup().add(tele_types.InlineKeyboardButton("🚶 Идти дальше", callback_data="game4_node_dock_success"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        update_game_progress(user_id, "ch4_dock_done" + saved_flags)

    # --- ЭТАП 3-6: ЛАБОРАТОРИЯ И ДЕТЕКТИВ ---
    elif call.data == "game4_node_dock_success":
        text = (f"🔬 **ЭТАП 4: БИО-ЛАБОРАТОРИЯ**\n\n"
                f"Вы попали в зал, где в капсулах спят существа, не похожие ни на что земное. \n"
                f"Марти: 'Смотрите! На столах — старые фотографии людей. Но они датированы 1985 годом. "
                f"Как это возможно здесь, на краю галактики?'\n\n"
                f"Тут явно есть чем поживиться для нашего Архива.")
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("📸 Осмотреть фото", callback_data="game4_item_photo"),
            tele_types.InlineKeyboardButton("💾 Проверить терминал", callback_data="game4_item_module"),
            tele_types.InlineKeyboardButton("🚪 К центральному узлу", callback_data="game4_node_scare")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        update_game_progress(user_id, "ch4_lab_search" + saved_flags)

    elif call.data == "game4_item_photo":
        if "item_photo" not in current_node:
            add_xp(user_id, 1, username)
            update_game_progress(user_id, current_node + "_item_photo")
            msg = "✅ **ПРЕДМЕТ:** Помятое фото команды 'Мариуполь-1' (+1 Пыль).\n\n"
        else: msg = "📦 Фото уже в вашем планшете.\n\n"
        kb = tele_types.InlineKeyboardMarkup().add(tele_types.InlineKeyboardButton("🔙 К обыску", callback_data="game4_node_lab"))
        bot.edit_message_text(msg + "На фото изображен человек, удивительно похожий на вашего отца.", call.message.chat.id, call.message.message_id, reply_markup=kb)

    elif call.data == "game4_item_module":
        if "item_module" not in current_node:
            add_xp(user_id, 1, username)
            update_game_progress(user_id, current_node + "_item_module")
            msg = "✅ **ПРЕДМЕТ:** Шифровальный модуль (+1 Пыль).\n\n"
        else: msg = "📦 Модуль уже извлечен.\n\n"
        kb = tele_types.InlineKeyboardMarkup().add(tele_types.InlineKeyboardButton("🔙 К обыску", callback_data="game4_node_lab"))
        bot.edit_message_text(msg + "С помощью него можно читать мысли Объекта Зеро.", call.message.chat.id, call.message.message_id, reply_markup=kb)

    # --- ЭТАП 7-10: ХОРРОР И ПАЗЛ ---
    elif call.data == "game4_node_scare":
        text = ("😱 **ЭТАП 7: ШЕПОТ ЯДРА**\n\n"
                "Голоса в голове становятся громче. 'Вернись... ты обещал...'. \n"
                "Марти замер, его ошейник искрит: 'Хозяин, я вижу ИХ. Тени на стенах — это не тени. "
                "Это отпечатки сознаний тех, кто был здесь до нас'.\n\n"
                "Путь преграждает нейро-замок. Нужно сопоставить цвета мха.")
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("🧩 Выбрать Фиолетовый (Логика)", callback_data="game4_node_console"),
            tele_types.InlineKeyboardButton("🧩 Выбрать Зеленый", callback_data="game4_puzzle_fail")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        update_game_progress(user_id, "ch4_puzzle_node" + saved_flags)

    elif call.data == "game4_puzzle_fail":
        bot.answer_callback_query(call.id, "❌ Неверно! Мох начал выделять токсичный газ. Назад!", show_alert=True)
        return

    # --- ЭТАП 11-14: ЯДРО (Таймер 2 - 30 мин) ---
    elif call.data == "game4_node_console":
        if "core_diag_done" in current_node:
             run_scenario(bot, type('obj', (object,), {'from_user': call.from_user, 'data': 'game4_check_core', 'message': call.message}))
             return

        set_game_timer(user_id, 30)
        text = ("🧠 **ЭТАП 11: ЯДРО ОБЪЕКТА**\n\n"
                "Вы в центре астероида. Перед вами — Обьект Зеро. Это не камень. "
                "Это гигантский биологический сервер, пульсирующий в ритме сердца. \n\n"
                "Марти: 'Мне нужно **30 минут**, чтобы подключиться и понять, как это остановить. "
                "Хозяин, я чувствую... я чувствую всё их горе'.")
        kb = tele_types.InlineKeyboardMarkup().add(tele_types.InlineKeyboardButton("🔄 Завершить анализ", callback_data="game4_check_core"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        update_game_progress(user_id, "ch4_core_diag_wait" + saved_flags)

    elif call.data == "game4_check_core":
        text = ("✅ **АНАЛИЗ ЗАВЕРШЕН**\n\n"
                "Марти открыл глаза, они светятся белым: 'Это не враг. Это ковчег. Академия хотела "
                "превратить его в оружие, но мы можем использовать его, чтобы отправить сигнал на Землю! "
                "Но тогда Академия узнает наши координаты'.")
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("📡 Отправить сигнал (Герой)", callback_data="game4_end_hero"),
            tele_types.InlineKeyboardButton("🚀 Сбежать с Ядром (Беглец)", callback_data="game4_end_escape"),
            tele_types.InlineKeyboardButton("💀 Уничтожить всё (Мрак)", callback_data="game4_end_dark")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        update_game_progress(user_id, "ch4_core_diag_done" + saved_flags)

    # --- ЭТАП 15-20: ФИНАЛЫ С ЗАЩИТОЙ ---
    elif call.data == "game4_end_hero":
        if "ch4_claimed" not in current_node:
            add_xp(user_id, 100, username)
            update_game_progress(user_id, "ch4_done_hero" + saved_flags + "_ch4_claimed")
            res = "💰 **НАГРАДА:** 100 Пыли (Легенда Академии)."
        else:
            add_xp(user_id, 10, username)
            update_game_progress(user_id, "ch4_done_hero" + saved_flags)
            res = "✨ **НАГРАДА ЗА ПОВТОР:** 10 Пыли."
        
        bot.edit_message_text(f"🏆 **ФИНАЛ: ГОЛОС ЗЕМЛИ**\n\nВы спасли данные и дали надежду. {res}", call.message.chat.id, call.message.message_id)

    elif call.data == "game4_end_escape":
        if "ch4_claimed" not in current_node:
            add_xp(user_id, 50, username)
            update_game_progress(user_id, "ch4_done_escape" + saved_flags + "_ch4_claimed")
            res = "💰 **НАГРАДА:** 50 Пыли."
        else:
            add_xp(user_id, 10, username)
            update_game_progress(user_id, "ch4_done_escape" + saved_flags)
            res = "✨ **НАГРАДА ЗА ПОВТОР:** 10 Пыли."
            
        bot.edit_message_text(f"🥈 **ФИНАЛ: ХРАНИТЕЛЬ ТАЙН**\n\nВы исчезли в пустоте, забрав Ядро с собой. {res}", call.message.chat.id, call.message.message_id)

    elif call.data == "game4_end_dark":
        if "ch4_claimed" not in current_node:
            add_xp(user_id, 15, username)
            update_game_progress(user_id, "ch4_done_dark" + saved_flags + "_ch4_claimed")
            res = "💰 **НАГРАДА:** 15 Пыли."
        else:
            add_xp(user_id, 5, username)
            update_game_progress(user_id, "ch4_done_dark" + saved_flags)
            res = "✨ **НАГРАДА ЗА ПОВТОР:** 5 Пыли."
            
        bot.edit_message_text(f"💀 **ФИНАЛ: ПЕПЕЛ В ПУСТОТЕ**\n\nВы решили, что человечество не готово к этому. Станция взорвана. {res}", call.message.chat.id, call.message.message_id)

    # Вспомогательный узел для возврата к обыску
    elif call.data == "game4_node_lab":
        run_scenario(bot, type('obj', (object,), {'from_user': call.from_user, 'data': 'game4_node_dock_success', 'message': call.message}))
