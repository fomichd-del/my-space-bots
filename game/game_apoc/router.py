from . import scenario1, scenario2, scenario3, scenario4, scenario5
from database import get_game_status

def route_apoc(bot, call):
    user_id = call.from_user.id
    data = call.data
    
    # Распределяем сигналы по главам
    if data.startswith("apoc_n1_") or data.startswith("apoc_craft_"):
        scenario1.run_scenario(bot, call)
        
    elif data.startswith("apoc_s2_"):
        scenario2.run_scenario(bot, call)
        
    elif data.startswith("apoc_s3_"):
        scenario3.run_scenario(bot, call)
        
    elif data.startswith("apoc_s4_"):
        scenario4.run_scenario(bot, call)
        
    elif data.startswith("apoc_s5_") or data == "apoc_s5_start":
        scenario5.run_scenario(bot, call)

    elif data == "apoc_reset":
        scenario1.reset_game(bot, call)
        
    elif data == "apoc_soon":
        bot.answer_callback_query(call.id, "🚧 Эта глава еще в разработке.", show_alert=True)
