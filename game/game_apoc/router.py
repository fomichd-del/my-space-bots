from . import scenario1
from database import get_game_status

def route_apoc(bot, call):
    user_id = call.from_user.id
    data = call.data
    
    # Получаем текущий статус
    current_node, _ = get_game_status(user_id)
    if current_node is None:
        current_node = "apoc_start"

    # --- ЛОГИКА ПЕРЕХОДОВ ---
    if data == "apoc_start":
        scenario1.run_scenario(bot, call)
    
    # Обработка всех узлов первой главы
    elif data.startswith("apoc_n1_"): # n1 = node chapter 1
        scenario1.run_scenario(bot, call)
        
    # Обработка крафта
    elif data.startswith("apoc_craft_"):
        scenario1.handle_craft(bot, call)

    # Обработка сброса
    elif data == "apoc_reset":
        scenario1.reset_game(bot, call)
