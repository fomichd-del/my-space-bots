from telebot import types as tele_types

def get_games_menu():
    report = (
        "🎮 **ИГРОВОЙ ОТСЕК АКАДЕМИИ**\n\n"
        "Здесь собраны интерактивные модули. Выбери миссию для погружения:\n\n"
        "🚀 **Глава 1: Дневник юного космонавта**\n"
        "Детективное расследование на станции 'Авалон-7'.\n"
        "💰 Награда: до **50 ед. Звездной пыли**.\n\n"
        "🪐 **Глава 2: Тень Земли**\n"
        "Допрос в Отсеке Безопасности Академии. Твои секреты под угрозой.\n"
        "💰 Награда: *Данные засекречены*."
    )
    
    kb = tele_types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        tele_types.InlineKeyboardButton("🚀 Начать Главу 1", callback_data="game_start"),
        tele_types.InlineKeyboardButton("🪐 Начать Главу 2", callback_data="game2_start")
    )
    
    return report, kb
