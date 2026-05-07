from telebot import types as tele_types

# 1. ГЛАВНОЕ МЕНЮ ИГР (Список всех игр)
def get_main_games_menu():
    report = (
        "🎮 **ИГРОВОЙ ОТСЕК АКАДЕМИИ**\n\n"
        "Пилот, выбери симуляцию для погружения. Каждая игра — это отдельная история с уникальными наградами."
    )
    kb = tele_types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        tele_types.InlineKeyboardButton("🚀 Дневник юного космонавта", callback_data="select_game_diary"),
        # Сюда в будущем: tele_types.InlineKeyboardButton("☄️ Охотники за астероидами", callback_data="select_game_asteroids")
    )
    return report, kb

# 2. МЕНЮ ГЛАВ (Для игры "Дневник юного космонавта")
def get_diary_chapters_menu():
    report = (
        "🚀 **ДНЕВНИК ЮНОГО КОСМОНАВТА**\n\n"
        "Сага о заброшенной станции 'Авалон-7' и тайнах Сектора Зеро.\n"
        "Выбери доступную часть:"
    )
    kb = tele_types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        tele_types.InlineKeyboardButton("📁 Глава 1: Протокол 'Эхо'", callback_data="game_start"),
        tele_types.InlineKeyboardButton("🪐 Глава 2: Тень Земли", callback_data="game2_start"),
        tele_types.InlineKeyboardButton("⬅️ Назад к списку игр", callback_data="game_main_menu")
    )
    return report, kb
