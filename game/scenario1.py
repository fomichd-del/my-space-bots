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
        # 🟢 УМНЫЙ СТАРТ: Проверка точки сохранения
        if current_node and current_node not in ["start", "shluz_entry"]:
            # Если глава уже была завершена, не пускаем во вторую петлю выдачи наград
            if current_node == "chapter1_finished":
                text = (f"🛰 **БОРТОВОЙ ЖУРНАЛ**\n\n"
                        f"{username}, Глава 1 официально завершена. Все отчеты сданы, а награды получены.\n"
                        f"Желаете сбросить прогресс и пройти миссию заново (без повторной награды)?")
                kb = tele_types.InlineKeyboardMarkup(row_width=1)
                kb.add(tele_types.InlineKeyboardButton("♻️ Начать заново (Сброс)", callback_data="game_reset"))
                kb.add(tele_types.InlineKeyboardButton("🏠 На мостик", callback_data="game_back_to_profile"))
                bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
                return

            text = (f"🛰 **БОРТОВОЙ ЖУРНАЛ**\n\n"
                    f"{username}, системы восстановили последний сеанс связи.\n"
                    f"Желаете продолжить миссию или начать заново?")
            
            kb = tele_types.InlineKeyboardMarkup(row_width=1)
            
            if current_node == "hacking_panel":
                kb.add(tele_types.InlineKeyboardButton("🔄 Проверить статус взлома", callback_data="game_check_hack"))
            elif current_node == "calculating_trajectory":
                kb.add(tele_types.InlineKeyboardButton("🔄 Проверить расчеты", callback_data="game_check_trajectory"))
            elif current_node == "shluz_unlocked":
                kb.add(tele_types.InlineKeyboardButton("🚶 Войти в коридор", callback_data="game_node_corridor"))
            elif current_node == "keycard_found":
                kb.add(tele_types.InlineKeyboardButton("🧬 В Секретную Лабораторию", callback_data="game_node_secret_lab"))
            else:
                kb.add(tele_types.InlineKeyboardButton("🔄 Обновить статус", callback_data="game_check_hack"))

            kb.add(tele_types.InlineKeyboardButton("♻️ Начать заново (Сброс)", callback_data="game_reset"))
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
            return

        # Обычный старт для новых игроков
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

    # --- ВЕТКА ПАНЕЛИ ---
    elif call.data == "game_node_panel":
        set_game_timer(user_id, 10)
        text = ("⚙️ Марти подключился к панели:\n\n"
                "— Хозяин, тут протокол 'Эхо'. Мне нужно **10 минут**. "
                "Мне кажется, из вентиляции за нами кто-то наблюдает...")
        
        kb = tele_types.InlineKeyboardMarkup(row_width=1)
        kb.add(tele_types.InlineKeyboardButton("🔄 Проверить готовность", callback_data="game_check_hack"))
        kb.add(tele_types.InlineKeyboardButton("🏠 На мостик", callback_data="game_back_to_profile"))
        
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        update_game_progress(user_id, "hacking_panel")

    elif call.data == "game_check_hack":
        text = (f"✅ **ВЗЛОМ ЗАВЕРШЕН**\n\n"
                f"Марти довольно вильнул хвостом, и экран панели вспыхнул ровным зеленым светом. "
                f"Тяжелые створки шлюза с лязгом разошлись, открывая путь в темный коридор станции.\n\n"
                f"— Путь свободен, Хозяин. Но сканеры показывают странные колебания температуры впереди.")
        
        kb = tele_types.InlineKeyboardMarkup(row_width=1)
        kb.add(
            tele_types.InlineKeyboardButton("🚶 Войти в коридор", callback_data="game_node_corridor"),
            tele_types.InlineKeyboardButton("📦 Вернуться к шкафчики", callback_data="game_node_closet")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        update_game_progress(user_id, "shluz_unlocked")

    elif call.data == "game_node_corridor":
        text = (f"🌌 Вы вышли в главный коридор. Здесь царит невесомость и хаос: парят обрывки документов "
                f"и пустые контейнеры. В конце коридора видна дверь в Сектор Зеро.\n\n"
                f"Марти остановился: 'Хозяин, без координат мы не откроем ту дверь. Нужно либо "
                f"вскрыть шкафчики в шлюзе, либо искать другой путь'.")
        
        kb = tele_types.InlineKeyboardMarkup(row_width=1)
        kb.add(tele_types.InlineKeyboardButton("🛰 Ввести координаты (если есть)", callback_data="game_node_panel_with_coords"))
        kb.add(tele_types.InlineKeyboardButton("🔙 Вернуться в шлюз", callback_data="game_start"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    elif call.data == "game_node_medalion" or call.data == "game_node_marty_bring":
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
        update_game_progress(user_id, "shluz_coords_found")

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

    elif call.data == "game_check_trajectory":
        text = (f"✅ **РАСЧЕТ ЗАВЕРШЕН**\n\n"
                f"Точка ведет внутрь станции, в скрытый ярус. "
                f"За фальш-панелью открылся проход. Это Сектор Зеро. "
                f"Там нет кислорода.")
        kb = tele_types.InlineKeyboardMarkup(row_width=1)
        kb.add(tele_types.InlineKeyboardButton("🔦 Спуститься в Сектор Зеро", callback_data="game_node_sector_zero"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

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

    elif call.data == "game_node_light_trap":
        text = (f"💡 Вы щелкаете тумблером прожектора. Яркий луч разрезает мрак...\n\n"
                f"И в ту же секунду фиолетовый мох на стенах начинает стремительно расти в сторону света! "
                f"Щупальца оплетают ваши ноги. Система скафандра выдает каскад ошибок.\n\n"
                f"— Назад! — Марти пытается перегрызть светящиеся нити.\n\n"
                f"Энергия падает! Вам нужно срочно выключить свет, чтобы они отстали.")
        kb = tele_types.InlineKeyboardMarkup(row_width=1)
        kb.add(tele_types.InlineKeyboardButton("🔋 Выключить свет и замереть", callback_data="game_node_sector_zero"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

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

    elif call.data == "game_node_safe_search":
        text = (f"🗄 Сейф не заперт. Внутри вы находите дневник капитана. Последняя запись: \n\n"
                f"'Сектор Зеро — это не лаборатория. Это убежище. Мы пытались спрятать их здесь от того, "
                f"что пришло вместе с сигналом из Солнечной системы'. \n\n"
                f"Вы понимаете: угроза пришла с Земли.")
        kb = tele_types.InlineKeyboardMarkup(row_width=1)
        kb.add(tele_types.InlineKeyboardButton("🩺 Теперь к кокону...", callback_data="game_node_open_cocoon"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

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
        # Простая защита от спама в промежуточном узле
        if current_node == "moss_collected":
            bot.answer_callback_query(call.id, "🧪 Образец уже в контейнере!", show_alert=True)
            return
        
        add_xp(user_id, 3, username) 
        update_game_progress(user_id, "moss_collected")
        text = (f"🧪 Марти срезал образец мха. По всей станции раздался тихий стон.\n\n"
                f"✅ **Бортовой компьютер:** Начислено +3 Звездной пыли!\n\n"
                f"— Мох темнеет, — шепчет Марти. — Мы его разозлили. Действуем быстрее!")
        kb = tele_types.InlineKeyboardMarkup(row_width=1)
        kb.add(tele_types.InlineKeyboardButton("⚔️ Вскрыть кокон немедленно", callback_data="game_node_cut_cocoon"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    elif call.data == "game_node_cut_cocoon":
        text = (f"⚔️ Лазерный резак рассекает оболочку. Изнутри вываливается тело капитана. "
                f"Он не дышит, но его кожа мерцает холодным светом.\n\n"
                f"Из зажатого кулака капитана выпадает **Золотая Ключ-карта**. На ней выгравирован "
                f"логотип, которого нет в учебниках Академии.\n\n"
                f"— Хозяин! — Марти указывает на дверь в конце зала. — Эта карта от Секретной Лаборатории. "
                f"Если мы зайдем туда, найдем ответы... и не только их.")
        kb = tele_types.InlineKeyboardMarkup(row_width=1)
        kb.add(
            tele_types.InlineKeyboardButton("🧬 Войти в Секретную Лабораторию", callback_data="game_node_secret_lab"),
            tele_types.InlineKeyboardButton("🏃 Бежать к челноку (Конец главы)", callback_data="game_node_escape_chapter")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        update_game_progress(user_id, "keycard_found")

    elif call.data == "game_node_secret_lab":
        text = (f"🧬 Вы входите в стерильную лабораторию. Здесь хранятся капсулы с "
                f"**Концентрированной Звездной Пылью**. \n\n"
                f"Вы нашли истинную цель экспедиции 'Авалона'. Это не была наука. Это была добыча.\n\n"
                f"Вы забираете контейнеры. Ваша награда в конце главы будет максимальной!")
        kb = tele_types.InlineKeyboardMarkup(row_width=1)
        kb.add(tele_types.InlineKeyboardButton("🚀 Завершить Главу 1", callback_data="game_node_escape_chapter_gold"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        update_game_progress(user_id, "in_secret_lab")

    # --- ФИНАЛЫ ГЛАВЫ С ЗАЩИТОЙ ОТ ПОВТОРНОГО НАЧИСЛЕНИЯ ---
    elif call.data == "game_node_escape_chapter":
        if current_node != "chapter1_finished":  # 🟢 Проверка: если еще не закончил
            add_xp(user_id, 20, username)
            update_game_progress(user_id, "chapter1_finished") # 🟢 Ставим метку финала
            reward_text = "💰 Награда за прохождение: **20 Звездной пыли**."
        else:
            reward_text = "✨ Вы уже получили награду за эту миссию."

        text = (f"🏁 **ГЛАВА 1 ЗАВЕРШЕНА**\n\n"
                f"Вы успешно покинули Сектор Зеро. Капитан спасен (?), но вопросов стало больше.\n\n"
                f"{reward_text}\n\n"
                f"Продолжение следует... Следите за обновлениями!")
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="Markdown")

    elif call.data == "game_node_escape_chapter_gold":
        if current_node != "chapter1_gold_finished": # 🟢 Проверка на золотой финал
            add_xp(user_id, 50, username)
            update_game_progress(user_id, "chapter1_gold_finished") # 🟢 Метка золотого финала
            reward_text = "💰 Награда (с учетом секретов): **50 Звездной пыли**."
        else:
            reward_text = "✨ Вы уже получили максимальную награду за эту главу."

        text = (f"🏆 **ГЛАВА 1: ЗОЛОТОЙ ФИНАЛ**\n\n"
                f"Вы не только выжили, но и раскрыли тайну 'Авалона'. Контрабанда пыли подтверждена.\n\n"
                f"{reward_text}\n\n"
                f"Продолжение следует... Теперь Академия Орион у вас в долгу.")
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="Markdown")
