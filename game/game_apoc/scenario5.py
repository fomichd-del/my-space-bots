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

    # --- [ 1. БЕЗОПАСНЫЙ ПАРСИНГ ТАЙМЕРА (БРОНЕБОЙНЫЙ) ] ---
    if timer_end:
        # Если база вернула время текстом, превращаем его в объект datetime
        if isinstance(timer_end, str):
            try:
                # Очищаем строку от миллисекунд и лишних букв T (ISO формат)
                clean_time = timer_end.split('.')[0].replace('T', ' ')
                timer_end = datetime.strptime(clean_time, "%Y-%m-%d %H:%M:%S")
            except Exception as e:
                # Если формат совсем дикий, выведем это в консоль (терминал), чтобы вы увидели!
                print(f"🚨 ОШИБКА ТАЙМЕРА: {e} | То, что выдала база: {timer_end}")
                timer_end = None
                
        # Если время еще не вышло - блокируем и показываем окно
        if timer_end and datetime.now() < timer_end:
            mins = int((timer_end - datetime.now()).total_seconds() // 60) + 1
            # Текст алерта сокращен, чтобы точно влезть в лимиты Telegram
            bot.answer_callback_query(call.id, f"⌛️ Процесс идет... Осталось {mins} мин.", show_alert=True)
            return

    # --- [ ЭТАП 1: ПЕРВЫЙ РАССВЕТ ] ---
    if call.data == "apoc_s5_start":
        text = (f"🌅 **ЭТАП 1: ПОСЛЕ БУРИ**\n"
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
        text = (f"🏥 **ЭТАП 2: ХИРУРГИЯ ДУШИ**\n\n"
                f"К вам приносят первого пациента — старик с сильным воспалением в области челюсти. После стазиса био-мох "
                f"оставил глубокие следы в мягких тканях. Вам нужно провести экстренную санацию, чтобы остановить сепсис. "
                f"У вас только старый набор инструментов и ваш Лазерный Бор.\n\n"
                f"Марти: 'Док, тут нужна ювелирная точность. Помните, как вы учили: при вскрытии глубоких полостей "
                f"главное — не задеть сосудисто-нервный пучок. Чтобы обезболить и очистить канал максимально эффективно, "
                f"на какой зоне пульпы нам нужно сосредоточить резонанс Бора? Вспомните анатомию: где находится "
                f"самая чувствительная точка входа нерва в корневой канал?'")
        # Логика: Апикальное отверстие (Apex).
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("Направить луч на апикальное отверстие", callback_data="apoc_s5_3"),
            tele_types.InlineKeyboardButton("Работать по коронковой части", callback_data="apoc_s5_med_fail"),
            tele_types.InlineKeyboardButton("Использовать общую дезинфекцию", callback_data="apoc_s5_med_fail")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 3: КОСМИЧЕСКИЙ РАДАР ] ---
    elif call.data == "apoc_s5_3":
        update_game_progress(user_id, current_node + "_logic_apex_done")
        add_xp(user_id, 50, username)
        text = (f"📡 **ЭТАП 3: СИГНАЛ В ПУСТОТУ**\n\n"
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
        update_game_progress(user_id, current_node + "_satellite_link")
        text = (f"👣 **ЭТАП 4: ПЕРВЫЕ ГОСТИ**\n\n"
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
        update_game_progress(user_id, current_node + "_base_fortified")
        text = (f"⚔️ **ЭТАП 5: СТОЛКНОВЕНИЕ**\n\n"
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

    # --- [ ОБРАБОТЧИКИ ОШИБОК ] ---
    elif call.data == "apoc_s5_med_fail":
        bot.answer_callback_query(call.id, "❌ Пациенту больно! Инфекция распространяется. Вспоминайте точку Apex!", show_alert=True)
        return

    elif call.data == "apoc_s5_astro_fail":
        bot.answer_callback_query(call.id, "❌ Ошибка ключа. Спутник не распознает созвездие. Посмотрите на небо — ищите W!", show_alert=True)
        return

  # --- [ ЭТАП 6: ГНЕВ СЕМЕНИ ] ---
    elif call.data == "apoc_s5_6":
        add_xp(user_id, 45, username)
        text = (f"⚡️ **ЭТАП 6: РЕЗОНАНС ВЕРТИКАЛИ**\n"
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
        text = (f"🔬 **ЭТАП 7: ПРОВЕРКА НА ЧИСТОТУ**\n\n"
                f"Вы собираете выживших для обязательного осмотра. Это единственный способ выявить скрытые био-импланты "
                f"Академии, через которые они транслируют страх. Вы используете Анализатор, чтобы проверить структуру эмали каждого. "
                f"У агентов «Ориона» она заменена на синтетический полимер.\n\n"
                f"Марти: 'Док, смотрите на этого парня. Он утверждает, что он местный рыбак. Но его «клыки» ведут себя странно "
                f"под ультрафиолетом. Чтобы не ошибиться и не обвинить невиновного, вспомните: сколько клыков (cuspids) "
                f"в норме должно быть у взрослого человека во рту? Любое другое число выдаст в нем аугментированного шпиона!'.")
        # Логика: 4 клыка (2 сверху, 2 снизу).
        kb = tele_types.InlineKeyboardMarkup(row_width=3).add(
            tele_types.InlineKeyboardButton("2", callback_data="apoc_s5_spy_fail"),
            tele_types.InlineKeyboardButton("4", callback_data="apoc_s5_8"),
            tele_types.InlineKeyboardButton("6", callback_data="apoc_s5_spy_fail")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 8: ЦИФРОВОЙ КУПОЛ ] ---
    elif call.data == "apoc_s5_8":
        update_game_progress(user_id, current_node + "_spy_captured")
        add_xp(user_id, 30, username)
        text = (f"🛡 **ЭТАП 8: СЕТЕВОЙ ЩИТ**\n\n"
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
        update_game_progress(user_id, current_node + "_shield_active")
        text = (f"📜 **ЭТАП 9: ЗАВЕЩАНИЕ «ОРИОНА»**\n\n"
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
        text = (f"🏗 **ЭТАП 10: ПРИЗРАКИ ЗАВОДА**\n\n"
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

    # --- [ ОБРАБОТЧИКИ ОШИБОК ] ---
    elif call.data == "apoc_s5_spy_fail":
        bot.answer_callback_query(call.id, "❌ Марти: 'Док, вы ошиблись! Этот парень просто болен, а настоящий шпион чуть не ускользнул!'", show_alert=True)
        return

    elif call.data == "apoc_s5_shield_fail":
        bot.answer_callback_query(call.id, "❌ Купол не синхронизируется. Ориентир выбран неверно. Ищите созвездие-навигатор!", show_alert=True)
        return

  # --- [ ЭТАП 11: ШЕПОТ ТУННЕЛЕЙ ] ---
    elif call.data == "apoc_s5_11":
        text = (f"🌊 **ЭТАП 11: СЫРОСТЬ И СТАЛЬ**\n"
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
        text = (f"⚙️ **ЭТАП 12: ГИДРАВЛИЧЕСКИЙ ЗАМОК**\n\n"
                f"Вы добираетесь до пульта. Это массивная стальная панель с тремя рычагами. Над ними — схема "
                f"верхней челюсти, разделенная на сегменты. Голос системы безопасности Академии: «Для сброса давления "
                f"подтвердите знание структуры верхних опор. Сколько корней у первого верхнего моляра в стандартной анатомии?»\n\n"
                f"Марти: 'Док, это снова проверка на «своего». Верхние моляры — это атланты, держащие свод. "
                f"Если введем неверное количество корней, рычаги заблокируются, и нас просто зальет кипятком из системы охлаждения!'.")
        # Логика: У первого верхнего моляра (6-й зуб) обычно 3 корня (2 щечных и 1 небный).
        kb = tele_types.InlineKeyboardMarkup(row_width=3).add(
            tele_types.InlineKeyboardButton("2", callback_data="apoc_s5_roots_fail"),
            tele_types.InlineKeyboardButton("3", callback_data="apoc_s5_13"),
            tele_types.InlineKeyboardButton("4", callback_data="apoc_s5_roots_fail")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 13: СХВАТКА С ЦЕРБЕРОМ ] ---
    elif call.data == "apoc_s5_13":
        update_game_progress(user_id, current_node + "_logic_roots_done")
        add_xp(user_id, 40, username)
        text = (f"🐕 **ЭТАП 13: СТАЛЬНОЙ ОГЛАЛТЕЛОСТЬ**\n\n"
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
        text = (f"🎭 **ЭТАП 14: ОТКРОВЕНИЕ ЛИНДЕРА**\n\n"
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
        update_game_progress(user_id, current_node + "_terminal_attacked")
        text = (f"☢️ **ЭТАП 15: ТОЧКА НЕВОЗВРАТА**\n\n"
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

    # --- [ ОБРАБОТЧИКИ ОШИБОК ] ---
    elif call.data == "apoc_s5_roots_fail":
        bot.answer_callback_query(call.id, "❌ Неверно! Давление растет! Вспомните анатомию верхних моляров — сколько у них корней?", show_alert=True)
        return

    elif call.data == "apoc_s5_combat_fail":
        bot.answer_callback_query(call.id, "⚠️ Опасно! Фонарь только выдал вашу позицию! Цербер атакует!", show_alert=True)
        return

  # --- [ ЭТАП 16: СИНХРОНИЗАЦИЯ ДУШ ] ---
    elif call.data == "apoc_s5_16":
        text = (f"🧬 **ЭТАП 16: ЯДРО ЖИЗНИ**\n"
                f"──────────────────────────\n"
                f"Влад делает шаг в шахту Реактора. Потоки чистой энергии окутывают его, пытаясь растворить его физическую оболочку в био-коде города. "
                f"Вы видите, как его очертания начинают дрожать, становясь прозрачными. Семя в центре Реактора пульсирует, требуя полной отдачи.\n\n"
                f"Марти: 'Док, он теряет себя! Городской массив слишком огромен, он поглощает его сознание. Нам нужно "
                f"создать «якорь» через ваш Анализатор. Подайте на него сигнал, основанный на базовых константах человеческого тела. "
                f"Вспомните, сколько постоянных зубов в норме у взрослого человека, если исключить зубы мудрости? "
                f"Это число станет биологическим фильтром, который не даст Владу превратиться в чистую энергию!'.")
        # Логика: 28 зубов (без зубов мудрости).
        kb = tele_types.InlineKeyboardMarkup(row_width=3).add(
            tele_types.InlineKeyboardButton("20", callback_data="apoc_s5_anchor_fail"),
            tele_types.InlineKeyboardButton("28", callback_data="apoc_s5_17"),
            tele_types.InlineKeyboardButton("32", callback_data="apoc_s5_anchor_fail")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 17: ОРБИТАЛЬНЫЙ ГНЕВ ] ---
    elif call.data == "apoc_s5_17":
        update_game_progress(user_id, current_node + "_human_anchor_set")
        add_xp(user_id, 45, username)
        # Устанавливаем таймер на стабилизацию (например, 5 минут)
        set_game_timer(user_id, 300) 
        text = (f"🛰 **ЭТАП 17: НЕБО ПАДАЕТ**\n\n"
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
        update_game_progress(user_id, current_node + "_orbital_strike_deflected")
        text = (f"🔥 **ЭТАП 18: ПЕПЕЛ И ИСТИНА**\n\n"
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
        text = (f"💥 **ЭТАП 19: ФИНАЛЬНЫЙ ВЫСТРЕЛ**\n\n"
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
        update_game_progress(user_id, current_node + "_vlad_saved_human")
        text = (f"🌿 **ЭТАП 20: ЗЕЛЕНЫЙ МАРИУПОЛЬ**\n\n"
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

    # --- [ ОБРАБОТЧИКИ ОШИБОК ] ---
    elif call.data == "apoc_s5_anchor_fail":
        bot.answer_callback_query(call.id, "❌ Марти: 'Док, сигнал нестабилен! Влад начинает растворяться! Вспомните базу постоянных зубов!'", show_alert=True)
        return

    elif call.data == "apoc_s5_marti_hero":
        bot.answer_callback_query(call.id, "🐶 Марти: 'Я бы с радостью, Док, но там напряжение в 10 киловольт! Лучше используйте Бор!'", show_alert=True)
        return

  # --- [ ЭТАП 21: ФУНДАМЕНТ БУДУЩЕГО ] ---
    elif call.data == "apoc_s5_21":
        text = (f"🏗 **ЭТАП 21: ПЕРВЫЙ КАМЕНЬ**\n"
                f"──────────────────────────\n"
                f"Воздух над «Меотидой» стал чистым. Теперь нужно решить, что станет сердцем нашего нового дома. "
                f"Вы указываете на прибрежный холм: там будет Обсерватория «Зенит». \n\n"
                f"Марти: 'Док, Влад уже начал проектировать линзы. Но для настройки телескопа нам нужно "
                f"откалибровать зеркала. Система спрашивает: сколько зубов в одной челюсти "
                f"взрослого человека (без учета зубов мудрости)?'")
        # Логика: 14 зубов.
        kb = tele_types.InlineKeyboardMarkup(row_width=3).add(
            tele_types.InlineKeyboardButton("14", callback_data="apoc_s5_22"),
            tele_types.InlineKeyboardButton("16", callback_data="apoc_s5_const_fail"),
            tele_types.InlineKeyboardButton("10", callback_data="apoc_s5_const_fail")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 22: ПЕРВЫЙ УРОЖАЙ ] ---
    elif call.data == "apoc_s5_22":
        update_game_progress(user_id, current_node + "_observatory_start")
        text = (f"🌾 **ЭТАП 22: БИО-РЕГЕНЕРАЦИЯ**\n\n"
                f"Пока строится обсерватория, Влад обнаруживает, что очищенный мох превратился в плодородный ил. "
                f"Нам нужно засеять первые поля, чтобы прокормить выживших. Но в почве остались «фиолетовые споры». \n\n"
                f"Марти: 'Док, чтобы нейтрализовать остатки химии Академии, нам нужен раствор с идеальным pH. "
                f"Влад говорит, что для защиты эмали растений нужен тот же баланс, что и в слюне здорового человека. "
                f"Какое значение pH считается нейтральным и безопасным для тканей?'.")
        # Логика: 7.0 (нейтральный pH).
        kb = tele_types.InlineKeyboardMarkup(row_width=3).add(
            tele_types.InlineKeyboardButton("5.5", callback_data="apoc_s5_ph_fail"),
            tele_types.InlineKeyboardButton("7.0", callback_data="apoc_s5_23"),
            tele_types.InlineKeyboardButton("8.5", callback_data="apoc_s5_ph_fail")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 23: ШЕПОТ ГЛУБИН ] ---
    elif call.data == "apoc_s5_23":
        add_xp(user_id, 30, username)
        text = (f"🌊 **ЭТАП 23: ТАЙНА МОРСКОГО ДНА**\n\n"
                f"Поля засеяны, но радар «Меотиды» фиксирует странный объект в Азовском море. Это старая подводная лаборатория "
                f"вашего отца, которая начала подавать сигнал после очистки Ядра. \n\n"
                f"Марти: 'Док, там хранятся резервные копии памяти всех жителей до 1985 года! Если мы их достанем, "
                f"люди смогут вспомнить свою настоящую жизнь. Но шлюз лаборатории заблокирован. Код доступа — "
                f"это порядковый номер самого твердого зуба в челюсти, который дед называл «глазным»'.")
        # Логика: Клык (3-й зуб от центра).
        kb = tele_types.InlineKeyboardMarkup(row_width=3).add(
            tele_types.InlineKeyboardButton("1", callback_data="apoc_s5_code_fail"),
            tele_types.InlineKeyboardButton("3", callback_data="apoc_s5_24"),
            tele_types.InlineKeyboardButton("6", callback_data="apoc_s5_code_fail")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 24: ВОЗВРАЩЕНИЕ ИМЕН ] ---
    elif call.data == "apoc_s5_24":
        update_game_progress(user_id, current_node + "_memory_restored")
        text = (f"💾 **ЭТАП 24: ЦИФРОВОЕ ВОСКРЕШЕНИЕ**\n\n"
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
        text = (f"🎯 **ЭТАП 25: ОГНЕННЫЙ ДОЖДЬ**\n\n"
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
        text = (f"🔭 **ЭТАП 26: ОКУЛЯР СУДЬБЫ**\n"
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
        add_xp(user_id, 70, username)
        text = (f"📼 **ЭТАП 27: ГОЛОС СКВОЗЬ ВРЕМЯ**\n\n"
                f"Луч захватывает спутник, и вместо ответного огня система «Орион» внезапно начинает транслировать "
                f"скрытый архив. На всех экранах появляется ваш отец. Он стоит здесь же, в этой обсерватории, "
                f"за день до того, как его не стало. \n\n"
                f"**ОТЕЦ:** 'Дима, если этот сигнал пробился, значит, ты победил страх. Семя — это не оружие. "
                f"Это био-архив нашей цивилизации. Мы боялись потерять всё, что знали, и создали систему сохранения. "
                f"Но Академия превратила её в клетку. Влад — это живой ключ к свободе. Чтобы отключить протокол контроля, "
                f"введи финальный код. Он равен количеству корней у всех твоих резцов. Это символ того, что человек "
                f"крепко стоит на своей земле одной опорой, но вместе мы — фундамент'.")
        # Логика: У каждого из 8 резцов (4 сверху, 4 снизу) по 1 корню. Итого 8.
        kb = tele_types.InlineKeyboardMarkup(row_width=3).add(
            tele_types.InlineKeyboardButton("4", callback_data="apoc_s5_final_code_fail"),
            tele_types.InlineKeyboardButton("8", callback_data="apoc_s5_28"),
            tele_types.InlineKeyboardButton("16", callback_data="apoc_s5_final_code_fail")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 28: БИТВА В ВЕРХНИХ СЛОЯХ ] ---
    elif call.data == "apoc_s5_28":
        update_game_progress(user_id, current_node + "_final_code_accepted")
        text = (f"📡 **ЭТАП 28: ПАДЕНИЕ ИДОЛОВ**\n\n"
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
        text = (f"🏙 **ЭТАП 29: НОВЫЙ ПОЛДЕНЬ**\n\n"
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

    # --- [ ЭТАП 30: ЭПИЛОГ И ТИТРЫ ] ---
    elif call.data.startswith("apoc_s5_30"):
        # Определяем концовку на основе выбора
        ending = "Свободы" if "freedom" in call.data else "Порядка" if "order" in call.data else "Милосердия"
        update_game_progress(user_id, current_node + f"_apoc_game_complete_{ending}")
        add_xp(user_id, 1000, username)
        
        text = (f"🏆 **ФИНАЛ: ПУТЬ {ending.upper()}**\n"
                f"──────────────────────────\n"
                f"Командор, ваша история подошла к концу. Вы прошли путь от маленькой клиники до спасения человечества. "
                f"Мариуполь стал маяком новой цивилизации, а Обсерватория «Зенит» — её сердцем.\n\n"
                f"**ВАШИ ИТОГИ:**\n"
                f"🧬 **Влад** остался человеком, сохранив искру жизни.\n"
                f"🐕 **Марти** стал легендой поселения, «собакой, победившей роботов».\n"
                f"🪐 **Академия Орион** изгнана с Земли, но небо навсегда осталось под вашим присмотром.\n"
                f"🦷 **Медицинское наследие** отца восстановлено и служит людям.\n\n"
                f"Вы закрываете дневник юного космонавта. Впереди — бесконечность.\n\n"
                f"**СПАСИБО ЗА ИГРУ, ДМИТРИЙ ВЛАДИМИРОВИЧ!**")
        
        bot.send_message(call.message.chat.id, text, parse_mode="Markdown")
        # Здесь можно вызвать финальное меню или просто закончить

    # --- [ ОБРАБОТЧИКИ ОШИБОК ] ---
    elif call.data == "apoc_s5_final_code_fail":
        bot.answer_callback_query(call.id, "❌ Ошибка кода! Вспомните анатомию: сколько резцов у взрослого человека и сколько у них корней? Только один у каждого!", show_alert=True)
        return

    elif call.data == "apoc_s5_overload_fail":
        bot.answer_callback_query(call.id, "⚠️ Слишком медленно! Ручное управление заблокировано. Используйте заземление!", show_alert=True)
        return
