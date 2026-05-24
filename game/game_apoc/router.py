from . import scenario1, scenario2, scenario3, scenario4, scenario5
from database import get_game_status # 🟢 ДОБАВЛЕН ИМПОРТ ДЛЯ ЧТЕНИЯ БАЗЫ

def route_apoc(bot, call):
    data = call.data
    user_id = call.from_user.id
    
    # --- 0. ПОДСТРАХОВКА МЕНЮ ГЛАВ ---
    if data == "apoc_menu":
        from .. import menu
        report, kb = menu.get_apoc_chapters_menu()
        bot.edit_message_text(report, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
        return

    # 🟢 --- 1. УМНЫЙ ПЕРЕХВАТ КНОПКИ "ПРОДОЛЖИТЬ" --- 🟢
    # Узнаем реальное сохранение игрока и отправляем его в правильный сценарий,
    # даже если он нажал "Продолжить" в меню совершенно другой главы.
    apoc_resumes = ["resume_game", "resume_game_2", "resume_game_3", "resume_game_4", "resume_game_5"]
    
    if data in apoc_resumes:
        raw_node, _ = get_game_status(user_id)
        if not raw_node: 
            raw_node = "apoc_start"
        
        # Вытаскиваем чистую локацию без флагов инвентаря
        loc = raw_node.split('|')[0]
        
        # Магия: Подменяем нажатую кнопку на реальную локацию сохранения
        call.data = loc  
        data = loc       
        
        try: bot.answer_callback_query(call.id, "🔄 Экспедиция продолжена!")
        except: pass

    # --- 2. РОУТИНГ ПО СЦЕНАРИЯМ ---
    # Теперь переменная 'data' содержит точную локацию (например apoc_s4_15).
    # Роутер безошибочно направит её в нужный файл!

    # ГЛАВА 1
    if data in ["apoc_start", "apoc_s1_start", "game_reset_all", "apoc_ch1_completed_screen"] or data.startswith("apoc_n1_") or data.startswith("apoc_craft_"):
        scenario1.run_scenario(bot, call)
        
    # ГЛАВА 2
    elif data in ["apoc_s2_start", "game_reset_ch2", "apoc_ch2_completed_screen"] or data.startswith("apoc_s2_"):
        scenario2.run_scenario(bot, call)

    # ГЛАВА 3
    elif data in ["apoc_s3_start", "game_reset_ch3", "apoc_ch3_completed_screen"] or data.startswith("apoc_s3_"):
        scenario3.run_scenario(bot, call)

    # ГЛАВА 4
    elif data in ["apoc_s4_start", "game_reset_ch4", "apoc_ch4_completed_screen"] or data.startswith("apoc_s4_"):
        scenario4.run_scenario(bot, call)

    # ГЛАВА 5
    elif data in ["apoc_s5_start", "game_reset_ch5", "apoc_ch5_completed_screen", "apoc_game_completed_screen"] or data.startswith("apoc_s5_"):
        scenario5.run_scenario(bot, call)

    # --- 3. СИСТЕМНЫЕ КНОПКИ ---
    elif data == "apoc_soon":
        try: bot.answer_callback_query(call.id, "🚧 Эта глава еще в разработке.", show_alert=True)
        except: pass
