from game import scenario1, scenario2 # Сюда будешь добавлять новые сценарии

def route_game(bot, call):
    """
    Универсальный распределитель игровых запросов.
    """
    data = call.data
    
    # Глава 2 (Все кнопки начинаются на game2_)
    if data.startswith('game2_'):
        scenario2.run_scenario(bot, call)
        
    # Глава 1 (Все кнопки начинаются на game_ и не относятся ко 2 главе)
    elif data.startswith('game_'):
        scenario1.run_scenario(bot, call)
        
    # Сюда в будущем добавишь: elif data.startswith('game3_'): ...
