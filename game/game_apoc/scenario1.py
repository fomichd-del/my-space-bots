import telebot
from datetime import datetime
from telebot import types as tele_types
from database import (
    get_game_status, set_game_node, reset_game, set_game_timer, add_xp, 
    has_completed_chapter, mark_chapter_completed, is_timer_expired
)

def run_scenario(bot, call):
    user_id = call.from_user.id
    username = call.from_user.first_name if call.from_user.first_name else "Док"
    
    # 🔴 --- [ ПРИНУДИТЕЛЬНЫЙ СБРОС - ДОЛЖЕН БЫТЬ ПЕРВЫМ ] --- 🔴
    if call.data == "game_reset_all":
        reset_game(user_id, "apoc_start") # Очищаем базу
        set_game_timer(user_id, 0)
        
        # Подменяем call.data, чтобы код ниже поймал старт игры
        call.data = "apoc_start" 
        
        try: 
            bot.answer_callback_query(call.id, "🔄 Система очищена. Перезапуск...", show_alert=True)
        except: 
            pass
            
        # ❌ УДАЛЯЕМ строку: return run_scenario(bot, call)
        # Код просто пойдет дальше вниз!

    # 1. Получаем статус из базы (он подтянет свежеиспеченный apoc_start)
    raw_node, timer_end = get_game_status(user_id)
    if not raw_node: raw_node = "apoc_start"
        
    print(f"DEBUG: User {user_id} current_node: {raw_node}, timer: {timer_end}")
    
    # --- [ АБСОЛЮТНАЯ ЗАЩИТА ТАЙМЕРА ] ---
    if call.data not in ["apoc_s1_start", "resume_game", "game_reset_all", "game_main_menu"]:
        if not is_timer_expired(user_id):
            try: bot.answer_callback_query(call.id, "⌛️ Объект заблокирован. Ожидайте завершения процесса!", show_alert=True)
            except: pass
            return

    # --- ЛОКАЛЬНЫЕ ПОМОЩНИКИ ---
    def get_loc(node_str): return node_str.split('|')[0]
    def has_flag(node_str, flag): return f"|{flag}" in node_str or flag in node_str.split('|')[1:]
    def add_flag(node_str, flag): return node_str if has_flag(node_str, flag) else f"{node_str}|{flag}"
    def set_loc(node_str, new_loc):
        parts = node_str.split('|')
        parts[0] = new_loc
        return '|'.join(parts)

    current_node = raw_node
    loc = get_loc(current_node)

    # 🟢 --- [ ВХОД В ИГРУ И УМНОЕ МЕНЮ ] --- 🟢
    if call.data == "apoc_s1_start":
        if loc in ["apoc_start", "start"]:
            call.data = "apoc_start"
        elif loc == "apoc_ch1_completed_screen":
            call.data = "apoc_ch1_completed_screen"
        else:
            text = "🔙 *ВОЗВРАЩЕНИЕ В БУНКЕР*\nКомандор, вы остановились на этапе выживания. Что делаем?"
            kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
                tele_types.InlineKeyboardButton("▶️ Продолжить игру", callback_data="resume_game"),
                tele_types.InlineKeyboardButton("🔄 Сбросить и начать заново", callback_data="game_reset_all"),
                tele_types.InlineKeyboardButton("🔙 В меню Хаба", callback_data="game_main_menu")
            )
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
            return

    if call.data == "resume_game":
        call.data = loc
        try: bot.answer_callback_query(call.id, "🔄 Сохранение загружено!")
        except: pass

    # 💾 --- [ АВТОСОХРАНЕНИЕ КОМНАТЫ ] --- 💾
    MAJOR_NODES = [
        "apoc_start", "apoc_n1_investigate", "apoc_n1_pc_check", "apoc_n1_pantry",
        "apoc_n1_tool_choice", "apoc_n1_base_menu", "apoc_n1_secret_entry",
        "apoc_n1_secret_hall", "apoc_n1_secret_files", "apoc_n1_workbench", 
        "apoc_n1_search_1", "apoc_n1_search_2", "apoc_n1_frozen_door", 
        "apoc_n1_melt_success", "apoc_n1_vent_enter", "apoc_n1_stealth_success", 
        "apoc_n1_climb", "apoc_n1_valve_turn", "apoc_n1_generator_room", 
        "apoc_n1_decode_radio", "apoc_n1_stairwell", "apoc_n1_lift_fix", 
        "apoc_n1_final_ascent", "apoc_ch1_completed_screen", "apoc_n1_res_1"
    ]
    if call.data in MAJOR_NODES:
        current_node = set_loc(current_node, call.data)
        set_game_node(user_id, current_node)
        loc = call.data

    # 🏆 --- [ ЭКРАН ЗАВЕРШЕННОЙ ГЛАВЫ ] --- 🏆
    if call.data == "apoc_ch1_completed_screen":
        text = (f"🏆 **ГЛАВА 1: ПРОЙДЕНА**\n"
                f"──────────────────────────\n"
                f"Вы успешно запустили реактор и выжили в бункере.\n\n"
                f"Марти ждет команду, чтобы отправиться во вторую главу!")
        
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("🚀 Начать Главу 2", callback_data="apoc_s2_start"),
            tele_types.InlineKeyboardButton("🔄 Пройти Главу 1 заново", callback_data="game_reset_all"),
            tele_types.InlineKeyboardButton("🔙 В меню Хаба", callback_data="game_main_menu")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        return

    # --- [ ЭТАП 1: ПРОБУЖДЕНИЕ ] ---
    if call.data == "apoc_start":
        text = (f"☢️ *ПРОТОКОЛ: ЧИСТОЕ НЕБО | ТЕНЬ В БУНКЕРЕ*\n"
                f"──────────────────────────\n"
                f"Вы приходите в себя на холодном полу. Голова гудит, будто по ней постучали титановым ломом. "
                f"В бункере темно, лишь аварийные лампы мигают алым, как глаза голодного волка.\n\n"
                f"Марти (той-пудель в потрепанном жилете) сидит рядом и сосредоточенно вылизывает лапу. "
                f"Его звуковой модуль шипит: 'О, Док, вы живы. Я уже начал присматривать себе нового хозяина среди мутантов... Шучу. "
                f"Хотя их печенье выглядит заманчиво. У нас проблема: главный реактор отключен вручную. Это не сбой. Нас посетили'.\n\n"
                f"**ВАША ЦЕЛЬ:** Восстановить питание, расследовать взлом и выбраться на поверхность.")
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("🔍 Осмотреть место происшествия", callback_data="apoc_n1_investigate"),
            tele_types.InlineKeyboardButton("🖥 Проверить терминал", callback_data="apoc_n1_pc_check"),
            tele_types.InlineKeyboardButton("🔄 Сбросить прогресс", callback_data="game_reset_all"),
            tele_types.InlineKeyboardButton("🔙 В меню Хаба", callback_data="game_main_menu")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 2: ДЕТЕКТИВ (Осмотр) ] ---
    elif call.data == "apoc_n1_investigate":
        text = (f"🔦 *ПОИСК УЛИК*\n\n"
                f"Вы включаете фонарик. Луч света выхватывает перевернутый стол и... Марти указывает носом на угол.\n\n"
                f"— Смотрите, Док. Силовой кабель не перегорел. Он перекушен. И это сделал не я, мои зубы слишком аристократичны для такой грязной работы. "
                f"Тут явно был кто-то с кусачками. Или очень злыми зубами'.\n\n"
                f"На пыльном полу виднеется странный след.")
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("🔌 Осмотреть кабель", callback_data="apoc_n1_clue_wire"),
            tele_types.InlineKeyboardButton("👣 Изучить след", callback_data="apoc_n1_clue_boot"),
            tele_types.InlineKeyboardButton("🔙 Вернуться", callback_data="apoc_start")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 3-4: УЛИКИ (Секреты) ] ---
    elif call.data == "apoc_n1_clue_wire":
        if not has_flag(current_node, "wire"):
            current_node = add_flag(current_node, "wire")
            set_game_node(user_id, current_node)
            add_xp(user_id, 2, username)
            msg = "✅ *УЛИКА:* Медный кабель со следами смазки. Кто-то смазывал инструменты.\n\n"
        else: msg = "📦 Вы уже изучили этот кабель.\n\n"
        kb = tele_types.InlineKeyboardMarkup().add(tele_types.InlineKeyboardButton("🔙 Назад к осмотру", callback_data="apoc_n1_investigate"))
        bot.edit_message_text(msg + "Марти: 'Запах... пахнет дешевым машинным маслом из Сектора 4. Кажется, у нас гости из Трущоб'.", call.message.chat.id, call.message.message_id, reply_markup=kb)

    elif call.data == "apoc_n1_clue_boot":
        if not has_flag(current_node, "boot"):
            current_node = add_flag(current_node, "boot")
            set_game_node(user_id, current_node)
            add_xp(user_id, 2, username)
            msg = "✅ *УЛИКА:* Отпечаток тяжелого армейского сапога 44-го размера.\n\n"
        else: msg = "📦 След зафиксирован в базе.\n\n"
        kb = tele_types.InlineKeyboardMarkup().add(tele_types.InlineKeyboardButton("🔙 Назад к осмотру", callback_data="apoc_n1_investigate"))
        bot.edit_message_text(msg + "— Ого! — Марти присвистнул. — Док, у вас 39-й, а у меня лапы. Значит, это точно не мы в лунатизме бродили'.", call.message.chat.id, call.message.message_id, reply_markup=kb)

    # --- [ ЭТАП 5: ЛОГИЧЕСКАЯ ЗАГАДКА (Терминал) ] ---
    elif call.data == "apoc_n1_pc_check":
        if has_flag(current_node, "pc_done"):
            bot.answer_callback_query(call.id, "🖥 Система уже взломана!")
            call.data = "apoc_n1_base_menu"
            return run_scenario(bot, call)

        text = ("🖥 *ТЕРМИНАЛ: ЗАБЛОКИРОВАНО*\n\n"
                "Экран требует пароль администратора. В углу висит стикер с подсказкой: 'Год, когда всё началось в Мариуполе'.\n\n"
                "Марти: 'Док, я знаю, вы тогда еще пешком под стол ходили, но память ученого должна подсказать дату! Это связано с вашей семье'.")
        kb = tele_types.InlineKeyboardMarkup(row_width=2).add(
            tele_types.InlineKeyboardButton("⌨️ 1982", callback_data="apoc_n1_pc_fail"),
            tele_types.InlineKeyboardButton("⌨️ 1985", callback_data="apoc_n1_pc_success"),
            tele_types.InlineKeyboardButton("⌨️ 1991", callback_data="apoc_n1_pc_fail"),
            tele_types.InlineKeyboardButton("⌨️ 2024", callback_data="apoc_n1_pc_fail")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    elif call.data == "apoc_n1_pc_success":
        if not has_flag(current_node, "pc_done"):
            current_node = add_flag(current_node, "pc_done")
            set_game_node(user_id, current_node)
            add_xp(user_id, 5, username)
            
        text = ("🔓 *ДОСТУП РАЗРЕШЕН*\n\n"
                "Вы вошли в систему. Логи показывают: 'Внешнее вмешательство. Дверь шлюза открыта кодом 0441'.\n\n"
                "Марти: 'Док, смотрите! Кто-то скачал чертежи вашего Костюма. Нас не просто грабили, нас изучали'.")
        kb = tele_types.InlineKeyboardMarkup().add(tele_types.InlineKeyboardButton("🚶 Продолжить", callback_data="apoc_n1_base_menu"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    elif call.data == "apoc_n1_pc_fail":
        bot.answer_callback_query(call.id, "❌ ОТКАЗАНО В ДОСТУПЕ. Неверный пароль! Марти: 'Док, ну вы чего? Это же год вашего рождения!'", show_alert=True)
        return
    
    # --- [ ЭТАП 6: КЛАДОВАЯ (Инвентарь) ] ---
    elif call.data == "apoc_n1_pantry":
        text = ("📦 *ЗАПАСЫ И ПЫЛЬ*\n\n"
                "Вы заходите в кладовую. Полки пусты, но за старым ящиком с надписью 'Спирт' (который, конечно, пуст) Марти находит аптечку.\n\n"
                "Марти: 'Док, тут только просроченный пластырь и... О! Флакон с йодом. В нашем мире это почти жидкое золото. "
                "Кстати, вы знали, что йод открыли случайно, когда кот химика Куртуа прыгнул на стол и разбил колбы? "
                "Надеюсь, мне не придется прыгать на ваши колбы, чтобы вы что-то открыли!'.")
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("🎒 Взять аптечку", callback_data="apoc_n1_item_meds"),
            tele_types.InlineKeyboardButton("🚶 Идти к Верстаку", callback_data="apoc_n1_base_menu")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 7: ТРЕВОГА (Атмосфера) ] ---
    elif call.data == "apoc_n1_item_meds":
        if not has_flag(current_node, "meds"):
            current_node = add_flag(current_node, "meds")
            set_game_node(user_id, current_node)
            add_xp(user_id, 1, username)
            
        text = ("🚨 *СИГНАЛ ТРЕВОГИ*\n\n"
                "Как только вы взяли аптечку, в бункере завыла сирена. Датчики радиации зашкаливают. \n\n"
                "Марти: 'Док! Вентиляция засосала порцию 'свежего' воздуха с поверхности. У нас есть пара минут, пока фильтры не сдохли совсем. "
                "Нам СРОЧНО нужен костюм!'.")
        kb = tele_types.InlineKeyboardMarkup().add(tele_types.InlineKeyboardButton("🏃 Бежать к Верстаку", callback_data="apoc_n1_base_menu"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 8: ВЫБОР ИНСТРУМЕНТА (Логика) ] ---
    elif call.data == "apoc_n1_tool_choice":
        text = ("🛠 *ВЫБОР ИНСТРУМЕНТА*\n\n"
                "На верстаке лежат два прибора: старый паяльник и лазерный скальпель.\n\n"
                "Марти: 'Док, скальпель круче, но он жрет батарею как не в себя. Паяльник надежнее. "
                "Что возьмем для тонкой работы над вашим костюмом?'.")
        kb = tele_types.InlineKeyboardMarkup(row_width=2).add(
            tele_types.InlineKeyboardButton("🔥 Паяльник", callback_data="apoc_n1_tool_iron"),
            tele_types.InlineKeyboardButton("⚡️ Скальпель", callback_data="apoc_n1_tool_laser")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 9: КАЛИБРОВКА (Мини-игра) ] ---
    elif call.data.startswith("apoc_n1_tool_"):
        text = ("📡 *КАЛИБРОВКА СЕНСОРОВ*\n\n"
                "Инструмент в руках. Теперь нужно настроить частоту звукового модуля Марти.\n\n"
                "Марти: 'Док, настройте на частоту, кратную 3, но не больше 10. Быстрее!'.")
        kb = tele_types.InlineKeyboardMarkup(row_width=3).add(
            tele_types.InlineKeyboardButton("📟 5 Hz", callback_data="apoc_n1_calib_fail"),
            tele_types.InlineKeyboardButton("📟 9 Hz", callback_data="apoc_n1_calib_success"),
            tele_types.InlineKeyboardButton("📟 11 Hz", callback_data="apoc_n1_calib_fail")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    elif call.data == "apoc_n1_calib_fail":
        bot.answer_callback_query(call.id, "❌ СБОЙ! Марти: 'Док, кратно 3 и меньше 10! Вспоминайте таблицу умножения!'", show_alert=True)
        return

    elif call.data == "apoc_n1_calib_success":
        try: bot.answer_callback_query(call.id, "✅ Идеальная частота! Инструмент готов к работе.")
        except: pass
        call.data = "apoc_n1_craft_suit"
        return handle_craft(bot, call, current_node)
    
   # --- [ ЭТАП 10: ЦЕНТРАЛЬНЫЙ ОТСЕК И ТАЙНЫЙ ЛЮК ] ---
    elif call.data == "apoc_n1_base_menu":
        text = (f"🛠 *ЦЕНТРАЛЬНЫЙ ОТСЕК*\n"
                f"──────────────────────────\n"
                f"Вы стоите в центре своего убежища. Сверху капает конденсат, а старый стоматологический кабинет деда в углу выглядит "
                f"пугающе мирно на фоне ржавых стен бункера. \n\n"
                f"Марти запрыгнул на кожаное кресло и начал интенсивно царапать пол под ним лапой: "
                f"'Док, я не хочу вас пугать, но из-под этого антикварного трона тянет холодом, как из открытого космоса. "
                f"И пахнет... старым формалином и секретами. Похоже, под нами есть еще один ярус!'.\n\n"
                f"Чтобы пробраться дальше, вам нужно решить: искать ресурсы на поверхности или спуститься в прошлое?")
        
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("🕳 Спуститься в секретный подвал", callback_data="apoc_n1_secret_entry"),
            tele_types.InlineKeyboardButton("🧵 Перейти к Верстаку", callback_data="apoc_n1_workbench"),
            tele_types.InlineKeyboardButton("📦 Обыскать склад ", callback_data="apoc_n1_search_1"),
            tele_types.InlineKeyboardButton("💊 Заглянуть в кладовую", callback_data="apoc_n1_pantry"),
            tele_types.InlineKeyboardButton("🔦 Обыскать лабораторию", callback_data="apoc_n1_search_2"),
            tele_types.InlineKeyboardButton("⬅️ Выйти в меню симуляций", callback_data="game_main_menu")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        
    # --- [ ЭТАП 10-A: ВХОД В АРХИВ-X ] ---
    elif call.data == "apoc_n1_secret_entry":
        text = ("📉 *ЛОГИЧЕСКИЙ ЗАМОК*\n\n"
                "Вы отодвигаете кресло. Под ним — люк из титанового сплава. На панели ввода всего две цифры. \n\n"
                "Марти: 'Док, тут гравировка на латыни. *Dentes*... это зубы! И дата... 1985. "
                "Подсказка гласит: Число зубов взрослого человека минус последние две цифры года, когда этот кабинет был запечатан'.\n\n"
                "**МАРТИ:** 'Док, вы же профи! 32 зуба минус... сколько там было? Шевелите извилинами!'")
        
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
        if not has_flag(current_node, "secret_entered"):
            current_node = add_flag(current_node, "secret_entered")
            set_game_node(user_id, current_node)
            add_xp(user_id, 10, username)
            
        text = ("🦷 *ЗАПРЕТНАЯ ЗОНА*\n\n"
                "Люк открывается с пневматическим шипением. Вы спускаетесь в идеально чистую комнату. "
                "Здесь хранятся прототипы инструментов, которые опередили свое время на десятилетия.\n\n"
                "Марти замер у шкафа: 'Док, посмотрите на этот мотор для бормашины. Он выдает 500 тысяч оборотов в минуту. "
                "Если мы вставим его в мой сканер, я смогу различать молекулы на расстоянии километра!'.")
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("⚙️ Снять мотор", callback_data="apoc_n1_secret_motor"),
            tele_types.InlineKeyboardButton("📂 Открыть папку 'Мариуполь-85'", callback_data="apoc_n1_secret_files"),
            tele_types.InlineKeyboardButton("🧗 Вернуться наверх", callback_data="apoc_n1_base_menu")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 10-C: СЕКРЕТНЫЕ ФАЙЛЫ ] ---
    elif call.data == "apoc_n1_secret_files":
        if not has_flag(current_node, "files"):
            current_node = add_flag(current_node, "files")
            set_game_node(user_id, current_node)
            
        text = ("📜 *ТАЙНЫЙ ОТЧЕТ*\n\n"
                "В папке лежит рентгеновский снимок. На нем запечатлена челюсть, полностью заросшая фиолетовыми кристаллами. \n\n"
                "Марти читает подпись: 'Заражение произошло через пломбу из метеоритного железа. Пациент номер ноль'. \n\n"
                "Док, ваш дед первым обнаружил этот вирус еще в 1985-м в Мариуполе! И Академия Орион знала об этом... Они следили за ним'.")
        kb = tele_types.InlineKeyboardMarkup().add(tele_types.InlineKeyboardButton("🔙 Назад к инструментам", callback_data="apoc_n1_secret_hall"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 10-D: ЛЕГЕНДАРНЫЙ МОТОР ] ---
    elif call.data == "apoc_n1_secret_motor":
        if not has_flag(current_node, "super_motor"):
            current_node = add_flag(current_node, "super_motor")
            set_game_node(user_id, current_node)
            
        text = ("✅ *ЛЕГЕНДАРНЫЙ ТРОФЕЙ*\n\n"
                "Вы бережно извлекаете мотор. Это настоящее сокровище старого мира.\n\n"
                "Марти: 'Теперь я не просто той-пудель, я — стратегический радар! Док, с этой штукой мы "
                "скрафтим сканер гораздо быстрее!'.\n\n"
                "🎁 **БОНУС:** Таймеры крафта сокращены на 5 минут!")
        kb = tele_types.InlineKeyboardMarkup().add(tele_types.InlineKeyboardButton("🧗 Вернуться в хаб", callback_data="apoc_n1_base_menu"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

   # --- [ ПЕРЕХОД К ВЕРСТАКУ ] ---
    elif call.data == "apoc_n1_workbench":
        if has_flag(current_node, "suit_fixed"):
            text = "🛠 *ВЕРСТАК*\n\nВаш защитный костюм готов и надет! Марти: 'Смотритесь отлично, Док! Радиация нам больше не страшна.'."
            kb = tele_types.InlineKeyboardMarkup().add(tele_types.InlineKeyboardButton("🔙 Вернуться в Хаб", callback_data="apoc_n1_base_menu"))
        elif has_flag(current_node, "cloth"):
            text = "🛠 *ВЕРСТАК*\n\nУ вас есть брезент. Марти готов помочь сшить защитный костюм."
            kb = tele_types.InlineKeyboardMarkup().add(
                tele_types.InlineKeyboardButton("⚒ Скрафтить Костюм", callback_data="apoc_n1_tool_choice"),
                tele_types.InlineKeyboardButton("🔙 Назад", callback_data="apoc_n1_base_menu")
            )
        else:
            text = "🛠 *ВЕРСТАК*\n\nЗдесь пока пусто. Марти: 'Док, нам нужен плотный материал, например, брезент со склада!'."
            kb = tele_types.InlineKeyboardMarkup().add(tele_types.InlineKeyboardButton("🔙 Назад", callback_data="apoc_n1_base_menu"))
            
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    elif call.data == "apoc_n1_craft_suit":
        return handle_craft(bot, call, current_node)
    
    # --- [ ЭТАПЫ 11-15: СЛОЖНЫЙ ПОИСК ] ---
    elif call.data == "apoc_n1_search_1":
        if has_flag(current_node, "cloth"):
            bot.answer_callback_query(call.id, "📦 Вы уже вскрыли этот замок и забрали брезент!", show_alert=True)
            call.data = 'apoc_n1_base_menu'
            return run_scenario(bot, call)

        # ЗАЩИТА ОТ ДВОЙНОГО ЗАПУСКА ТАЙМЕРА
        if not has_flag(current_node, "sklad_timer_started"):
            current_node = add_flag(current_node, "sklad_timer_started")
            set_game_node(user_id, current_node)
            set_game_timer(user_id, 15)

        text = ("📦 *СКЛАД: ТЯЖЕЛЫЙ ТРУД*\n\n"
                "Вы начинаете разгребать завалы. Марти нашел коробку с надписью 'Хлам', но она заперта на магнитный замок.\n\n"
                "Ожидание: **15 минут**.")
        kb = tele_types.InlineKeyboardMarkup().add(tele_types.InlineKeyboardButton("🔄 Вскрыть замок", callback_data="apoc_n1_res_1"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    elif call.data == "apoc_n1_res_1":
        if not has_flag(current_node, "cloth"):
            current_node = add_flag(current_node, "cloth")
            set_game_node(user_id, current_node)
            add_xp(user_id, 3, username)
            msg = "✅ *УСПЕХ: СКЛАД ОТКРЫТ*\n\nВы вскрыли ящик. Внутри оказался плотный брезент и пара старых фильтров. Это пригодится для костюма!"
        else:
            msg = "📦 Вы уже забрали всё ценное из этого ящика."
            
        kb = tele_types.InlineKeyboardMarkup().add(tele_types.InlineKeyboardButton("🔙 К хабу", callback_data="apoc_n1_base_menu"))
        bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 16: ТЕХНИЧЕСКИЙ ШЛЮЗ ] ---
    elif call.data == "apoc_n1_search_2":
        text = (f"🚿 *ТЕХНИЧЕСКИЙ УЗЕЛ*\n\n"
                f"Вы пробираетесь через старый блок дезинфекции. Под ногами хрустит битое стекло. На кафеле — свежие фиолетовые лужи.\n\n"
                f"Марти: 'Док, это не просто грязь. Это питательная среда 'Фиолетовый Реагент'. Ее использовали в НИИ для ускорения роста клеток. "
                f"Запах... как в стоматологии, только с примесью гнили. Смотрите, на двери — отпечаток ладони. Он свежий!'.")
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("🧬 Взять пробу жидкости", callback_data="apoc_n1_clue_liquid"),
            tele_types.InlineKeyboardButton("❄️ Дверь в лабораторию", callback_data="apoc_n1_frozen_door"),
            tele_types.InlineKeyboardButton("🔙 В центральный отсек", callback_data="apoc_n1_base_menu")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    elif call.data == "apoc_n1_clue_liquid":
        if not has_flag(current_node, "liquid"):
            current_node = add_flag(current_node, "liquid")
            set_game_node(user_id, current_node)
            add_xp(user_id, 3, username)
            msg = "✅ *УЛИКА:* Фиолетовый био-реагент. Это среда для выращивания 'Умного Мха'.\n\n"
        else: msg = "📦 Проба уже взята.\n\n"
        kb = tele_types.InlineKeyboardMarkup().add(tele_types.InlineKeyboardButton("🔙 Назад", callback_data="apoc_n1_search_2"))
        bot.edit_message_text(msg + "Марти: 'Кажется, наш вор — биолог. Или очень умный мутант'.", call.message.chat.id, call.message.message_id, reply_markup=kb)

    # --- [ ЭТАП 17: ЗАМЕРЗШАЯ ДВЕРЬ ] ---
    elif call.data == "apoc_n1_frozen_door":
        text = ("❄️ *ЛЕДЯНОЙ ЗАМОК*\n\n"
                "Дверь в лабораторию покрыта инеем. Система охлаждения дала сбой, и механизм намертво заклинило.\n\n"
                "Марти: 'Док, если мы дернем — сломаем ручку. Помните, мы нашли флакон с йодом в кладовой? "
                "Если смешать его с остатками спирта в замке, произойдет реакция с выделением тепла. Пробуем?'.")
        kb = tele_types.InlineKeyboardMarkup(row_width=1)
        if has_flag(current_node, "meds"):
            kb.add(tele_types.InlineKeyboardButton("🧪 Использовать Йод из аптечки", callback_data="apoc_n1_melt_success"))
        else:
            kb.add(tele_types.InlineKeyboardButton("🔥 Пытаться отогреть руками", callback_data="apoc_n1_melt_fail"))
        kb.add(tele_types.InlineKeyboardButton("🔙 Назад", callback_data="apoc_n1_search_2"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    elif call.data == "apoc_n1_melt_fail":
        bot.answer_callback_query(call.id, "🥶 Руки примерзают к металлу! Марти: 'Док, не глупите, так мы только кожу оставим на двери. Нужен йод!'", show_alert=True)

    # --- [ ЭТАП 18: ТЕНЬ В ТЕМНОТЕ ] ---
    elif call.data == "apoc_n1_melt_success":
        text = ("👥 *ТЕНЬ В ТЕМНОТЕ*\n\n"
                "Лед зашипел и стаял. Дверь со стоном открылась. В глубине лаборатории вы видите... фигуру человека. Он стоит спиной к вам и что-то ищет в шкафах.\n\n"
                "Марти (шепотом): 'Док... я не чую тепла. Это не человек. Это либо старая голограмма, либо... Тс-с-с! Он оборачивается!'.")
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("🎤 Окликнуть: 'Кто здесь?'", callback_data="apoc_n1_shadow_talk"),
            tele_types.InlineKeyboardButton("🤫 Подкрасться ближе", callback_data="apoc_n1_shadow_sneak")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 19: УЛИКА: МАСКА ] ---
    elif call.data == "apoc_n1_shadow_talk" or call.data == "apoc_n1_shadow_sneak":
        if not has_flag(current_node, "mask"):
            current_node = add_flag(current_node, "mask")
            set_game_node(user_id, current_node)
            if call.data == "apoc_n1_shadow_sneak": add_xp(user_id, 5, username)
            
        action_text = "Вы выкрикиваете имя, но фигура рассыпается облаком пыли. Это была запись системы безопасности." if call.data == "apoc_n1_shadow_talk" else "Вы бесшумно крадетесь вперед и пытаетесь схватить незнакомца за плечо... но ваша рука проходит сквозь него! Фигура рассыпается пикселями. Это голограмма."
            
        text = (f"👤 *ПУСТОТА*\n\n"
                f"{action_text}\n\n"
                f"На полу вы находите маску Академии Орион. \n\n"
                f"Марти: 'Док, нас опередили. Они забрали данные! В вентиляцию, быстро, мы еще можем их догнать!'.")
        kb = tele_types.InlineKeyboardMarkup().add(tele_types.InlineKeyboardButton("🏃 Прыгнуть в вентиляцию", callback_data="apoc_n1_vent_enter"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
    
    # --- [ ЭТАП 20: ВЕНТИЛЯЦИОННЫЕ ШАХТЫ (Стелс) ] ---
    elif call.data == "apoc_n1_vent_enter":
        text = ("💨 *ТЕСНЫЕ ТРУБЫ*\n\n"
                "Вы ползете по вентиляции. Пыль забивает фильтры маски. Впереди слышен механический скрежет.\n\n"
                "Марти: 'Тихо! Впереди дрон-уборщик серии 'Чистота-9'. Но после Сбоя его программа 'уборки' включает в себя расчленение любых биологических объектов. "
                "Он блокирует проход к генераторной. Док, используем мой звуковой модуль?'")
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("🔊 Имитировать писк крыс", callback_data="apoc_n1_stealth_rats"),
            tele_types.InlineKeyboardButton("🎤 Записать эхо шагов в коридоре", callback_data="apoc_n1_stealth_steps"),
            tele_types.InlineKeyboardButton("👊 Попробовать вырубить дрона ломом", callback_data="apoc_n1_stealth_fight")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    elif call.data == "apoc_n1_stealth_rats":
        text = ("✅ *УСПЕХ*\n\nМарти выдал серию высокочастотных писков. Дрон замер, его красные окуляры повернулись в сторону шахты. "
                "Механический паук резво укатился проверять 'грызунов'. Путь свободен!")
        kb = tele_types.InlineKeyboardMarkup().add(tele_types.InlineKeyboardButton("🧗 Идти к шахте лифта", callback_data="apoc_n1_stealth_success"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    elif call.data == "apoc_n1_stealth_steps":
        text = ("✅ *ОТЛИЧНЫЙ МАНЕВР*\n\nМарти идеально сымитировал звук тяжелых шагов бригады зачистки. "
                "Программа дрона дала сбой, он решил, что зона уже обслуживается, и улетел на подзарядку! Путь свободен!")
        kb = tele_types.InlineKeyboardMarkup().add(tele_types.InlineKeyboardButton("🧗 Идти к шахте лифта", callback_data="apoc_n1_stealth_success"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    elif call.data == "apoc_n1_stealth_fight":
        bot.answer_callback_query(call.id, "💥 Плохая идея! Дрон едва не отпилил вам палец. Придется использовать хитрость Марти!", show_alert=True)
        return

    # --- [ ЭТАП 21: ВЕРТИКАЛЬНЫЙ ПОДЪЕМ ] ---
    elif call.data == "apoc_n1_stealth_success":
        text = ("🧗 *ВЕРТИКАЛЬНЫЙ ПРЕДЕЛ*\n\n"
                "Дрон остался позади. Вы выходите в шахту грузового лифта. Трос оборван, нужно лезть вверх по ржавым скобам прямо над пропастью.\n\n"
                "Марти: 'Я запрыгну к вам в рюкзак. Только не смотрите вниз, Док, я не хочу, чтобы мой последний вид был кучей мусора на дне шахты!'.")
        kb = tele_types.InlineKeyboardMarkup().add(tele_types.InlineKeyboardButton("🧗 Лезть вверх", callback_data="apoc_n1_climb"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 22: КАМЕРА СЛЕЖЕНИЯ ] ---
    elif call.data == "apoc_n1_climb":
        text = ("👁 *ГЛАЗ АКАДЕМИИ*\n\n"
                "На уровне 3-го этажа вы замираете. Прямо перед вашим лицом — скрытая камера. Ее линза поворачивается, фокусируясь на вас.\n\n"
                "Марти: 'Нас засекли! Нужно отключить ее, пока сигнал не ушел на сервер Академии. Перережьте кабель!'.")
        kb = tele_types.InlineKeyboardMarkup(row_width=2).add(
            tele_types.InlineKeyboardButton("✂️ Синий провод", callback_data="apoc_n1_cam_success"),
            tele_types.InlineKeyboardButton("✂️ Красный провод", callback_data="apoc_n1_cam_fail")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 23: ПАРОВОЙ ПРОРЫВ ] ---
    elif call.data == "apoc_n1_cam_success" or call.data == "apoc_n1_cam_fail":
        if call.data == "apoc_n1_cam_fail":
            try: bot.answer_callback_query(call.id, "⚡️ Вас ударило током, но камера отключилась!", show_alert=True)
            except: pass
            
        text = ("💨 **ЭТАП 23: ГОРЯЧИЙ ПРИЕМ**\n\n"
                "Камера ослепла, но в этот момент из лопнувшей трубы рядом вырывается струя раскаленного пара! Путь перекрыт.\n\n"
                "Марти: 'Док, вентиль справа! Его заклинило, нужно приложить всю силу!'.")
        kb = tele_types.InlineKeyboardMarkup().add(tele_types.InlineKeyboardButton("⚙️ Крутить вентиль", callback_data="apoc_n1_valve_turn"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 24: РЖАВЫЙ РЫЧАГ ] ---
    elif call.data == "apoc_n1_valve_turn":
        text = ("🏗 *РЫЧАГ СУДЬБЫ*\n\n"
                "Пар утих. Вы стоите перед дверью в генераторную. Огромный рычаг блокировки заржавел намертво.\n\n"
                "Марти: 'Помните тот медный кабель со смазкой, который мы нашли в начале? Он весь в машинном масле! Это наш шанс!'.")
        kb = tele_types.InlineKeyboardMarkup(row_width=1)
        if has_flag(current_node, "wire"):
            kb.add(tele_types.InlineKeyboardButton("💧 Смазать рычаг маслом", callback_data="apoc_n1_generator_room"))
        else:
            kb.add(tele_types.InlineKeyboardButton("🔨 Ударить ломом", callback_data="apoc_n1_gen_noise"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
    
    elif call.data == "apoc_n1_gen_noise":
        bot.answer_callback_query(call.id, "🔊 СКРЕЖЕТ! Дверь поддалась, но вы наделали много шума. Потеряно 5 XP.", show_alert=True)
        call.data = "apoc_n1_generator_room"
        return run_scenario(bot, call)

    # --- [ ЭТАП 25: ЗАГАДКА ГЕНЕРАТОРА ] ---
    elif call.data == "apoc_n1_generator_room":
        if not has_flag(current_node, "generator"):
            current_node = add_flag(current_node, "generator")
            set_game_node(user_id, current_node)
            
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

    elif call.data == "apoc_n1_gen_fail":
        bot.answer_callback_query(call.id, "⚡️ ЗЗЗЗЗТ! Неверная фаза! Вспоминайте таблицу Менделеева: Углерод - 6-й элемент!", show_alert=True)

    elif call.data == "apoc_n1_gen_success":
        if not has_flag(current_node, "truth"):
            current_node = add_flag(current_node, "truth")
            set_game_node(user_id, current_node)
            add_xp(user_id, 10, username)
            
        text = ("🔥 **ПИТАНИЕ ВОССТАНОВЛЕНО**\n\n"
                "Свет с миганием загорается во всем бункере. Мох испуганно сжимается. Но в этом свете вы видите то, что повергает вас в шок.\n\n"
                "На стене у генератора висит старая фотография. На ней — ваш дед, Дмитрий Владимирович, в таком же бункере. "
                "В руках у него странный прибор, подозрительно похожий на тот самый 'Сканер', который мы пытаемся собрать.")
        kb = tele_types.InlineKeyboardMarkup().add(tele_types.InlineKeyboardButton("📻 Проверить радиостанцию", callback_data="apoc_n1_decode_radio"))
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

    elif call.data == "apoc_n1_clue_radio":
        if not has_flag(current_node, "radio"):
            current_node = add_flag(current_node, "radio")
            set_game_node(user_id, current_node)
            add_xp(user_id, 3, username)
            bot.answer_callback_query(call.id, "📡 Частота сохранена! Марти скачал обрывок аудиодневника деда. Получено 3 XP.", show_alert=True)
        else:
            bot.answer_callback_query(call.id, "📡 Данные уже скачаны в память Марти.", show_alert=True)

    # --- [ ЭТАП 27: ПЕРЕХОД (Логика/Крафт) ] ---
    elif call.data == "apoc_n1_stairwell":
        text = ("🪜 **ЭТАП 27: ВЕРТИКАЛЬНЫЙ ПРЕДЕЛ**\n\n"
                "Лестница на крышу заблокирована обвалом. Единственный путь — технический лифт, но у него перегорел предохранитель.\n\n"
                "Марти: 'Док, я могу замкнуть контакты своим жилетом, но меня может слегка... поджарить. "
                "Или вы можете попробовать собрать перемычку из того медного кабеля, который мы нашли в начале главы'.")
        kb = tele_types.InlineKeyboardMarkup(row_width=1)
        if has_flag(current_node, "wire"):
            kb.add(tele_types.InlineKeyboardButton("🛠 Использовать кабель из улик", callback_data="apoc_n1_lift_fix"))
        else:
            kb.add(tele_types.InlineKeyboardButton("🐕 Рискнуть Марти (Плохо для отношений)", callback_data="apoc_n1_marty_risk"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    elif call.data == "apoc_n1_marty_risk":
        bot.answer_callback_query(call.id, "🐕 БЗЗЗТ! Марти вскрикнул, и от него пошел дымок. Лифт заработал, но вы потеряли 5 XP за жестокость!", show_alert=True)
        call.data = "apoc_n1_lift_fix"
        return run_scenario(bot, call)

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
        if not has_flag(current_node, "secret_found"):
            current_node = add_flag(current_node, "secret_found")
            set_game_node(user_id, current_node)
            add_xp(user_id, 5, username)
            
        text = ("💎 **ЭТАП 29: ТАЙНИК ЗА СТЕНКОЙ**\n\n"
                "Лифт застрял на секунду, и вы заметили в стене шахты нишу. Там лежит старая стоматологическая аптечка вашего деда.\n\n"
                "Внутри — **Антисептик 'Орион'**. Это мощное средство, которое позволит нам лечить раны во 2-й главе.\n\n"
                "Марти: 'Ого! Дед знал, где прятать заначки. Теперь мы точно не загнемся от первой же царапины мутанта!'.")
        kb = tele_types.InlineKeyboardMarkup().add(tele_types.InlineKeyboardButton("🚀 Выйти на крышу", callback_data="apoc_n1_final_ascent"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 30: ФИНАЛ ГЛАВЫ (Моральный выбор) ] --
    elif call.data == "apoc_n1_final_ascent":
        text = (f"☀️ *ГЛОТОК ЯДА*\n\n"
                f"Вы на крыше НИИ. Перед вами расстилается мертвый город. Вдали виднеются шпили торгового центра.\n\n"
                f"У самих солнечных панелей вы находите того самого 'вора'. Это робот-андроид старой модели, он сильно поврежден. "
                f"В его груди — тот самый фиолетовый мох, который служит ему батареей.\n\n"
                f"Робот (хрипит): 'Док... не выключай... мне нужно... донести... семя...'.\n\n"
                f"Марти: 'Док, если мы его отключим — получим кучу редких запчастей для вашего костюма и мой сканер станет в два раза мощнее. "
                f"Но если поможем ему... кто знает, может он расскажет, откуда у него фото вашего деда?'")
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("🔧 Разобрать робота", callback_data="apoc_n1_end_power"),
            tele_types.InlineKeyboardButton("🔋 Поделиться энергией", callback_data="apoc_n1_end_knowledge")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # 🏆 --- [ ФИНАЛЫ: РАСЧЕТ НАГРАДЫ И СОХРАНЕНИЕ ] --- 🏆
    elif call.data in ["apoc_n1_end_power", "apoc_n1_end_knowledge"]:
        
        is_first_time = not has_completed_chapter(user_id, "chapter_1")
        
        if is_first_time:
            xp_reward = 150 if call.data == "apoc_n1_end_knowledge" else 100
            dust_reward = xp_reward
            mark_chapter_completed(user_id, "chapter_1")
            reward_msg = f"🎁 **ДЖЕКПОТ ЗА ПЕРВОЕ ПРОХОЖДЕНИЕ:**\n✨ Опыт: +{xp_reward} XP\n💎 Пыль: +{dust_reward} ед.\n"
        else:
            xp_reward = 20
            dust_reward = 20
            reward_msg = f"🔄 **НАГРАДА ЗА ПОВТОРНОЕ ПРОХОЖДЕНИЕ:**\n✨ Опыт: +{xp_reward} XP\n💎 Пыль: +{dust_reward} ед.\n"

        # Защита от фарма опыта внутри одной сессии
        if not has_flag(current_node, "ch1_done"):
            add_xp(user_id, xp_reward, username) 
            current_node = add_flag(current_node, "ch1_done")
            
        # КРИТИЧЕСКИЙ ФИКС: Локация должна обновляться ВСЕГДА, даже при повторах!
        current_node = set_loc(current_node, "apoc_ch1_completed_screen")
        set_game_node(user_id, current_node)
        loc = "apoc_ch1_completed_screen"
            
        if call.data == "apoc_n1_end_power":
            text = ("🦾 *ФИНАЛ: ПУТЬ СИЛЫ*\n\n"
                    "Вы безжалостно разбираете андроида. Ваше выживание важнее. Запчасти отличные, а сканер теперь работает на 200%. "
                    "В глазах Марти читается легкое непонимание, но он преданно виляет хвостом.\n\n"
                    f"{reward_msg}\n"
                    "🎉 **ГЛАВА 1 ЗАВЕРШЕНА!** Вы открыли доступ ко второй главе.")
        else:
            text = ("🧠 *ФИНАЛ: ПУТЬ ЗНАНИЯ*\n\n"
                    "Вы отдаете часть заряда своего костюма роботу. Его окуляры слабо загораются.\n\n"
                    "Робот: '...Спасибо, Создатель... Ищите... ответы... под Кислотными болотами...'.\n"
                    "Сказав это, он отключается навсегда. Марти уважительно кивает.\n\n"
                    f"{reward_msg}\n"
                    "🎉 **ГЛАВА 1 ЗАВЕРШЕНА!** Вы открыли доступ ко второй главе.")
            
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("🚀 Начать Главу 2", callback_data="apoc_s2_start"),
            tele_types.InlineKeyboardButton("🏆 Вернуться в меню", callback_data="game_main_menu")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

# --- ПОДФУНКЦИЯ КРАФТА ---
def handle_craft(bot, call, current_node):
    user_id = call.from_user.id
    
    def has_flag(node_str, flag): return f"|{flag}" in node_str or flag in node_str.split('|')[1:]
    def add_flag(node_str, flag): return node_str if has_flag(node_str, flag) else f"{node_str}|{flag}"
    def set_loc(node_str, new_loc):
        parts = node_str.split('|')
        parts[0] = new_loc
        return '|'.join(parts)
    
    time_needed = 20
    if has_flag(current_node, "super_motor"):
        time_needed = 12
        bonus_text = "⚡️ Благодаря мотору из кабинета деда, работа идет в два раза быстрее!"
    else:
        bonus_text = "🔧 Обычные инструменты работают медленно, но верно."

    if "suit" in call.data:
        # ЗАЩИТА ТАЙМЕРА КРАФТА ОТ ПОВТОРНОГО ЗАПУСКА
        if not has_flag(current_node, "craft_timer_started"):
            current_node = add_flag(current_node, "craft_timer_started")
            set_game_timer(user_id, time_needed)
            
        current_node = add_flag(current_node, "suit_fixed")
        current_node = set_loc(current_node, "apoc_n1_base_menu")
        set_game_node(user_id, current_node)
        
        msg = (f"⚒ *ИДЕТ КРАФТ КОСТЮМА*\n\n"
               f"{bonus_text}\n\n"
               f"Марти подбадривает: 'Док, еще немного, и вы будете выглядеть как настоящий герой пустошей!'.\n\n"
               f"Готовность через **{time_needed} минут**.")
        
        kb = tele_types.InlineKeyboardMarkup().add(
            tele_types.InlineKeyboardButton("🔄 Проверить готовность", callback_data="apoc_n1_base_menu")
        )
        bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
