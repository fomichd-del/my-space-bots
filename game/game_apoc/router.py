from . import scenario1, scenario2, scenario3, scenario4, scenario5

def route_apoc(bot, call):
    data = call.data
    
    # --- 0. ПОДСТРАХОВКА МЕНЮ ГЛАВ ---
    if data == "apoc_menu":
        from .. import menu
        report, kb = menu.get_apoc_chapters_menu()
        bot.edit_message_text(report, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        return

    # --- 1. РОУТИНГ ПО СЦЕНАРИЯМ ---
    # Вся умная проверка прогресса теперь работает внутри самих сценариев!

    # ГЛАВА 1
    if data in ["apoc_start", "apoc_s1_start", "game_reset_all", "resume_game", "apoc_ch1_completed_screen"] or data.startswith("apoc_n1_") or data.startswith("apoc_craft_"):
        scenario1.run_scenario(bot, call)
        
    # ГЛАВА 2
    elif data in ["apoc_s2_start", "resume_game_2", "game_reset_ch2", "apoc_ch2_completed_screen"] or data.startswith("apoc_s2_"):
        scenario2.run_scenario(bot, call)

    # ГЛАВА 3
    elif data in ["apoc_s3_start", "resume_game_3", "game_reset_ch3", "apoc_ch3_completed_screen"] or data.startswith("apoc_s3_"):
        scenario3.run_scenario(bot, call)

    # ГЛАВА 4
    elif data in ["apoc_s4_start", "resume_game_4", "game_reset_ch4", "apoc_ch4_completed_screen"] or data.startswith("apoc_s4_"):
        scenario4.run_scenario(bot, call)

    # ГЛАВА 5
    elif data in ["apoc_s5_start", "resume_game_5", "game_reset_ch5", "apoc_ch5_completed_screen"] or data.startswith("apoc_s5_"):
        scenario5.run_scenario(bot, call)

    # --- 2. СИСТЕМНЫЕ КНОПКИ ---
    elif data == "apoc_soon":
        bot.answer_callback_query(call.id, "🚧 Эта глава еще в разработке.", show_alert=True)
