from game import menu, scenario1, scenario2, scenario3, scenario4, scenario5 # 🟢 Проверь, что импорт scenario3 тут есть
from database import get_game_status

def route_game(bot, call):
    user_id = call.from_user.id
    data = call.data
    
    # Получаем текущий статус прогресса из базы
    current_node, _ = get_game_status(user_id)
    if current_node is None:
        current_node = "start"

    # --- 1. НАВИГАЦИЯ ПО МЕНЮ ---
    if data == "game_main_menu":
        report, kb = menu.get_main_games_menu()
        bot.edit_message_text(report, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
    
    elif data == "game_select_diary":
        report, kb = menu.get_diary_chapters_menu()
        bot.edit_message_text(report, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- 2. ПРОВЕРКА ДОСТУПА К ГЛАВАМ (БЛОКИРОВКИ) ---

    # Запуск ГЛАВЫ 2
    elif data == "game2_start":
        ch1_ready = any(mark in current_node for mark in ["chapter1_finished", "chapter1_gold_finished"])
        if ch1_ready or current_node.startswith("ch2_"):
            scenario2.run_scenario(bot, call)
        else:
            bot.answer_callback_query(call.id, "🛑 ДОСТУП ОГРАНИЧЕН! Сначала завершите Главу 1.", show_alert=True)

    # Запуск ГЛАВЫ 3 (🟢 ОБНОВЛЕНО)
    elif data == "game3_start":
        # Проверяем метки завершения второй главы
        ch2_ready = any(mark in current_node for mark in ["ch2_done_hero", "ch2_done_escape", "ch2_done_normal"])
        
        # Если 2 глава пройдена ИЛИ пилот уже находится внутри 3 главы (для перезаходов)
        if ch2_ready or current_node.startswith("ch3_"):
            bot.answer_callback_query(call.id, "🚀 Прыжок в гиперпространство...")
            scenario3.run_scenario(bot, call) # 🟢 АКТИВИРУЕМ ВЫЗОВ
        else:
            bot.answer_callback_query(call.id, "🔒 ЗАБЛОКИРОВАНО! Пройдите Главу 2, чтобы открыть Гл. 3.", show_alert=True)

    # --- 3. ОБРАБОТКА АЛЕРТОВ И СЦЕНАРИЕВ ---
    elif data == "game_soon_alert":
        bot.answer_callback_query(call.id, "🚧 Эта глава еще в разработке. Марти полирует обшивку...", show_alert=True)
    
    elif data == "game_locked_alert":
        bot.answer_callback_query(call.id, "🔒 Требуется ранг Капитана. Продолжайте обучение!", show_alert=True)

    # 🟢 ОБРАБОТКА ВСЕХ КНОПОК пятой ГЛАВЫ
    elif data.startswith('game5_'):
        scenario3.run_scenario(bot, call)
    
    # 🟢 ОБРАБОТКА ВСЕХ КНОПОК четвертой ГЛАВЫ
    elif data.startswith('game4_'):
        scenario3.run_scenario(bot, call)
    
    # 🟢 ОБРАБОТКА ВСЕХ КНОПОК ТРЕТЬЕЙ ГЛАВЫ
    elif data.startswith('game3_'):
        scenario3.run_scenario(bot, call)

    # Обработка второй главы
    elif data.startswith('game2_'):
        scenario2.run_scenario(bot, call)

    # Обработка первой главы
    elif data.startswith('game_'):
        scenario1.run_scenario(bot, call)
