import telebot
from datetime import datetime
from telebot import types as tele_types
# Импортируем функции базы данных
from database import get_game_status, update_game_progress, set_game_timer, add_xp

def run_scenario(bot, call):
    user_id = call.from_user.id
    username = call.from_user.first_name if call.from_user.first_name else "Пилот"
    
    current_node, timer_end = get_game_status(user_id)
    
    # 1. Глобальная проверка таймера
    if timer_end and datetime.now() < timer_end:
        remaining = timer_end - datetime.now()
        mins = int(remaining.total_seconds() // 60)
        bot.answer_callback_query(call.id, f"⏳ Марти занят. Будет готов через {mins} мин.", show_alert=True)
        return

    # 2. Навигация по сюжету
    if call.data == "game_start":
        text = (f"🛰 **БОРТОВОЙ ЖУРНАЛ: ЗАПИСЬ #1**\n\n"
                f"{username}, шлюз 'Авалона-7' встретил вас ледяным сквозняком. "
                f"Марти замер, его сенсоры сканируют темноту. Перед вами — разбитая панель управления и "
                f"ряд запертых шкафчиков экипажа.\n\n"
                "С чего начнете?")
        
        kb = tele_types.InlineKeyboardMarkup(row_width=1)
        kb.add(
            tele_types.InlineKeyboardButton("🔍 Осмотреть панель", callback_data="game_node_panel"),
            tele_types.InlineKeyboardButton("📦 Вскрыть шкафчики", callback_data="game_node_closet"),
            tele_types.InlineKeyboardButton("🛑 Сбросить прогресс", callback_data="game_reset")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        update_game_progress(user_id, "shluz_entry")

    elif call.data == "game_reset":
        update_game_progress(user_id, "start")
        bot.answer_callback_query(call.id, "Бортовой журнал очищен.")
        call.data = "game_start"
        run_scenario(bot, call)

    # --- ВЕТКА ШКАФЧИКОВ ---
    elif call.data == "game_node_closet":
        text = (f"📦 Внутри шкафчика стенки покрыты замерзшей фиолетовой субстанцией. "
                f"Марти внезапно оскалился и издал низкий рык. Под ворохом одежды лежит "
                f"**серебряный медальон**, пульсирующий в такт вашему сердцу.\n\n"
                f"Что сделаете?")
        
        kb = tele_types.InlineKeyboardMarkup(row_width=1)
        kb.add(
            tele_types.InlineKeyboardButton("🖐 Взять медальон (Риск)", callback_data="game_node_medalion"),
            tele_types.InlineKeyboardButton("🐕 Попросить Марти (Безопасно)", callback_data="game_node_marty_bring"),
            tele_types.InlineKeyboardButton("⬅️ Назад к панели", callback_data="game_start")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        update_game_progress(user_id, "shluz_closet")

        # --- ВЕТКА ПАНЕЛИ (ТАЙМЕР 10 МИН) ---
    elif call.data == "game_node_panel":
        set_game_timer(user_id, 10)
        text = ("⚙️ Марти подключился к панели:\n\n"
                "— Хозяин, тут протокол 'Эхо'. Мне нужно **10 минут**. "
                "Мне кажется, из вентиляции за нами кто-то наблюдает...")
        
        kb = tele_types.InlineKeyboardMarkup(row_width=1)
        # 🟢 ТЕПЕРЬ КНОПКА ВЕДЕТ НА ПРОВЕРКУ ВЗЛОМА
        kb.add(tele_types.InlineKeyboardButton("🔄 Проверить готовность", callback_data="game_check_hack"))
        kb.add(tele_types.InlineKeyboardButton("🏠 На мостик", callback_data="game_back_to_profile"))
        
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        update_game_progress(user_id, "hacking_panel")

    # 🟢 НОВЫЙ УЗЕЛ: РЕЗУЛЬТАТ ВЗЛОМА ПЕРВОЙ ПАНЕЛИ
    elif call.data == "game_check_hack":
        # Если 10 минут НЕ прошли, сработает глобальная проверка в начале файла (return)
        # Если время ВЫШЛО, бот покажет этот текст:
        text = (f"✅ **ВЗЛОМ ЗАВЕРШЕН**\n\n"
                f"Марти довольно вильнул хвостом, и экран панели вспыхнул ровным зеленым светом. "
                f"Тяжелые створки шлюза с лязгом разошлись, открывая путь в темный коридор станции.\n\n"
                f"— Путь свободен, Хозяин. Но сканеры показывают странные колебания температуры впереди.")
        
        kb = tele_types.InlineKeyboardMarkup(row_width=1)
        kb.add(
            tele_types.InlineKeyboardButton("🚶 Войти в коридор", callback_data="game_node_corridor"),
            tele_types.InlineKeyboardButton("📦 Вернуться к шкафчикам", callback_data="game_node_closet")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        update_game_progress(user_id, "shluz_unlocked")

    # 🟢 СЦЕНА: КОРИДОР (Промежуточная точка)
    elif call.data == "game_node_corridor":
        text = (f"🌌 Вы вышли в главный коридор. Здесь царит невесомость и хаос: парят обрывки документов "
                f"и пустые контейнеры. В конце коридора видна дверь в Сектор Зеро.\n\n"
                f"Марти остановился: 'Хозяин, без координат мы не откроем ту дверь. Нужно либо "
                f"вскрыть шкафчики в шлюзе, либо искать другой путь'.")
        
        kb = tele_types.InlineKeyboardMarkup(row_width=1)
        # Если у игрока уже есть координаты (он взял медальон), появится кнопка ввода
        kb.add(tele_types.InlineKeyboardButton("🛰 Ввести координаты (если есть)", callback_data="game_node_panel_with_coords"))
        kb.add(tele_types.InlineKeyboardButton("🔙 Вернуться в шлюз", callback_data="game_start"))
        
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")


    # --- ВЕТКА МЕДАЛЬОНА И КООРДИНАТ ---
    elif call.data == "game_node_medalion":
        text = (f"🖐 Вы касаетесь металла. Зрение вспыхивает белым светом! \n\n"
                f"В шлеме горят координаты: **42.0081 // -19.4402**.\n"
                f"Шепот в динамиках: 'Не ищите нас... оно уже здесь'.\n\n"
                f"Медальон почернел, но данные выжжены в памяти.")
        kb = tele_types.InlineKeyboardMarkup(row_width=1)
        kb.add(
            tele_types.InlineKeyboardButton("🛰 Ввести координаты", callback_data="game_node_panel_with_coords"),
            tele_types.InlineKeyboardButton("🏠 На мостик", callback_data="game_back_to_profile")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    elif call.data == "game_node_panel_with_coords":
        set_game_timer(user_id, 30)
        text = (f"📟 Вы ввели координаты. Терминал залил рубку багровым светом.\n\n"
                f"— Хозяин, идет поиск в архивах 'Стикс'. Вычисление траектории займет **30 минут**.\n"
                f"Магнитные замки шлюза заблокированы.")
        kb = tele_types.InlineKeyboardMarkup()
        kb.add(tele_types.InlineKeyboardButton("🔄 Проверить результат", callback_data="game_check_trajectory"))
        kb.add(tele_types.InlineKeyboardButton("🏠 На мостик", callback_data="game_back_to_profile"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        update_game_progress(user_id, "calculating_trajectory")

    # --- ПРОВЕРКА РЕЗУЛЬТАТА ТРАЕКТОРИИ ---
    elif call.data == "game_check_trajectory":
        text = (f"✅ **РАСЧЕТ ЗАВЕРШЕН**\n\n"
                f"Точка ведет внутрь станции, в скрытый ярус. "
                f"За фальш-панелью открылся проход. Это Сектор Зеро. "
                f"Там нет кислорода.")
        kb = tele_types.InlineKeyboardMarkup(row_width=1)
        kb.add(tele_types.InlineKeyboardButton("🔦 Спуститься в Сектор Зеро", callback_data="game_node_sector_zero"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- СЕКТОР ЗЕРО ---
    elif call.data == "game_node_sector_zero":
        text = (f"🌑 В Секторе Зеро абсолютная темнота. Вы слышите только свое дыхание. "
                f"Марти видит тепловые следы: 'Стены пульсируют теплом'. "
                f"В конце коридора что-то движется.")
        kb = tele_types.InlineKeyboardMarkup(row_width=1)
        kb.add(
            tele_types.InlineKeyboardButton("🔦 Прожектор (Риск)", callback_data="game_node_light_trap"),
            tele_types.InlineKeyboardButton("🛰 Сенсоры Марти (Безопасно)", callback_data="game_node_marty_vision")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- СЕНСОРЫ МАРТИ И КАПИТАН ---
    elif call.data == "game_node_marty_vision":
        text = (f"🐕 Мир окрасился в синий. На потолке висит огромный фиолетовый кокон. "
                f"Внутри — капитан 'Авалона'. Его ДНК перестраивается. "
                f"Рядом стоит старый сейф.")
        kb = tele_types.InlineKeyboardMarkup(row_width=1)
        kb.add(
            tele_types.InlineKeyboardButton("🩺 Осмотреть кокон", callback_data="game_node_open_cocoon"),
            tele_types.InlineKeyboardButton("🗄 Осмотреть сейф", callback_data="game_node_safe_search")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- ДЕТЕКТИВНАЯ НАХОДКА В СЕЙФЕ ---
    elif call.data == "game_node_safe_search":
        text = (f"🗄 Сейф не заперт. Внутри вы находите дневник капитана. Последняя запись: \n\n"
                f"'Сектор Зеро — это не лаборатория. Это убежище. Мы пытались спрятать их здесь от того, "
                f"что пришло вместе с сигналом из Солнечной системы'. \n\n"
                f"Вы понимаете: угроза пришла с Земли.")
        kb = tele_types.InlineKeyboardMarkup(row_width=1)
        kb.add(tele_types.InlineKeyboardButton("🩺 Теперь к кокону...", callback_data="game_node_open_cocoon"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- ОСМОТР КОКОНА (СБОР ОБРАЗЦА) ---
    elif call.data == "game_node_open_cocoon":
        text = (f"🩺 Вы приближаетесь к пульсирующему кокону. Фиолетовые нити похожи на живые нейроны.\n\n"
                f"— Хозяин, если мы возьмем образец этого мха, я смогу его изучить. "
                f"Это может спровоцировать систему, но награда того стоит.")
        kb = tele_types.InlineKeyboardMarkup(row_width=1)
        kb.add(
            tele_types.InlineKeyboardButton("🧪 Собрать образец (Бонус +3 Пыли)", callback_data="game_node_collect_moss"),
            tele_types.InlineKeyboardButton("⚔️ Вскрыть кокон резаком", callback_data="game_node_cut_cocoon")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    elif call.data == "game_node_collect_moss":
        add_xp(user_id, 3, username) 
        text = (f"🧪 Марти срезал образец мха. По всей станции раздался тихий стон.\n\n"
                f"✅ **Бортовой компьютер:** Начислено +3 Звездной пыли!\n\n"
                f"— Мох темнеет, — шепчет Марти. — Мы его разозлили. Действуем быстрее!")
        kb = tele_types.InlineKeyboardMarkup(row_width=1)
        kb.add(tele_types.InlineKeyboardButton("⚔️ Вскрыть кокон немедленно", callback_data="game_node_cut_cocoon"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- ВСКРЫТИЕ КОКОНА И НАХОДКА КЛЮЧ-КАРТЫ ---
    elif call.data == "game_node_cut_cocoon":
        text = (f"⚔️ Лазерный резак рассекает оболочку. Изнутри вываливается тело капитана. "
                f"Он не дышит, но его кожа мерцает холодным светом.\n\n"
                f"Из зажатого кулака капитана выпадает **Золотая Ключ-карта**. На ней выгравирован "
                f"логотип, которого нет в учебниках Академии.\n\n"
                f"— Хозяин! — Марти (male) указывает на дверь в конце зала. — Эта карта от Секретной Лаборатории. "
                f"Если мы зайдем туда, найдем ответы... и не только их.")
        kb = tele_types.InlineKeyboardMarkup(row_width=1)
        kb.add(
            tele_types.InlineKeyboardButton("🧬 Войти в Секретную Лабораторию", callback_data="game_node_secret_lab"),
            tele_types.InlineKeyboardButton("🏃 Бежать к челноку (Конец главы)", callback_data="game_node_escape_chapter")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        update_game_progress(user_id, "keycard_found")

    # --- СЕКРЕТНАЯ ЛАБОРАТОРИЯ (ДВОЙНАЯ НАГРАДА) ---
    elif call.data == "game_node_secret_lab":
        text = (f"🧬 Вы входите в стерильную лабораторию. Здесь хранятся капсулы с "
                f"**Концентрированной Звездной Пылью**. \n\n"
                f"Вы нашли истинную цель экспедиции 'Авалона'. Это не была наука. Это была добыча.\n\n"
                f"Вы забираете контейнеры. Ваша награда в конце главы будет максимальной!")
        kb = tele_types.InlineKeyboardMarkup(row_width=1)
        kb.add(tele_types.InlineKeyboardButton("🚀 Завершить Главу 1", callback_data="game_node_escape_chapter_gold"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- ФИНАЛЫ ГЛАВЫ ---
    elif call.data == "game_node_escape_chapter":
        add_xp(user_id, 20, username)
        text = (f"🏁 **ГЛАВА 1 ЗАВЕРШЕНА**\n\n"
                f"Вы успешно покинули Сектор Зеро. Капитан спасен (?), но вопросов стало больше.\n\n"
                f"💰 Награда за прохождение: **20 Звездной пыли**.\n\n"
                f"Продолжение следует... Следите за обновлениями!")
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="Markdown")

    elif call.data == "game_node_escape_chapter_gold":
        add_xp(user_id, 50, username) # Увеличенная награда за секретную лабу
        text = (f"🏆 **ГЛАВА 1: ЗОЛОТОЙ ФИНАЛ**\n\n"
                f"Вы не только выжили, но и раскрыли тайну 'Авалона'. Контрабанда пыли подтверждена.\n\n"
                f"💰 Награда (с учетом секретов): **50 Звездной пыли**.\n\n"
                f"Продолжение следует... Теперь Академия Орион у вас в долгу.")
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="Markdown")
