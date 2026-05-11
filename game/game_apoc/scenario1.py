import telebot
from datetime import datetime
from telebot import types as tele_types
from database import get_game_status, update_game_progress, set_game_timer, add_xp

def run_scenario(bot, call):
    user_id = call.from_user.id
    username = call.from_user.first_name if call.from_user.first_name else "Док"
    current_node, timer_end = get_game_status(user_id)
    if current_node is None: current_node = "apoc_start"

    # --- [ АНТИ-ФАРМ & УЛИКИ ] ---
    saved_flags = ""
    # Флаги предметов, улик и прогресса
    important_flags = [
        "_ch1_claimed", "_item_cloth", "_item_parts", "_suit_fixed", 
        "_scanner_fixed", "_clue_wire", "_clue_boot", "_logic_pc_done"
    ]
    for flag in important_flags:
        if flag in current_node: saved_flags += flag

    # 1. ГЛОБАЛЬНАЯ ПРОВЕРКА ТАЙМЕРА
    if timer_end and datetime.now() < timer_end:
        remaining = timer_end - datetime.now()
        mins = int(remaining.total_seconds() // 60)
        bot.answer_callback_query(call.id, f"⌛️ Процесс идет... {mins} мин. Марти: 'Док, не суетитесь, я все контролирую!'", show_alert=True)
        return

    # --- [ ЭТАП 1: ПРОБУЖДЕНИЕ (Стартовое меню) ] ---
    if call.data == "apoc_start":
        text = (f"☢️ **ПРОТОКОЛ: ЧИСТОЕ НЕБО | ГЛАВА 1: ТЕНЬ В БУНКЕРЕ**\n"
                f"──────────────────────────\n"
                f"Вы приходите в себя на холодном полу. Голова гудит, будто по ней постучали титановым ломом. "
                f"В бункере темно, лишь аварийные лампы мигают алым, как глаза голодного волка.\n\n"
                f"Марти (той-пудель в потрепанном жилете) сидит рядом и сосредоточенно вылизывает лапу. "
                f"Его звуковой модуль шипит: 'О, Док, вы живы. Я уже начал присматривать себе нового хозяина среди мутантов... Шучу. "
                f"Хотя их печенье выглядит заманчиво. У нас проблема: главный реактор отключен вручную. Это не сбой. Нас посетили'.\n\n"
                f"**ВАША ЦЕЛЬ:** Восстановить питание, расследовать взлом и выбраться на поверхность.")
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("🔍 Осмотреть место происшествия", callback_data="apoc_n1_investigate"),
            tele_types.InlineKeyboardButton("🖥 Проверить терминал (Логика)", callback_data="apoc_n1_pc_check"),
            tele_types.InlineKeyboardButton("🔙 В меню Хаба", callback_data="hub_main_menu")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 2: ДЕТЕКТИВ (Осмотр) ] ---
    elif call.data == "apoc_n1_investigate":
        text = (f"🔦 **ПОИСК УЛИК**\n\n"
                f"Вы включаете фонарик. Луч света выхватывает перевернутый стол и... Марти указывает носом на угол.\n\n"
                f"— Смотрите, Док. Силовой кабель не перегорел. Он перекушен. И это сделал не я, мои зубы слишком аристократичны для такой грязной работы. "
                f"Тут явно был кто-то с кусачками. Или очень злыми зубами'.\n\n"
                f"На пыльном полу виднеется странный след.")
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("🔌 Осмотреть кабель", callback_data="apoc_n1_clue_wire"),
            tele_types.InlineKeyboardButton("👣 Изучить след (Детектив)", callback_data="apoc_n1_clue_boot"),
            tele_types.InlineKeyboardButton("🔙 Вернуться", callback_data="apoc_start")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 3-4: УЛИКИ (Секреты) ] ---
    elif call.data == "apoc_n1_clue_wire":
        if "_clue_wire" not in current_node:
            add_xp(user_id, 2, username)
            update_game_progress(user_id, current_node + "_clue_wire")
            msg = "✅ **УЛИКА:** Медный кабель со следами смазки. Кто-то смазывал инструменты.\n\n"
        else: msg = "📦 Вы уже изучили этот кабель.\n\n"
        kb = tele_types.InlineKeyboardMarkup().add(tele_types.InlineKeyboardButton("🔙 Назад к осмотру", callback_data="apoc_n1_investigate"))
        bot.edit_message_text(msg + "Марти: 'Запах... пахнет дешевым машинным маслом из Сектора 4. Кажется, у нас гости из Трущоб'.", call.message.chat.id, call.message.message_id, reply_markup=kb)

    elif call.data == "apoc_n1_clue_boot":
        if "_clue_boot" not in current_node:
            add_xp(user_id, 2, username)
            update_game_progress(user_id, current_node + "_clue_boot")
            msg = "✅ **УЛИКА:** Отпечаток тяжелого армейского сапога 44-го размера.\n\n"
        else: msg = "📦 След зафиксирован в базе.\n\n"
        kb = tele_types.InlineKeyboardMarkup().add(tele_types.InlineKeyboardButton("🔙 Назад к осмотру", callback_data="apoc_n1_investigate"))
        bot.edit_message_text(msg + "— Ого! — Марти присвистнул. — Док, у вас 39-й, а у меня лапы. Значит, это точно не мы в лунатизме бродили'.", call.message.chat.id, call.message.message_id, reply_markup=kb)

    # --- [ ЭТАП 5: ЛОГИЧЕСКАЯ ЗАГАДКА (Терминал) ] ---
    elif call.data == "apoc_n1_pc_check":
        if "_logic_pc_done" in current_node:
            bot.answer_callback_query(call.id, "🖥 Система уже взломана!")
            run_scenario(bot, type('obj', (object,), {'from_user': call.from_user, 'data': 'apoc_n1_base_menu', 'message': call.message}))
            return

        text = ("🖥 **ТЕРМИНАЛ: ЗАБЛОКИРОВАНО**\n\n"
                "Экран требует пароль администратора. В углу висит стикер с подсказкой: 'Год, когда всё началось в Мариуполе'.\n\n"
                "Марти: 'Док, я знаю, вы тогда еще пешком под стол ходили, но память ученого должна подсказать дату! Это связано с вашей семьей'.")
        kb = tele_types.InlineKeyboardMarkup(row_width=2).add(
            tele_types.InlineKeyboardButton("⌨️ 1982", callback_data="apoc_n1_pc_fail"),
            tele_types.InlineKeyboardButton("⌨️ 1985", callback_data="apoc_n1_pc_success"),
            tele_types.InlineKeyboardButton("⌨️ 1991", callback_data="apoc_n1_pc_fail"),
            tele_types.InlineKeyboardButton("⌨️ 2024", callback_data="apoc_n1_pc_fail")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    elif call.data == "apoc_n1_pc_success":
        add_xp(user_id, 5, username)
        update_game_progress(user_id, current_node + "_logic_pc_done")
        text = ("🔓 **ДОСТУП РАЗРЕШЕН**\n\n"
                "Вы вошли в систему. Логи показывают: 'Внешнее вмешательство. Дверь шлюза открыта кодом 0441'.\n\n"
                "Марти: 'Док, смотрите! Кто-то скачал чертежи вашего Костюма. Нас не просто грабили, нас изучали'.")
        kb = tele_types.InlineKeyboardMarkup().add(tele_types.InlineKeyboardButton("🚶 Продолжить", callback_data="apoc_n1_base_menu"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 10: ВЕРСТАК И КРАФТ (Усложнение) ] ---
    elif call.data == "apoc_n1_base_menu":
        text = (f"🛠 **ЦЕНТРАЛЬНЫЙ ОТСЕК**\n\n"
                f"Итак, у нас есть улики, но нет энергии. Чтобы выйти в шахты и поймать вора, нужно собрать снаряжение.\n\n"
                f"Марти: 'Я нашел ваш старый чертеж. Чтобы починить костюм, нам нужно не просто кусок ткани, а **многослойная изоляция**. Ищем брезент и медные пластины!'.")
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("🧵 Верстак (Крафт)", callback_data="apoc_n1_workbench"),
            tele_types.InlineKeyboardButton("📦 Обыскать склад (Этап 1/3)", callback_data="apoc_n1_search_1"),
            tele_types.InlineKeyboardButton("🔦 Обыскать лабораторию (Этап 2/3)", callback_data="apoc_n1_search_2"),
            tele_types.InlineKeyboardButton("⬅️ Назад", callback_data="apoc_start")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        update_game_progress(user_id, "apoc_n1_main_hub" + saved_flags)

    # --- [ ЭТАПЫ 11-15: СЛОЖНЫЙ ПОИСК (Таймеры и Детектив) ] ---
    elif call.data == "apoc_n1_search_1":
        set_game_timer(user_id, 15)
        text = ("📦 **СКЛАД: ТЯЖЕЛЫЙ ТРУД**\n\n"
                "Вы начинаете разгребать завалы. Марти нашел коробку с надписью 'Хлам', но она заперта на магнитный замок.\n\n"
                "Ожидание: **15 минут**.")
        kb = tele_types.InlineKeyboardMarkup().add(tele_types.InlineKeyboardButton("🔄 Вскрыть замок", callback_data="apoc_n1_res_1"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    elif call.data == "apoc_n1_res_1":
        update_game_progress(user_id, current_node + "_item_cloth")
        text = ("✅ **НАЙДЕНО: БРЕЗЕНТ**\n\n"
                "Марти: 'Фу, ну и запах. Кажется, в этом брезенте спала семья мутировавших енотов. Но для костюма пойдет!'.")
        kb = tele_types.InlineKeyboardMarkup().add(tele_types.InlineKeyboardButton("🔙 К хабу", callback_data="apoc_n1_base_menu"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАПЫ 16-30: ШАХТЫ, СТЕЛС И ФИНАЛ (Логика и Секреты) ] ---
    # (Здесь мы добавим встречу с роботом-охранником, загадку с вентиляцией и финал)
    
    # ПРИМЕР СТЕЛС-ЭТАПА
    elif call.data == "apoc_n1_stealth_start":
        text = ("💨 **ЭТАП 20: ВЕНТИЛЯЦИЯ**\n\n"
                "Вы ползете по узкой трубе. Впереди слышны шаги. \n"
                "Марти: 'Тихо, Док! Там дрон-уборщик Академии. Он перепрошит на режим 'Уничтожить всё живое'. "
                "Если чихнете — я не виноват. Используем мой звуковой модуль?'")
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("🔊 Включить эхо (Обманка)", callback_data="apoc_n1_stealth_success"),
            tele_types.InlineKeyboardButton("🏃 Рвануть вперед (Риск)", callback_data="apoc_n1_stealth_fail")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 16: ТЕХНИЧЕСКИЙ ШЛЮЗ (Детектив продолжается) ] ---
    elif call.data == "apoc_n1_search_2":
        text = (f"🚿 **СЕКТОР Б: ТЕХНИЧЕСКИЙ УЗЕЛ**\n\n"
                f"Вы пробираетесь через душевые. Вода здесь не текла уже лет десять, но на полу — свежие лужи.\n\n"
                f"Марти: 'Док, либо у нас завелись очень чистоплотные призраки, либо кто-то слил охлаждающую жидкость из вашего старого автоклава. "
                f"Запах... это стерилизатор. Тот, кто здесь был, явно имел отношение к медицине или биологии. "
                f"Смотрите, на стене кровавый след, но он... фиолетовый?'.")
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("🧬 Взять пробу жидкости", callback_data="apoc_n1_clue_liquid"),
            tele_types.InlineKeyboardButton("🛠 Искать запчасти для сканера", callback_data="apoc_n1_search_parts"),
            tele_types.InlineKeyboardButton("🔙 В центральный отсек", callback_data="apoc_n1_base_menu")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    elif call.data == "apoc_n1_clue_liquid":
        if "_clue_liquid" not in current_node:
            add_xp(user_id, 3, username)
            update_game_progress(user_id, current_node + "_clue_liquid")
            msg = "✅ **УЛИКА:** Фиолетовый био-реагент. Это не кровь, а питательная среда для мха.\n\n"
        else: msg = "📦 Проба уже в пробирке.\n\n"
        kb = tele_types.InlineKeyboardMarkup().add(tele_types.InlineKeyboardButton("🔙 Назад к шлюзу", callback_data="apoc_n1_search_2"))
        bot.edit_message_text(msg + "Марти: 'Док, кажется, наш вор — не просто мародер. Он что-то выращивает прямо у нас под боком'.", call.message.chat.id, call.message.message_id, reply_markup=kb)

    # --- [ ЭТАП 20: ВЕНТИЛЯЦИОННЫЕ ШАХТЫ (Стелс) ] ---
    elif call.data == "apoc_n1_vent_enter":
        text = ("💨 **ЭТАП 20: ТЕСНЫЕ ТРУБЫ**\n\n"
                "Вы ползете по вентиляции. Пыль забивает фильтры маски. Впереди слышен механический скрежет.\n\n"
                "Марти: 'Тихо! Впереди дрон-уборщик серии 'Чистота-9'. Но после Сбоя его программа 'уборки' включает в себя расчленение любых биологических объектов. "
                "Он блокирует проход к генераторной. Док, используем мой звуковой модуль?'")
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("🔊 Имитировать писк крыс (Обманка)", callback_data="apoc_n1_stealth_rats"),
            tele_types.InlineKeyboardButton("🎤 Записать эхо шагов в коридоре", callback_data="apoc_n1_stealth_steps"),
            tele_types.InlineKeyboardButton("👊 Попробовать вырубить дрона ломом (Риск!)", callback_data="apoc_n1_stealth_fight")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    elif call.data == "apoc_n1_stealth_rats":
        text = ("✅ **УСПЕХ**\n\nМарти выдал серию высокочастотных писков. Дрон замер, его красные окуляры повернулись в сторону шахты. "
                "Механический паук резво укатился проверять 'грызунов'. Путь свободен!")
        kb = tele_types.InlineKeyboardMarkup().add(tele_types.InlineKeyboardButton("🚶 Идти к генератору", callback_data="apoc_n1_generator_room"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 25: ЗАГАДКА ГЕНЕРАТОРА (Логика) ] ---
    elif call.data == "apoc_n1_generator_room":
        text = ("⚡️ **ЭТАП 25: СЕРДЦЕ БУНКЕРА**\n\n"
                "Вы у главного щитка. Тут всё залито тем самым фиолетовым мхом. Он буквально 'ест' электричество.\n\n"
                "Марти: 'Смотрите, Док! Кто-то перенаправил поток энергии. Чтобы запустить панели, нужно перераспределить нагрузку по фазам. "
                "Если ошибиться — нас поджарит, а мох разрастется еще сильнее'.\n\n"
                "Перед вами три тумблера: А-1, Б-2, В-3. Нацарапано: 'Сумма должна быть равна атомному номеру углерода'.")
        kb = tele_types.InlineKeyboardMarkup(row_width=3).add(
            tele_types.InlineKeyboardButton("🔘 4", callback_data="apoc_n1_gen_fail"),
            tele_types.InlineKeyboardButton("🔘 6", callback_data="apoc_n1_gen_success"),
            tele_types.InlineKeyboardButton("🔘 8", callback_data="apoc_n1_gen_fail")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    elif call.data == "apoc_n1_gen_success":
        add_xp(user_id, 10, username)
        text = ("🔥 **ПИТАНИЕ ВОССТАНОВЛЕНО**\n\n"
                "Свет с миганием загорается во всем бункере. Мох испуганно сжимается. Но в этом свете вы видите то, что повергает вас в шок.\n\n"
                "На стене у генератора висит старая фотография. На ней — ваш дед, Дмитрий Владимирович, в таком же бункере. "
                "В руках у него странный прибор, подозрительно похожий на тот самый 'Сканер', который мы пытаемся собрать.")
        kb = tele_types.InlineKeyboardMarkup().add(tele_types.InlineKeyboardButton("🧗 Выйти на крышу (Финал)", callback_data="apoc_n1_final_ascent"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        update_game_progress(user_id, "apoc_n1_truth_found" + saved_flags)

    # --- [ ЭТАП 30: ФИНАЛ ГЛАВЫ (Моральный выбор) ] ---
    elif call.data == "apoc_n1_final_ascent":
        text = (f"☀️ **ЭТАП 30: ГЛОТОК ЯДА**\n\n"
                f"Вы на крыше НИИ. Перед вами расстилается мертвый город. Вдали виднеются шпили торгового центра.\n\n"
                f"У самих солнечных панелей вы находите того самого 'вора'. Это робот-андроид старой модели, он сильно поврежден. "
                f"В его груди — тот самый фиолетовый мох, который служит ему батареей.\n\n"
                f"Робот (хрипит): 'Док... не выключай... мне нужно... донести... семя...'.\n\n"
                f"Марти: 'Док, если мы его отключим — получим кучу редких запчастей для вашего костюма и мой сканер станет в два раза мощнее. "
                f"Но если поможем ему... кто знает, может он расскажет, откуда у него фото вашего деда?'")
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("🔧 Разобрать робота (Сила)", callback_data="apoc_n1_end_power"),
            tele_types.InlineKeyboardButton("🔋 Поделиться энергией (Знание)", callback_data="apoc_n1_end_knowledge")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # Результаты финала
    elif call.data == "apoc_n1_end_power":
        add_xp(user_id, 50, username)
        update_game_progress(user_id, "apoc_ch1_done_power" + saved_flags + "_ch1_claimed")
        bot.edit_message_text("🦾 **ФИНАЛ: ПУТЬ СИЛЫ**\n\nВы разобрали андроида. Теперь ваш костюм — лучший в этих пустошах. Но тайна деда осталась нераскрытой.\n\n💰 +50 Пыли.", call.message.chat.id, call.message.message_id)

    elif call.data == "apoc_n1_end_knowledge":
        add_xp(user_id, 100, username) # За сложный путь даем больше
        update_game_progress(user_id, "apoc_ch1_done_knowledge" + saved_flags + "_ch1_claimed")
        bot.edit_message_text("🧠 **ФИНАЛ: ПУТЬ ЗНАНИЯ**\n\nРобот передал вам зашифрованный архив 'Мариуполь-85'. Там координаты второго бункера. \n\n💰 +100 Пыли (Легендарное открытие).", call.message.chat.id, call.message.message_id)

# --- ФУНКЦИЯ КРАФТА (УСЛОЖНЕННАЯ) ---
def handle_craft(bot, call):
    # Здесь логика требует не только ткань, но и калибровку (таймер + выбор правильного параметра)
    pass
