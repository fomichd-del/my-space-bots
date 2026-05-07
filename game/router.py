from game import menu, scenario1, scenario2

def route_game(bot, call):
    data = call.data
    
    # --- НАВИГАЦИЯ ПО МЕНЮ ---
    
    # Показать главный список игр
    if data == "game_main_menu":
        report, kb = menu.get_main_games_menu()
        bot.edit_message_text(report, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
    
    # Показать главы игры "Дневник"
    elif data == "select_game_diary":
        report, kb = menu.get_diary_chapters_menu()
        bot.edit_message_text(report, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")

    # --- ЗАПУСК СЦЕНАРИЕВ ---

    elif data.startswith('game2_'):
        scenario2.run_scenario(bot, call)
        
    elif data.startswith('game_'):
        scenario1.run_scenario(bot, call)
