import telebot
from datetime import datetime
from telebot import types as tele_types
from database import get_game_status, update_game_progress, set_game_timer, add_xp

def run_scenario(bot, call):
    user_id = call.from_user.id
    username = call.from_user.first_name if call.from_user.first_name else "Пилот"
    
    current_node, timer_end = get_game_status(user_id)
    
    # 1. Глобальная проверка таймера
    if timer_end and datetime.now() < timer_end:
        remaining = timer_end - datetime.now()
        mins = int(remaining.total_seconds() // 60)
        bot.answer_callback_query(call.id, f"⏳ Марти калибрует щиты. Осталось {mins} мин.", show_alert=True)
        return

    # 2. УМНЫЙ СТАРТ (Точка сохранения)
    if call.data == "game2_start":
        if current_node and current_node.startswith("ch2_") and current_node != "ch2_start":
            text = (f"🛰 **БОРТОВОЙ ЖУРНАЛ: ГЛАВА 2**\n\n"
                    f"Пилот {username}, системы восстановили последний сеанс связи. "
                    f"Ваш статус: `{current_node}`.\n\n"
                    f"Продолжаем?")
            kb = tele_types.InlineKeyboardMarkup(row_width=1)
            # Автоматическая маршрутизация
            if "hangar_hack" in current_node:
                kb.add(tele_types.InlineKeyboardButton("🔄 Проверить готовность щитов", callback_data="game2_check_hack"))
            elif "interrogation" in current_node:
                kb.add(tele_types.InlineKeyboardButton("🚪 Вернуться в допросную", callback_data="game2_interrogation_room"))
            elif "searching" in current_node:
                kb.add(tele_types.InlineKeyboardButton("🕵️ Продолжить обыск", callback_data="game2_stealth_search"))
            else:
                kb.add(tele_types.InlineKeyboardButton("🚀 Продолжить", callback_data="game2_interrogation_room"))
            
            kb.add(tele_types.InlineKeyboardButton("♻️ Начать Главу 2 заново", callback_data="game2_reset"))
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
            return

        # Вступление
        text = (f"🛰 **ГЛАВА 2: ТЕНЬ ЗЕМЛИ**\n\n"
                f"Ваш челнок замер в ангаре 'Орион-Прайм'. Марти нервно дергает ухом:\n"
                f"— Хозяин, я чую неладное. Нас не встречает почетный караул. "
                f"Нас встречают 'Серые мундиры' из Службы Безопасности.\n\n"
                f"Вещи из Сектора Зеро пульсируют в грузовом отсеке. Сигнал с Земли "
                f"начинает резонировать с системами станции. Нужно решать быстро!")
        kb = tele_types.InlineKeyboardMarkup(row_width=1)
        kb.add(
            tele_types.InlineKeyboardButton("🧳 Спрятать улики в Марти (15 мин)", callback_data="game2_hide_evidence"),
            tele_types.InlineKeyboardButton("🚶 Идти на допрос открыто", callback_data="game2_interrogation_room")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        update_game_progress(user_id, "ch2_start")

    elif call.data == "game2_reset":
        update_game_progress(user_id, "ch2_start")
        bot.answer_callback_query(call.id, "Журнал Главы 2 сброшен.")
        run_scenario(bot, type('obj', (object,), {'from_user': call.from_user, 'data': 'game2_start', 'message': call.message}))

    # --- ТАЙМЕР: ЭКРАНИРОВАНИЕ ---
    elif call.data == "game2_hide_evidence":
        set_game_timer(user_id, 15)
        text = ("⚙️ Вы активируете скрытый отсек в Марти. \n\n"
                "— Понял, Хозяин. Включаю протокол 'Тихий омут'. Мне нужно **15 минут**, "
                "чтобы полностью экранировать артефакты. А пока... постарайтесь не "
                "выглядеть как контрабандист!")
        kb = tele_types.InlineKeyboardMarkup().add(tele_types.InlineKeyboardButton("🔄 Проверить готовность", callback_data="game2_check_hack"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        update_game_progress(user_id, "ch2_hangar_hack")

    elif call.data == "game2_check_hack":
        text = ("✅ **ЭКРАНИРОВАНИЕ ЗАВЕРШЕНО**\n\n"
                "Марти довольно чихнул. Теперь вы чисты. Двое охранников уже ведут вас по "
                "стерильным коридорам к Офицеру Веклеру.")
        kb = tele_types.InlineKeyboardMarkup().add(tele_types.InlineKeyboardButton("🚪 Войти в допросную", callback_data="game2_interrogation_room"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        update_game_progress(user_id, "ch2_shields_done")

    # --- ДОПРОС ---
    elif call.data == "game2_interrogation_room":
        text = (f"🔦 Допросная #4. Офицер Веклер сверлит вас взглядом. \n\n"
                f"— Пилот {username}, давайте без сказок. Что случилось на 'Авалоне'? "
                f"Почему капитан мертв, а ваш бортовой пес выглядит так, будто сожрал "
                f"флешку с секретными кодами?")
        kb = tele_types.InlineKeyboardMarkup(row_width=1)
        kb.add(
            tele_types.InlineKeyboardButton("📜 Рассказать про Сектор Зеро", callback_data="game2_talk_truth"),
            tele_types.InlineKeyboardButton("🤥 Сказать, что станция была пуста", callback_data="game2_talk_lie"),
            tele_types.InlineKeyboardButton("🐕 Отвлечь его выходкой Марти", callback_data="game2_marty_distract")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        update_game_progress(user_id, "ch2_interrogation")

    # --- ВЕТКА: ОТВЛЕЧЕНИЕ И ОБЫСК ---
    elif call.data == "game2_marty_distract":
        text = ("🐕 Марти внезапно начал громко чесаться и 'случайно' опрокинул кофе на "
                "терминал Веклера. Пока Офицер ругается и вытирает стол, у вас есть "
                "шанс осмотреть его открытый ящик или терминал!")
        kb = tele_types.InlineKeyboardMarkup(row_width=1)
        kb.add(
            tele_types.InlineKeyboardButton("🔎 Обыскать ящик стола", callback_data="game2_search_desk"),
            tele_types.InlineKeyboardButton("💻 Взглянуть в терминал", callback_data="game2_search_terminal"),
            tele_types.InlineKeyboardButton("🚶 Вернуться на стул", callback_data="game2_interrogation_room")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        update_game_progress(user_id, "ch2_searching")

    # ПРЕДМЕТ 1: ДАТАПАД (+1 Пыль)
    elif call.data == "game2_search_desk":
        if "item_datapad" not in current_node:
            add_xp(user_id, 1, username)
            update_game_progress(user_id, current_node + "_item_datapad")
            msg = "✅ **НАЙДЕНО:** Старый датапад охранника (+1 Пыль).\n\n"
        else:
            msg = "Тут больше ничего нет.\n\n"
        text = msg + "В ящике куча бумаг и датапад с надписью 'Стикс'. Похоже, Веклер тоже ведет свое расследование."
        kb = tele_types.InlineKeyboardMarkup().add(tele_types.InlineKeyboardButton("💻 К терминалу", callback_data="game2_search_terminal"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # ПРЕДМЕТ 2: ФЛЕШКА (+1 Пыль)
    elif call.data == "game2_search_terminal":
        if "item_usb" not in current_node:
            add_xp(user_id, 1, username)
            update_game_progress(user_id, current_node + "_item_usb")
            msg = "✅ **НАЙДЕНО:** Зашифрованная флешка (+1 Пыль).\n\n"
        else:
            msg = "Флешка уже у вас.\n\n"
        text = msg + "В порту терминала торчит накопитель. Вы быстро прячете его в рукав. Веклер возвращается!"
        kb = tele_types.InlineKeyboardMarkup().add(tele_types.InlineKeyboardButton("🪑 Сесть на место", callback_data="game2_final_choice"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- ФИНАЛЬНЫЙ ВЫБОР ---
    elif call.data == "game2_final_choice" or call.data == "game2_talk_truth" or call.data == "game2_talk_lie":
        text = ("⚠️ **ТРЕВОГА НА СТАНЦИИ!**\n\n"
                "Стены содрогнулись. Свет сменился на аварийный красный. \n"
                "— Что это?! — вскрикнул Веклер. — Внешний сигнал... он идет с Земли!\n\n"
                "Марти шепчет: 'Хозяин, это наш шанс. Мы можем сбежать к челноку или "
                "помочь Веклеру заблокировать вирус'.")
        kb = tele_types.InlineKeyboardMarkup(row_width=1)
        kb.add(
            tele_types.InlineKeyboardButton("🛡 Помочь Академии (Финал ГЕРОЙ)", callback_data="game2_end_hero"),
            tele_types.InlineKeyboardButton("🏃 Бежать к челноку (Финал БЕГЛЕЦ)", callback_data="game2_end_escape"),
            tele_types.InlineKeyboardButton("😶 Сдаться властям (Финал ТЕРПИЛА)", callback_data="game2_end_normal")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- КОНЦОВКИ ---
    
    # 1. ЛУЧШАЯ (50 Пыли)
    elif call.data == "game2_end_hero":
        if "ch2_done" not in current_node:
            add_xp(user_id, 50, username)
            update_game_progress(user_id, "ch2_done_hero")
            reward = "💰 Награда: **50 Звездной пыли**."
        else: reward = "✨ Награда уже получена."
        
        text = (f"🏆 **ФИНАЛ: ГЕРОЙ ОРИОНА**\n\n"
                f"Вы использовали данные с флешки, чтобы закрыть порты станции. Вирус с Земли "
                f"отбит! Веклер жмет вам руку: 'Пилот, я был неправ. Вы спасли тысячи жизней'.\n\n"
                f"{reward}\n\n"
                f"Теперь вы — секретный агент Академии. Продолжение следует!")
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="Markdown")

    # 2. СРЕДНЯЯ (25 Пыли)
    elif call.data == "game2_end_escape":
        if "ch2_done" not in current_node:
            add_xp(user_id, 25, username)
            update_game_progress(user_id, "ch2_done_escape")
            reward = "💰 Награда: **25 Звездной пыли**."
        else: reward = "✨ Награда уже получена."
        
        text = (f"🥈 **ФИНАЛ: ВОЛЬНЫЙ ПИЛОТ**\n\n"
                f"Пока все паниковали, вы и Марти проскользнули в ангар и угнали свой челнок. "
                f"Академия теперь считает вас дезертиром, но артефакты остались у вас.\n\n"
                f"{reward}\n\n"
                f"Вы в розыске. Продолжение следует!")
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="Markdown")

    # 3. ОБЫЧНАЯ (5 Пыли)
    elif call.data == "game2_end_normal":
        if "ch2_done" not in current_node:
            add_xp(user_id, 5, username)
            update_game_progress(user_id, "ch2_done_normal")
            reward = "💰 Награда: **5 Звездной пыли**."
        else: reward = "✨ Награда уже получена."
        
        text = (f"🥉 **ФИНАЛ: ПОД СТРАЖЕЙ**\n\n"
                f"Вы решили довериться закону, но Веклер конфисковал всё имущество. "
                f"Вас заперли в карантинном блоке до выяснения обстоятельств.\n\n"
                f"{reward}\n\n"
                f"Вас ждет долгий суд. Продолжение следует!")
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="Markdown")
