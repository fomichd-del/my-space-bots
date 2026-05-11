import telebot
from datetime import datetime
from telebot import types as tele_types
from database import get_game_status, update_game_progress, set_game_timer, add_xp

def run_scenario(bot, call):
    user_id = call.from_user.id
    username = call.from_user.first_name if call.from_user.first_name else "Док"
    current_node, timer_end = get_game_status(user_id)
    if current_node is None: current_node = "apoc_start"

    # --- [ АНТИ-ФАРМ СИСТЕМА ] ---
    # Сохраняем все ресурсы и прогресс крафта
    saved_flags = ""
    important_flags = ["_ch1_claimed", "_item_cloth", "_item_parts", "_suit_fixed", "_scanner_fixed"]
    for flag in important_flags:
        if flag in current_node:
            saved_flags += flag

    # 1. ГЛОБАЛЬНАЯ ПРОВЕРКА ТАЙМЕРА
    if timer_end and datetime.now() < timer_end:
        remaining = timer_end - datetime.now()
        mins = int(remaining.total_seconds() // 60)
        bot.answer_callback_query(call.id, f"🧪 Процесс идет... Еще {mins} мин. Марти следит за индикаторами!", show_alert=True)
        return

    # 2. УМНЫЙ СТАРТ (Меню и Локатор)
    if call.data == "apoc_start":
        from . import menu  # Импорт меню из текущей папки
        report, kb = menu.get_apoc_chapters_menu()
        
        # Если игрок уже начал главу, добавляем статус локации
        if "apoc_n1_" in current_node and "_ch1_claimed" not in current_node:
            if "_suit_fixed" in current_node: loc = "Шлюз бункера. Костюм готов."
            elif "searching" in current_node: loc = "Складские стеллажи. Поиск хлама."
            elif "workbench" in current_node: loc = "У верстака. Идет ремонт."
            else: loc = "Жилой отсек бункера."
            report = f"📍 **ПОСЛЕДНЯЯ ГЕОПОЗИЦИЯ:** *{loc}*\n\n" + report

        bot.edit_message_text(report, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        return

    # --- [ ЭТАП 1: ПРОЛОГ В БУНКЕРЕ ] ---
    elif call.data == "apoc_n1_start":
        text = (f"☢️ **ГЛАВА 1: РАДИОМОЛЧАНИЕ**\n\n"
                f"Док {username}, вы в своем убежище. Вентиляция работает на последнем издыхании. "
                f"Марти (той-пудель в тех-жилете) ворчит: 'Док, энергия 3%. Нужно выйти на крышу НИИ к панелям, "
                f"но без герметичного костюма мы не пройдем и десяти метров'.\n\n"
                f"Ваш старый скафандр 'Сталкер' нуждается в серьезном ремонте.")
        
        kb = tele_types.InlineKeyboardMarkup(row_width=1)
        kb.add(
            tele_types.InlineKeyboardButton("🛠 Перейти к Верстаку", callback_data="apoc_n1_workbench"),
            tele_types.InlineKeyboardButton("📦 Искать ткань в ящиках", callback_data="apoc_n1_search_cloth"),
            tele_types.InlineKeyboardButton("⬅️ В меню выбора", callback_data="apoc_start")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        update_game_progress(user_id, "apoc_n1_base" + saved_flags)

    # --- [ ЭТАП 2: ПОИСК ТКАНИ (Таймер 10 мин) ] ---
    elif call.data == "apoc_n1_search_cloth":
        if "_item_cloth" in current_node:
            bot.answer_callback_query(call.id, "📦 Тут пусто. Вся ткань уже на верстаке!", show_alert=True)
            return
        
        set_game_timer(user_id, 10)
        update_game_progress(user_id, "apoc_n1_searching_cloth" + saved_flags)
        text = ("📦 **ПОИСК МАТЕРИАЛОВ**\n\nВы разгребаете завалы старого оборудования. Марти залез в узкую щель под стеллаж...\n\n"
                "Ожидание: **10 минут**.")
        kb = tele_types.InlineKeyboardMarkup().add(tele_types.InlineKeyboardButton("🔄 Проверить добычу", callback_data="apoc_n1_res_cloth"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    elif call.data == "apoc_n1_res_cloth":
        add_xp(user_id, 2, username) 
        update_game_progress(user_id, "apoc_n1_base" + saved_flags + "_item_cloth")
        text = "✅ **УСПЕХ**\n\nНайдено: **Рулон прорезиненной ткани**. Марти довольно машет хвостом. Теперь можно чинить костюм!"
        kb = tele_types.InlineKeyboardMarkup().add(tele_types.InlineKeyboardButton("🛠 К Верстаку", callback_data="apoc_n1_workbench"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ЭТАП 3: ВЕРСТАК (ХАБ КРАФТА) ] ---
    elif call.data == "apoc_n1_workbench":
        has_cloth = "_item_cloth" in current_node
        suit_ok = "_suit_fixed" in current_node
        scanner_ok = "_scanner_fixed" in current_node
        
        text = "🛠 **МАСТЕРСКАЯ БУНКЕРА**\n──────────────────\n"
        kb = tele_types.InlineKeyboardMarkup(row_width=1)

        # Статус Костюма
        if suit_ok:
            text += "🛡 Костюм 'Сталкер': **ГОТОВ**\n"
        else:
            text += f"🛡 Костюм 'Сталкер': {'🔴 Нужна ткань' if not has_cloth else '🟢 Готов к сборке'}\n"
            if has_cloth: kb.add(tele_types.InlineKeyboardButton("⚒ Чинить Костюм (20 мин)", callback_data="apoc_craft_suit"))
            else: kb.add(tele_types.InlineKeyboardButton("🔍 Искать ткань", callback_data="apoc_n1_search_cloth"))

        # Статус Сканера (Появляется только после костюма)
        if suit_ok:
            if scanner_ok:
                text += "📡 Сканер Марти: **ГОТОВ**\n"
            else:
                has_parts = "_item_parts" in current_node
                text += f"📡 Сканер Марти: {'🔴 Нужны детали' if not has_parts else '🟢 Готов к сборке'}\n"
                if has_parts: kb.add(tele_types.InlineKeyboardButton("⚒ Собрать Сканер (15 мин)", callback_data="apoc_craft_scanner"))
                else: kb.add(tele_types.InlineKeyboardButton("📦 Искать детали в НИИ", callback_data="apoc_n1_search_parts"))

        text += f"\nМарти: 'Док,{' мы почти готовы к выходу!' if suit_ok else ' без костюма на улицу ни ногой!'}'"
        
        if suit_ok:
            kb.add(tele_types.InlineKeyboardButton("🚪 ВЫЙТИ НА ПОВЕРХНОСТЬ", callback_data="apoc_n1_surface"))
        
        kb.add(tele_types.InlineKeyboardButton("🔙 Назад", callback_data="apoc_n1_start"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        update_game_progress(user_id, "apoc_n1_workbench" + saved_flags)

    # --- [ ЭТАП 4: ПОИСК ДЕТАЛЕЙ ДЛЯ СКАНЕРА ] ---
    elif call.data == "apoc_n1_search_parts":
        set_game_timer(user_id, 15)
        update_game_progress(user_id, "apoc_n1_searching_parts" + saved_flags)
        text = "📦 **ПОИСК ЭЛЕКТРОНИКИ**\n\nВы разбираете старый осциллограф в углу лаборатории. Марти использует свой нос, чтобы найти медные провода.\n\nНужно **15 минут**."
        kb = tele_types.InlineKeyboardMarkup().add(tele_types.InlineKeyboardButton("🔄 Проверить результат", callback_data="apoc_n1_res_parts"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    elif call.data == "apoc_n1_res_parts":
        add_xp(user_id, 3, username)
        update_game_progress(user_id, "apoc_n1_base" + saved_flags + "_item_parts")
        text = "✅ **НАЙДЕНО**\n\nМикросхемы и линза у вас. Можно собирать сканер для Марти!"
        kb = tele_types.InlineKeyboardMarkup().add(tele_types.InlineKeyboardButton("🛠 К Верстаку", callback_data="apoc_n1_workbench"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- [ ФИНАЛ ГЛАВЫ И ВЫХОД ] ---
    elif call.data == "apoc_n1_surface":
        text = (f"☀️ **ПОВЕРХНОСТЬ: ТИХИЙ ПРИГОРОД**\n\n"
                f"Тяжелая гермодверь со скрипом открывается. Ослепительный свет... \n"
                f"Вы стоите на руинах. Город зарос странными желтыми цветами. Воздух дрожит от зноя.\n\n"
                f"Марти (активируя модуль): 'Док, я вижу движение в торговом центре. Там может быть синтезатор. "
                f"{'Мой новый сканер уже ловит сигнал!' if '_scanner_fixed' in current_node else 'Жаль, сканер мы так и не доделали, придется идти вслепую...'}'")
        
        # Начисление финальной награды (Анти-фарм)
        if "_ch1_claimed" not in current_node:
            reward = 50 if "_scanner_fixed" in current_node else 30
            add_xp(user_id, reward, username)
            update_game_progress(user_id, "apoc_ch1_done" + saved_flags + "_ch1_claimed")
            res_text = f"💰 **НАГРАДА:** {reward} Пыли."
        else:
            res_text = "✨ Глава пройдена. Награда за повтор: 5 Пыли."
            add_xp(user_id, 5, username)

        bot.edit_message_text(f"{text}\n\n{res_text}\n\n**ПРОДОЛЖЕНИЕ СЛЕДУЕТ...**", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

    # Вспомогательная логика продолжения
    elif call.data == "apoc_n1_continue_logic":
        if "searching_cloth" in current_node: call.data = "apoc_n1_res_cloth"
        elif "searching_parts" in current_node: call.data = "apoc_n1_res_parts"
        else: call.data = "apoc_n1_start"
        run_scenario(bot, call)

# --- [ УНИВЕРСАЛЬНАЯ ФУНКЦИЯ КРАФТА ] ---
def handle_craft(bot, call):
    user_id = call.from_user.id
    current_node, _ = get_game_status(user_id)
    
    if "suit" in call.data:
        set_game_timer(user_id, 20)
        update_game_progress(user_id, current_node + "_suit_fixed")
        msg = "⚒ **ИДЕТ КРАФТ КОСТЮМА...**\n\nВы герметизируете швы. Марти подтаскивает инструменты. Зайдите через **20 минут**."
    elif "scanner" in call.data:
        set_game_timer(user_id, 15)
        update_game_progress(user_id, current_node + "_scanner_fixed")
        msg = "⚒ **СБОРКА СКАНЕРА...**\n\nВы паяете микросхемы на ошейнике Марти. Работа тонкая. Нужно **15 минут**."
    
    bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, parse_mode="Markdown")

def reset_game(bot, call):
    update_game_progress(call.from_user.id, "apoc_start")
    bot.answer_callback_query(call.id, "История Дока и Марти обнулена.")
    run_scenario(bot, call)
