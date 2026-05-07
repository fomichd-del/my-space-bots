from telebot import types as tele_types

def get_games_menu():
    report = (
        "🎮 **ИГРОВОЙ ОТСЕК АКАДЕМИИ**\n\n"
        "Выбери доступную миссию:\n\n"
        "🚀 **Глава 1: Дневник юного космонавта**\n"
        "Станция 'Авалон-7'.\n\n"
        "🪐 **Глава 2: Тень Земли**\n"
        "Допрос в Академии."
    )
    kb = tele_types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        tele_types.InlineKeyboardButton("🚀 Начать Главу 1", callback_data="game_start"),
        tele_types.InlineKeyboardButton("🪐 Начать Главу 2", callback_data="game2_start")
    )
    return report, kb
