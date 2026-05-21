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
    if call.data not in ["apoc_s3_start", "resume_game_3", "game_reset_ch3", "game_main_menu"]:
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
    if call.data == "apoc_s3_start":
        # Проверяем прохождение ГЛАВЫ 2
        if not has_completed_chapter(user_id, "chapter_2"):
            try: bot.answer_callback_query(call.id, "🔒 Доступ заблокирован! Сначала завершите Главу 2.", show_alert=True)
            except: pass
            return

        if loc in ["apoc_ch2_completed_screen", "apoc_start", "start"]:
            call.data = "apoc_s3_scene_1"
            current_node = set_loc(current_node, "apoc_s3_scene_1")
            set_game_node(user_id, current_node)
            loc = "apoc_s3_scene_1"
        elif loc == "apoc_s3_scene_1":
            pass
        else:
            text = (f"🔙 *ВОЗВРАЩЕНИЕ В ЭКСПЕДИЦИЮ*\n"
                    f"──────────────────────────\n"
                    f"Командор, вы остановились в Главе 3. Марти готов продолжать движение!\n\n"
                    f"Что делаем?")
            kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
                tele_types.InlineKeyboardButton("▶️ Продолжить экспедицию", callback_data="resume_game_3"),
                tele_types.InlineKeyboardButton("🔄 Начать Главу 3 заново", callback_data="game_reset_ch3"),
                tele_types.InlineKeyboardButton("🔙 В меню Хаба", callback_data="game_main_menu")
            )
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
            return

    if call.data == "resume_game_3":
        call.data = loc
        try: bot.answer_callback_query(call.id, "🔄 Экспедиция продолжена!")
        except: pass

    if call.data == "game_reset_ch3":
        current_node = set_loc(current_node, "apoc_s3_scene_1")
        set_game_timer(user_id, 0)
        set_game_node(user_id, current_node)
        call.data = "apoc_s3_scene_1"
        try: bot.answer_callback_query(call.id, "🔄 Глава 3 начата заново!", show_alert=True)
        except: pass

    # 💾 --- [ АВТОСОХРАНЕНИЕ КОМНАТЫ ] --- 💾
    MAJOR_NODES = [
        "apoc_s3_scene_1", "apoc_s3_2", "apoc_s3_3", "apoc_s3_4", "apoc_s3_5", 
        "apoc_s3_6", "apoc_s3_7", "apoc_s3_8", "apoc_s3_9", "apoc_s3_10", 
        "apoc_s3_11", "apoc_s3_12", "apoc_s3_13", "apoc_s3_14", "apoc_s3_15", 
        "apoc_s3_16", "apoc_s3_17", "apoc_s3_18", "apoc_s3_19", "apoc_s3_20", 
        "apoc_s3_21", "apoc_s3_22", "apoc_s3_23", "apoc_s3_24", "apoc_s3_25", 
        "apoc_s3_26", "apoc_s3_27", "apoc_s3_28", "apoc_s3_29", "apoc_s3_30", "apoc_ch3_completed_screen"
    ]
    if call.data in MAJOR_NODES:
        current_node = set_loc(current_node, call.data)
        set_game_node(user_id, current_node)
        loc = call.data

    # 🏆 --- [ ЭКРАН ЗАВЕРШЕННОЙ ГЛАВЫ ] --- 🏆
    if call.data == "apoc_ch3_completed_screen":
        text = (f"🏆 **ГЛАВА 3: ПРОЙДЕНА**\n"
                f"──────────────────────────\n"
                f"Семя Жизни в ваших руках. Мариуполь готов к пробуждению.\n\n"
                f"Марти ждет отправки в Глубинный Архив!")
        
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("🚀 Начать Главу 4", callback_data="apoc_s4_start"),
            tele_types.InlineKeyboardButton("🔄 Пройти Главу 3 заново", callback_data="game_reset_ch3"),
            tele_types.InlineKeyboardButton("🔙 В меню Хаба", callback_data="game_main_menu")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        return

    # --- [ ЭТАП 1: ГНИЛЫЕ ДЖУНГЛИ МАРИУПОЛЯ ] ---
    if call.data == "apoc_s3_scene_1":
        text = (f"🏙 *ГОРОД, КОТОРЫЙ ПОМНИТ*\n"
                f"──────────────────────────\n"
                f"Вы стоите на разбитой эстакаде, глядя на панораму Мариуполя. Небоскребы, которые когда-то были символом прогресса 2020-х, "
                f"теперь наклонились друг к другу, удерживаемые колоссальными фиолетовыми лианами. Воздух здесь не кислый, как в болотах, "
                f"он... металлический. Био-анализатор на руке сходит с ума, выдавая тысячи ДНК-совпадений с каждым деревом.\n\n"
                f"Марти: 'Док, добро пожаловать домой. Ну, в то, что от него осталось. Мой радар ловит странный сигнал: это не Академия, "
                f"это старая трансляция из 1985-го. Она идет по кругу, как заевшая пластинка. 'Семя' где-то под нами, в глубине фундамента клиники. "
                f"Но посмотрите на дорогу... Асфальт взломан изнутри. Что-то очень большое прошло здесь совсем недавно'.\n\n"
                f"Вы сжимаете пропуск в кармане. Лицо на фото кажется всё более знакомым, но память всё еще заблокирована.")
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("📡 Настроить Анализатор на эхо-частоту", callback_data="apoc_s3_2"),
            tele_types.InlineKeyboardButton("🔎 Осмотреть взломанный асфальт", callback_data="apoc_s3_clue_track")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 2: РАДИО ПРИЗРАКОВ ] ---
    elif call.data == "apoc_s3_2":
        if not has_flag(current_node, "clue_frequency"):
            current_node = add_flag(current_node, "clue_frequency")
            set_game_node(user_id, current_node)

        text = (f"📻 *СИГНАЛ ИЗ ПРОШЛОГО*\n\n"
                f"Вы крутите ручку настройки на Анализаторе. Сквозь белый шум прорывается голос диктора: '...в Мариуполе сегодня +25, "
                f"клиника на проспекте Мира приглашает на бесплатную диагностику... Проект Семя — это ваше будущее...'. \n\n"
                f"Марти: 'Слышите это? Это не просто радио. Это зацикленный код управления био-массой. "
                f"Тот, кто его запустил, хотел, чтобы мох рос в определенном ритме. Если мы пойдем по этой частоте, "
                f"мы обойдем ловушки Академии. Но путь преграждает заброшенный блокпост. Там всё еще работают турели 'Орион'. \n\n"
                f"Док, нам нужно найти способ отключить их, не поднимая шума. Посмотрите на тот старый рекламный щит, "
                f"там кажется есть сервисный люк'.")
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("🛠 Взломать сервисный люк", callback_data="apoc_s3_3"),
            tele_types.InlineKeyboardButton("🏃 Проскочить рывком", callback_data="apoc_s3_sprint_fail")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 3: СЕРВИСНЫЙ УЗЕЛ (Загадка) ] ---
    elif call.data == "apoc_s3_3":
        text = (f"⚙️ *МЕХАНИКА ТРЕВОГИ*\n\n"
                f"Люк поддается со скрипом. Внутри — мешанина из проводов и старых реле. Вы видите панель управления турелями. "
                f"На ней выцарапано: 'Пароль — это число каналов в нижнем клыке взрослого человека'. \n\n"
                f"Марти: 'Опять эти ваши стоматологические шуточки! Док, вспоминайте практику. Сколько каналов в клыке? "
                f"Если ошибетесь — турели превратят нас в решето, и Марти-в-жилете станет Марти-в-дырочку!'.")
        kb = tele_types.InlineKeyboardMarkup(row_width=3).add(
            tele_types.InlineKeyboardButton("🔘 1", callback_data="apoc_s3_4"),
            tele_types.InlineKeyboardButton("🔘 2", callback_data="apoc_s3_logic_fail"),
            tele_types.InlineKeyboardButton("🔘 3", callback_data="apoc_s3_logic_fail")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 4: ТЕНИ В НЕБОСКРЕБАХ ] ---
    elif call.data == "apoc_s3_4":
        if not has_flag(current_node, "logic_drill_done"):
            current_node = add_flag(current_node, "logic_drill_done")
            set_game_node(user_id, current_node)
            add_xp(user_id, 10, username)

        text = (f"🔓 *БЕЗОПАСНЫЙ ПРОХОД*\n\n"
                f"Турели с тихим щелчком опускают стволы. Вы проходите мимо блокпоста. \n\n"
                f"Марти: 'Фух, пронесло. Смотрите, Док! В окне третьего этажа того здания... Там снова этот парень в халате. "
                f"Он не просто идет, он... калибрует ретрансляторы. Он готовит город к чему-то масштабному. "
                f"И посмотрите, что он выронил... это же ваша старая ключ-карта от клиники! Но она светится так, "
                f"будто в ней встроен ядерный реактор. Нам нужно ее подобрать, пока мох не поглотил пластик'.")
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("💳 Подобрать карту", callback_data="apoc_s3_5"),
            tele_types.InlineKeyboardButton("🔭 Проследить за паломником через Анализатор", callback_data="apoc_s3_clue_spy")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 5: КЛЮЧ-КАРТА 'ЗЕНИТ' ] ---
    elif call.data == "apoc_s3_5":
        if not has_flag(current_node, "item_keycard"):
            current_node = add_flag(current_node, "item_keycard")
            set_game_node(user_id, current_node)

        text = (f"💳 *ЗОЛОТОЙ КЛЮЧ*\n\n"
                f"Вы поднимаете карту. Она тяжелее обычной и вибрирует в такт вашему пульсу. \n\n"
                f"Марти: 'Это не просто пропуск. Это 'Мастер-ключ Зенит'. Он открывает любые двери в радиусе трех километров, "
                f"включая секретный архив под клиникой. Но есть нюанс: Академия Орион теперь точно видит нас на своих радарах. "
                f"Карта работает как маяк. Мы теперь — самая яркая мишень в Мариуполе. \n\n"
                f"Впереди — вход в метро. Это самый быстрый путь к проспекту Мира, но там внизу... темно и пахнет сырым мясом. "
                f"Ну что, Док, спустимся в кроличью нору?'.")
        kb = tele_types.InlineKeyboardMarkup().add(
            tele_types.InlineKeyboardButton("🚇 Спуститься в метро", callback_data="apoc_s3_6")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 6: СПУСК В ЗЕВ МЕТРО ] ---
    elif call.data == "apoc_s3_6":
        text = (f"🚇 *ПОДЗЕМНЫЙ ПУЛЬС*\n"
                f"──────────────────────────\n"
                f"Вы спускаетесь по застывшему эскалатору. Ступени покрыты скользким фиолетовым налетом, "
                f"который слабо светится под вашими шагами. Внизу, в вестибюле, вместо поездов — гигантские сплетения корней, "
                f"похожие на магистральные кабели. Они уходят вглубь тоннелей, пульсируя в такт тому самому сигналу 'биения сердца'.\n\n"
                f"Марти: 'Док, включите ПНВ. Тут внизу воздух такой густой, что его можно резать скальпелем. "
                f"Мои сенсоры фиксируют движение в конце платформы. Это не люди, это автоматика Академии Орион... или то, "
                f"во что она превратилась после контакта с мхом. И посмотрите на стены — старая мозаика Мариуполя "
                f"переписана. Кто-то вытравил на ней формулы нуклеотидов поверх изображений рабочих и сталеваров'.")
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("🔦 Обыскать кассу", callback_data="apoc_s3_clue_ticket"),
            tele_types.InlineKeyboardButton("🚶 Пройти к путям", callback_data="apoc_s3_7")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 7: ПЕРРОН ПРИЗРАКОВ ] ---
    elif call.data == "apoc_s3_7":
        text = (f"🚉 *ПОЕЗД В НИКУДА*\n\n"
                f"На путях стоит состав метро, но его вагоны срослись с бетоном. Двери заклинены, но внутри горит свет. "
                f"Там, на сиденьях, вместо пассажиров — манекены из ТЦ, облепленные датчиками. Анализатор выдает странную ошибку: "
                f"'Обнаружен активный протокол обучения'. \n\n"
                f"Марти: 'Док, кажется, это место использовали как полигон для обкатки системы переноса сознания. "
                f"Смотрите на кабину машиниста — она заблокирована кодовым замком Академии. Чтобы пройти по тоннелю дальше, "
                f"нам нужно подать питание на рельсы через этот пульт. Но система запрашивает подтверждение возраста проекта 'Семя'.")
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("📟 Ввести код доступа", callback_data="apoc_s3_8"),
            tele_types.InlineKeyboardButton("👊 Попробовать выбить дверь", callback_data="apoc_s3_kick_fail")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 8: ЗАГАДКА МОЛОЧНЫХ ЗУБОВ ] ---
    elif call.data == "apoc_s3_8":
        text = (f"🦷 *ДЕТСКИЙ ШИФР*\n\n"
                f"На панели пульта высвечивается старое детское фото... это снова вы, но вам тут года три. "
                f"Рядом вопрос системы: 'Полный комплект первой смены для инициализации'. \n\n"
                f"Марти: 'Док, это проверка на базовую биологию! Сколько зубов в молочном прикусе у ребенка? "
                f"Дед всегда говорил, что это фундамент, на котором строится вся система. Вспоминайте, сколько их должно быть, "
                f"прежде чем они начнут меняться на ваши рабочие инструменты!'.")
        kb = tele_types.InlineKeyboardMarkup(row_width=3).add(
            tele_types.InlineKeyboardButton("🔘 10", callback_data="apoc_s3_milk_fail"),
            tele_types.InlineKeyboardButton("🔘 20", callback_data="apoc_s3_9"),
            tele_types.InlineKeyboardButton("🔘 32", callback_data="apoc_s3_milk_fail")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 9: ТЕМНЫЙ ТОННЕЛЬ (СТЕЛС) ] ---
    elif call.data == "apoc_s3_9":
        if not has_flag(current_node, "logic_milk_done"):
            current_node = add_flag(current_node, "logic_milk_done")
            set_game_node(user_id, current_node)
            add_xp(user_id, 12, username)

        text = (f"👣 *ШЕПОТ В ТЕМНОТЕ*\n\n"
                f"С гулом включается аварийное освещение. Тоннель впереди озаряется мертвенно-белым светом. "
                f"Вы идете по шпалам, и Марти внезапно гасит свой фонарь. \n\n"
                f"Марти: 'Тихо, Док. Впереди — Сталкер-перехватчик Академии. Это паукообразный дрон, он настроен на звук шагов. "
                f"Мы не можем его уничтожить — его броня выдержит взрыв гранаты. Нам нужно пройти мимо, используя вибрацию рельсов "
                f"как прикрытие. Включаем демпферы на ваших сапогах. Шагайте в ритм биения мха... раз-два... раз-два...'.")
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("🤫 Идти в ритм", callback_data="apoc_s3_10"),
            tele_types.InlineKeyboardButton("🏃 Пробежать быстро", callback_data="apoc_s3_run_fail")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 10: СТАНЦИЯ 'ПРОСПЕКТ МИРА' ] ---
    elif call.data == "apoc_s3_10":
        text = (f"🚉 *ПОДНОЖИЕ КЛИНИКИ*\n\n"
                f"Вы выходите на станцию 'Проспект Мира'. Здесь всё завалено стоматологическими креслами, "
                f"вывезенными из вашей клиники наверху. Они расставлены кругом, как будто здесь проводили какой-то ритуал. "
                f"В центре круга лежит старый рентгеновский снимок, который светится фиолетовым. \n\n"
                f"Марти: 'Док, мы на месте. Клиника прямо над нами. Но посмотрите на этот снимок... "
                f"На нем ваша челюсть, но вместо корней зубов — микросхемы, уходящие прямо в мозг. "
                f"Это не снимок пациента, это чертеж... чертеж ВАС. \n\n"
                f"Сверху раздается грохот — Академия начала штурм здания. Нам нужно прорываться на поверхность!'.")
        kb = tele_types.InlineKeyboardMarkup().add(
            tele_types.InlineKeyboardButton("🧗 Выбраться через вентшахту", callback_data="apoc_s3_11")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 11: ВЕРТИКАЛЬНЫЙ ПОДЪЕМ ] ---
    elif call.data == "apoc_s3_11":
        text = (f"🪜 *ВДОХ ПРОШЛОГО*\n"
                f"──────────────────────────\n"
                f"Вы карабкаетесь вверх по узкой вентиляционной шахте. Пыль, которой здесь не касались десятилетиями, забивает фильтры, "
                f"но сквозь неё вы начинаете чувствовать знакомый, почти родной запах... смесь антисептика, полимера для пломб и старой бумаги. "
                f"Сверху доносятся глухие удары — Академия Орион уже высадила десант на крышу и планомерно зачищает этаж за этажом.\n\n"
                f"Марти, зацепившись когтями за ваш рюкзак, тихо шепчет: 'Док, если мы выберемся прямо в коридор, нас встретят "
                f"с распростертыми объятиями и заряженными винтовками. Я чувствую вибрацию тяжелых ботинок прямо над нами. "
                f"Но посмотрите на эту распределительную коробку... Она запитана отдельно от основной сети здания. Похоже, "
                f"дед оставил здесь 'черный ход' для своих'.")
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("Перерезать красную жилу питания", callback_data="apoc_s3_12"),
            tele_types.InlineKeyboardButton("Подключить Био-анализатор к порту", callback_data="apoc_s3_analyze_port")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 12: ХОЛЛ КЛИНИКИ (РЕГИСТРАТУРА) ] ---
    elif call.data == "apoc_s3_12":
        text = (f"🦷 *ПЕРВЫЙ ПАЦИЕНТ*\n\n"
                f"Вы выбиваете решетку и бесшумно спрыгиваете в холл регистратуры. Зрелище напоминает застывшую во времени сцену из сюрреалистичного фильма. "
                f"Стойка из темного дерева оплетена фиолетовыми венами мха, а на стенах висят дипломы на имя Дмитрия Владимировича Фомиченко. "
                f"Но буквы на них медленно меняются прямо у вас на глазах, превращаясь в двоичный код.\n\n"
                f"Марти: 'Смотрите на кресла в зоне ожидания! Там сидят не люди, а те самые оболочки-пустышки, которых мы видели в метро. "
                f"Они подключены к общей сети здания. Если хоть один из них 'проснется' и зафиксирует ваше лицо, "
                f"вся Академия узнает наши координаты через секунду. Док, в регистрационном журнале под слоем пыли что-то лежит. "
                f"Это похоже на старый слепок челюсти, но он сделан из чистого золота'.")
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("Изучить золотой слепок", callback_data="apoc_s3_clue_gold"),
            tele_types.InlineKeyboardButton("Пройти в сторону лечебных кабинетов", callback_data="apoc_s3_13")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 13: ЗАГАДКА 'ВОСЬМЕРКИ' ] ---
    elif call.data == "apoc_s3_13":
        text = (f"📂 *СЕКРЕТНЫЙ АРХИВАТОР*\n\n"
                f"Вы подходите к двери своего бывшего кабинета. Она заблокирована массивным механическим диском, который выглядит "
                f"как нечто среднее между сейфовым замком и анатомической моделью челюсти. На нем выгравированы номера зубов. \n\n"
                f"Марти: 'Тут записка на дверной ручке: «Мудрость приходит последней, но открывает все двери». "
                f"Док, это же явный намек! Какой номер в международной классификации присваивается третьему моляру, который "
                f"все называют зубом мудрости? Если мы повернем диск не на то число, сработает система стерилизации... "
                f"и нас просто выжгут озоном'.")
        kb = tele_types.InlineKeyboardMarkup(row_width=3).add(
            tele_types.InlineKeyboardButton("Число 6", callback_data="apoc_s3_drill_fail"),
            tele_types.InlineKeyboardButton("Число 8", callback_data="apoc_s3_14"),
            tele_types.InlineKeyboardButton("Число 32", callback_data="apoc_s3_drill_fail")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 14: ПАТРУЛЬ В КОРИДОРЕ ] ---
    elif call.data == "apoc_s3_14":
        if not has_flag(current_node, "logic_wisdom_done"):
            current_node = add_flag(current_node, "logic_wisdom_done")
            set_game_node(user_id, current_node)
            add_xp(user_id, 15, username)

        text = (f"👣 *ОХОТА НА СОЗДАТЕЛЯ*\n\n"
                f"Замок щелкает, и дверь приоткрывается, но в этот момент в конце коридора вспыхивают мощные тактические фонари. "
                f"Грубый механический голос через громкоговоритель разносится по этажу: 'Объект Фомиченко, оставайтесь на месте! "
                f"Любое сопротивление приведет к немедленной деструкции биологического носителя. Вы — собственность Академии Орион!'.\n\n"
                f"Марти: 'Док, это штурмовой дрон класса 'Экзекутор'. У него тепловизоры и пулеметы калибра 7.62. "
                f"Если мы сейчас закроемся в кабинете, они просто взорвут стену. Нам нужно отвлечь их. "
                f"Смотрите, на столике стоит старая ультразвуковая мойка для инструментов. Если выкрутить её на максимум, "
                f"она создаст такие помехи, что у этого жестяного парня вылетят все предохранители!'.")
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("Активировать ультразвуковую мойку", callback_data="apoc_s3_15"),
            tele_types.InlineKeyboardButton("Бросить в дрон тяжелый автоклав", callback_data="apoc_s3_patrol_fail")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 15: КАБИНЕТ №1 (ПОРОГ ТАЙНЫ) ] ---
    elif call.data == "apoc_s3_15":
        text = (f"🚪 *СЕРДЦЕ ЛАБОРАТОРИИ*\n\n"
                f"Ультразвук взрывается невыносимым писком. Дрон в коридоре начинает хаотично вращать башней, расстреливая потолок в приступе электронного безумия. "
                f"Вы заскакиваете в кабинет и захлопываете дверь. Тишина внутри кажется оглушительной. \n\n"
                f"Это ваш кабинет. Здесь всё так, как вы оставили... или так, как КТО-ТО хотел, чтобы вы это увидели. "
                f"На рабочем столе, под зеленым светильником, лежит раскрытый ежедневник. Последняя запись датирована завтрашним числом 2026 года, "
                f"но написана она почерком вашего деда: *«Круг замкнулся. Семя требует посадки в почву, которая его породила»*.\n\n"
                f"Марти: 'Док... посмотрите на пол. Под вашим рабочим креслом нет ковра. Там стеклянная панель, "
                f"а под ней... Боже, там целый город в миниатюре, выращенный из костной ткани!'.")
        kb = tele_types.InlineKeyboardMarkup().add(
            tele_types.InlineKeyboardButton("Изучить костяной макет города", callback_data="apoc_s3_16")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 16: КОСТЯНОЙ МАКЕТ ГОРОДА ] ---
    elif call.data == "apoc_s3_16":
        text = (f"🦴 *ГЕОМЕТРИЯ ПЛОТИ*\n"
                f"──────────────────────────\n"
                f"Вы опускаетесь на колени перед стеклянной панелью. Под ней раскинулся Мариуполь, но выполненный не из пластика или дерева, "
                f"а из идеально структурированной костной ткани. Здания-позвонки, эстакады-ребра и центральная площадь, напоминающая "
                f"огромный коренной зуб. Био-анализатор начинает сканировать макет, и по костяным улочкам пробегают фиолетовые импульсы света.\n\n"
                f"Марти: 'Док, это не просто карта. Это нейронная сеть. Смотрите, импульсы сходятся в одной точке — прямо под вашим стоматологическим креслом. "
                f"Этот макет показывает состояние «Семени» в реальном времени. Видите те черные пятна на окраинах? Это зоны, где Академия Орион "
                f"уже вытравила мох химикатами. Город страдает, Док. Он буквально кричит на частотах, которые мы только что поймали. "
                f"Нам нужно активировать главный терминал, но я не вижу здесь никаких кнопок. Только ваше старое оборудование'.")
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("Осмотреть стоматологическое кресло", callback_data="apoc_s3_17"),
            tele_types.InlineKeyboardButton("Считать данные с зуба-макета", callback_data="apoc_s3_clue_tooth_map")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 17: КРЕСЛО УПРАВЛЕНИЯ ] ---
    elif call.data == "apoc_s3_17":
        text = (f"🛋 *ИНТЕРФЕЙС ИЗ ПРОШЛОГО*\n\n"
                f"Вы подходите к креслу. Оно выглядит как обычное стоматологическое оборудование из середины 2020-х, но при вашем приближении "
                f"подголовник мягко разворачивается, а из подлокотников выдвигаются тонкие иглы-коннекторы. Это не место для пациента, "
                f"это био-интерфейс, созданный специально под вашу нервную систему.\n\n"
                f"Марти: 'Док, я бы на вашем месте туда не садился без страховки, но у нас нет выбора. Дверь кабинета уже начинают "
                f"прожигать термическими зарядами. Если мы не войдем в систему сейчас, Академия заберет макет вместе с нами. "
                f"Смотрите, на панели управления креслом мигает индикатор. Требуется ввод даты инициализации протокола. "
                f"Дед всегда говорил: «Всё началось в тот день, когда ты сделал свой первый вдох в этом городе».")
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("Ввести год рождения на панели", callback_data="apoc_s3_18"),
            tele_types.InlineKeyboardButton("Поискать скрытый рычаг под сиденьем", callback_data="apoc_s3_chair_fail")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 18: АВТОРИЗАЦИЯ 1985 ] ---
    elif call.data == "apoc_s3_18":
        if not has_flag(current_node, "logic_year_done"):
            current_node = add_flag(current_node, "logic_year_done")
            set_game_node(user_id, current_node)
            add_xp(user_id, 20, username)

        text = (f"📟 *ЦИФРОВОЕ ПЕРЕРОЖДЕНИЕ*\n\n"
                f"Вы вводите «1985». Кресло издает мелодичный сигнал, и по вашей коже пробегает легкий разряд статического электричества. "
                f"Иглы в подлокотниках замирают в миллиметре от ваших запястьев, считывая биопотенциал. Экран перед вами вспыхивает, "
                f"показывая трехмерную модель вашего собственного черепа, но с интегрированными модулями «Семени».\n\n"
                f"Марти: 'Сработало! Система опознала Создателя. Но подождите... терминал выдает текстовое сообщение. "
                f"Оно было заблокировано сорок лет. Текст гласит: «Дмитрий, Семя — это не оружие. Это страховка на случай, "
                f"если человечество забудет, как быть человечным». Чтобы получить полный доступ к архиву клиники, "
                f"вам нужно подтвердить статус врача. Выберите инструмент, который отделяет жизнь от гнили'.")
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("Выбрать стоматологический экскаватор", callback_data="apoc_s3_19"),
            tele_types.InlineKeyboardButton("Выбрать щипцы для удаления", callback_data="apoc_s3_tool_fail")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 19: ГОЛОС ИЗ БЕЗДНЫ ] ---
    elif call.data == "apoc_s3_19":
        text = (f"🔈 *ШЕПОТ ПРЯМО В МОЗГ*\n\n"
                f"Как только вы выбираете инструмент для очистки полостей, динамики в кабинете начинают транслировать голос. "
                f"Это не запись и не радиоэхо. Это синтезированный голос, который звучит одновременно и как ваш собственный, "
                f"и как голос вашего деда. Он кажется объемным, исходящим от самих стен.\n\n"
                f"Голос: 'Дмитрий Владимирович... Вы наконец дома. Я — это то, что осталось от сознания архитекторов Мариуполя. "
                f"Мы спрятали Семя не в земле, а в памяти. Чтобы пробудить его полностью, вам нужно спуститься в подвал, "
                f"в стерилизационную зону. Там находится инкубатор. Но берегитесь: Академия Орион прислала не только дронов. "
                f"Среди них есть тот, кто называет себя Навигатором. Он знает о вас больше, чем вы сами'.")
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("Запросить координаты инкубатора", callback_data="apoc_s3_20"),
            tele_types.InlineKeyboardButton("Спросить про Навигатора", callback_data="apoc_s3_clue_navigator")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 20: ЛАЗЕРНЫЙ БОР ] ---
    elif call.data == "apoc_s3_20":
        if not has_flag(current_node, "item_laser_drill"):
            current_node = add_flag(current_node, "item_laser_drill")
            set_game_node(user_id, current_node)

        text = (f"🔦 *ИНСТРУМЕНТ ВЫЖИВАНИЯ*\n\n"
                f"Из потайного отделения в столе выдвигается футляр. В нем лежит прибор, напоминающий вашу старую турбинную установку, "
                f"но вместо бора на конце — фокусирующая линза из фиолетового кристалла. Это **Лазерный Бор «Орион-1»**.\n\n"
                f"Марти: 'Ничего себе игрушка! Док, с этой штукой мы прорежем любую броню Академии. И посмотрите, "
                f"он питается напрямую от вашего Анализатора. Но у нас проблема: дверь кабинета только что вынесли. "
                f"В коридоре дым и тяжелые шаги. Навигатор здесь. Он не похож на робота... он похож на человека, "
                f"но его лицо скрыто зеркальной маской. Нам нужно решить: прорываться с боем или искать путь через шахту лифта'.")
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("Использовать Лазерный Бор на двери", callback_data="apoc_s3_21"),
            tele_types.InlineKeyboardButton("Броситься к шахте лифта", callback_data="apoc_s3_elevator_start")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 21: ЗЕРКАЛЬНЫЙ НАВИГАТОР ] ---
    elif call.data == "apoc_s3_21":
        text = (f"🌑 *ТЕНЬ В ОТРАЖЕНИИ*\n"
                f"──────────────────────────\n"
                f"Дым медленно оседает. Навигатор делает шаг в кабинет, и вы видите в его зеркальной маске собственное отражение — испачканное пылью лицо человека, "
                f"который за одну ночь узнал о себе больше, чем за всю жизнь. Навигатор не поднимает винтовку. Он просто стоит, и от него исходит холод, "
                f"который не зафиксирует ни один тепловизор.\n\n"
                f"**НАВИГАТОР:** 'Дмитрий... вы так отчаянно цепляетесь за эти стены. Вы думаете, что это ваша клиника? Что это ваше прошлое? "
                f"Это всего лишь обертка для данных, которые принадлежат Академии по праву наследования. Ваш дед совершил ошибку, решив, что "
                f"память целого города можно доверить одному человеку. Сдайте пропуск, и мы сохраним вашу биологическую структуру'.\n\n"
                f"Марти (тихо рычит, припадая к полу): 'Док, я сканирую его... под броней нет сердцебиения в привычном смысле. Там течет "
                f"синтетическая кровь, смешанная с фиолетовым соком мха. Он — полукровка. Если мы сейчас не используем Бор, он просто "
                f"заморозит нас своим присутствием. Жгите его!'.")
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("Направить луч Бора в маску Навигатора", callback_data="apoc_s3_22"),
            tele_types.InlineKeyboardButton("Попытаться заговорить зубы", callback_data="apoc_s3_nav_talk")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 22: ДУЭЛЬ НА ЛАЗЕРАХ ] ---
    elif call.data == "apoc_s3_22":
        text = (f"🔥 *ФИОЛЕТОВАЯ ВСПЫШКА*\n\n"
                f"Вы нажимаете на спуск Лазерного Бора. Фиолетовый луч с воем рассекает воздух, врезаясь в зеркальную маску. "
                f"На секунду кажется, что металл плавится, но Навигатор лишь слегка наклоняет голову. Маска поглощает энергию, "
                f"перераспределяя её по броне. Однако ударная волна заставляет его отступить на шаг назад в коридор.\n\n"
                f"**НАВИГАТОР:** 'Детские игрушки. Вы пытаетесь лечить пульпит там, где нужна ампутация всего мира'.\n\n"
                f"Марти: 'Док, это наш шанс! Пока его системы перегружены поглощением энергии, прыгайте в тот люк под креслом! "
                f"Костяной макет города раздвинулся, открывая прямой спуск в зону стерилизации. Это единственный путь вниз. "
                f"Если он зайдет обратно — нам конец! Прыгаем!'.")
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("Прыгнуть в открывшийся люк под креслом", callback_data="apoc_s3_23")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 23: ЗОНА СТЕРИЛИЗАЦИИ ] ---
    elif call.data == "apoc_s3_23":
        text = (f"❄️ *ХОЛОДНЫЙ ПЕРЕХОД*\n\n"
                f"Вы скользите по металлическому желобу и приземляетесь на мягкий, пружинистый слой мха внизу. Это подвал клиники, "
                f"но он не похож на обычное техническое помещение. Стены здесь облицованы матовым титаном, а вдоль них стоят огромные "
                f"цилиндрические баки, в которых в голубоватой жидкости плавают... зубы. Сотни, тысячи образцов, каждый в своей ячейке.\n\n"
                f"Марти: 'Ого... Док, кажется, ваш дед собирал не просто базу данных, а генетический банк всего Мариуполя. "
                f"Зубы — это же идеальный контейнер для ДНК, они хранятся вечно. Посмотрите на терминал в центре — это "
                f"управление системой автоклавирования. Чтобы пройти дальше к инкубатору, нам нужно запустить цикл очистки, "
                f"иначе био-защита превратит нас в пепел еще на входе'.")
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("Активировать терминал автоклава", callback_data="apoc_s3_24"),
            tele_types.InlineKeyboardButton("Изучить маркировку на баках", callback_data="apoc_s3_clue_dna_bank")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 24: ЗАГАДКА АВТОКЛАВА ] ---
    elif call.data == "apoc_s3_24":
        text = (f"🧼 *ПАРАДОКС ЧИСТОТЫ*\n\n"
                f"Экран терминала мигает красным. Система запрашивает ввод критических параметров для режима полной дезинфекции 'Протокол-1985'. "
                f"На дисплее три варианта температурного режима. Сообщение от системы: 'Только максимальная стерильность откроет путь к Семени'.\n\n"
                f"Марти: 'Док, это ваш профиль! При какой температуре в режиме форсированной стерилизации погибают даже самые "
                f"устойчивые споры мха? Вспоминайте свои рабочие будни, это должно быть число, которое вы вбивали в автоклав тысячу раз!'.")
        kb = tele_types.InlineKeyboardMarkup(row_width=3).add(
            tele_types.InlineKeyboardButton("100°C", callback_data="apoc_s3_temp_fail"),
            tele_types.InlineKeyboardButton("134°C", callback_data="apoc_s3_25"),
            tele_types.InlineKeyboardButton("180°C", callback_data="apoc_s3_temp_fail")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 25: ПУТЬ К ИНКУБАТОРУ ] ---
    elif call.data == "apoc_s3_25":
        if not has_flag(current_node, "logic_autoclave_done"):
            current_node = add_flag(current_node, "logic_autoclave_done")
            set_game_node(user_id, current_node)
            add_xp(user_id, 15, username)

        text = (f"🟢 *СТЕРИЛЬНЫЙ ПРОХОД*\n\n"
                f"Раздается мощный выброс пара. Стены отсека начинают раздвигаться, открывая проход в ярко освещенный коридор, "
                f"стены которого покрыты не мхом, а живой белой тканью, напоминающей эмаль. Био-анализатор выдает сообщение: "
                f"'ОБЪЕКТ: ИНКУБАТОР. СТАТУС: ГОТОВНОСТЬ 98%'.\n\n"
                f"Марти: 'Док, мы почти у цели! Но посмотрите на датчики... Навигатор не прыгнул за нами, он обходит здание "
                f"через пожарную лестницу снаружи. Он хочет заблокировать нас в самом Инкубаторе. Нам нужно "
                f"действовать быстрее. Там, за дверью, я вижу нечто огромное... Это и есть Семя Жизни?'.")
        kb = tele_types.InlineKeyboardMarkup().add(
            tele_types.InlineKeyboardButton("Войти в зал Инкубатора", callback_data="apoc_s3_26")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 26: ЗАЛ БЕЛОГО ЛОТОСА ] ---
    elif call.data == "apoc_s3_26":
        text = (f"🌱 *СЕРДЦЕ ИНКУБАТОРА*\n"
                f"──────────────────────────\n"
                f"Вы входите в зал, который больше напоминает внутреннюю часть гигантской жемчужины. Стены плавно изгибаются, "
                f"переходя в купол, а в самом центре, в чаше из костяного фарфора, пульсирует «Семя Жизни». Это не зерно и не кристалл. "
                f"Это био-органическое ядро, переплетенное светящимися капиллярами. Оно выглядит как идеальный белый цветок, "
                f"лепестки которого сделаны из живой эмали.\n\n"
                f"Марти (завороженно): 'Док... мои датчики зашкаливают. Это ядро транслирует код восстановления для всей планеты. "
                f"Если мы его активируем, мох перестанет пожирать города и начнет их восстанавливать. Но посмотрите на консоль управления... "
                f"Она требует финального подтверждения личности через «Ритм Роста». Система хочет знать, когда закладывается "
                f"фундамент взрослой жизни. Похоже, дед снова зашифровал всё через вашу профессию'.")
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("Подойди к консоли «Семени»", callback_data="apoc_s3_27")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 27: ЗАГАДКА ШЕСТОГО ГОДА ] ---
    elif call.data == "apoc_s3_27":
        text = (f"🦷 *КОД КОРЕННОГО ПУТИ*\n\n"
                f"Консоль проецирует в воздух голограмму детской челюсти. Вопрос системы звучит прямо у вас в голове: "
                f"«В каком возрасте у человека появляется фундамент постоянства — первый моляр, который не сменяет никого, а просто приходит первым?»\n\n"
                f"Марти: 'Док, это же база! Первый постоянный зуб, «шестерка». В каком возрасте он обычно прорезывается у детей? "
                f"Это и есть ключ к запуску протокола наследования. Ошибиться нельзя — если мы введем неверную цифру, "
                f"Семя уйдет в режим саморазрушения, и мы останемся в этом подвале навсегда!'.")
        kb = tele_types.InlineKeyboardMarkup(row_width=3).add(
            tele_types.InlineKeyboardButton("Возраст 3", callback_data="apoc_s3_root_fail"),
            tele_types.InlineKeyboardButton("Возраст 6", callback_data="apoc_s3_28"),
            tele_types.InlineKeyboardButton("Возраст 12", callback_data="apoc_s3_root_fail")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 28: ЯВЛЕНИЕ НАВИГАТОРА ] ---
    elif call.data == "apoc_s3_28":
        if not has_flag(current_node, "logic_molar_done"):
            current_node = add_flag(current_node, "logic_molar_done")
            set_game_node(user_id, current_node)
            add_xp(user_id, 20, username)

        text = (f"👤 *ОТРАЖЕНИЕ В МАСКЕ*\n\n"
                f"Как только вы вводите число «6», Семя вспыхивает ослепительным светом. Но в этот момент тяжелые гермодвери зала "
                f"сминаются, как бумажные. В проеме стоит Навигатор. Его зеркальная маска покрыта трещинами после вашего удара Лазером, "
                f"и сквозь них видны... ваши собственные глаза. \n\n"
                f"**НАВИГАТОР:** 'Вы ввели код... значит, инстинкты Создателя всё еще живы. Но вы — лишь черновик, Дмитрий. "
                f"Я — версия 2.0, оптимизированная Академией Орион. Мой Мариуполь будет идеальным, без боли и лишних эмоций. "
                f"Семя принадлежит мне!'.\n\n"
                f"Марти: 'Док, он не просто клон, он — ваша копия, лишенная совести! Он собирается перехватить контроль над ядром. "
                f"Используйте Лазерный Бор, чтобы перегрузить систему охлаждения Инкубатора. Это создаст дымовую завесу и позволит "
                f"нам выкрасть ядро!'.")
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("Ударить Лазерным Бором по трубкам охлаждения", callback_data="apoc_s3_29")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 29: ИЗВЛЕЧЕНИЕ СЕМЕНИ ] ---
    elif call.data == "apoc_s3_29":
        text = (f"💥 *ХАОС В СТЕРИЛЬНОЙ ЗОНЕ*\n\n"
                f"Луч лазера разрезает титановые трубки. По залу разносится ледяной туман, скрывая вас от Навигатора. Слышны его яростные крики "
                f"и звук активируемого оружия. Вы бросаетесь к чаше и хватаете Семя. Оно теплое и пульсирует прямо у вас в ладонях, "
                f"синхронизируясь с вашим сердцебиением. \n\n"
                f"Марти: 'Хватайте его и бежим! Там, за постаментом, есть аварийный лифт для доставки био-материалов. "
                f"Он ведет прямиком на поверхность, в обход всех патрулей! Док, это наш единственный шанс выбраться живыми "
                f"и сохранить надежду на спасение города. Прыгайте в кабину!'.")
        kb = tele_types.InlineKeyboardMarkup(row_width=1).add(
            tele_types.InlineKeyboardButton("Запрыгнуть в аварийный лифт", callback_data="apoc_s3_30")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # 🏆 --- [ ЭТАП 30: ФИНАЛ ГЛАВЫ 3 ] --- 🏆
    elif call.data == "apoc_s3_30":
        is_first_time = not has_completed_chapter(user_id, "chapter_3")
        
        if is_first_time:
            xp_reward = 200
            dust_reward = 200
            mark_chapter_completed(user_id, "chapter_3")
            reward_msg = f"🎁 **ДЖЕКПОТ ЗА ПЕРВОЕ ПРОХОЖДЕНИЕ:**\n✨ Опыт: +{xp_reward} XP\n💎 Пыль: +{dust_reward} ед.\n"
        else:
            xp_reward = 30
            dust_reward = 30
            reward_msg = f"🔄 **НАГРАДА ЗА ПОВТОРНОЕ ПРОХОЖДЕНИЕ:**\n✨ Опыт: +{xp_reward} XP\n💎 Пыль: +{dust_reward} ед.\n"

        if not has_flag(current_node, "ch3_done"):
            add_xp(user_id, xp_reward, username)
            current_node = add_flag(current_node, "ch3_done")
            current_node = set_loc(current_node, "apoc_ch3_completed_screen")
            set_game_node(user_id, current_node)

        text = (f"🏙 *РАССВЕТ НАД РУИНАМИ*\n\n"
                f"Вы выбираетесь на крышу самого высокого здания на проспекте Мира. Вы стоите над Мариуполем, сжимая в руках "
                f"сияющее Белое Семя. Внизу, в утреннем тумане, город кажется огромным спящим зверем. Теперь у вас есть ключ к его пробуждению.\n\n"
                f"Марти (вытирая лапой пыль с жилета): 'Док... мы сделали это. Мы вырвали сердце города из рук Академии. "
                f"Но посмотрите на горизонт. Они поднимают в воздух весь свой флот. Нам ждет долгий путь к Глубинному Архиву. "
                f"Но теперь я уверен — с вашими зубоврачебными навыками и моим носом мы перекусим этот апокалипсис пополам!'.\n\n"
                f"{reward_msg}\n"
                f"🚀 **ГЛАВА 3 ЗАВЕРШЕНА. Глава 4: Глубинный Архив разблокирована.**")
        
        kb = tele_types.InlineKeyboardMarkup().add(
            tele_types.InlineKeyboardButton("🚀 Начать Главу 4", callback_data="apoc_s4_start"),
            tele_types.InlineKeyboardButton("🏆 Вернуться в меню симуляций", callback_data="game_main_menu")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ОБРАБОТЧИКИ ОШИБОК ] ---
    elif call.data in ["apoc_s3_logic_fail", "apoc_s3_milk_fail", "apoc_s3_drill_fail", "apoc_s3_temp_fail", "apoc_s3_root_fail"]:
        bot.answer_callback_query(call.id, "❌ Марти: 'Док, это неправильное число! Система блокируется! Перепроверьте свои медицинские справочники!'", show_alert=True)
        return
    elif call.data in ["apoc_s3_sprint_fail", "apoc_s3_kick_fail", "apoc_s3_run_fail", "apoc_s3_patrol_fail", "apoc_s3_chair_fail", "apoc_s3_tool_fail"]:
        bot.answer_callback_query(call.id, "⚠️ ОПАСНО: Прямое столкновение приведет к гибели! Марти: 'Ищите обходной путь, Док, не лезьте на рожон!'", show_alert=True)
        return
    elif call.data == "apoc_s3_analyze_port":
        bot.answer_callback_query(call.id, "🔌 Порт защищен шифром деда. Марти: 'Док, тут нужен прямой контакт, резать провода было быстрее!'", show_alert=True)
        return
    elif call.data == "apoc_s3_elevator_start":
        bot.answer_callback_query(call.id, "🚫 ЛИФТ ЗАБЛОКИРОВАН. Навигатор перерезал питание сверху! Марти: 'Только Бор, Док! Жгите замок!'", show_alert=True)
        return
    elif call.data == "apoc_s3_nav_talk":
        bot.answer_callback_query(call.id, "🎭 Навигатор смеется: 'Слова — это шум. Ваша ДНК говорит громче'. Он поднимает оружие!", show_alert=True)
        return

    # --- [ ДЕТЕКТИВНЫЕ НАХОДКИ ] ---
    elif call.data.startswith("apoc_s3_clue_"):
        clue_key = call.data.replace("apoc_s3_", "")
        if not has_flag(current_node, clue_key):
            current_node = add_flag(current_node, clue_key)
            set_game_node(user_id, current_node)
            add_xp(user_id, 5, username)
        
        responses = {
            "clue_dna_bank": "🦷 МАРКИРОВКА: 'Образец 1985-А. Генетическая память сохранена'. Это база данных целого поколения!",
            "clue_track": "👣 Следы ведут вглубь города. Это не человеческая походка, а тяжелые шаги Навигатора.",
            "clue_spy": "🔭 Навигатор калибрует частоту мха. Он настраивает город как музыкальный инструмент.",
            "clue_gold": "🏆 Золотой слепок — это зашифрованный ключ доступа. На нем дата: 1985 год.",
            "clue_navigator": "👤 Навигатор — это результат проекта 'Д-85'. Он верит, что он истинный наследник.",
            "clue_ticket": "🎫 КАССА: Вы нашли старый жетон метро. На нем нацарапано: 'Не верь отражениям. Навигатор лжет'.",
            "clue_tooth_map": "🦷 МАКЕТ: Зуб резонирует! Био-анализатор скачал скрытые чертежи подвалов клиники."
        }
        bot.answer_callback_query(call.id, responses.get(clue_key, "Инфо получено."), show_alert=True)
