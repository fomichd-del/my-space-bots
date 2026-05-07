from game import menu, scenario1, scenario2

def route_game(bot, call):
    data = call.data
    
    # 1. Навигация по меню
    if data == "game_main_menu":
        report, kb = menu.get_main_games_menu()
        bot.edit_message_text(report, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
    
    elif data == "game_select_diary":
        report, kb = menu.get_diary_chapters_menu()
        bot.edit_message_text(report, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # 🟢 2. УВЕДОМЛЕНИЯ ДЛЯ ЗАКРЫТЫХ ГЛАВ (НОВЫЕ ПУНКТЫ)
    elif data == "game_soon_alert":
        bot.answer_callback_query(call.id, "🚧 Эта глава еще находится в разработке. Марти обрабатывает данные...", show_alert=True)
    
    elif data == "game_locked_alert":
        bot.answer_callback_query(call.id, "🔒 Доступ заблокирован. Требуется ранг Капитана и выше.", show_alert=True)

    # 3. ЗАПУСК СЦЕНАРИЕВ
    elif data.startswith('game2_'):
        scenario2.run_scenario(bot, call)
        
    elif data.startswith('game_'):
        scenario1.run_scenario(bot, call)
