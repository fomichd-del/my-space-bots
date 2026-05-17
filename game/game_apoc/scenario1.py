import telebot
from datetime import datetime
from telebot import types as tele_types
from database import get_game_status, update_game_progress, set_game_timer, add_xp

def run_scenario(bot, call):
    user_id = call.from_user.id
    username = call.from_user.first_name if call.from_user.first_name else "Док"
    current_node, timer_end = get_game_status(user_id)
    
    # Защита от пустой базы
    if current_node is None: 
        current_node = "apoc_start"

    # --- [ 1. БЕЗОПАСНЫЙ ПАРСИНГ ТАЙМЕРА (ИСПРАВЛЕНИЕ ОШИБКИ) ] ---
    if timer_end:
        # Если БД вернула время как текст, аккуратно превращаем его в объект времени
        if isinstance(timer_end, str):
            try:
                clean_time = timer_end.split('.')[0] # Отрезаем миллисекунды если есть
                timer_end = datetime.strptime(clean_time, "%Y-%m-%d %H:%M:%S")
            except:
                timer_end = None
                
        # Если время еще не вышло - блокируем и показываем алерт
        if timer_end and datetime.now() < timer_end:
            mins = int((timer_end - datetime.now()).total_seconds() // 60) + 1
            bot.answer_callback_query(call.id, f"⌛️ Процесс идет... Осталось около {mins} мин. Марти: 'Терпение!'", show_alert=True)
            return

    # ВНИМАНИЕ: Блок saved_flags полностью удален, чтобы не стирать память!

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

# --- [ ЭТАП 6: КЛАДОВАЯ (Инвентарь) ] ---
    elif call.data == "apoc_n1_pantry":
        text = ("📦 **ЭТАП 6: ЗАПАСЫ И ПЫЛЬ**\n\n"
                "Вы заходите в кладовую. Полки пусты, но за старым ящиком с надписью 'Спирт' (который, конечно, пуст) Марти находит аптечку.\n\n"
                "Марти: 'Док, тут только просроченный пластырь и... О! Флакон с йодом. В нашем мире это почти жидкое золото. "
                "Кстати, вы знали, что йод открыли случайно, когда кот химика Куртуа прыгнул на стол и разбил колбы? "
                "Надеюсь, мне не придется прыгать на ваши колбы, чтобы вы что-то открыли!'.")
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("🎒 Взять аптечку (+1 Пыль)", callback_data="apoc_n1_item_meds"),
            tele_types.InlineKeyboardButton("🚶 Идти к Верстаку", callback_data="apoc_n1_base_menu")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 7: ТРЕВОГА (Атмосфера) ] ---
    elif call.data == "apoc_n1_item_meds":
        add_xp(user_id, 1, username)
        update_game_progress(user_id, current_node + "_item_meds")
        text = ("🚨 **ЭТАП 7: СИГНАЛ ТРЕВОГИ**\n\n"
                "Как только вы взяли аптечку, в бункере завыла сирена. Датчики радиации зашкаливают. \n\n"
                "Марти: 'Док! Вентиляция засосала порцию 'свежего' воздуха с поверхности. У нас есть пара минут, пока фильтры не сдохли совсем. "
                "Нам СРОЧНО нужен костюм!'.")
        kb = tele_types.InlineKeyboardMarkup().add(tele_types.InlineKeyboardButton("🏃 Бежать к Верстаку", callback_data="apoc_n1_base_menu"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 8: ВЫБОР ИНСТРУМЕНТА (Логика) ] ---
    elif call.data == "apoc_n1_tool_choice":
        text = ("🛠 **ЭТАП 8: ВЫБОР ИНСТРУМЕНТА**\n\n"
                "На верстаке лежат два прибора: старый паяльник и лазерный скальпель.\n\n"
                "Марти: 'Док, скальпель круче, но он жрет батарею как не в себя. Паяльник надежнее. "
                "Что возьмем для тонкой работы над вашим костюмом?'.")
        kb = tele_types.InlineKeyboardMarkup(row_width=2).add(
            tele_types.InlineKeyboardButton("🔥 Паяльник (Надежность)", callback_data="apoc_n1_tool_iron"),
            tele_types.InlineKeyboardButton("⚡️ Скальпель (Скорость)", callback_data="apoc_n1_tool_laser")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 9: КАЛИБРОВКА (Мини-игра) ] ---
    elif call.data.startswith("apoc_n1_tool_"):
        text = ("📡 **ЭТАП 9: КАЛИБРОВКА СЕНСОРОВ**\n\n"
                "Инструмент в руках. Теперь нужно настроить частоту звукового модуля Марти.\n\n"
                "Марти: 'Док, настройте на частоту, кратную 3, но не больше 10. Быстрее!'.")
        kb = tele_types.InlineKeyboardMarkup(row_width=3).add(
            tele_types.InlineKeyboardButton("📟 5 Hz", callback_data="apoc_n1_calib_fail"),
            tele_types.InlineKeyboardButton("📟 9 Hz", callback_data="apoc_n1_calib_success"),
            tele_types.InlineKeyboardButton("📟 11 Hz", callback_data="apoc_n1_calib_fail")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
    
   # --- [ ЭТАП 10: ЦЕНТРАЛЬНЫЙ ОТСЕК И ТАЙНЫЙ ЛЮК ] ---
    elif call.data == "apoc_n1_base_menu":
        text = (f"🛠 **ЭТАП 10: ЦЕНТРАЛЬНЫЙ ОТСЕК**\n"
                f"──────────────────────────\n"
                f"Вы стоите в центре своего убежища. Сверху капает конденсат, а старый стоматологический кабинет деда в углу выглядит "
                f"пугающе мирно на фоне ржавых стен бункера. \n\n"
                f"Марти запрыгнул на кожаное кресло и начал интенсивно царапать пол под ним лапой: "
                f"'Док, я не хочу вас пугать, но из-под этого антикварного трона тянет холодом, как из открытого космоса. "
                f"И пахнет... старым формалином и секретами. Похоже, под нами есть еще один ярус!'.\n\n"
                f"Чтобы пробраться дальше, вам нужно решить: искать ресурсы на поверхности или спуститься в прошлое?")
        
        kb = tele_types.InlineKeyboardMarkup(row_width=1)
        kb.add(
            tele_types.InlineKeyboardButton("🕳 Спуститься в секретный подвал", callback_data="apoc_n1_secret_entry"),
            tele_types.InlineKeyboardButton("🧵 Перейти к Верстаку (Крафт)", callback_data="apoc_n1_workbench"),
            tele_types.InlineKeyboardButton("📦 Обыскать склад (Этап 1/3)", callback_data="apoc_n1_search_1"),
            tele_types.InlineKeyboardButton("🔦 Обыскать лабораторию (Этап 2/3)", callback_data="apoc_n1_search_2"),
            tele_types.InlineKeyboardButton("⬅️ Назад к входу", callback_data="apoc_start")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        update_game_progress(user_id, "apoc_n1_main_hub" + saved_flags)

# --- [ ЭТАП 10-A: ВХОД В АРХИВ-X ] ---
    elif call.data == "apoc_n1_secret_entry":
        text = ("📉 **ЭТАП 10-A: ЛОГИЧЕСКИЙ ЗАМОК**\n\n"
                "Вы отодвигаете кресло. Под ним — люк из титанового сплава. На панели ввода всего две цифры. \n\n"
                "Марти: 'Док, тут гравировка на латыни. *Dentes*... это зубы! И дата... 1985. "
                "Подсказка гласит: Число зубов взрослого человека минус последние две цифры года, когда этот кабинет был запечатан'.\n\n"
                "**МАРТИ:** 'Док, вы же профи! 32 зуба минус... сколько там было? Шевелите извилинами!'")
        
        # Загадка: 32 - 85 = -53 (берем 53)
        kb = tele_types.InlineKeyboardMarkup(row_width=2).add(
            tele_types.InlineKeyboardButton("⌨️ 32", callback_data="apoc_n1_secret_fail"),
            tele_types.InlineKeyboardButton("⌨️ 53", callback_data="apoc_n1_secret_hall"),
            tele_types.InlineKeyboardButton("⌨️ 13", callback_data="apoc_n1_secret_fail"),
            tele_types.InlineKeyboardButton("⌨️ 85", callback_data="apoc_n1_secret_fail")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    elif call.data == "apoc_n1_secret_fail":
        bot.answer_callback_query(call.id, "🚫 НЕВЕРНЫЙ КОД. Попробуйте еще раз!", show_alert=True)
        return

    # --- [ ЭТАП 10-B: СЕКРЕТНЫЙ КАБИНЕТ ] ---
    elif call.data == "apoc_n1_secret_hall":
        add_xp(user_id, 10, username)
        text = ("🦷 **ЭТАП 10-B: ЗАПРЕТНАЯ ЗОНА**\n\n"
                "Люк открывается с пневматическим шипением. Вы спускаетесь в идеально чистую комнату. "
                "Здесь хранятся прототипы инструментов, которые опередили свое время на десятилетия.\n\n"
                "Марти замер у шкафа: 'Док, посмотрите на этот мотор для бормашины. Он выдает 500 тысяч оборотов в минуту. "
                "Если мы вставим его в мой сканер, я смогу различать молекулы на расстоянии километра!'.")
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("⚙️ Снять мотор (Улучшение сканера)", callback_data="apoc_n1_secret_motor"),
            tele_types.InlineKeyboardButton("📂 Открыть папку 'Мариуполь-85'", callback_data="apoc_n1_secret_files"),
            tele_types.InlineKeyboardButton("🧗 Вернуться наверх", callback_data="apoc_n1_base_menu")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 10-C: СЕКРЕТНЫЕ ФАЙЛЫ ] ---
    elif call.data == "apoc_n1_secret_files":
        update_game_progress(user_id, current_node + "_clue_files")
        text = ("📜 **ЭТАП 10-C: ТАЙНЫЙ ОТЧЕТ**\n\n"
                "В папке лежит рентгеновский снимок. На нем запечатлена челюсть, полностью заросшая фиолетовыми кристаллами. \n\n"
                "Марти читает подпись: 'Заражение произошло через пломбу из метеоритного железа. Пациент номер ноль'. \n\n"
                "Док, ваш дед первым обнаружил этот вирус еще в 1985-м в Мариуполе! И Академия Орион знала об этом... Они следили за ним'.")
        kb = tele_types.InlineKeyboardMarkup().add(tele_types.InlineKeyboardButton("🔙 Назад к инструментам", callback_data="apoc_n1_secret_hall"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 10-D: ЛЕГЕНДАРНЫЙ МОТОР ] ---
    elif call.data == "apoc_n1_secret_motor":
        update_game_progress(user_id, current_node + "_item_super_motor")
        text = ("✅ **ЭТАП 10-D: ЛЕГЕНДАРНЫЙ ТРОФЕЙ**\n\n"
                "Вы бережно извлекаете мотор. Это настоящее сокровище старого мира.\n\n"
                "Марти: 'Теперь я не просто той-пудель, я — стратегический радар! Док, с этой штукой мы "
                "скрафтим сканер гораздо быстрее!'.\n\n"
                "🎁 **БОНУС:** Таймеры крафта сокращены на 5 минут!")
        kb = tele_types.InlineKeyboardMarkup().add(tele_types.InlineKeyboardButton("🧗 Вернуться в хаб", callback_data="apoc_n1_base_menu"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
    
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

    # --- [ ЭТАП 16: ТЕХНИЧЕСКИЙ ШЛЮЗ ] ---
    elif call.data == "apoc_n1_search_2":
        text = (f"🚿 **ЭТАП 16: ТЕХНИЧЕСКИЙ УЗЕЛ**\n\n"
                f"Вы пробираетесь через старый блок дезинфекции. Под ногами хрустит битое стекло. На кафеле — свежие фиолетовые лужи.\n\n"
                f"Марти: 'Док, это не просто грязь. Это питательная среда 'Фиолетовый Реагент'. Ее использовали в НИИ для ускорения роста клеток. "
                f"Запах... как в стоматологии, только с примесью гнили. Смотрите, на двери — отпечаток ладони. Он свежий!'.")
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("🧬 Взять пробу жидкости", callback_data="apoc_n1_clue_liquid"),
            tele_types.InlineKeyboardButton("❄️ Дверь в лабораторию (Этап 17)", callback_data="apoc_n1_frozen_door"),
            tele_types.InlineKeyboardButton("🔙 В центральный отсек", callback_data="apoc_n1_base_menu")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    elif call.data == "apoc_n1_clue_liquid":
        if "_clue_liquid" not in current_node:
            add_xp(user_id, 3, username)
            update_game_progress(user_id, current_node + "_clue_liquid")
            msg = "✅ **УЛИКА:** Фиолетовый био-реагент. Это среда для выращивания 'Умного Мха'.\n\n"
        else: msg = "📦 Проба уже взята.\n\n"
        kb = tele_types.InlineKeyboardMarkup().add(tele_types.InlineKeyboardButton("🔙 Назад", callback_data="apoc_n1_search_2"))
        bot.edit_message_text(msg + "Марти: 'Кажется, наш вор — биолог. Или очень умный мутант'.", call.message.chat.id, call.message.message_id, reply_markup=kb)

    # --- [ ЭТАП 17: ЗАМЕРЗШАЯ ДВЕРЬ ] ---
    elif call.data == "apoc_n1_frozen_door":
        text = ("❄️ **ЭТАП 17: ЛЕДЯНОЙ ЗАМОК**\n\n"
                "Дверь в лабораторию покрыта инеем. Система охлаждения дала сбой, и механизм намертво заклинило.\n\n"
                "Марти: 'Док, если мы дернем — сломаем ручку. Помните, мы нашли флакон с йодом в кладовой? "
                "Если смешать его с остатками спирта в замке, произойдет реакция с выделением тепла. Пробуем?'.")
        kb = tele_types.InlineKeyboardMarkup(row_width=1)
        if "_item_meds" in current_node:
            kb.add(tele_types.InlineKeyboardButton("🧪 Использовать Йод из аптечки", callback_data="apoc_n1_melt_success"))
        else:
            kb.add(tele_types.InlineKeyboardButton("🔥 Пытаться отогреть руками (Риск)", callback_data="apoc_n1_melt_fail"))
        kb.add(tele_types.InlineKeyboardButton("🔙 Назад", callback_data="apoc_n1_search_2"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 18: ТЕНЬ В ТЕМНОТЕ ] ---
    elif call.data == "apoc_n1_melt_success":
        text = ("👥 **ЭТАП 18: ТЕНЬ В ТЕМНОТЕ**\n\n"
                "Лед зашипел и стаял. Дверь со стоном открылась. В глубине лаборатории вы видите... фигуру человека. Он стоит спиной к вам и что-то ищет в шкафах.\n\n"
                "Марти (шепотом): 'Док... я не чую тепла. Это не человек. Это либо старая голограмма, либо... Тс-с-с! Он оборачивается!'.")
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("🎤 Окликнуть: 'Кто здесь?'", callback_data="apoc_n1_shadow_talk"),
            tele_types.InlineKeyboardButton("🤫 Подкрасться ближе", callback_data="apoc_n1_shadow_sneak")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 19: УЛИКА: МАСКА ] ---
    elif call.data == "apoc_n1_shadow_talk":
        update_game_progress(user_id, current_node + "_clue_mask")
        text = ("👤 **ЭТАП 19: ПУСТОТА**\n\n"
                "Вы выкрикиваете имя, но фигура рассыпается облаком пыли. Это была запись системы безопасности. \n\n"
                "На полу, там где стоял призрак, вы находите маску Академии Орион. \n\n"
                "Марти: 'Док, Академия была здесь недавно. Они что-то забрали из сейфа вашего деда. Нам нужно в вентиляцию, чтобы догнать их!'.")
        kb = tele_types.InlineKeyboardMarkup().add(tele_types.InlineKeyboardButton("🏃 Прыгнуть в вентиляцию (Этап 20)", callback_data="apoc_n1_vent_enter"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
    
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

# --- [ ЭТАП 21: ВЕРТИКАЛЬНЫЙ ПОДЪЕМ ] ---
    elif call.data == "apoc_n1_stealth_success":
        text = ("🧗 **ЭТАП 21: ВЕРТИКАЛЬНЫЙ ПРЕДЕЛ**\n\n"
                "Дрон остался позади. Вы выходите в шахту грузового лифта. Трос оборван, нужно лезть вверх по ржавым скобам прямо над пропастью.\n\n"
                "Марти: 'Я запрыгну к вам в рюкзак. Только не смотрите вниз, Док, я не хочу, чтобы мой последний вид был кучей мусора на дне шахты!'.")
        kb = tele_types.InlineKeyboardMarkup().add(tele_types.InlineKeyboardButton("🧗 Лезть вверх (Этап 22)", callback_data="apoc_n1_climb"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 22: КАМЕРА СЛЕЖЕНИЯ ] ---
    elif call.data == "apoc_n1_climb":
        text = ("👁 **ЭТАП 22: ГЛАЗ АКАДЕМИИ**\n\n"
                "На уровне 3-го этажа вы замираете. Прямо перед вашим лицом — скрытая камера. Ее линза поворачивается, фокусируясь на вас.\n\n"
                "Марти: 'Нас засекли! Нужно отключить ее, пока сигнал не ушел на сервер Академии. Перережьте кабель!'.")
        kb = tele_types.InlineKeyboardMarkup(row_width=2).add(
            tele_types.InlineKeyboardButton("✂️ Синий провод (Данные)", callback_data="apoc_n1_cam_success"),
            tele_types.InlineKeyboardButton("✂️ Красный провод (Питание)", callback_data="apoc_n1_cam_fail")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 23: ПАРОВОЙ ПРОРЫВ ] ---
    elif call.data == "apoc_n1_cam_success":
        text = ("💨 **ЭТАП 23: ГОРЯЧИЙ ПРИЕМ**\n\n"
                "Камера ослепла, но в этот момент из лопнувшей трубы рядом вырывается струя раскаленного пара! Путь перекрыт.\n\n"
                "Марти: 'Док, вентиль справа! Его заклинило, нужно приложить всю силу!'.")
        kb = tele_types.InlineKeyboardMarkup().add(tele_types.InlineKeyboardButton("⚙️ Крутить вентиль (Этап 24)", callback_data="apoc_n1_valve_turn"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 24: РЖАВЫЙ РЫЧАГ ] ---
    elif call.data == "apoc_n1_valve_turn":
        text = ("🏗 **ЭТАП 24: РЫЧАГ СУДЬБЫ**\n\n"
                "Пар утих. Вы стоите перед дверью в генераторную. Огромный рычаг блокировки заржавел намертво.\n\n"
                "Марти: 'Помните тот медный кабель со смазкой, который мы нашли в начале? Он весь в машинном масле! Это наш шанс!'.")
        kb = tele_types.InlineKeyboardMarkup(row_width=1)
        if "_clue_wire" in current_node:
            kb.add(tele_types.InlineKeyboardButton("💧 Смазать рычаг маслом (Успех)", callback_data="apoc_n1_generator_room"))
        else:
            kb.add(tele_types.InlineKeyboardButton("🔨 Ударить ломом (Шум привлечет врагов)", callback_data="apoc_n1_gen_noise"))
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

# --- [ ЭТАП 26: ЗАШИФРОВАННЫЙ КАНАЛ (Детектив) ] ---
    elif call.data == "apoc_n1_decode_radio":
        text = ("📟 **ЭТАП 26: ПРИЗРАКИ В ЭФИРЕ**\n\n"
                "После запуска генератора старая радиостанция на стене внезапно ожила. Сквозь треск слышен голос.\n\n"
                "Голос: '...объект 85-Мариуполь... протокол выполнен... мы уходим в ТЦ...'.\n\n"
                "Марти: 'Док, это старая запись. Но смотрите на частоту — она заблокирована программно. "
                "Тот, кто был здесь до нас, пытался скрыть это сообщение от Академии. Кажется, ваш дед оставил этот 'хвост' специально для вас'.")
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("📡 Сканировать частоту (Опыт)", callback_data="apoc_n1_clue_radio"),
            tele_types.InlineKeyboardButton("🧗 Искать выход к лестнице", callback_data="apoc_n1_stairwell")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 27: ПЕРЕХОД (Логика/Крафт) ] ---
    elif call.data == "apoc_n1_stairwell":
        text = ("🪜 **ЭТАП 27: ВЕРТИКАЛЬНЫЙ ПРЕДЕЛ**\n\n"
                "Лестница на крышу заблокирована обвалом. Единственный путь — технический лифт, но у него перегорел предохранитель.\n\n"
                "Марти: 'Док, я могу замкнуть контакты своим жилетом, но меня может слегка... поджарить. "
                "Или вы можете попробовать собрать перемычку из того медного кабеля, который мы нашли в начале главы'.")
        kb = tele_types.InlineKeyboardMarkup(row_width=1)
        if "_clue_wire" in current_node:
            kb.add(tele_types.InlineKeyboardButton("🛠 Использовать кабель из улик", callback_data="apoc_n1_lift_fix"))
        else:
            kb.add(tele_types.InlineKeyboardButton("🐕 Рискнуть Марти (Плохо для отношений)", callback_data="apoc_n1_marty_risk"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 28: ЛИФТ (Шутки Марти) ] ---
    elif call.data == "apoc_n1_lift_fix":
        text = ("🏗 **ЭТАП 28: ПОДЪЕМ**\n\n"
                "Лифт со скрипом тронулся. Вы медленно ползете вверх сквозь этажи разрушенного НИИ. В щели видны заброшенные лаборатории.\n\n"
                "Марти: 'Знаете, Док, в книгах по истории писали, что раньше в лифтах играла музыка. "
                "Я бы сейчас не отказался от чего-нибудь бодрого. Но вместо этого у нас только скрежет металла и запах вашей немытой головы. "
                "Кстати, вы знали, что пудели не потеют? Мы идеальные существа для постапокалипсиса!'.")
        kb = tele_types.InlineKeyboardMarkup().add(tele_types.InlineKeyboardButton("👀 Осмотреться в шахте", callback_data="apoc_n1_shaft_secret"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 29: СЕКРЕТ В ШАХТЕ (Скрытая улика) ] ---
    elif call.data == "apoc_n1_shaft_secret":
        add_xp(user_id, 5, username)
        update_game_progress(user_id, current_node + "_secret_found")
        text = ("💎 **ЭТАП 29: ТАЙНИК ЗА СТЕНКОЙ**\n\n"
                "Лифт застрял на секунду, и вы заметили в стене шахты нишу. Там лежит старая стоматологическая аптечка вашего деда.\n\n"
                "Внутри — **Антисептик 'Орион'**. Это мощное средство, которое позволит нам лечить раны во 2-й главе.\n\n"
                "Марти: 'Ого! Дед знал, где прятать заначки. Теперь мы точно не загнемся от первой же царапины мутанта!'.")
        kb = tele_types.InlineKeyboardMarkup().add(tele_types.InlineKeyboardButton("🚀 Выйти на крышу", callback_data="apoc_n1_final_ascent"))
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

    # Результаты финала главы 1
    elif call.data == "apoc_n1_end_power":
        if "apoc_ch1_done" not in current_node:
            add_xp(user_id, 50, username)
            # ВАЖНО: Добавляем флаг к текущему прогрессу (current_node + ...)
            update_game_progress(user_id, current_node + "_apoc_ch1_done_power")
        bot.edit_message_text("🦾 **ФИНАЛ: ПУТЬ СИЛЫ**...", call.message.chat.id, call.message.message_id)

    elif call.data == "apoc_n1_end_knowledge":
        if "apoc_ch1_done" not in current_node:
            add_xp(user_id, 100, username) 
            update_game_progress(user_id, current_node + "_apoc_ch1_done_knowledge")
        bot.edit_message_text("🧠 **ФИНАЛ: ПУТЬ ЗНАНИЯ**...", call.message.chat.id, call.message.message_id)

# --- ФУНКЦИЯ КРАФТА (УСЛОЖНЕННАЯ) ---
def handle_craft(bot, call):
    user_id = call.from_user.id
    current_node, _ = get_game_status(user_id)
    
    # ПРОВЕРКА БОНУСА (Мотор из подвала)
    time_needed = 20
    if "_item_super_motor" in current_node:
        time_needed = 12 # Существенное ускорение!
        bonus_text = "⚡️ Благодаря мотору из кабинета деда, работа идет в два раза быстрее!"
    else:
        bonus_text = "🔧 Обычные инструменты работают медленно, но верно."

    if "suit" in call.data:
        set_game_timer(user_id, time_needed)
        update_game_progress(user_id, current_node + "_suit_fixed")
        msg = (f"⚒ **ИДЕТ КРАФТ КОСТЮМА**\n\n"
               f"{bonus_text}\n\n"
               f"Марти подбадривает: 'Док, еще немного, и вы будете выглядеть как настоящий герой пустошей!'.\n\n"
               f"Готовность через **{time_needed} минут**.")
        bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, parse_mode="Markdown")
