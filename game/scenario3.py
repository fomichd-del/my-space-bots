import telebot
from datetime import datetime, timedelta
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
        bot.answer_callback_query(call.id, f"⏳ Марти просил не беспокоить. Готовность через {mins} мин.", show_alert=True)
        return

    # 2. УМНЫЙ СТАРТ (Точки восстановления)
    if call.data == "game3_start":
        # Если игрок уже в 3 главе, возвращаем его на место
        if current_node and current_node.startswith("ch3_") and current_node != "ch3_start":
            text = (f"🛰 **СЕАНС СВЯЗИ: ГЛАВА 3**\n\n"
                    f"Пилот {username}, вы находитесь в секторе: `{current_node}`.\n"
                    f"Марти готов продолжать. Прыгаем?")
            kb = tele_types.InlineKeyboardMarkup(row_width=1)
            
            if "wait" in current_node: kb.add(tele_types.InlineKeyboardButton("🔄 Проверить готовность", callback_data="game3_check_jump"))
            elif "scan" in current_node: kb.add(tele_types.InlineKeyboardButton("🔄 Результаты сканера", callback_data="game3_check_scan"))
            elif "search" in current_node: kb.add(tele_types.InlineKeyboardButton("🔍 Продолжить обыск", callback_data="game3_search_hub"))
            else: kb.add(tele_types.InlineKeyboardButton("🚀 Продолжить миссию", callback_data="game3_node_arrival"))
            
            kb.add(tele_types.InlineKeyboardButton("♻️ Сбросить Главу 3", callback_data="game3_reset"))
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
            return

        # --- ЭТАП 1: МУЛЬТИ-СТАРТ (Зависит от финала 2 главы) ---
        kb = tele_types.InlineKeyboardMarkup(row_width=1)
        
        if "ch2_done_hero" in current_node:
            start_text = (f"🌟 **ЭТАП 1: ПУТЬ АГЕНТА**\n\n"
                         f"Вы — национальный герой Академии. Вам выделили новый 'Стриж-4' и "
                         f"отправили на край системы к маяку 'Эхо-Прайм'.\n\n"
                         f"Марти (в новом ошейнике): 'Хозяин, я чувствую себя важной персоной! "
                         f"Но этот сигнал... он идет из самого центра Пустоты. Нам нужно проверить маяк'.")
            kb.add(tele_types.InlineKeyboardButton("🛰 Лететь к маяку", callback_data="game3_node_prejump"))
            
        elif "ch2_done_escape" in current_node:
            start_text = (f"🏴 **ЭТАП 1: ПУТЬ ИЗГОЯ**\n\n"
                         f"Вы в бегах. Челнок дымит, топливо на исходе. Вы скрываетесь в астероидном поясе.\n\n"
                         f"Марти (ворчливо): 'Хозяин, я питаюсь от батарейки фонарика! Нам нужно "
                         f"найти заброшенную базу, чтобы не замерзнуть. Мои датчики поймали сигнал... "
                         f"такой же, как на Авалоне'.")
            kb.add(tele_types.InlineKeyboardButton("☄️ Искать укрытие", callback_data="game3_node_prejump"))
            
        else: # ch2_done_normal или ошибка
            start_text = (f"⛓ **ЭТАП 1: ПУТЬ УЗНИКА**\n\n"
                         f"Вас везут в тюремном транспорте. Но внезапно станция содрогается, "
                         f"система охраны отключается, а ваша камера открывается.\n\n"
                         f"Марти (вылезая из сумки охранника): 'Псс! Хозяин! Я украл ключи! "
                         f"Бежим к ангару, пока этот странный сигнал сводит с ума охрану!'")
            kb.add(tele_types.InlineKeyboardButton("🏃 Бежать к ангару", callback_data="game3_node_prejump"))

        bot.edit_message_text(start_text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        update_game_progress(user_id, "ch3_start")

    elif call.data == "game3_reset":
        update_game_progress(user_id, "ch3_done_hero") # Временно возвращаем статус для теста
        bot.answer_callback_query(call.id, "Журнал обнулен.")
        run_scenario(bot, type('obj', (object,), {'from_user': call.from_user, 'data': 'game3_start', 'message': call.message}))

    # --- ЭТАП 2: ЗАГАДКА (Ремонт/Взлом) ---
    elif call.data == "game3_node_prejump":
        text = (f"⚙️ **ЭТАП 2: КРИТИЧЕСКИЙ УЗЕЛ**\n\n"
                f"Для совершения прыжка (или побега) нужно соединить нейросеть Марти с кораблем. \n"
                f"Марти: 'Хозяин, тут три гнезда: Альфа, Бета и Гамма. Если перепутаем — мой хвост превратится в антенну!'\n\n"
                f"Подсказка: Цвет маяка был фиолетовым. В спектре это сумма Синего и Красного.")
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("🧩 Соединить Бета (Синий + Красный)", callback_data="game3_node_jump_wait"),
            tele_types.InlineKeyboardButton("🧩 Соединить Альфа (Зеленый)", callback_data="game3_node_fail_puzzle")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        update_game_progress(user_id, "ch3_puzzle")

    elif call.data == "game3_node_fail_puzzle":
        bot.answer_callback_query(call.id, "💥 Искры из глаз! Марти недовольно тявкает. Попробуй еще раз.", show_alert=True)
        return

    # --- ЭТАП 3: ТАЙМЕР 20 МИН ---
    elif call.data == "game3_node_jump_wait":
        set_game_timer(user_id, 20)
        text = (f"🚀 **ЭТАП 3: ПРЫЖОК В НЕИЗВЕСТНОСТЬ**\n\n"
                f"Двигатели завыли. Пространство начало сжиматься.\n\n"
                f"— Хозяин, — Марти устроился на коленях. — Прыжок через Пустоту займет **20 минут**. "
                f"Я пока просканирую кассету, которую мы нашли во 2 главе. Отдохните.")
        kb = tele_types.InlineKeyboardMarkup().add(tele_types.InlineKeyboardButton("🔄 Проверить выход из гиперпространства", callback_data="game3_check_jump"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        update_game_progress(user_id, "ch3_jump_wait")

    elif call.data == "game3_check_jump":
        text = (f"✨ **ВЫХОД ИЗ ГИПЕРА**\n\n"
                f"Звезды снова стали точками. Перед вами — станция 'Стикс-9'. Она выглядит мертвой, "
                f"но всё её освещение горит странным фиолетовым светом.")
        kb = tele_types.InlineKeyboardMarkup().add(tele_types.InlineKeyboardButton("🚢 Стыковаться", callback_data="game3_node_arrival"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        update_game_progress(user_id, "ch3_arrival")

    # --- ЭТАП 4-6: ПОИСК УЛИК (+1 Пыль за каждый) ---
    elif call.data == "game3_node_arrival":
        text = (f"🏚 **ЭТАП 4: МЕРТВЫЙ ХАБ**\n\n"
                f"Вы внутри станции. Повсюду парят чашки с кофе и забытые личные вещи. \n"
                f"Марти: 'Тут никого нет... уже несколько дней. Но я чувствую, что за нами наблюдают "
                f"через камеры'. \n\n"
                f"Может, осмотримся в поисках ресурсов?")
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("🗄 Обыскать шкафчики", callback_data="game3_search_locker"),
            tele_types.InlineKeyboardButton("☕️ Проверить столовую", callback_data="game3_search_canteen"),
            tele_types.InlineKeyboardButton("🚧 Идти к Главному Компьютеру", callback_data="game3_node_horrorevent")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        update_game_progress(user_id, "ch3_hub_search")

    elif call.data == "game3_search_locker":
        if "item_stars" not in current_node:
            add_xp(user_id, 1, username); update_game_progress(user_id, current_node + "_item_stars")
            msg = "✅ **НАЙДЕНО:** Карта звезд 'Стикса' (+1 Пыль).\n\n"
        else: msg = "Тут только старая форма.\n\n"
        kb = tele_types.InlineKeyboardMarkup().add(tele_types.InlineKeyboardButton("🔙 Назад", callback_data="game3_node_arrival"))
        bot.edit_message_text(msg + "Эта карта поможет не заблудиться.", call.message.chat.id, call.message.message_id, reply_markup=kb)

    elif call.data == "game3_search_canteen":
        if "item_cup" not in current_node:
            add_xp(user_id, 1, username); update_game_progress(user_id, current_node + "_item_cup")
            msg = "✅ **НАЙДЕНО:** Старая кружка с паролем (+1 Пыль).\n\n"
        else: msg = "Кофе-машина сломана.\n\n"
        kb = tele_types.InlineKeyboardMarkup().add(tele_types.InlineKeyboardButton("🔙 Назад", callback_data="game3_node_arrival"))
        bot.edit_message_text(msg + "На дне кружки выцарапано: '8811'.", call.message.chat.id, call.message.message_id, reply_markup=kb)

    # --- ЭТАП 7: СТРАХ ---
    elif call.data == "game3_node_horrorevent":
        text = (f"😱 **ЭТАП 7: ТЕНЬ В ОТРАЖЕНИИ**\n\n"
                f"Вы проходите мимо зеркальной стены. Ваше отражение внезапно ОСТАНАВЛИВАЕТСЯ, "
                f"пока вы продолжаете идти. Отражение улыбается и прикладывает палец к губам.\n\n"
                f"Марти вздыбил шерсть: 'Х-хозяин... вы это видели? Сканеры говорят, что в комнате "
                f"только мы. Но я слышу, как кто-то дышит вам прямо в затылок...'")
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("🔦 Резко обернуться и включить свет", callback_data="game3_node_scare_fail"),
            tele_types.InlineKeyboardButton("🧘 Сохранять спокойствие и идти дальше", callback_data="game3_node_scan_start")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        update_game_progress(user_id, "ch3_scare_event")

    elif call.data == "game3_node_scare_fail":
        bot.answer_callback_query(call.id, "👻 Вспышка света! Вы видите бледное лицо, которое мгновенно растворяется в воздухе. Сердце бешено колотится.", show_alert=True)
        run_scenario(bot, type('obj', (object,), {'from_user': call.from_user, 'data': 'game3_node_scan_start', 'message': call.message}))

    # --- ЭТАП 8: ТАЙМЕР 30 МИН ---
    elif call.data == "game3_node_scan_start":
        set_game_timer(user_id, 30)
        text = (f"🖥 **ЭТАП 8: ГЛУБОКОЕ СКАНИРОВАНИЕ**\n\n"
                f"Вы добрались до терминала. Нужно просканировать всю станцию на наличие 'Земного вируса'.\n\n"
                f"Марти: 'Это займет **30 минут**. Я заблокирую двери. Давайте пока изучим "
                f"тот дневник, который мы нашли'. \n\n"
                f"В тишине станции слышны шаги... сверху.")
        kb = tele_types.InlineKeyboardMarkup().add(tele_types.InlineKeyboardButton("🔄 Проверить результаты сканера", callback_data="game3_check_scan"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        update_game_progress(user_id, "ch3_scan_wait")

    elif call.data == "game3_check_scan":
        text = (f"✅ **СКАН ЗАВЕРШЕН**\n\n"
                f"Источник сигнала не на станции. Он ВНУТРИ АСТЕРОИДА, к которому пристроена станция. "
                f"Там находится древний объект. Академия называет его 'Колыбель'.")
        kb = tele_types.InlineKeyboardMarkup().add(tele_types.InlineKeyboardButton("🕵️ Спуститься в шахты", callback_data="game3_node_mines"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        update_game_progress(user_id, "ch3_scan_done")

    # --- ЭТАП 9-11: ШАХТЫ И ЗАГАДКА ---
    elif call.data == "game3_node_mines":
        text = (f"⛏ **ЭТАП 9: ШАХТЫ СУДЬБЫ**\n\n"
                f"Стены шахт покрыты светящимся мхом. Он пульсирует в ритме вашего сердца. \n\n"
                f"Марти нашел старую сумку рабочего. Посмотрим?")
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("🎒 Обыскать сумку", callback_data="game3_item_wires"),
            tele_types.InlineKeyboardButton("🚪 К странной двери", callback_data="game3_node_final_gate")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    elif call.data == "game3_item_wires":
        if "wires" not in current_node:
            add_xp(user_id, 1, username); update_game_progress(user_id, current_node + "_wires")
            msg = "✅ **НАЙДЕНО:** Золотые провода (+1 Пыль).\n\n"
        else: msg = "Тут пусто.\n\n"
        kb = tele_types.InlineKeyboardMarkup().add(tele_types.InlineKeyboardButton("🚪 К двери", callback_data="game3_node_final_gate"))
        bot.edit_message_text(msg + "Эти провода отлично проводят нейро-сигналы.", call.message.chat.id, call.message.message_id, reply_markup=kb)

    # --- ЭТАП 12-14: ЗАГАДКА ДВЕРИ ---
    elif call.data == "game3_node_final_gate":
        text = (f"🗿 **ЭТАП 12: ДВЕРЬ КОЛЫБЕЛИ**\n\n"
                f"Перед вами огромная дверь из неизвестного черного металла. \n"
                f"Голос из динамика (Веклер?!): 'Пилот, если введешь код с кружки, ты откроешь Пандору'.\n\n"
                f"Марти: 'Хозяин, я чувствую, что Веклер (или то, что от него осталось) где-то рядом. Вводим код?'")
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("🔢 Ввести 8811", callback_data="game3_node_gate_open"),
            tele_types.InlineKeyboardButton("🔢 Ввести 0000", callback_data="game3_node_fail_puzzle")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        update_game_progress(user_id, "ch3_gate")

    # --- ЭТАП 15: ИНТРИГА И ПРЕДАТЕЛЬСТВО ---
    elif call.data == "game3_node_gate_open":
        text = (f"🔓 **ЭТАП 15: ВНУТРИ КОЛЫБЕЛИ**\n\n"
                f"Дверь разошлась. В центре зала парит Огромный Кристалл. \n"
                f"Из тени выходит фигура. Это... ВЫ сами, но в форме Адмирала Земли.\n\n"
                f"— Привет, — говорит двойник. — Я — это ты через 10 лет. Сигнал с Земли "
                f"это не вирус. Это твоя собственная память, посланная назад во времени, "
                f"чтобы остановить Академию.")
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("🤝 Поверить двойнику", callback_data="game3_end_twist_good"),
            tele_types.InlineKeyboardButton("🔫 Выстрелить в кристалл", callback_data="game3_end_twist_bad"),
            tele_types.InlineKeyboardButton("🐕 Спросить совета у Марти", callback_data="game3_end_marty_logic")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        update_game_progress(user_id, "ch3_climax")

    # --- ЭТАП 16-18: ФИНАЛЫ И ПОДАРКИ ---
    elif call.data == "game3_end_marty_logic":
        text = (f"🐕 Марти: 'Хозяин, его ДНК совпадает с вашим на 100%, но его сердце... "
                f"оно механическое. Это не вы. Это ИИ Земли, который хочет нас использовать'.")
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("🔫 Выстрелить в кристалл", callback_data="game3_end_twist_bad"),
            tele_types.InlineKeyboardButton("🤝 Рискнуть и объединиться", callback_data="game3_end_twist_good")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    elif call.data == "game3_end_twist_bad":
        if "done" not in current_node:
            add_xp(user_id, 70, username); update_game_progress(user_id, "ch3_done_true_end")
            res = "💰 Награда: **70 Пыли** (Истинный финал)."
        else: res = "✨ Награда получена."
        bot.edit_message_text(f"💥 **ФИНАЛ: ПАДЕНИЕ БОГОВ**\n\nКристалл разлетелся в пыль. Двойник исчез. \n"
                              f"Вы разорвали временную петлю. Теперь будущего не существует, и вы сами его напишете.\n\n{res}", call.message.chat.id, call.message.message_id)

    elif call.data == "game3_end_twist_good":
        if "done" not in current_node:
            add_xp(user_id, 30, username); update_game_progress(user_id, "ch3_done_twist_end")
            res = "💰 Награда: **30 Пыли** (Спорный финал)."
        else: res = "✨ Награда получена."
        bot.edit_message_text(f"🤝 **ФИНАЛ: СОЮЗ ДВУХ МИРОВ**\n\nВы объединились с двойником. Академия пала, "
                              f"но Земля теперь контролирует ваш разум. Вы стали Адмиралом, но потеряли свободу.\n\n{res}", call.message.chat.id, call.message.message_id)
