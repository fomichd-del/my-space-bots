import telebot
from datetime import datetime
from telebot import types as tele_types
from database import get_game_status, update_game_progress, set_game_timer, add_xp

def run_scenario(bot, call):
    user_id = call.from_user.id
    username = call.from_user.first_name if call.from_user.first_name else "Пилот"
    current_node, timer_end = get_game_status(user_id)
    
    # 0. ПРОВЕРКА ЗАВЕРШЕНИЯ ГЛАВЫ
    is_finished = any(mark in current_node for mark in ["ch5_done_ascend", "ch5_done_return", "ch5_done_sacrifice"])

    # 1. ГЛОБАЛЬНЫЙ ТАЙМЕР
    if timer_end and datetime.now() < timer_end and not is_finished:
        remaining = timer_end - datetime.now()
        mins = int(remaining.total_seconds() // 60)
        bot.answer_callback_query(call.id, f"📡 Сигнал нестабилен. Нужно подождать {mins} мин. для полной синхронизации!", show_alert=True)
        return

    # 2. УМНЫЙ СТАРТ (Восстановление сессии)
    if call.data == "game5_start":
        if is_finished:
            bot.answer_callback_query(call.id, "🎬 История завершена. Но архивы всегда доступны!", show_alert=True)
            return

        if current_node and current_node.startswith("ch5_") and current_node != "ch5_start":
            text = (f"🌌 **ФИНАЛЬНЫЙ СЕКТОР: `{current_node}`**\n\n"
                    f"Пилот {username}, мы на самом краю реальности. Марти держит лапу на пульсе.")
            kb = tele_types.InlineKeyboardMarkup(row_width=1)
            
            # Приоритетная проверка этапов
            if "memory_sync_wait" in current_node:
                kb.add(tele_types.InlineKeyboardButton("🔄 Завершить синхронизацию", callback_data="game5_check_sync"))
            elif "final_hack_wait" in current_node:
                kb.add(tele_types.InlineKeyboardButton("🔄 Взломать Колыбель", callback_data="game5_check_hack"))
            elif "bridge" in current_node:
                kb.add(tele_types.InlineKeyboardButton("🌉 На мостик управления", callback_data="game5_node_bridge"))
            elif "archive" in current_node:
                kb.add(tele_types.InlineKeyboardButton("📂 В личные архивы", callback_data="game5_node_archives"))
            else:
                kb.add(tele_types.InlineKeyboardButton("🚀 Продолжить путь", callback_data="game5_node_bridge"))
            
            kb.add(tele_types.InlineKeyboardButton("♻️ Сбросить Главу 5", callback_data="game5_reset"))
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
            return

        # --- ЭТАП 1: ВХОД В ПУСТОТУ ---
        text = (f"🌌 **ЭТАП 1: ГРАНИЦА РАЗУМА**\n\n"
                f"Вы проникли в самое сердце Объекта Зеро. Здесь законы физики перестают работать: "
                f"пол под ногами кажется прозрачным, а над головой сияют не звезды, а тысячи ярких нитей — "
                f"потоков чистой информации.\n\n"
                f"Марти (дрожа всем телом): 'Хозяин, я чувствую... я чувствую каждого пилота, который "
                f"когда-либо учился в Академии. Их мысли, их страхи. Это место — не просто сервер, это "
                f"коллективный разум. И, кажется, он хочет с нами поговорить'.\n\n"
                f"Впереди две двери: одна из холодного металла Академии, другая — заросшая светящимся мхом.")
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("🏛 В Сектор Академии", callback_data="game5_node_bridge"),
            tele_types.InlineKeyboardButton("🌿 В Сектор Колыбели (Детектив)", callback_data="game5_node_archives")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        update_game_progress(user_id, "ch5_start")

    elif call.data == "game5_reset":
        new_status = "ch4_done_hero" if "ch5_claimed" not in current_node else "ch4_done_hero_ch5_claimed"
        update_game_progress(user_id, new_status)
        bot.answer_callback_query(call.id, "Журнал финала обнулен.")
        run_scenario(bot, type('obj', (object,), {'from_user': call.from_user, 'data': 'game5_start', 'message': call.message}))

    # --- ЭТАП 2-5: АРХИВЫ И ТАЙНА 1985 (Детектив) ---
    elif call.data == "game5_node_archives":
        text = (f"📁 **ЭТАП 2: ЗАПРЕТНЫЕ ФАЙЛЫ**\n\n"
                f"Вы оказались в комнате, заставленной старым оборудованием с Земли. На мониторах — "
                f"герб города **Мариуполь** и дата: **май 1985 года**. \n\n"
                f"Марти: 'Хозяин, это данные об эксперименте по 'дальней связи'. "
                f"Оказывается, Объект Зеро был найден еще тогда! Но как он попал в космос? "
                f"И почему здесь лежат инструменты... стоматолога?'\n\n"
                f"На столе лежит странный набор и старый дневник.")
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("🦷 Осмотреть инструменты (Секрет)", callback_data="game5_item_tools"),
            tele_types.InlineKeyboardButton("📔 Прочитать дневник (Сюжет)", callback_data="game5_item_diary"),
            tele_types.InlineKeyboardButton("🌉 Идти на мостик", callback_data="game5_node_bridge")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        update_game_progress(user_id, "ch5_archive_search")

    elif call.data == "game5_item_tools":
        if "item_tools" not in current_node:
            add_xp(user_id, 2, username); update_game_progress(user_id, current_node + "_item_tools")
            msg = "✅ **СЕКРЕТ:** Найдены антикварные щипцы и зеркало (+2 Пыли).\n\n"
        else: msg = "📦 Инструменты уже у вас в сумке.\n\n"
        kb = tele_types.InlineKeyboardMarkup().add(tele_types.InlineKeyboardButton("🔙 Назад", callback_data="game5_node_archives"))
        bot.edit_message_text(msg + "На рукоятке выбито имя вашего деда. Кажется, эта миссия длится уже поколения.", call.message.chat.id, call.message.message_id, reply_markup=kb)

    elif call.data == "game5_item_diary":
        if "item_diary_5" not in current_node:
            add_xp(user_id, 1, username); update_game_progress(user_id, current_node + "_item_diary_5")
            msg = "✅ **ПРЕДМЕТ:** Дневник исследователя 1985 (+1 Пыль).\n\n"
        else: msg = "📦 Дневник уже просканирован.\n\n"
        kb = tele_types.InlineKeyboardMarkup().add(tele_types.InlineKeyboardButton("🔙 Назад", callback_data="game5_node_archives"))
        bot.edit_message_text(msg + "В нем говорится: 'Мы не нашли мох. Он нашел нас. Мы просто перевозчики'.", call.message.chat.id, call.message.message_id, reply_markup=kb)

    # --- ЭТАП 6-9: МОСТИК И СИНХРОНИЗАЦИЯ (Таймер 1) ---
    elif call.data == "game5_node_bridge":
        set_game_timer(user_id, 25)
        text = ("🌉 **ЭТАП 6: МОСТИК УПРАВЛЕНИЯ**\n\n"
                "Вы вышли к главному терминалу. Здесь нет кнопок, только сенсорные панели для лап... и рук. \n\n"
                "Марти: 'Хозяин, чтобы получить контроль над станцией, мне нужно **25 минут** на полную "
                "синхронизацию наших ДНК с Ядром. Это будет больно для нас обоих, но это единственный шанс "
                "понять истинные цели Адмирала'.")
        kb = tele_types.InlineKeyboardMarkup().add(tele_types.InlineKeyboardButton("🔄 Завершить синхронизацию", callback_data="game5_check_sync"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        update_game_progress(user_id, "ch5_memory_sync_wait")

    elif call.data == "game5_check_sync":
        text = ("✅ **СИНХРОНИЗАЦИЯ 100%**\n\n"
                "Вспышка! Вы видите всё: Академия Орион — это лишь прикрытие. Они хотели использовать мох, "
                "чтобы стереть индивидуальность людей и создать единый 'улей' под управлением корпорации Земли. \n\n"
                "Адмирал (голограмма): 'Вы опоздали. Протокол 'Слияние' уже запущен. Либо вы станете частью нас, либо исчезнете'.")
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("💻 Взломать систему (Нужен Опыт)", callback_data="game5_node_hack_start"),
            tele_types.InlineKeyboardButton("🔫 Выстрелить в консоль", callback_data="game5_end_sacrifice")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        update_game_progress(user_id, "ch5_sync_done")

    # --- ЭТАП 10-15: ФИНАЛЬНЫЙ ВЗЛОМ (Таймер 2) ---
    elif call.data == "game5_node_hack_start":
        if "final_hack_done" in current_node:
             run_scenario(bot, type('obj', (object,), {'from_user': call.from_user, 'data': 'game5_check_hack', 'message': call.message}))
             return

        set_game_timer(user_id, 40)
        text = ("⚡️ **ЭТАП 10: БИТВА РАЗУМОВ**\n\n"
                "Марти подключился к порту напрямую. Его шерсть встала дыбом от статики. \n"
                "Марти: 'Хозяин, я борюсь с их ИИ! Мне нужно **40 минут**, чтобы перехватить коды управления "
                "всеми кораблями Академии. Держите оборону!'. \n\n"
                "Из вентиляции начинают выходить охранные дроны...")
        kb = tele_types.InlineKeyboardMarkup().add(tele_types.InlineKeyboardButton("🔄 Удержать позицию", callback_data="game5_check_hack"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        update_game_progress(user_id, "ch5_final_hack_wait")

    elif call.data == "game5_check_hack":
        text = ("🔥 **ПОБЕДА В КИБЕРПРОСТРАНСТВЕ**\n\n"
                "Марти выдергивает кабель и тяжело дышит. 'Мы... мы сделали это. Все корабли "
                "Академии обесточены. Но Ядро Объекта Зеро перегружено. У нас есть один выбор, "
                "который изменит будущее всего человечества'.")
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("🌌 Вознестись (Стать Богом Мха)", callback_data="game5_end_ascend"),
            tele_types.InlineKeyboardButton("🌍 Вернуться на Землю (Обычная жизнь)", callback_data="game5_end_return"),
            tele_types.InlineKeyboardButton("💥 Уничтожить Объект (Жертва)", callback_data="game5_end_sacrifice")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        update_game_progress(user_id, "ch5_final_hack_done")

    # --- ФИНАЛЫ С ЗАЩИТОЙ ---
    elif call.data == "game5_end_ascend":
        if "ch5_claimed" not in current_node:
            add_xp(user_id, 200, username)
            update_game_progress(user_id, "ch5_done_ascend_ch5_claimed")
            res = "💰 **ГРАН-ПРИ:** 200 Пыли (Финал: Бессмертие)."
        else:
            add_xp(user_id, 20, username)
            res = "✨ **НАГРАДА ЗА ПОВТОР:** 20 Пыли."
        
        bot.edit_message_text(f"🌟 **ФИНАЛ: НОВАЯ ЭВОЛЮЦИЯ**\n\nВы слились с Объектом Зеро. Теперь вы — голос звезд. Академии больше нет, но человечество никогда не будет прежним.\n\n{res}", call.message.chat.id, call.message.message_id)

    elif call.data == "game5_end_return":
        if "ch5_claimed" not in current_node:
            add_xp(user_id, 100, username)
            update_game_progress(user_id, "ch5_done_return_ch5_claimed")
            res = "💰 **НАГРАДА:** 100 Пыли (Финал: Дом)."
        else:
            add_xp(user_id, 20, username)
            res = "✨ **НАГРАДА ЗА ПОВТОР:** 20 Пыли."
            
        bot.edit_message_text(f"🏡 **ФИНАЛ: ДОРОГА ДОМОЙ**\n\nВы заблокировали Ядро и улетели на Землю. Вы стали обычным стоматологом, как и хотели. Но иногда, глядя на звезды, вы слышите тихий лай Марти.\n\n{res}", call.message.chat.id, call.message.message_id)

    elif call.data == "game5_end_sacrifice":
        if "ch5_claimed" not in current_node:
            add_xp(user_id, 50, username)
            update_game_progress(user_id, "ch5_done_sacrifice_ch5_claimed")
            res = "💰 **НАГРАДА:** 50 Пыли (Финал: Чистый лист)."
        else:
            add_xp(user_id, 20, username)
            res = "✨ **НАГРАДА ЗА ПОВТОР:** 20 Пыли."
            
        bot.edit_message_text(f"💥 **ФИНАЛ: ПОСЛЕДНЯЯ ВСПЫШКА**\n\nВы взорвали Объект Зеро вместе с собой. Угроза устранена. Ваше имя станет легендой, которую будут шепотом рассказывать кадеты.\n\n{res}", call.message.chat.id, call.message.message_id)
