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
        bot.answer_callback_query(call.id, f"⏳ Нужно подождать. Марти будет готов через {mins} мин.", show_alert=True)
        return

    # 2. УМНЫЙ СТАРТ
    if call.data == "game2_start":
        if current_node and current_node.startswith("ch2_") and current_node != "ch2_start":
            text = (f"🛰 **БОРТОВОЙ ЖУРНАЛ: ГЛАВА 2**\n\n"
                    f"Пилот {username}, статус миссии: `{current_node}`.\n"
                    f"Станция 'Орион-Прайм' погружается в хаос. Продолжаем?")
            kb = tele_types.InlineKeyboardMarkup(row_width=1)
            
            if "hack" in current_node: kb.add(tele_types.InlineKeyboardButton("🔄 Проверить готовность Марти", callback_data="game2_check_hack"))
            elif "reboot" in current_node: kb.add(tele_types.InlineKeyboardButton("🔄 Проверить системы связи", callback_data="game2_check_reboot"))
            elif "interrogation" in current_node: kb.add(tele_types.InlineKeyboardButton("🚪 Вернуться к Веклеру", callback_data="game2_interrogation_room"))
            elif "vent" in current_node: kb.add(tele_types.InlineKeyboardButton("💨 Ползти дальше", callback_data="game2_vent_shaft"))
            else: kb.add(tele_types.InlineKeyboardButton("🚀 Продолжить", callback_data="game2_interrogation_room"))
            
            kb.add(tele_types.InlineKeyboardButton("♻️ Начать Главу 2 сначала", callback_data="game2_reset"))
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
            return

        # ЭТАП 1: Прибытие
        text = (f"🛰 **ЭТАП 1: ПРИЗЕМЛЕНИЕ**\n\n"
                f"Челнок замер. В ангаре подозрительно пусто. \n\n"
                f"— Хозяин, — Марти (male) навострил уши. — Сканеры СБ уже прощупывают наш корпус. "
                f"Если они найдут мох или артефакты, нас запрут до конца жизни. "
                f"Мне нужно спрятать их в своем экранированном отсеке!")
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("🧳 Спрятать улики в Марти", callback_data="game2_hide_evidence"),
            tele_types.InlineKeyboardButton("🚶 Идти открыто", callback_data="game2_interrogation_room")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        update_game_progress(user_id, "ch2_start")

    elif call.data == "game2_reset":
        update_game_progress(user_id, "ch2_start")
        run_scenario(bot, type('obj', (object,), {'from_user': call.from_user, 'data': 'game2_start', 'message': call.message}))

    # ЭТАП 2: Таймер 15 мин
    elif call.data == "game2_hide_evidence":
        set_game_timer(user_id, 15)
        text = ("🛠 **ЭТАП 2: МАСКИРОВКА**\n\n"
                "— Работаю! — Марти залез в тех-люк. — Мне нужно **15 минут**, чтобы "
                "создать анти-сигнал и подавить излучение артефакта. Ступайте в допросную, "
                "я проскользну через вентиляцию позже!")
        kb = tele_types.InlineKeyboardMarkup().add(tele_types.InlineKeyboardButton("🔄 Проверить готовность", callback_data="game2_check_hack"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        update_game_progress(user_id, "ch2_hangar_hack")

    elif call.data == "game2_check_hack":
        text = ("✅ **СКРЫТНОСТЬ 100%**\n\n"
                "Марти догнал вас у дверей СБ. Он выглядит как обычный пес, но его хвост "
                "слегка вибрирует от напряжения. Пора заходить.")
        kb = tele_types.InlineKeyboardMarkup().add(tele_types.InlineKeyboardButton("🚪 Войти в допросную", callback_data="game2_interrogation_room"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        update_game_progress(user_id, "ch2_ready_to_talk")

    # ЭТАП 3: Веклер
    elif call.data == "game2_interrogation_room":
        text = (f"🔦 **ЭТАП 3: ДОПРОС**\n\n"
                f"Офицер Веклер нервно курит синтетическую сигару.\n"
                f"— Пилот {username}, датчики зафиксировали странный всплеск в ангаре. "
                f"Вы что-то привезли? Или ваша собака просто неисправна?")
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("📜 Рассказать про 'Авалон-7'", callback_data="game2_talk_horror"),
            tele_types.InlineKeyboardButton("🐕 Отвлечь его", callback_data="game2_search_mode")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        update_game_progress(user_id, "ch2_interrogation")

    # ЭТАП 4: Сбор улик (Предметы 1 и 2)
    elif call.data == "game2_search_mode":
        text = ("🐕 Марти начал имитировать приступ бешенства, искря проводами. \n"
                "Веклер отскочил к стене. Пользуйтесь моментом!")
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("🔍 Обыскать стол", callback_data="game2_item_chip"),
            tele_types.InlineKeyboardButton("📂 Глянуть в сейф", callback_data="game2_item_tape"),
            tele_types.InlineKeyboardButton("🪑 Вернуться на место", callback_data="game2_talk_horror")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    elif call.data == "game2_item_chip":
        if "chip" not in current_node:
            add_xp(user_id, 1, username); update_game_progress(user_id, current_node + "_chip")
            msg = "✅ **НАЙДЕНО:** Чип управления СБ (+1 Пыль).\n\n"
        else: msg = "Чип уже у вас.\n\n"
        kb = tele_types.InlineKeyboardMarkup().add(tele_types.InlineKeyboardButton("🔙 Назад", callback_data="game2_search_mode"))
        bot.edit_message_text(msg + "Этот чип может открыть любую дверь на станции.", call.message.chat.id, call.message.message_id, reply_markup=kb)

    elif call.data == "game2_item_tape":
        if "tape" not in current_node:
            add_xp(user_id, 1, username); update_game_progress(user_id, current_node + "_tape")
            msg = "✅ **НАЙДЕНО:** Аудиокассета 'Запись 0-0' (+1 Пыль).\n\n"
        else: msg = "Кассета уже у вас.\n\n"
        kb = tele_types.InlineKeyboardMarkup().add(tele_types.InlineKeyboardButton("🔙 Назад", callback_data="game2_search_mode"))
        bot.edit_message_text(msg + "Тут голос капитана... он говорит о предательстве.", call.message.chat.id, call.message.message_id, reply_markup=kb)

    # ЭТАП 5: Темнота
    elif call.data == "game2_talk_horror":
        text = ("🚨 **ЭТАП 5: КРИК С ЗЕМЛИ**\n\n"
                "Свет гаснет. Станция содрогается. Из колонок доносится голос вашей матери, "
                "хотя она на Земле: 'Сынок, открой дверь...'.\n\n"
                "Веклер бледнеет: 'Это не может быть она...'. Он выбегает из комнаты, "
                "забыв про вас.")
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("💨 В вентиляцию", callback_data="game2_vent_shaft"),
            tele_types.InlineKeyboardButton("🏃 В коридор за Веклером", callback_data="game2_vent_shaft") # Ведет туда же для упрощения
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        update_game_progress(user_id, "ch2_horror_start")

    # ЭТАП 6: Вентиляция (Предмет 3)
    elif call.data == "game2_vent_shaft":
        text = ("💨 **ЭТАП 6: ТЕСНОТА**\n\n"
                "В трубах липко и пахнет сыростью. Марти светит фонариком.\n"
                "— Смотрите, Хозяин! Тут жетон охранника.")
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("🪪 Забрать жетон", callback_data="game2_item_token"),
            tele_types.InlineKeyboardButton("🚶 Ползти к Серверной", callback_data="game2_server_room")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        update_game_progress(user_id, "ch2_vent_crawl")

    elif call.data == "game2_item_token":
        if "token" not in current_node:
            add_xp(user_id, 1, username); update_game_progress(user_id, current_node + "_token")
        kb = tele_types.InlineKeyboardMarkup().add(tele_types.InlineKeyboardButton("🚶 Вперед", callback_data="game2_server_room"))
        bot.edit_message_text("✅ Жетон у вас. Двигаемся дальше.", call.message.chat.id, call.message.message_id, reply_markup=kb)

    # ЭТАП 7: Серверная
    elif call.data == "game2_server_room":
        text = ("🔬 **ЭТАП 7: СЕРВЕРНАЯ**\n\n"
                "Вы видите главные компьютеры. На них — логи проекта 'Стикс'. \n"
                "Марти: 'Они не просто изучали мох. Они хотели использовать его как антенну!'")
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("💾 Скачать данные (Нужен Чип)", callback_data="game2_lab_hack"),
            tele_types.InlineKeyboardButton("🚪 К тех-узлу", callback_data="game2_power_puzzle")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        update_game_progress(user_id, "ch2_lab_discovery")

    elif call.data == "game2_lab_hack":
        if "chip" in current_node:
            add_xp(user_id, 5, username); update_game_progress(user_id, current_node + "_data")
            msg = "🔓 **УСПЕХ!** Вы узнали, что Академия — это филиал земной корпорации. (+5 Пыли)"
        else: msg = "❌ Нужен Чип СБ для взлома!"
        bot.answer_callback_query(call.id, msg, show_alert=True)
        run_scenario(bot, type('obj', (object,), {'from_user': call.from_user, 'data': 'game2_power_puzzle', 'message': call.message}))

    # ЭТАП 8: Головоломка
    elif call.data == "game2_power_puzzle":
        text = ("⚡️ **ЭТАП 8: ЩИТОК ПИТАНИЯ**\n\n"
                "Чтобы открыть ангар, нужно перенаправить ток. Три рычага: 1, 2, 3.\n"
                "Марти: 'Хозяин, я думаю комбинация — это просто число ваших конечностей плюс мои!'")
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("🎚 Рычаг 2", callback_data="game2_puzzle_fail"),
            tele_types.InlineKeyboardButton("🎚 Рычаг 6", callback_data="game2_reboot_start")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        update_game_progress(user_id, "ch2_puzzle")

    elif call.data == "game2_puzzle_fail":
        bot.answer_callback_query(call.id, "💥 Искры! Попробуйте еще раз.", show_alert=True)
        return

    # ЭТАП 9: Таймер 30 мин (Большое действие)
    elif call.data == "game2_reboot_start":
        set_game_timer(user_id, 30)
        text = ("🌌 **ЭТАП 9: ГЛУБОКАЯ ПЕРЕЗАГРУЗКА**\n\n"
                "Питание пошло, но системам связи нужно **30 минут**, чтобы очиститься от "
                "вируса 'Стикс'. Станция замерла в тишине. \n\n"
                "— Хозяин, отдохните пока. Я прикрою шлюз. Этот перерыв нам обоим нужен.")
        kb = tele_types.InlineKeyboardMarkup().add(tele_types.InlineKeyboardButton("🔄 Проверить системы", callback_data="game2_check_reboot"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        update_game_progress(user_id, "ch2_reboot_wait")

    elif call.data == "game2_check_reboot":
        text = ("✅ **СИСТЕМЫ ОЧИЩЕНЫ**\n\n"
                "Связь восстановилась. Вы слышите, как патрули бегают по этажам. "
                "Путь к ангару свободен!")
        kb = tele_types.InlineKeyboardMarkup().add(tele_types.InlineKeyboardButton("🏃 Бежать к ангару", callback_data="game2_wounded_officer"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        update_game_progress(user_id, "ch2_path_clear")

    # ЭТАП 10: Дневник (Предмет 4)
    elif call.data == "game2_wounded_officer":
        text = ("🩸 **ЭТАП 10: ТЕЛО ВЕКЛЕРА**\n\n"
                "Вы нашли его у шлюза. Он не дышит. В руке зажат его личный дневник.")
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("📕 Взять дневник", callback_data="game2_item_diary"),
            tele_types.InlineKeyboardButton("🚀 Зайти в челнок", callback_data="game2_final_choice")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        update_game_progress(user_id, "ch2_wounded")

    elif call.data == "game2_item_diary":
        if "diary" not in current_node:
            add_xp(user_id, 1, username); update_game_progress(user_id, current_node + "_diary")
        kb = tele_types.InlineKeyboardMarkup().add(tele_types.InlineKeyboardButton("🚀 К ФИНАЛУ", callback_data="game2_final_choice"))
        bot.edit_message_text("✅ Дневник у вас. Там пароли от спутников Земли!", call.message.chat.id, call.message.message_id, reply_markup=kb)

    # ЭТАП 11: Финальный выбор
    elif call.data == "game2_final_choice":
        text = ("🚢 **ЭТАП 11: МОМЕНТ ИСТИНЫ**\n\n"
                "Вы в кресле пилота. Марти смотрит на станцию: 'Она умирает, Хозяин'.\n"
                "Выбор за вами. Как мы закончим этот кошмар?")
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("🛡 Спасти Академию", callback_data="game2_end_hero"),
            tele_types.InlineKeyboardButton("🚀 Улететь навсегда", callback_data="game2_end_escape"),
            tele_types.InlineKeyboardButton("🏳 Сдаться трибуналу", callback_data="game2_end_normal")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # ЭТАП 12: Финалы
    elif call.data == "game2_end_hero":
        if "done" not in current_node:
            add_xp(user_id, 50, username); update_game_progress(user_id, "ch2_done_hero")
            res = "💰 Награда: **50 Пыли**."
        else: res = "✨ Награда получена."
        bot.edit_message_text(f"🏆 **ФИНАЛ: ГЕРОЙ**\n\nВы уничтожили вирус ценой своей репутации. Академия спасена.\n\n{res}", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

    elif call.data == "game2_end_escape":
        if "done" not in current_node:
            add_xp(user_id, 25, username); update_game_progress(user_id, "ch2_done_escape")
            res = "💰 Награда: **25 Пыли**."
        else: res = "✨ Награда получена."
        bot.edit_message_text(f"🥈 **ФИНАЛ: БЕГЛЕЦ**\n\nВы в космосе. Свободны и опасны. За вами придут...\n\n{res}", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

    elif call.data == "game2_end_normal":
        if "done" not in current_node:
            add_xp(user_id, 5, username); update_game_progress(user_id, "ch2_done_normal")
            res = "💰 Награда: **5 Пыли**."
        else: res = "✨ Награда получена."
        bot.edit_message_text(f"🥉 **ФИНАЛ: ПОДОЗРЕВАЕМЫЙ**\n\nВы выбрали закон. Надеемся, суд будет справедлив.\n\n{res}", call.message.chat.id, call.message.message_id, parse_mode="Markdown")
