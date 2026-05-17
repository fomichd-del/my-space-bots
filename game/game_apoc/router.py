from . import scenario1, scenario2, scenario3, scenario4, scenario5
from database import get_game_status

def route_apoc(bot, call):
    user_id = call.from_user.id
    data = call.data
    
    # Получаем текущий статус из БД
    current_node, _ = get_game_status(user_id)
    if current_node is None:
        current_node = "apoc_start"

    # --- 0. ПОДСТРАХОВКА МЕНЮ ГЛАВ ---
    if data == "apoc_menu":
        from .. import menu
        report, kb = menu.get_apoc_chapters_menu()
        bot.edit_message_text(report, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        return

    # --- 1. СТАРТОВЫЕ КНОПКИ (С БЛОКИРОВКОЙ) ---
    
    # ГЛАВА 1 (Доступна всегда) -> 🟢 ИСПРАВЛЕНО: Добавлен перехват "apoc_start"
    if data == "apoc_start" or data == "apoc_s1_start" or data == "apoc_n1_start":
        scenario1.run_scenario(bot, call)
        
    # ГЛАВА 2
    elif data == "apoc_s2_start":
        if "apoc_ch1_done" in current_node or any(current_node.startswith(p) for p in ["apoc_s2", "apoc_s3", "apoc_s4", "apoc_s5"]):
            scenario2.run_scenario(bot, call)
        else:
            bot.answer_callback_query(call.id, "🛑 Сначала пройдите Главу 1!", show_alert=True)

    # ГЛАВА 3
    elif data == "apoc_s3_start":
        if "apoc_ch2_done" in current_node or any(current_node.startswith(p) for p in ["apoc_s3", "apoc_s4", "apoc_s5"]):
            scenario3.run_scenario(bot, call)
        else:
            bot.answer_callback_query(call.id, "🔒 Пройдите Главу 2, чтобы открыть эту.", show_alert=True)

    # ГЛАВА 4
    elif data == "apoc_s4_start":
        if "apoc_ch3_done" in current_node or any(current_node.startswith(p) for p in ["apoc_s4", "apoc_s5"]):
            scenario4.run_scenario(bot, call)
        else:
            bot.answer_callback_query(call.id, "🔒 Сначала завершите Главу 3.", show_alert=True)

    # ГЛАВА 5
    elif data == "apoc_s5_start":
        if "apoc_ch4_done" in current_node or current_node.startswith("apoc_s5"):
            scenario5.run_scenario(bot, call)
        else:
            bot.answer_callback_query(call.id, "🔒 Финал заблокирован. Пройдите Главу 4.", show_alert=True)

    # --- 2. ВНУТРЕННИЕ ШАГИ ИГРЫ (ОБРАБОТКА ЭТАПОВ) ---
    elif data.startswith("apoc_s5_"):
        scenario5.run_scenario(bot, call)
        
    elif data.startswith("apoc_s4_"):
        scenario4.run_scenario(bot, call)
        
    elif data.startswith("apoc_s3_"):
        scenario3.run_scenario(bot, call)
        
    elif data.startswith("apoc_s2_"):
        scenario2.run_scenario(bot, call)
        
    elif data.startswith("apoc_s1_") or data.startswith("apoc_n1_") or data.startswith("apoc_craft_"):
        scenario1.run_scenario(bot, call)

    # --- 3. СИСТЕМНЫЕ КНОПКИ ---
    elif data == "apoc_reset":
        scenario1.reset_game(bot, call)
        
    elif data == "apoc_soon":
        bot.answer_callback_query(call.id, "🚧 Эта глава еще в разработке.", show_alert=True)
