from . import scenario1
from database import get_game_status

def route_apoc(bot, call):
    user_id = call.from_user.id
    data = call.data
    
    # Получаем текущий статус из БД
    current_node, _ = get_game_status(user_id)
    if current_node is None:
        current_node = "apoc_start"

    # Навигация по первой главе
    if data == "apoc_start" or data.startswith("apoc_n1_"):
        scenario1.run_scenario(bot, call)
        
    # Обработка крафта
    elif data.startswith("apoc_craft_"):
        scenario1.handle_craft(bot, call)

    # Сброс прогресса конкретно этой игры
    elif data == "apoc_reset":
        scenario1.reset_game(bot, call)
