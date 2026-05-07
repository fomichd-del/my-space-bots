from game import menu, scenario1, scenario2, scenario3
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

    # Запуск ГЛАВЫ 2 (Требует прохождения ГЛАВЫ 1)
    elif data == "game2_start":
        # Проверяем метки завершения первой главы
        ch1_ready = any(mark in current_node for mark in ["chapter1_finished", "chapter1_gold_finished"])
        
        # Лайфхак для тестов: если статус уже ch2, значит он уже заходил туда
        if ch1_ready or current_node.startswith("ch2_"):
            scenario2.run_scenario(bot, call)
        else:
            bot.answer_callback_query(call.id, "🛑 ДОСТУП ОГРАНИЧЕН! Сначала завершите Главу 1: Протокол 'Эхо'.", show_alert=True)

    # Запуск ГЛАВЫ 3 (Требует прохождения ГЛАВЫ 2)
    elif data == "game3_start":
        # Проверяем метки завершения второй главы
        ch2_ready = any(mark in current_node for mark in ["ch2_done_hero", "ch2_done_escape", "ch2_done_normal"])
        
        if ch2_ready:
            # Когда создадим scenario3, добавим вызов здесь
            bot.answer_callback_query(call.id, "🚀 Подготовка к прыжку в Главу 3...", show_alert=False)
            # scenario3.run_scenario(bot, call)
        else:
            bot.answer_callback_query(call.id, "🔒 ЗАБЛОКИРОВАНО! Пройдите Главу 2, чтобы узнать свою судьбу и открыть Гл. 3.", show_alert=True)

    # --- 3. ОБРАБОТКА АЛЕРТОВ И СЦЕНАРИЕВ ---
    elif data == "game_soon_alert":
        bot.answer_callback_query(call.id, "🚧 Эта глава еще в разработке. Марти полирует обшивку челнока...", show_alert=True)
    
    elif data == "game_locked_alert":
        bot.answer_callback_query(call.id, "🔒 Требуется ранг Капитана. Продолжайте обучение!", show_alert=True)

    elif data.startswith('game_'):
        scenario1.run_scenario(bot, call)
