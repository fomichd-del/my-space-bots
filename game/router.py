from . import menu, scenario1, scenario2, scenario3, scenario4, scenario5
from .game_apoc import router as apoc_router # 🟢 Импорт роутера второй игры
from database import get_game_status

def route_game(bot, call):
    user_id = call.from_user.id
    data = call.data
    
    # 🟢 --- 1. ОБРАБОТКА ВТОРОЙ ИГРЫ (ЧИСТОЕ НЕБО) ---
    # Список ВСЕХ кнопок возврата и сброса для ВСЕХ глав Апокалипсиса
    apoc_system_buttons = [
        "resume_game", "game_reset_all",
        "resume_game_2", "game_reset_ch2",
        "resume_game_3", "game_reset_ch3",
        "resume_game_4", "game_reset_ch4",
        "resume_game_5", "game_reset_ch5"
    ]
    
    # Перехватываем сигналы, если они начинаются на apoc_ ИЛИ находятся в списке системных кнопок
    if data.startswith("apoc_") or data in apoc_system_buttons:
        if data == "apoc_menu":
            # Открываем меню глав второй игры
            report, kb = menu.get_apoc_chapters_menu()
            bot.edit_message_text(report, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        else:
            # Передаем управление внутрь папки game_apoc для игрового процесса
            apoc_router.route_apoc(bot, call)
        return # Обязательный выход, чтобы не идти в логику первой игры

    # 🚀 --- 2. ЛОГИКА ПЕРВОЙ ИГРЫ (ДНЕВНИК КОСМОНАВТА) ---
    # Получаем текущий статус прогресса из базы
    current_node, _ = get_game_status(user_id)
    if current_node is None:
        current_node = "start"

    # --- НАВИГАЦИЯ ПО ГЛАВНОМУ МЕНЮ ---
    if data == "game_main_menu":
        report, kb = menu.get_main_games_menu()
        bot.edit_message_text(report, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        return 
    
    elif data == "game_select_diary":
        report, kb = menu.get_diary_chapters_menu()
        bot.edit_message_text(report, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        return

    # --- ЗАПУСК ГЛАВ ПЕРВОЙ ИГРЫ (С ПРОВЕРКОЙ ПРОГРЕССА) ---

    # ГЛАВА 2
    elif data == "game2_start":
        ch1_ready = any(mark in current_node for mark in ["chapter1_finished", "chapter1_gold_finished"])
        if ch1_ready or current_node.startswith("ch2_"):
            scenario2.run_scenario(bot, call)
        else:
            bot.answer_callback_query(call.id, "🛑 Сначала завершите Главу 1!", show_alert=True)

    # ГЛАВА 3
    elif data == "game3_start":
        ch2_ready = any(mark in current_node for mark in ["ch2_done_hero", "ch2_done_escape", "ch2_done_normal"])
        if ch2_ready or current_node.startswith("ch3_"):
            scenario3.run_scenario(bot, call)
        else:
            bot.answer_callback_query(call.id, "🔒 Пройдите Главу 2, чтобы открыть Гл. 3.", show_alert=True)

    # ГЛАВА 4
    elif data == "game4_start":
        ch3_ready = any(mark in current_node for mark in ["ch3_done_true", "ch3_done_bad"])
        if ch3_ready or current_node.startswith("ch4_"):
            scenario4.run_scenario(bot, call)
        else:
            bot.answer_callback_query(call.id, "🔒 Глава 4 заблокирована. Пройдите Гл. 3.", show_alert=True)

    # ГЛАВА 5
    elif data == "game5_start":
        ch4_ready = any(mark in current_node for mark in ["ch4_done_hero", "ch4_done_escape", "ch4_done_dark"])
        if ch4_ready or current_node.startswith("ch5_"):
            scenario5.run_scenario(bot, call)
        else:
            bot.answer_callback_query(call.id, "🔒 Финал закрыт. Пройдите Гл. 4.", show_alert=True)

    # --- ОБРАБОТКА ВСЕХ ВНУТРЕННИХ КНОПОК ГЛАВ ПЕРВОЙ ИГРЫ ---

    # ГЛАВА 5 
    elif data.startswith('game5_'):
        scenario5.run_scenario(bot, call)
    
    # ГЛАВА 4 
    elif data.startswith('game4_'):
        scenario4.run_scenario(bot, call)
    
    # ГЛАВА 3
    elif data.startswith('game3_'):
        scenario3.run_scenario(bot, call)

    # ГЛАВА 2
    elif data.startswith('game2_'):
        scenario2.run_scenario(bot, call)

    # ГЛАВА 1 (Общий префикс 'game_')
    elif data.startswith('game_'):
        scenario1.run_scenario(bot, call)

    # Обработка заглушек
    elif data == "game_soon_alert":
        bot.answer_callback_query(call.id, "🚧 Эта глава еще в разработке.", show_alert=True)
