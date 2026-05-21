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
    
    # --- [ 1. АБСОЛЮТНАЯ ЗАЩИТА ТАЙМЕРА ] ---
    # Пропускаем системные кнопки входа, чтобы бот мог показать меню "Продолжить экспедицию"
    if call.data not in ["apoc_s5_start", "resume_game_5", "game_reset_ch5", "game_main_menu"]:
        if not is_timer_expired(user_id):
            try: bot.answer_callback_query(call.id, "⌛️ Объект заблокирован. Ожидайте завершения процесса!", show_alert=True)
            except: pass
            return

    raw_node, _ = get_game_status(user_id)
    if not raw_node: 
        raw_node = "apoc_start"

    # --- ЛОКАЛЬНЫЕ ПОМОЩНИКИ ДЛЯ РАБОТЫ СО СТРОКОЙ СОХРАНЕНИЯ ---
    def get_loc(node_str): return node_str.split('|')[0]
    def has_flag(node_str, flag): return f"|{flag}" in node_str or flag in node_str.split('|')[1:]
    def add_flag(node_str, flag): return node_str if has_flag(node_str, flag) else f"{node_str}|{flag}"
    def set_loc(node_str, new_loc):
        parts = node_str.split('|')
        parts[0] = new_loc
        return '|'.join(parts)

    current_node = raw_node
    loc = get_loc(current_node)

    # 🟢 --- [ ВХОД В ИГРУ И УМНОЕ МЕНЮ ВОЗВРАТА ] --- 🟢
    if call.data == "apoc_s5_start":
        # Жесткая проверка прохождения ГЛАВЫ 4
        if not has_completed_chapter(user_id, "chapter_4"):
            try: bot.answer_callback_query(call.id, "🔒 Доступ заблокирован! Сначала завершите Главу 4.", show_alert=True)
            except: pass
            return

        if loc in ["apoc_ch4_completed_screen", "apoc_start", "start", "apoc_s5_scene_1"]:
            call.data = "apoc_s5_scene_1"
        else:
            text = (f"🔙 *ФИНАЛЬНЫЙ РУБЕЖ*\n"
                    f"──────────────────────────\n"
                    f"Командор, вы остановились перед финалом истории. Марти волнуется.\n\n"
                    f"Что делаем?")
            kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
                tele_types.InlineKeyboardButton("▶️ Продолжить экспедицию", callback_data="resume_game_5"),
                tele_types.InlineKeyboardButton("🔄 Начать Главу 5 заново", callback_data="game_reset_ch5"),
                tele_types.InlineKeyboardButton("🔙 В меню Хаба", callback_data="game_main_menu")
            )
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
            return

    if call.data == "resume_game_5":
        call.data = loc
        try: bot.answer_callback_query(call.id, "🔄 Экспедиция продолжена!")
        except: pass

    # 💾 --- [ АВТОСОХРАНЕНИЕ КОМНАТЫ ] --- 💾
    MAJOR_NODES = [
        "apoc_s5_scene_1", "apoc_s5_2", "apoc_s5_3", "apoc_s5_4", "apoc_s5_5", 
        "apoc_s5_6", "apoc_s5_7", "apoc_s5_8", "apoc_s5_9", "apoc_s5_10", 
        "apoc_s5_11", "apoc_s5_12", "apoc_s5_13", "apoc_s5_14", "apoc_s5_15", 
        "apoc_s5_16", "apoc_s5_17", "apoc_s5_18", "apoc_s5_19", "apoc_s5_20", 
        "apoc_s5_21", "apoc_s5_22", "apoc_s5_23", "apoc_s5_24", "apoc_s5_25", 
        "apoc_s5_26", "apoc_s5_27", "apoc_s5_28", "apoc_s5_29", "apoc_game_completed_screen"
    ]
    if call.data in MAJOR_NODES:
        current_node = set_loc(current_node, call.data)
        set_game_node(user_id, current_node)
        loc = call.data

    # 🏆 --- [ ЭКРАН ЗАВЕРШЕННОЙ ИГРЫ ] --- 🏆
    if call.data == "apoc_game_completed_screen":
        text = (f"🏆 **ИСТОРИЯ ЗАВЕРШЕНА**\n"
                f"──────────────────────────\n"
                f"Мариуполь стал маяком новой цивилизации. Ваше имя навсегда вписано в историю.\n\n"
                f"Марти отдыхает на зеленой траве Городского Сада.")
        
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("🔄 Пройти Главу 5 заново", callback_data="game_reset_ch5"),
            tele_types.InlineKeyboardButton("🔙 В меню Хаба", callback_data="game_main_menu")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        return

    # --- [ ЭТАП 1: ПЕРВЫЙ РАССВЕТ ] ---
    if call.data == "apoc_s5_scene_1":
        text = (f"🌅 *ПОСЛЕ БУРИ*\n"
                f"──────────────────────────\n"
                f"Пыль от падения Небоскреба осела. Вы стоите в центре Городского Сада. Фиолетовое свечение исчезло, уступив "
                f"место мягкому розовому рассвету. Вокруг начинают шевелиться люди — те, кто десятилетиями был в стазисе. "
                f"Они дезориентированы, напуганы и больны.\n\n"
                f"Марти: 'Док, город жив! Но это только начало. У людей шок, их нервные окончания перегружены после "
                f"отключения сети «Орион». Нам нужно организовать первый пункт помощи прямо здесь, в беседке. "
                f"Влад... он изменился. Он сидит на траве и, кажется, слышит шепот каждого просыпающегося растения. "
                f"Он — наше главное преимущество, но Академия всё еще наблюдает за нами с орбиты'.")
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("Организовать медицинский штаб", callback_data="apoc_s5_2"),
            tele_types.InlineKeyboardButton("Попросить Влада просканировать окрестности", callback_data="apoc_s5_clue_scan")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 2: КЛИНИКА НАДЕЖДЫ ] ---
    elif call.data == "apoc_s5_2":
        text = (f"🏥 *ХИРУРГИЯ ДУШИ*\n\n"
                f"К вам приносят первого пациента — старик с сильным воспалением в области челюсти. После стазиса био-мох "
                f"оставил глубокие следы в мягких тканях. Вам нужно провести экстренную санацию, чтобы остановить сепсис. "
                f"У вас только старый набор инструментов и ваш Лазерный Бор.\n\n"
                f"Марти: 'Док, тут нужна ювелирная точность. Помните, как вы учили: при вскрытии глубоких полостей "
                f"главное — не задеть сосудисто-нервный пучок. Чтобы обезболить и очистить канал максимально эффективно, "
                f"на какой зоне пульпы нам нужно сосредоточить резонанс Бора? Вспомните анатомию: где находится "
                f"самая чувствительная точка входа нерва в корневой канал?'")
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("Направить луч на апикальное отверстие", callback_data="apoc_s5_3"),
            tele_types.InlineKeyboardButton("Работать по коронковой части", callback_data="apoc_s5_med_fail"),
            tele_types.InlineKeyboardButton("Использовать общую дезинфекцию", callback_data="apoc_s5_med_fail")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 3: КОСМИЧЕСКИЙ РАДАР ] ---
    elif call.data == "apoc_s5_3":
        if not has_flag(current_node, "logic_apex_done"):
            current_node = add_flag(current_node, "logic_apex_done")
            set_game_node(user_id, current_node)
            add_xp(user_id, 50, username)

        text = (f"📡 *СИГНАЛ В ПУСТОТУ*\n\n"
                f"Операция прошла успешно. Старик приходит в себя и шепчет координаты. Это заброшенная станция спутниковой связи "
                f"на окраине города. Если мы запустим её, мы сможем отследить оставшиеся дроны Академии.\n\n"
                f"Влад подходит к вам: 'Папа, я чувствую их. Они там, в темноте, за небом. Они готовят «Очищение». "
                f"Мне нужно соединить мой код с их радаром. Но система требует навигационный ключ — название созвездия, "
                f"которое дед называл «Королевой Неба», формой напоминающее латинскую букву W'.")
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("Ввести ключ: Кассиопея", callback_data="apoc_s5_4"),
            tele_types.InlineKeyboardButton("Ввести ключ: Андромеда", callback_data="apoc_s5_astro_fail"),
            tele_types.InlineKeyboardButton("Ввести ключ: Большая Медведица", callback_data="apoc_s5_astro_fail")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 4: ТЕНИ НА ГОРИЗОНТЕ ] ---
    elif call.data == "apoc_s5_4":
        if not has_flag(current_node, "satellite_link"):
            current_node = add_flag(current_node, "satellite_link")
            set_game_node(user_id, current_node)

        text = (f"👣 *ПЕРВЫЕ ГОСТИ*\n\n"
                f"Экран древнего монитора оживает, показывая сетку ПВО. Но вместо точек своих дронов вы видите три "
                f"черные капсулы, входящие в атмосферу прямо над вашим лагерем. Это «Инквизиторы» — элитный спецназ Академии. "
                f"Они прибыли, чтобы забрать Субъекта Ноль.\n\n"
                f"Марти (рычит): 'Док, они приземлятся через 10 минут. У нас нет армии, но у нас есть город. "
                f"Мы можем использовать систему автоматического полива парка, чтобы создать ловушку, или активировать "
                f"старые звуковые сирены, чтобы сбить их сенсоры. Влад готов помочь, но он боится'.")
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("Подготовить водную ловушку", callback_data="apoc_s5_5"),
            tele_types.InlineKeyboardButton("Использовать акустический удар", callback_data="apoc_s5_trap_fail")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 5: ОБОРОНА ПОСЕЛЕНИЯ ] ---
    elif call.data == "apoc_s5_5":
        if not has_flag(current_node, "base_fortified"):
            current_node = add_flag(current_node, "base_fortified")
            set_game_node(user_id, current_node)

        text = (f"⚔️ *СТОЛКНОВЕНИЕ*\n\n"
                f"Капсулы врезаются в землю с оглушительным грохотом. Из них выходят фигуры в зеркальной броне. "
                f"Но как только они вступают на газоны, вы включаете давление. Струи воды, насыщенные частицами Белого Семени, "
                f"ослепляют их визоры. Влад поднимает руку, и корни деревьев начинают сковывать врагов.\n\n"
                f"**ЛИНДЕР (командир инквизиторов):** 'Дмитрий, ты защищаешь ошибку природы. Сдай нам проект Влад, "
                f"и мы оставим Мариуполь в покое. Сопротивление бесполезно — орбитальное орудие наведено на парк'.\n\n"
                f"Марти: 'Он блефует, Док! Я вижу через радар, что их спутник еще не откалиброван. Но нам нужно "
                f"решить: вступить в переговоры или использовать энергию Влада для ответного удара прямо по орбите'.")
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("Дать Владу команду на контратаку", callback_data="apoc_s5_6"),
            tele_types.InlineKeyboardButton("Выйти на переговоры с Линдером", callback_data="apoc_s5_clue_negotiate")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 6: ГНЕВ СЕМЕНИ ] ---
    elif call.data == "apoc_s5_6":
        if not has_flag(current_node, "wrath_done"):
            current_node = add_flag(current_node, "wrath_done")
            set_game_node(user_id, current_node)
            add_xp(user_id, 45, username)

        text = (f"⚡️ *РЕЗОНАНС ВЕРТИКАЛИ*\n"
                f"──────────────────────────\n"
                f"Вы даете Владу знак. Мальчик закрывает глаза, и Белое Семя в его руках вспыхивает ослепительным столбом света, "
                f"уходящим в зенит. Орбитальное орудие Академии, уже начавшее прогрев, перегружается — обратный импульс "
                f"сжигает их цепи наведения. Инквизиторы в парке падают на колени, их зеркальная броня трескается от статики.\n\n"
                f"Марти: 'Док, это было... эпично! Мы только что ослепили «Орион» на этом секторе орбиты. Но Линдер и его "
                f"отряд успели отступить в сторону порта. Они не ушли насовсем. Более того, среди выживших в нашем лагере "
                f"начались волнения. Кто-то распускает слухи, что Влад — это демон, притянувший фиолетовый мох. "
                f"Нам нужно укрепить авторитет и доказать, что мы на стороне людей'.")
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("Провести инспекцию здоровья лагеря", callback_data="apoc_s5_7"),
            tele_types.InlineKeyboardButton("Искать подстрекателя через камеры", callback_data="apoc_s5_clue_traitor")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 7: ФИЛЬТР ЛОЯЛЬНОСТИ ] ---
    elif call.data == "apoc_s5_7":
        text = (f"🔬 *ПРОВЕРКА НА ЧИСТОТУ*\n\n"
                f"Вы собираете выживших для обязательного осмотра. Это единственный способ выявить скрытые био-импланты "
                f"Академии, через которые они транслируют страх. Вы используете Анализатор, чтобы проверить структуру эмали каждого. "
                f"У агентов «Ориона» она заменена на синтетический полимер.\n\n"
                f"Марти: 'Док, смотрите на этого парня. Он утверждает, что он местный рыбак. Но его «клыки» ведут себя странно "
                f"под ультрафиолетом. Чтобы не ошибиться и не обвинить невиновного, вспомните: сколько клыков (cuspids) "
                f"в норме должно быть у взрослого человека во рту? Любое другое число выдаст в нем аугментированного шпиона!'.")
        kb = tele_types.InlineKeyboardMarkup(row_width=3).add(
            tele_types.InlineKeyboardButton("2", callback_data="apoc_s5_spy_fail"),
            tele_types.InlineKeyboardButton("4", callback_data="apoc_s5_8"),
            tele_types.InlineKeyboardButton("6", callback_data="apoc_s5_spy_fail")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 8: ЦИФРОВОЙ КУПОЛ ] ---
    elif call.data == "apoc_s5_8":
        if not has_flag(current_node, "spy_captured"):
            current_node = add_flag(current_node, "spy_captured")
            set_game_node(user_id, current_node)
            add_xp(user_id, 30, username)

        text = (f"🛡 *СЕТЕВОЙ ЩИТ*\n\n"
                f"Шпион обезврежен — в его клыке-импланте оказался передатчик. Теперь у нас есть доступ к частотам Академии. "
                f"Чтобы защитить поселение от новых атак, нужно настроить частотный фильтр «Купол». \n\n"
                f"Влад садится за терминал: 'Папа, я могу развернуть энергию Семени через старые антенны, но мне "
                f"нужна точка привязки на небе. Система навигации требует указать на созвездие, которое в это время "
                f"года указывает на север и напоминает ковш с ручкой. Только через него мы сможем синхронизировать "
                f"защитное поле с магнитными полюсами'.")
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("Выбрать Большую Медведицу", callback_data="apoc_s5_9"),
            tele_types.InlineKeyboardButton("Выбрать Орион", callback_data="apoc_s5_shield_fail"),
            tele_types.InlineKeyboardButton("Выбрать Лебедя", callback_data="apoc_s5_shield_fail")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 9: ЧЕРТЕЖИ ОТЦА ] ---
    elif call.data == "apoc_s5_9":
        if not has_flag(current_node, "shield_active"):
            current_node = add_flag(current_node, "shield_active")
            set_game_node(user_id, current_node)

        text = (f"📜 *ЗАВЕЩАНИЕ «ОРИОНА»*\n\n"
                f"Купол активирован. Над парком вспыхивает невидимая пелена, отсекающая сигналы извне. В этот момент "
                f"один из выживших протягивает вам старый кожаный тубус, найденный в руинах клиники. \n\n"
                f"Внутри — оригинальные чертежи вашего отца. Там описан проект «Эгида». Оказывается, Семя не было "
                f"создано для войны. Это был проект терраформирования Марса, который Академия украла и применила на Земле. "
                f"Но там есть приписка: «Если Сбой случится, только резонанс 41-го года сможет вернуть процесс вспять». \n\n"
                f"Марти: 'Док, 41 год... Это же сейчас! Но для полного очищения города нам нужен «Первичный Реактор», "
                f"который спрятан под «Азовсталью». Линдер и Инквизиторы уже там — они хотят запустить процесс самоуничтожения, "
                f"чтобы город не достался нам'.")
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("Выдвигаться к Азовстали", callback_data="apoc_s5_10"),
            tele_types.InlineKeyboardButton("Подготовить транспорт для отряда", callback_data="apoc_s5_clue_transport")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 10: СТАЛЬНОЙ ГИГАНТ ] ---
    elif call.data == "apoc_s5_10":
        text = (f"🏗 *ПРИЗРАКИ ЗАВОДА*\n\n"
                f"Вы стоите у ворот огромного промышленного комплекса. Здесь фиолетовый мох всё еще силен, он оплел "
                f"доменные печи, превратив их в подобие спящих вулканов. Где-то в глубине слышен гул работающих турбин. \n\n"
                f"Марти: 'Системы Линдера заблокировали главный вход. Но я вижу технический лаз через дренажную систему. "
                f"Док, Влад говорит, что он слышит сердце завода. Оно бьется аритмично. Нам нужно пробраться внутрь "
                f"и найти пульт управления Реактором. Но будьте осторожны: Академия выставила здесь автоматические "
                f"охранные системы «Цербер»'.")
        kb = tele_types.InlineKeyboardMarkup().add(
            tele_types.InlineKeyboardButton("Войти в дренажные туннели", callback_data="apoc_s5_11")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 11: ШЕПОТ ТУННЕЛЕЙ ] ---
    elif call.data == "apoc_s5_11":
        text = (f"🌊 *СЫРОСТЬ И СТАЛЬ*\n"
                f"──────────────────────────\n"
                f"Вы спускаетесь в дренажную систему. Вода здесь светится слабым бирюзовым светом — Семя реагирует на "
                f"концентрацию органики в стоках. Влад идет впереди, его шаги не издают звука, но стены туннеля "
                f"будто расступаются перед ним.\n\n"
                f"Марти (принюхиваясь): 'Док, здесь пахнет озоном и жженой проводкой. «Церберы» Академии "
                f"где-то рядом. Они не используют зрение, они чувствуют вибрацию пола. Нам нужно двигаться "
                f"в такт работающим насосам, чтобы слиться с шумом завода. Влад говорит, что впереди развилка. "
                f"Левый путь ведет к охладителям, правый — к пульту управления давлением. Нам нужно снизить "
                f"напор в системе, чтобы открыть гермозатвор'.")
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("Идти к пульту управления давлением", callback_data="apoc_s5_12"),
            tele_types.InlineKeyboardButton("Проверить состояние охладителей", callback_data="apoc_s5_clue_coolant")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 12: ТРЕХМЕРНАЯ ОПОРА ] ---
    elif call.data == "apoc_s5_12":
        text = (f"⚙️ *ГИДРАВЛИЧЕСКИЙ ЗАМОК*\n\n"
                f"Вы добираетесь до пульта. Это массивная стальная панель с тремя рычагами. Над ними — схема "
                f"верхней челюсти, разделенная на сегменты. Голос системы безопасности Академии: «Для сброса давления "
                f"подтвердите знание структуры верхних опор. Сколько корней у первого верхнего моляра в стандартной анатомии?»\n\n"
                f"Марти: 'Док, это снова проверка на «своего». Верхние моляры — это атланты, держащие свод. "
                f"Если введем неверное количество корней, рычаги заблокируются, и нас просто зальет кипятком из системы охлаждения!'.")
        kb = tele_types.InlineKeyboardMarkup(row_width=3).add(
            tele_types.InlineKeyboardButton("2", callback_data="apoc_s5_roots_fail"),
            tele_types.InlineKeyboardButton("3", callback_data="apoc_s5_13"),
            tele_types.InlineKeyboardButton("4", callback_data="apoc_s5_roots_fail")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 13: СХВАТКА С ЦЕРБЕРОМ ] ---
    elif call.data == "apoc_s5_13":
        if not has_flag(current_node, "logic_roots_done"):
            current_node = add_flag(current_node, "logic_roots_done")
            set_game_node(user_id, current_node)
            add_xp(user_id, 40, username)

        text = (f"🐕 *СТАЛЬНОЙ ОГЛАЛТЕЛОСТЬ*\n\n"
                f"Рычаги поддаются, давление падает, и тяжелая дверь отходит в сторону. Но за ней вас уже ждет «Цербер» — "
                f"четвероногий робот-убийца с лазерным наведением. Он блокирует путь к Реактору. Его корпус покрыт "
                f"отражающим составом, который делает ваш Лазерный Бор бесполезным.\n\n"
                f"Марти: 'Док, он настроен на тепло! Влад, хватай папу за руку! Если Влад использует холод Семени, "
                f"мы станем невидимыми для его датчиков на несколько секунд. Это наш единственный шанс проскочить "
                f"к лестнице. Но нужно действовать мгновенно, пока Семя не перегрелось!'.")
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("Использовать тепловую маскировку Влада", callback_data="apoc_s5_14"),
            tele_types.InlineKeyboardButton("Попробовать ослепить робота фонарем", callback_data="apoc_s5_combat_fail")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 14: ПРОЕКТ «БЛИЗНЕЦЫ» ] ---
    elif call.data == "apoc_s5_14":
        text = (f"🎭 *ОТКРОВЕНИЕ ЛИНДЕРА*\n\n"
                f"Вы врываетесь в зал управления Реактором. Линдер стоит у терминала, вводя коды детонации. Он поворачивается, "
                f"и вы видите, что половина его лица заменена на цифровой интерфейс. \n\n"
                f"**ЛИНДЕР:** 'Ты так и не понял, Дмитрий. Вы с Навигатором — две стороны одной медали. Проект «Близнецы» "
                f"не подразумевал выживания обоих. Один должен был стать волей Академии, другой — защитником праха. "
                f"Но Семя выбрало тебя... и этого ребенка. Знаешь, почему он выглядит как твой сын? Потому что он — твоя "
                f"итерация из 1985-го, сохраненная в идеальной матрице. Ты защищаешь самого себя, Док. Но я сотру "
                f"эту матрицу вместе с заводом'.")
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("Атаковать терминал управления", callback_data="apoc_s5_15"),
            tele_types.InlineKeyboardButton("Попробовать перехватить контроль через Влада", callback_data="apoc_s5_clue_hack")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 15: СЕРДЦЕ АЗОВСТАЛИ ] ---
    elif call.data == "apoc_s5_15":
        if not has_flag(current_node, "terminal_attacked"):
            current_node = add_flag(current_node, "terminal_attacked")
            set_game_node(user_id, current_node)

        text = (f"☢️ *ТОЧКА НЕВОЗВРАТА*\n\n"
                f"Ваш выстрел разрушает консоль, но обратный отсчет уже запущен. Пол под ногами начинает вибрировать — "
                f"Первичный Реактор внизу входит в критическую фазу. Линдер исчезает в облаке пара, оставляя вас "
                f"перед зияющей шахтой Реактора. \n\n"
                f"Влад подходит к самому краю: 'Папа, я знаю, что делать. Семя должно соединиться с ядром. "
                f"Это остановит взрыв и запустит очищение воздуха по всему Приазовью. Но если я спущусь туда, "
                f"я могу... измениться. Ты готов отпустить меня, чтобы спасти город?'.\n\n"
                f"Марти: 'Док, радары сходят с ума! Орбитальная группировка «Орион» начала снижение. Они хотят "
                f"забрать Реактор целиком, вырвав его из земли вместе с нами! Нам нужно решить прямо сейчас!'.")
        kb = tele_types.InlineKeyboardMarkup().add(
            tele_types.InlineKeyboardButton("Разрешить Владу войти в Реактор", callback_data="apoc_s5_16")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 16: СИНХРОНИЗАЦИЯ ДУШ ] ---
    elif call.data == "apoc_s5_16":
        text = (f"🧬 *ЯДРО ЖИЗНИ*\n"
                f"──────────────────────────\n"
                f"Влад делает шаг в шахту Реактора. Потоки чистой энергии окутывают его, пытаясь растворить его физическую оболочку в био-коде города. "
                f"Вы видите, как его очертания начинают дрожать, становясь прозрачными. Семя в центре Реактора пульсирует, требуя полной отдачи.\n\n"
                f"Марти: 'Док, он теряет себя! Городской массив слишком огромен, он поглощает его сознание. Нам нужно "
                f"создать «якорь» через ваш Анализатор. Подайте на него сигнал, основанный на базовых константах человеческого тела. "
                f"Вспомните, сколько постоянных зубов в норме у взрослого человека, если исключить зубы мудрости? "
                f"Это число станет биологическим фильтром, который не даст Владу превратиться в чистую энергию!'.")
        kb = tele_types.InlineKeyboardMarkup(row_width=3).add(
            tele_types.InlineKeyboardButton("20", callback_data="apoc_s5_anchor_fail"),
            tele_types.InlineKeyboardButton("28", callback_data="apoc_s5_17"),
            tele_types.InlineKeyboardButton("32", callback_data="apoc_s5_anchor_fail")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 17: ОРБИТАЛЬНЫЙ ГНЕВ ] ---
    elif call.data == "apoc_s5_17":
        if not has_flag(current_node, "human_anchor_set"):
            current_node = add_flag(current_node, "human_anchor_set")
            set_game_node(user_id, current_node)
            add_xp(user_id, 45, username)
            # Внимание: таймер! 
            set_game_timer(user_id, 5) 

        text = (f"🛰 *НЕБО ПАДАЕТ*\n\n"
                f"Число 28 сработало! Процесс стабилизировался, Влад сохраняет человеческий облик, но он всё еще внутри потока. "
                f"В этот момент небо над заводом раскалывается. Академия Орион начала орбитальную бомбардировку. "
                f"Их лучи бьют по куполу цеха, пытаясь прервать очищение.\n\n"
                f"Марти: 'Док, они перегружают наши щиты! Нам нужно перенаправить энергию Реактора обратно на их спутники. "
                f"Влад готов выпустить импульс, но ему нужен точный вектор на Полярную звезду — наш вечный северный навигатор. "
                f"В каком созвездии нам искать альфу, чтобы замкнуть орбитальное кольцо?'")
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("Малая Медведица", callback_data="apoc_s5_18"),
            tele_types.InlineKeyboardButton("Большая Медведица", callback_data="apoc_s5_astro_fail"),
            tele_types.InlineKeyboardButton("Дракон", callback_data="apoc_s5_astro_fail")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 18: ПОСЛЕДНИЙ РУБЕЖ ЛИНДЕРА ] ---
    elif call.data == "apoc_s5_18":
        if not has_flag(current_node, "orbital_strike_deflected"):
            current_node = add_flag(current_node, "orbital_strike_deflected")
            set_game_node(user_id, current_node)

        text = (f"🔥 *ПЕПЕЛ И ИСТИНА*\n\n"
                f"Импульс уходит в небо, и один из спутников Академии взрывается ослепительной искрой. Гул бомбардировки затихает. "
                f"Но из дыма у входа появляется Линдер. Он тяжело ранен, его броня оплавлена, но в руках он сжимает "
                f"ручной детонатор, подключенный к резервуарам с фиолетовым газом под вашими ногами.\n\n"
                f"**ЛИНДЕР:** 'Если я не могу владеть этим городом, то и жизни в нем не будет. Мой палец на кнопке, Дмитрий. "
                f"Сдай мне Влада сейчас, или я превращу «Азовсталь» и всё ваше поселение в братскую могилу. "
                f"У тебя есть 10 секунд, чтобы решить: жизнь сына или будущее города'.")
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("Броситься на Линдера с Лазерным Бором", callback_data="apoc_s5_19"),
            tele_types.InlineKeyboardButton("Приказать Марти перегрызть кабель", callback_data="apoc_s5_marti_hero")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 19: КРАХ ПРЕДАТЕЛЯ ] ---
    elif call.data == "apoc_s5_19":
        text = (f"💥 *ФИНАЛЬНЫЙ ВЫСТРЕЛ*\n\n"
                f"Вы делаете рывок. Линдер нажимает на кнопку, но вместо взрыва раздается лишь шипение. Влад, всё еще "
                f"связанный с Реактором, за долю секунды изменил состав газа в трубах, превратив его в инертный туман. "
                f"Ваш Лазерный Бор прожигает интерфейс на груди Линдера. \n\n"
                f"**ЛИНДЕР:** 'Вы... вы победили... но Академия не остановится... Смена... уже... началась...'\n\n"
                f"Он падает, и его тело начинает быстро распадаться на цифровые пиксели — он сам был лишь сложным аватаром. "
                f"Марти: 'Док, это конец Линдера, но Реактор достиг пика! Нам нужно вытащить Влада, пока дверь в шахту "
                f"не заварилась навсегда под давлением очищенного кислорода!'.")
        kb = tele_types.InlineKeyboardMarkup().add(
            tele_types.InlineKeyboardButton("Вытащить Влада из шахты", callback_data="apoc_s5_20")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 20: ПЕРВЫЙ ВДОХ НОВОГО МИРА ] ---
    elif call.data == "apoc_s5_20":
        if not has_flag(current_node, "vlad_saved_human"):
            current_node = add_flag(current_node, "vlad_saved_human")
            set_game_node(user_id, current_node)

        text = (f"🌿 *ЗЕЛЕНЫЙ МАРИУПОЛЬ*\n\n"
                f"Вы вытягиваете Влада из света. Он падает в ваши руки — живой, теплый, с обычным человеческим пульсом. "
                f"В этот момент мощная волна свежего воздуха вырывается из завода и проносится над городом. "
                f"Фиолетовый мох на глазах превращается в изумрудную траву. Люди в поселении начинают дышать полной грудью.\n\n"
                f"Марти (радостно лая): 'Док! Мы это сделали! Воздух чист! Радар показывает, что силы Академии "
                f"в этом секторе полностью дезориентированы. Мы получили передышку. Но посмотрите на небо... "
                f"спутники «Ориона» уходят на перегруппировку. Нам нужно подготовить город к долгой обороне и "
                f"начать строительство нового дома'.")
        kb = tele_types.InlineKeyboardMarkup().add(
            tele_types.InlineKeyboardButton("Начать этап восстановления города", callback_data="apoc_s5_21")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 21: ФУНДАМЕНТ БУДУЩЕГО ] ---
    elif call.data == "apoc_s5_21":
        text = (f"🏗 *ПЕРВЫЙ КАМЕНЬ*\n"
                f"──────────────────────────\n"
                f"Воздух над «Меотидой» стал чистым. Теперь нужно решить, что станет сердцем нашего нового дома. "
                f"Вы указываете на прибрежный холм: там будет Обсерватория «Зенит». \n\n"
                f"Марти: 'Док, Влад уже начал проектировать линзы. Но для настройки телескопа нам нужно "
                f"откалибровать зеркала. Система спрашивает: сколько зубов в одной челюсти "
                f"взрослого человека (без учета зубов мудрости)?'")
        kb = tele_types.InlineKeyboardMarkup(row_width=3).add(
            tele_types.InlineKeyboardButton("14", callback_data="apoc_s5_22"),
            tele_types.InlineKeyboardButton("16", callback_data="apoc_s5_const_fail"),
            tele_types.InlineKeyboardButton("10", callback_data="apoc_s5_const_fail")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 22: ПЕРВЫЙ УРОЖАЙ ] ---
    elif call.data == "apoc_s5_22":
        if not has_flag(current_node, "observatory_start"):
            current_node = add_flag(current_node, "observatory_start")
            set_game_node(user_id, current_node)

        text = (f"🌾 *БИО-РЕГЕНЕРАЦИЯ*\n\n"
                f"Пока строится обсерватория, Влад обнаруживает, что очищенный мох превратился в плодородный ил. "
                f"Нам нужно засеять первые поля, чтобы прокормить выживших. Но в почве остались «фиолетовые споры». \n\n"
                f"Марти: 'Док, чтобы нейтрализовать остатки химии Академии, нам нужен раствор с идеальным pH. "
                f"Влад говорит, что для защиты эмали растений нужен тот же баланс, что и в слюне здорового человека. "
                f"Какое значение pH считается нейтральным и безопасным для тканей?'.")
        kb = tele_types.InlineKeyboardMarkup(row_width=3).add(
            tele_types.InlineKeyboardButton("5.5", callback_data="apoc_s5_ph_fail"),
            tele_types.InlineKeyboardButton("7.0", callback_data="apoc_s5_23"),
            tele_types.InlineKeyboardButton("8.5", callback_data="apoc_s5_ph_fail")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 23: ШЕПОТ ГЛУБИН ] ---
    elif call.data == "apoc_s5_23":
        if not has_flag(current_node, "ph_logic_done"):
            current_node = add_flag(current_node, "ph_logic_done")
            set_game_node(user_id, current_node)
            add_xp(user_id, 30, username)

        text = (f"🌊 *ТАЙНА МОРСКОГО ДНА*\n\n"
                f"Поля засеяны, но радар «Меотиды» фиксирует странный объект в Азовском море. Это старая подводная лаборатория "
                f"вашего отца, которая начала подавать сигнал после очистки Ядра. \n\n"
                f"Марти: 'Док, там хранятся резервные копии памяти всех жителей до 1985 года! Если мы их достанем, "
                f"люди смогут вспомнить свою настоящую жизнь. Но шлюз лаборатории заблокирован. Код доступа — "
                f"это порядковый номер самого твердого зуба в челюсти, который дед называл «глазным»'.")
        kb = tele_types.InlineKeyboardMarkup(row_width=3).add(
            tele_types.InlineKeyboardButton("1", callback_data="apoc_s5_code_fail"),
            tele_types.InlineKeyboardButton("3", callback_data="apoc_s5_24"),
            tele_types.InlineKeyboardButton("6", callback_data="apoc_s5_code_fail")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 24: ВОЗВРАЩЕНИЕ ИМЕН ] ---
    elif call.data == "apoc_s5_24":
        if not has_flag(current_node, "memory_restored"):
            current_node = add_flag(current_node, "memory_restored")
            set_game_node(user_id, current_node)

        text = (f"💾 *ЦИФРОВОЕ ВОСКРЕШЕНИЕ*\n\n"
                f"Вы загружаете данные в сеть поселения. Люди замирают. К ним возвращаются воспоминания: лица родителей, "
                f"запах моря в детстве, их настоящие имена. Город перестает быть сборищем теней и становится обществом.\n\n"
                f"Влад: 'Папа, они теперь знают, кто они. И они смотрят на нас. Нам нужно дать им символ. "
                f"Обсерватория почти готова, зеркала поймали первый свет Канопуса. Но Академия «Орион» "
                f"направила к нам свой последний «Дрон-Жнец», чтобы уничтожить сервер памяти!'.")
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("Развернуть ПВО завода на перехват", callback_data="apoc_s5_25"),
            tele_types.InlineKeyboardButton("Использовать резонанс Обсерватории", callback_data="apoc_s5_clue_laser")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 25: ПЕРЕХВАТ В ЗЕНИТЕ ] ---
    elif call.data == "apoc_s5_25":
        text = (f"🎯 *ОГНЕННЫЙ ДОЖДЬ*\n\n"
                f"Дрон Академии вспыхивает в небе, как падающая звезда. Обломки падают далеко в море. Поселение ликует. "
                f"Вы стоите на пороге новой эры. У вас есть еда, память и защита. \n\n"
                f"Марти: 'Это была их последняя попытка помешать нам на земле. Теперь они будут бить только из космоса. "
                f"Док, Обсерватория готова к финальной калибровке. Влад ждет вас у главного окуляра. "
                f"Пришло время заглянуть за край и поставить точку в этой войне'.")
        kb = tele_types.InlineKeyboardMarkup().add(
            tele_types.InlineKeyboardButton("Войти в Обсерваторию для финала", callback_data="apoc_s5_26")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 26: ГЛАЗ ЦИКЛОПА ] ---
    elif call.data == "apoc_s5_26":
        text = (f"🔭 *ОКУЛЯР СУДЬБЫ*\n"
                f"──────────────────────────\n"
                f"Вы входите в зал управления обсерваторией. Огромная линза из чистого кварца направлена в бездну. "
                f"Влад стоит у консоли, его пальцы порхают над сенсорами. На экранах — тепловая карта орбиты, где "
                f"пульсирует алая точка. Это «Сердце Ориона» — главный спутник-координатор.\n\n"
                f"Влад: 'Папа, чтобы пробить их щиты, нам нужно сфокусировать луч через созвездие, которое "
                f"дед называл «Северным Крестом». Оно летит по Млечному Пути и указывает на лебединую верность нашему миру. "
                f"Только через его главную звезду Денеб мы сможем передать код очищения на всю планету'.")
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("Навести телескоп на созвездие Лебедя", callback_data="apoc_s5_27"),
            tele_types.InlineKeyboardButton("Искать созвездие Лиры", callback_data="apoc_s5_astro_fail"),
            tele_types.InlineKeyboardButton("Искать созвездие Орла", callback_data="apoc_s5_astro_fail")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 27: ПОСЛЕДНЯЯ ЗАПИСЬ (1985) ] ---
    elif call.data == "apoc_s5_27":
        if not has_flag(current_node, "telescope_aligned"):
            current_node = add_flag(current_node, "telescope_aligned")
            set_game_node(user_id, current_node)
            add_xp(user_id, 70, username)

        text = (f"📼 *ГОЛОС СКВОЗЬ ВРЕМЯ*\n\n"
                f"Луч захватывает спутник, и вместо ответного огня система «Орион» внезапно начинает транслировать "
                f"скрытый архив. На всех экранах появляется ваш отец. Он стоит здесь же, в этой обсерватории, "
                f"за день до того, как его не стало. \n\n"
                f"**ОТЕЦ:** 'Дима, если этот сигнал пробился, значит, ты победил страх. Семя — это не оружие. "
                f"Это био-архив нашей цивилизации. Мы боялись потерять всё, что знали, и создали систему сохранения. "
                f"Но Академия превратила её в клетку. Влад — это живой ключ к свободе. Чтобы отключить протокол контроля, "
                f"введи финальный код. Он равен количеству корней у всех твоих резцов. Это символ того, что человек "
                f"крепко стоит на своей земле одной опорой, но вместе мы — фундамент'.")
        kb = tele_types.InlineKeyboardMarkup(row_width=3).add(
            tele_types.InlineKeyboardButton("4", callback_data="apoc_s5_final_code_fail"),
            tele_types.InlineKeyboardButton("8", callback_data="apoc_s5_28"),
            tele_types.InlineKeyboardButton("16", callback_data="apoc_s5_final_code_fail")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 28: БИТВА В ВЕРХНИХ СЛОЯХ ] ---
    elif call.data == "apoc_s5_28":
        if not has_flag(current_node, "final_code_accepted"):
            current_node = add_flag(current_node, "final_code_accepted")
            set_game_node(user_id, current_node)

        text = (f"📡 *ПАДЕНИЕ ИДОЛОВ*\n\n"
                f"Код «8» принят. Орбитальная сеть Академии начинает распадаться. Спутники один за другим "
                f"выходят из строя и сгорают в атмосфере, превращаясь в яркие метеоры. Контроль «Ориона» над Землей "
                f"официально прекращен. Но ИИ спутника делает последний шаг — он направляет остатки энергии на "
                f"терминал Обсерватории, чтобы уничтожить вас вместе с данными.\n\n"
                f"Марти (прыгая на пульт): 'Док, перегрузка! Влад, держись за меня! Нужно перенаправить поток "
                f"в землю, в корни «Меотиды»! Если мы не успеем, здание станет пеплом за 5 секунд!'.")
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("Заземлить энергию через стальные опоры", callback_data="apoc_s5_29"),
            tele_types.InlineKeyboardButton("Попробовать отключить питание вручную", callback_data="apoc_s5_overload_fail")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 29: ГОРИЗОНТ СОБЫТИЙ ] ---
    elif call.data == "apoc_s5_29":
        text = (f"🏙 *НОВЫЙ ПОЛДЕНЬ*\n\n"
                f"Энергия уходит в землю, заставляя весь холм светиться мягким белым светом. Тишина. Впервые за сорок лет "
                f"в небе нет ни одного шпионского дрона. Вы выходите на балкон. Перед вами Мариуполь — живой, зеленый, "
                f"наполненный голосами проснувшихся людей. \n\n"
                f"Влад подходит к вам. Он больше не проект, не субъект и не наследник. Он просто ваш сын, который "
                f"смотрит на мир с надеждой. \n\n"
                f"**ВЛАД:** 'Папа, смотри... там, в порту, пришвартовался первый корабль. И люди... они больше не боятся. "
                f"Что мы скажем им завтра? Каким будет наш первый закон в этом новом мире?'.")
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("«Порядок и Знание»", callback_data="apoc_s5_30_order"),
            tele_types.InlineKeyboardButton("«Свобода и Исследование»", callback_data="apoc_s5_30_freedom"),
            tele_types.InlineKeyboardButton("«Милосердие и Труд»", callback_data="apoc_s5_30_mercy")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # 🏆 --- [ ЭТАП 30: ЭПИЛОГ И ТИТРЫ ] --- 🏆
    elif call.data.startswith("apoc_s5_30"):
        ending = "Свободы" if "freedom" in call.data else "Порядка" if "order" in call.data else "Милосердия"
        is_first_time = not has_completed_chapter(user_id, "chapter_5")
        
        if is_first_time:
            xp_reward = 1000
            dust_reward = 500
            mark_chapter_completed(user_id, "chapter_5")
            reward_msg = f"🎁 **ГРАНД-ФИНАЛ ПРОЙДЕН:**\n✨ Опыт: +{xp_reward} XP\n💎 Пыль: +{dust_reward} ед.\n"
        else:
            xp_reward = 100
            dust_reward = 100
            reward_msg = f"🔄 **НАГРАДА ЗА ПОВТОРНОЕ ПРОХОЖДЕНИЕ:**\n✨ Опыт: +{xp_reward} XP\n💎 Пыль: +{dust_reward} ед.\n"

        if not has_flag(current_node, "ch5_done"):
            add_xp(user_id, xp_reward, username)
            current_node = add_flag(current_node, "ch5_done")
            current_node = add_flag(current_node, f"ending_{ending}")
            current_node = set_loc(current_node, "apoc_game_completed_screen")
            set_game_node(user_id, current_node)

        text = (f"🏆 *ФИНАЛ: ПУТЬ {ending.upper()}*\n"
                f"──────────────────────────\n"
                f"Командор, ваша история подошла к концу. Вы прошли путь от маленькой клиники до спасения человечества. "
                f"Мариуполь стал маяком новой цивилизации, а Обсерватория «Зенит» — её сердцем.\n\n"
                f"**ВАШИ ИТОГИ:**\n"
                f"🧬 *Влад* остался человеком, сохранив искру жизни.\n"
                f"🐕 *Марти* стал легендой поселения, «собакой, победившей роботов».\n"
                f"🪐 *Академия Орион* изгнана с Земли, но небо навсегда осталось под вашим присмотром.\n"
                f"🦷 *Медицинское наследие* отца восстановлено и служит людям.\n\n"
                f"{reward_msg}\n"
                f"Вы закрываете дневник юного космонавта. Впереди — бесконечность.\n\n"
                f"*СПАСИБО ЗА ИГРУ, ДМИТРИЙ ВЛАДИМИРОВИЧ!*")
        
        kb = tele_types.InlineKeyboardMarkup().add(
            tele_types.InlineKeyboardButton("🏆 Вернуться в главное меню", callback_data="game_main_menu")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # =====================================================================
    # --- [ БЛОК ОБРАБОТЧИКОВ ОШИБОК И ДЕТЕКТИВНЫХ УЛИК ] ---
    # =====================================================================
    elif call.data == "apoc_s5_med_fail":
        bot.answer_callback_query(call.id, "❌ Пациенту больно! Инфекция распространяется. Вспоминайте точку Apex!", show_alert=True)
        return
    elif call.data == "apoc_s5_astro_fail":
        bot.answer_callback_query(call.id, "❌ Ошибка ключа. Спутник не распознает созвездие. Посмотрите на небо!", show_alert=True)
        return
    elif call.data == "apoc_s5_trap_fail":
        bot.answer_callback_query(call.id, "⚠️ ОШИБКА: Инквизиторы используют фильтры шума! Акустика их не берет. Включайте воду!", show_alert=True)
        return
    elif call.data == "apoc_s5_spy_fail":
        bot.answer_callback_query(call.id, "❌ Марти: 'Док, вы ошиблись! Этот парень просто болен, а настоящий шпион чуть не ускользнул!'", show_alert=True)
        return
    elif call.data == "apoc_s5_shield_fail":
        bot.answer_callback_query(call.id, "❌ Купол не синхронизируется. Ориентир выбран неверно. Ищите созвездие-ковш!", show_alert=True)
        return
    elif call.data == "apoc_s5_roots_fail":
        bot.answer_callback_query(call.id, "❌ Неверно! Давление растет! Вспомните анатомию верхних моляров — сколько у них корней?", show_alert=True)
        return
    elif call.data == "apoc_s5_combat_fail":
        bot.answer_callback_query(call.id, "⚠️ Опасно! Фонарь только выдал вашу позицию! Цербер атакует!", show_alert=True)
        return
    elif call.data == "apoc_s5_anchor_fail":
        bot.answer_callback_query(call.id, "❌ Марти: 'Док, сигнал нестабилен! Влад начинает растворяться! Вспомните базу постоянных зубов!'", show_alert=True)
        return
    elif call.data == "apoc_s5_marti_hero":
        bot.answer_callback_query(call.id, "🐶 Марти: 'Я бы с радостью, Док, но там напряжение в 10 киловольт! Лучше используйте Бор!'", show_alert=True)
        return
    elif call.data == "apoc_s5_const_fail":
        bot.answer_callback_query(call.id, "❌ Марти: 'Док, математика не сходится! Вспомните, сколько зубов в одной челюсти взрослого без восьмерок?'", show_alert=True)
        return
    elif call.data == "apoc_s5_ph_fail":
        bot.answer_callback_query(call.id, "❌ Марти: 'Док, кислота или щелочь убьют посевы! Нам нужен идеальный нейтральный баланс!'", show_alert=True)
        return
    elif call.data == "apoc_s5_code_fail":
        bot.answer_callback_query(call.id, "❌ Марти: 'Док, замок пищит! Глазной зуб — это клык. Какой он по счету от центра?'", show_alert=True)
        return
    elif call.data == "apoc_s5_final_code_fail":
        bot.answer_callback_query(call.id, "❌ Ошибка кода! Вспомните анатомию: сколько резцов у взрослого человека и сколько у них корней? Только один у каждого!", show_alert=True)
        return
    elif call.data == "apoc_s5_overload_fail":
        bot.answer_callback_query(call.id, "⚠️ Слишком медленно! Ручное управление заблокировано. Используйте заземление!", show_alert=True)
        return
    elif call.data == "apoc_s5_clue_scan":
        if not has_flag(current_node, "clue_scan"):
            current_node = add_flag(current_node, "clue_scan")
            set_game_node(user_id, current_node)
            add_xp(user_id, 5, username)
        bot.answer_callback_query(call.id, "🔍 СКАНИРОВАНИЕ: Влад чувствует слабые сигналы под землей. Это старые коммуникации, они нам еще пригодятся.", show_alert=True)
        return
    elif call.data == "apoc_s5_clue_negotiate":
        if not has_flag(current_node, "clue_negotiate"):
            current_node = add_flag(current_node, "clue_negotiate")
            set_game_node(user_id, current_node)
            add_xp(user_id, 5, username)
        bot.answer_callback_query(call.id, "🗣 ПЕРЕГОВОРЫ: Линдер не слушает. Его шлем блокирует внешние звуки. Он пришел только уничтожать.", show_alert=True)
        return
    elif call.data == "apoc_s5_clue_traitor":
        if not has_flag(current_node, "clue_traitor"):
            current_node = add_flag(current_node, "clue_traitor")
            set_game_node(user_id, current_node)
            add_xp(user_id, 5, username)
        bot.answer_callback_query(call.id, "📷 КАМЕРЫ: Записи стерты! Кто-то профессионально заметает следы. Действовать нужно через прямой осмотр.", show_alert=True)
        return
    elif call.data == "apoc_s5_clue_transport":
        if not has_flag(current_node, "clue_transport"):
            current_node = add_flag(current_node, "clue_transport")
            set_game_node(user_id, current_node)
            add_xp(user_id, 5, username)
        bot.answer_callback_query(call.id, "🚙 ТРАНСПОРТ: Старый электрокар Академии разряжен. Пешком мы доберемся быстрее и незаметнее.", show_alert=True)
        return
    elif call.data == "apoc_s5_clue_coolant":
        if not has_flag(current_node, "clue_coolant"):
            current_node = add_flag(current_node, "clue_coolant")
            set_game_node(user_id, current_node)
            add_xp(user_id, 5, username)
        bot.answer_callback_query(call.id, "❄️ ОХЛАДИТЕЛИ: Уровень фреона в норме. Проблема не здесь, идите к пульту давления!", show_alert=True)
        return
    elif call.data == "apoc_s5_clue_hack":
        if not has_flag(current_node, "clue_hack"):
            current_node = add_flag(current_node, "clue_hack")
            set_game_node(user_id, current_node)
            add_xp(user_id, 5, username)
        bot.answer_callback_query(call.id, "💻 ВЗЛОМ: Защита Линдера квантовая. Влад не может ее пробить, не рискуя своим разумом. Используйте Бор!", show_alert=True)
        return
    elif call.data == "apoc_s5_clue_laser":
        if not has_flag(current_node, "clue_laser"):
            current_node = add_flag(current_node, "clue_laser")
            set_game_node(user_id, current_node)
            add_xp(user_id, 5, username)
        bot.answer_callback_query(call.id, "🔭 РЕЗОНАНС: Зеркала еще не откалиброваны для боевого луча. Придется сбивать дедовским способом!", show_alert=True)
        return
