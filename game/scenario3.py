import telebot
from datetime import datetime
from telebot import types as tele_types
from database import get_game_status, update_game_progress, set_game_timer, add_xp

def run_scenario(bot, call):
    user_id = call.from_user.id
    username = call.from_user.first_name if call.from_user.first_name else "Пилот"
    current_node, timer_end = get_game_status(user_id)
    
    # 1. ГЛОБАЛЬНАЯ ПРОВЕРКА ТАЙМЕРА (Блокировка действий при ожидании)
    if timer_end and datetime.now() < timer_end:
        remaining = timer_end - datetime.now()
        mins = int(remaining.total_seconds() // 60)
        bot.answer_callback_query(call.id, f"⏳ Марти калибрует сенсоры. Готовность через {mins} мин.", show_alert=True)
        return

    # 2. УМНЫЙ СТАРТ (Точки восстановления — ИСПРАВЛЕНО)
    if call.data == "game3_start":
        if current_node and current_node.startswith("ch3_") and current_node != "ch3_start":
            text = (f"🛰 **СЕАНС СВЯЗИ: ГЛАВА 3**\n\n"
                    f"Пилот {username}, восстанавливаем сектор: `{current_node}`.\n"
                    f"Марти готов продолжать. Прием!")
            kb = tele_types.InlineKeyboardMarkup(row_width=1)
            
            # Приоритетная проверка специфических статусов (чтобы не было петель)
            if "scan_wait" in current_node:
                kb.add(tele_types.InlineKeyboardButton("🔄 Результаты сканера", callback_data="game3_check_scan"))
            elif "jump_wait" in current_node:
                kb.add(tele_types.InlineKeyboardButton("🔄 Проверить прыжок", callback_data="game3_check_jump"))
            elif "gate" in current_node:
                kb.add(tele_types.InlineKeyboardButton("🗿 Вернуться к Двери", callback_data="game3_node_final_gate"))
            elif "mines" in current_node:
                kb.add(tele_types.InlineKeyboardButton("⛏ Вернуться в шахты", callback_data="game3_node_mines"))
            else:
                kb.add(tele_types.InlineKeyboardButton("🚀 Продолжить миссию", callback_data="game3_node_arrival"))
            
            kb.add(tele_types.InlineKeyboardButton("♻️ Сбросить Главу 3", callback_data="game3_reset"))
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
            return

        # --- ЭТАП 1: МУЛЬТИ-СТАРТ ---
        kb = tele_types.InlineKeyboardMarkup(row_width=1)
        if "ch2_done_hero" in current_node:
            t = "🌟 **ЭТАП 1: ПУТЬ АГЕНТА**\n\nВы — герой Академии. Ваш новый корабль готов к прыжку к маяку 'Эхо'."
            kb.add(tele_types.InlineKeyboardButton("🛰 Лететь к маяку", callback_data="game3_node_prejump"))
        elif "ch2_done_escape" in current_node:
            t = "🏴 **ЭТАП 1: ПУТЬ ИЗГОЯ**\n\nВы в бегах. Нужно найти заброшенную базу в астероидах, чтобы выжить."
            kb.add(tele_types.InlineKeyboardButton("☄️ Искать укрытие", callback_data="game3_node_prejump"))
        else:
            t = "⛓ **ЭТАП 1: ПУТЬ УЗНИКА**\n\nТюрьма повреждена! Бегите к ангару, пока Марти взламывает замки."
            kb.add(tele_types.InlineKeyboardButton("🏃 Бежать к ангару", callback_data="game3_node_prejump"))
        
        bot.edit_message_text(t, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        update_game_progress(user_id, "ch3_start")

    elif call.data == "game3_reset":
        update_game_progress(user_id, "ch3_done_hero") 
        bot.answer_callback_query(call.id, "Журнал обнулен.")
        run_scenario(bot, type('obj', (object,), {'from_user': call.from_user, 'data': 'game3_start', 'message': call.message}))

    # --- ЭТАП 2: ЗАГАДКА ---
    elif call.data == "game3_node_prejump":
        text = (f"⚙️ **ЭТАП 2: НЕЙРО-СТЫКОВКА**\n\n"
                f"Марти: 'Хозяин, для прыжка нужно выбрать частоту. Фиолетовый — это Синий + Красный. "
                f"Куда втыкаем кабель?'")
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("🧩 Гнездо 'Бета' (Синий+Красный)", callback_data="game3_node_jump_wait"),
            tele_types.InlineKeyboardButton("🧩 Гнездо 'Альфа' (Зеленый)", callback_data="game3_node_fail_puzzle")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        update_game_progress(user_id, "ch3_puzzle")

    elif call.data == "game3_node_fail_puzzle":
        bot.answer_callback_query(call.id, "💥 Искры! Марти недоволен. Пробуй еще раз!", show_alert=True)
        return

    # --- ЭТАП 3: ТАЙМЕР 20 МИН (ПРЫЖОК) ---
    elif call.data == "game3_node_jump_wait":
        set_game_timer(user_id, 20)
        text = (f"🚀 **ЭТАП 3: ГИПЕРПРОСТРАНСТВО**\n\n"
                f"Прыжок займет **20 минут**. Марти: 'Я пока подремлю... или посчитаю электроовец'.")
        kb = tele_types.InlineKeyboardMarkup().add(tele_types.InlineKeyboardButton("🔄 Выйти из гипера", callback_data="game3_check_jump"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        update_game_progress(user_id, "ch3_jump_wait")

    elif call.data == "game3_check_jump":
        text = (f"✨ **ЭТАП 4: ПРИБЫТИЕ**\n\nПеред вами станция 'Стикс-9'. Она светится фиолетовым. Жутко.")
        kb = tele_types.InlineKeyboardMarkup().add(tele_types.InlineKeyboardButton("🚢 Стыковаться", callback_data="game3_node_arrival"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        update_game_progress(user_id, "ch3_arrival")

    # --- ЭТАПЫ 5-6: ОБЫСК ---
    elif call.data == "game3_node_arrival":
        text = (f"🏚 **ЭТАП 5: ПУСТЫЕ КОРИДОРЫ**\n\n"
                f"Марти: 'Тут пахнет одиночеством и старым кофе'. Осмотримся?")
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("🗄 Шкафчики (Предмет)", callback_data="game3_search_locker"),
            tele_types.InlineKeyboardButton("☕️ Столовая (Предмет)", callback_data="game3_search_canteen"),
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
        bot.edit_message_text(msg + "Старая карта секторов.", call.message.chat.id, call.message.message_id, reply_markup=kb)

    elif call.data == "game3_search_canteen":
        if "item_cup" not in current_node:
            add_xp(user_id, 1, username); update_game_progress(user_id, current_node + "_item_cup")
            msg = "✅ Найдена кружка с кодом '8811' (+1 Пыль).\n\n"
        else: msg = "Кофемашина мертва.\n\n"
        kb = tele_types.InlineKeyboardMarkup().add(tele_types.InlineKeyboardButton("🔙 Назад", callback_data="game3_node_arrival"))
        bot.edit_message_text(msg + "Полезная находка.", call.message.chat.id, call.message.message_id, reply_markup=kb)

    # --- ЭТАП 7: ХОРРОР ---
    elif call.data == "game3_node_horrorevent":
        text = (f"😱 **ЭТАП 7: ОТРАЖЕНИЕ**\n\n"
                f"Ваше отражение в стекле не шевелится. Оно просто смотрит на вас. "
                f"Марти: 'Хозяин, бежим отсюда к терминалу!'")
        kb = tele_types.InlineKeyboardMarkup().add(
            tele_types.InlineKeyboardButton("🏃 Бежать к терминалу", callback_data="game3_node_scan_start")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        update_game_progress(user_id, "ch3_scare")

    # --- ЭТАП 8: ТАЙМЕР 30 МИН (СКАНЕР) ---
    elif call.data == "game3_node_scan_start":
        set_game_timer(user_id, 30)
        text = (f"🖥 **ЭТАП 8: СКАНИРОВАНИЕ**\n\n"
                f"Марти заблокировал двери. Сканирование продлится **30 минут**. \n\n"
                f"Слышите? Кто-то скребется в дверь снаружи...")
        kb = tele_types.InlineKeyboardMarkup().add(tele_types.InlineKeyboardButton("🔄 Результаты", callback_data="game3_check_scan"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        update_game_progress(user_id, "ch3_scan_wait") # 🟢 Важное имя!

    elif call.data == "game3_check_scan":
        text = (f"✅ **СКАН ЗАВЕРШЕН**\n\nСигнал идет из шахт астероида. Нам нужно вглубь.")
        kb = tele_types.InlineKeyboardMarkup().add(tele_types.InlineKeyboardButton("🕵️ В шахты", callback_data="game3_node_mines"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        update_game_progress(user_id, "ch3_scan_done")

    # --- ЭТАПЫ 9-11: ШАХТЫ ---
    elif call.data == "game3_node_mines":
        text = (f"⛏ **ЭТАП 9: ГЛУБИНА**\n\nТут повсюду светящийся мох. Марти нашел сумку.")
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("🎒 Обыскать сумку", callback_data="game3_item_wires"),
            tele_types.InlineKeyboardButton("🚪 К Двери Колыбели", callback_data="game3_node_final_gate")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        update_game_progress(user_id, "ch3_mines")

    elif call.data == "game3_item_wires":
        if "wires" not in current_node:
            add_xp(user_id, 1, username); update_game_progress(user_id, current_node + "_wires")
            msg = "✅ Найдены золотые провода (+1 Пыль).\n\n"
        else: msg = "Пусто.\n\n"
        kb = tele_types.InlineKeyboardMarkup().add(tele_types.InlineKeyboardButton("🚪 К Двери", callback_data="game3_node_final_gate"))
        bot.edit_message_text(msg + "Пригодятся для ремонта.", call.message.chat.id, call.message.message_id, reply_markup=kb)

    # --- ЭТАПЫ 12-14: ДВЕРЬ ---
    elif call.data == "game3_node_final_gate":
        text = (f"🗿 **ЭТАП 12: ЧЕРНАЯ ДВЕРЬ**\n\nНужен код доступа. Марти: 'Хозяин, помнишь кружку?'")
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("🔢 Ввести 8811", callback_data="game3_node_gate_open"),
            tele_types.InlineKeyboardButton("🔢 Ввести 0000", callback_data="game3_node_fail_puzzle")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        update_game_progress(user_id, "ch3_gate")

    # --- ЭТАПЫ 15-18: ФИНАЛ ---
    elif call.data == "game3_node_gate_open":
        text = (f"🔓 **ЭТАП 15: КОЛЫБЕЛЬ**\n\n"
                f"В центре — Кристалл. И... ваш Двойник из будущего.\n"
                f"— Привет. Я — это ты. Помоги мне остановить Академию.")
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("🤝 Поверить себе", callback_data="game3_end_twist_good"),
            tele_types.InlineKeyboardButton("🔫 Стрелять в кристалл", callback_data="game3_end_twist_bad"),
            tele_types.InlineKeyboardButton("🐕 Послушать Марти", callback_data="game3_end_marty_logic")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        update_game_progress(user_id, "ch3_climax")

    elif call.data == "game3_end_marty_logic":
        text = (f"🐕 Марти: 'Это не человек, это ИИ в твоем облике! Не верь ему!'")
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("🔫 Стрелять в кристалл", callback_data="game3_end_twist_bad"),
            tele_types.InlineKeyboardButton("🤝 Рискнуть", callback_data="game3_end_twist_good")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    elif call.data == "game3_end_twist_bad":
        if "done" not in current_node:
            add_xp(user_id, 70, username); update_game_progress(user_id, "ch3_done_true")
            res = "💰 +70 Пыли (Истинный финал)."
        else: res = "Получено."
        bot.edit_message_text(f"🏆 **ФИНАЛ: СВОБОДА**\n\nВы разбили кристалл и петлю времени. Теперь вы сами пишете свою судьбу!\n\n{res}", call.message.chat.id, call.message.message_id)

    elif call.data == "game3_end_twist_good":
        if "done" not in current_node:
            add_xp(user_id, 30, username); update_game_progress(user_id, "ch3_done_bad")
            res = "💰 +30 Пыли."
        else: res = "Получено."
        bot.edit_message_text(f"🤝 **ФИНАЛ: МАРИОНЕТКА**\n\nВы объединились с двойником, но стали рабом Земной корпорации. Жаль.\n\n{res}", call.message.chat.id, call.message.message_id)
